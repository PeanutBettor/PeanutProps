"""Combine team volume and player share into a projected mean, then a count distribution.

    mu = share * REF * (team_passes_hat / REF) ** beta_role * minutes / 90

With beta_role = 1 this is team_passes_hat x share-while-on-pitch x minutes/90. Minutes are an INPUT
(prompt 3 builds the minutes model); the backtest feeds actual minutes.
"""
from __future__ import annotations

import hashlib
import inspect
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from . import dist
from .data import History
from .share import REF, ShareParams, estimate_shares
from .team import TeamModel, TeamParams, TeamRatings

MODEL_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class DistParams:
    family: str = "nbinom"           # "poisson" | "nbinom"
    size: tuple = (("ALL", 20.0),)   # NB size r; ("ALL", r) or one entry per role

    def size_of(self, role: str):
        if self.family == "poisson":
            return None
        s = dict(self.size)
        return s.get(role, s.get("ALL"))


@dataclass(frozen=True)
class ModelParams:
    team: TeamParams = field(default_factory=TeamParams)
    share: ShareParams = field(default_factory=ShareParams)
    dist: DistParams = field(default_factory=DistParams)

    def to_json(self) -> dict:
        return {"team": asdict(self.team), "share": {**asdict(self.share), "beta": dict(self.share.beta)},
                "dist": {"family": self.dist.family, "size": dict(self.dist.size)}}

    @classmethod
    def from_json(cls, d: dict) -> "ModelParams":
        sh = dict(d["share"])
        sh["beta"] = tuple((r, float(sh["beta"][r])) for r in ("GK", "DEF", "MID", "FWD"))
        return cls(TeamParams(**d["team"]), ShareParams(**sh),
                   DistParams(d["dist"]["family"], tuple((k, float(v)) for k, v in d["dist"]["size"].items())))


# Files whose code determines a projection. Reporting/CLI code is deliberately excluded.
VERSIONED_FILES = ("data.py", "team.py", "share.py", "dist.py", "project.py")


def model_version(params: ModelParams) -> str:
    """Hash of the parameters and the source of every file that affects a projection."""
    h = hashlib.sha256(json.dumps(params.to_json(), sort_keys=True).encode())
    for f in (MODEL_DIR / n for n in VERSIONED_FILES):
        h.update(f.name.encode())
        h.update(f.read_bytes())
    return h.hexdigest()[:12]


def team_projection(hist: History, targets: pd.DataFrame, season: str, team_model: TeamModel,
                    ratings: TeamRatings | None = None) -> pd.DataFrame:
    """targets: one row per team-match (team, opponent, is_home, kickoff)."""
    hist.check_target(targets["kickoff"])
    r = ratings or team_model.ratings(hist, season)
    out = targets.copy()
    out["team_proj"] = [r.expected(t, o, h) for t, o, h in zip(out["team"], out["opponent"], out["is_home"])]
    out["team_n_matches"] = out["team"].map(r.n_matches).fillna(0).astype(int)
    return out


def project_players(hist: History, targets: pd.DataFrame, season: str, team_model: TeamModel,
                    params: ModelParams, team_proj: pd.DataFrame | None = None) -> pd.DataFrame:
    """targets: player_id, team, opponent, is_home, role, kickoff, match_id, minutes (input).

    Returns targets with team_proj, share, mu. Rows that cannot be projected get mu = NaN and a reason.
    """
    hist.check_target(targets["kickoff"])
    if team_proj is None:
        tkeys = targets[["match_id", "team", "opponent", "is_home", "kickoff"]].drop_duplicates()
        team_proj = team_projection(hist, tkeys, season, team_model)
    out = targets.merge(team_proj[["match_id", "team", "team_proj", "team_n_matches"]], on=["match_id", "team"], how="left")
    sh = estimate_shares(hist, out, season, params.share)
    for c in ("share", "share_long", "role_prior", "n_apps_team", "raw_share"):
        out[c] = sh[c].to_numpy()
    beta = out["role"].map(dict(params.share.beta))
    out["mu"] = out["share"] * REF * (out["team_proj"] / REF) ** beta * out["minutes"] / 90.0
    out["no_proj_reason"] = np.select(
        [out["role"].isna(), out["team_proj"].isna(), out["share"].isna()],
        ["role_missing", "team_volume_unavailable", "share_unavailable"], default="")
    out.loc[out["no_proj_reason"] != "", "mu"] = np.nan
    return out


def add_distribution(df: pd.DataFrame, dp: DistParams, lines=(20.5, 30.5, 40.5, 50.5, 60.5, 70.5)) -> pd.DataFrame:
    out = df.copy()
    ok = out["mu"].notna() & (out["mu"] > 0)
    size = out["role"].map(dp.size_of) if dp.family == "nbinom" else None
    for c in ("median", "p10", "p90"):
        out[c] = np.nan
    if ok.any():
        r = None if size is None else size[ok].to_numpy(float)
        s = dist.summary(out.loc[ok, "mu"].to_numpy(), r)
        for c in ("median", "p10", "p90"):
            out.loc[ok, c] = s[c]
        for L in lines:
            out.loc[ok, f"p_over_{L}"] = dist.prob_over(L, out.loc[ok, "mu"].to_numpy(), r)
    out["nb_size"] = size if size is not None else np.inf
    return out


# ---- baselines ---------------------------------------------------------------------------------

def baselines(hist: History, targets: pd.DataFrame, season: str) -> pd.DataFrame:
    """Passes per 90 x (minutes / 90): season-to-date, last 5 and last 10 appearances (any team)."""
    hist.check_target(targets["kickoff"])
    app = hist.app
    ids = targets["player_id"].unique()
    ph = app[app["player_id"].isin(ids)].sort_values("kickoff")
    out = targets[["player_id"]].copy()
    std = ph[ph["season"] == season].groupby("player_id")[["passes", "minutes"]].sum()
    per90 = {"base_std": std["passes"] / std["minutes"] * 90}
    for n in (5, 10):
        lastn = ph.groupby("player_id").tail(n).groupby("player_id")[["passes", "minutes"]].sum()
        per90[f"base_last{n}"] = lastn["passes"] / lastn["minutes"] * 90
    for k, s in per90.items():
        out[k] = out["player_id"].map(s).to_numpy() * targets["minutes"].to_numpy() / 90.0
    return out.drop(columns=["player_id"])
