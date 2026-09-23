"""Player share of team passes while on the pitch.

For a past appearance i of a player at his current team:
    exposure_i = REF * (team_total_i / REF) ** beta_role * minutes_i / 90
    share_i    = passes_i / exposure_i
With beta_role = 1 this is exactly passes / (team passes x fraction of the match played), i.e. the
player's share of team passes while he was on the pitch (team passes are assumed spread evenly over
the match; per-minute team passes are not in the data). beta_role < 1 lets a role's passes scale less
than 1:1 with team volume (goalkeepers, for example); beta is chosen by validation.

Empirical-Bayes shrinkage, all in "full-match equivalents" of exposure (1 unit = REF team passes):

    role prior   R = (team's role-group passes + k_league * REF * G_role) / (team's role exposure + k_league * REF)
                     G_role = league-wide share for the role (current + previous season)
    long-term    L = (sum m_i (1 - decay^k_i) y_i + k_role * REF * R) / (sum m_i (1 - decay^k_i) e_i + k_role * REF)
    recent       S = (sum m_i decay^k_i y_i + k_long * REF * L) / (sum m_i decay^k_i e_i + k_long * REF)

m_i = 1 for appearances of >= 20 minutes and `short_weight` otherwise; k_i = appearances ago (0 = latest).
Each appearance's weight is split between the layers (decay^k to recent, 1 - decay^k to long-term), so no
appearance is counted twice: a player with one appearance has L = R and S is his single match shrunk
toward the role prior; a player with many appearances has L near his own long-run rate.
Only appearances for the player's *current* team are used, so a transfer resets the player to the new
team's role prior R and his share then updates from there.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np
import pandas as pd

from .data import History, ROLES, previous_season

REF = 450.0  # reference team passes per match (roughly the league mean)
SHORT_MINUTES = 20


@dataclass(frozen=True)
class ShareParams:
    decay: float = 0.9
    k_long: float = 3.0
    k_role: float = 3.0
    k_league: float = 5.0
    short_weight: float = 0.5
    beta: tuple = (("GK", 1.0), ("DEF", 1.0), ("MID", 1.0), ("FWD", 1.0))

    def beta_of(self, role: str) -> float:
        return dict(self.beta)[role]

    def with_beta(self, role: str, value: float) -> "ShareParams":
        b = dict(self.beta)
        b[role] = value
        return ShareParams(self.decay, self.k_long, self.k_role, self.k_league, self.short_weight,
                           tuple((r, b[r]) for r in ROLES))


def exposure(team_total, minutes, beta) -> np.ndarray:
    return REF * (np.asarray(team_total, float) / REF) ** np.asarray(beta, float) * np.asarray(minutes, float) / 90.0


def estimate_shares(hist: History, targets: pd.DataFrame, season: str, p: ShareParams) -> pd.DataFrame:
    """Return targets with columns share, share_long, role_prior, n_apps_team, n_apps_recent_weight.

    targets needs: player_id, team, role.
    """
    app = hist.app
    out = targets[["player_id", "team", "role"]].copy()
    beta_map = dict(p.beta)

    # --- league and team role priors: current + previous season ---------------------------------
    recent_seasons = {season, previous_season(season)}
    pool = app[app["season"].isin(recent_seasons)]
    if len(pool):
        e_pool = exposure(pool["team_total"], pool["minutes"], pool["role"].map(beta_map))
        m_pool = np.where(pool["minutes"] >= SHORT_MINUTES, 1.0, p.short_weight)
        tmp = pd.DataFrame({"team": pool["team"].to_numpy(), "role": pool["role"].to_numpy(),
                            "y": m_pool * pool["passes"].to_numpy(), "e": m_pool * e_pool})
        league = tmp.groupby("role")[["y", "e"]].sum()
        G = (league["y"] / league["e"]).to_dict()
        tr = tmp.groupby(["team", "role"])[["y", "e"]].sum()
    else:
        G, tr = {}, pd.DataFrame(columns=["y", "e"])
    kl = p.k_league * REF

    def role_prior(team, role):
        g = G.get(role, np.nan)
        if (team, role) in tr.index:
            y, e = tr.loc[(team, role)]
            return (y + kl * g) / (e + kl)
        return g

    out["role_prior"] = [role_prior(t, r) for t, r in zip(out["team"], out["role"])]

    # --- player history at current team ---------------------------------------------------------
    keys = out[["player_id", "team"]].drop_duplicates()
    ph = app.merge(keys, on=["player_id", "team"], how="inner")
    if len(ph):
        ph = ph.sort_values("kickoff")
        e = exposure(ph["team_total"], ph["minutes"], ph["role"].map(beta_map))
        m = np.where(ph["minutes"] >= SHORT_MINUTES, 1.0, p.short_weight)
        rank = ph.groupby(["player_id", "team"]).cumcount(ascending=False).to_numpy()
        w = m * p.decay ** rank
        lw = m - w  # = m * (1 - decay**rank)
        agg = pd.DataFrame({"player_id": ph["player_id"].to_numpy(), "team": ph["team"].to_numpy(),
                            "ly": lw * ph["passes"].to_numpy(), "le": lw * e,
                            "ry": w * ph["passes"].to_numpy(), "re": w * e,
                            "ay": m * ph["passes"].to_numpy(), "ae": m * e, "n": 1}) \
            .groupby(["player_id", "team"], as_index=False).sum()
        out = out.merge(agg, on=["player_id", "team"], how="left")
    else:
        for c in ("ly", "le", "ry", "re", "ay", "ae", "n"):
            out[c] = np.nan
    for c in ("ly", "le", "ry", "re", "ay", "ae", "n"):
        out[c] = out[c].fillna(0.0)
    kr, kg = p.k_role * REF, p.k_long * REF
    out["share_long"] = (out["ly"] + kr * out["role_prior"]) / (out["le"] + kr)
    out["share"] = (out["ry"] + kg * out["share_long"]) / (out["re"] + kg)
    out["n_apps_team"] = out["n"].astype(int)
    # raw share = all appearances at this team, minutes-weighted, no shrinkage (diagnostic only)
    out["raw_share"] = np.where(out["ae"] > 0, out["ay"] / out["ae"].where(out["ae"] > 0, 1), np.nan)
    return out.drop(columns=["ly", "le", "ry", "re", "ay", "ae", "n"])
