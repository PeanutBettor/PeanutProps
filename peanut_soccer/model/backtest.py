"""Walk-forward backtest, parameter tuning and the one-time holdout run.

Walk-forward: matches are grouped into chronological match-week blocks. For each block the history is
every match completed before the block's first kickoff, the model is refit on that history, and the
block's matches are projected. Minutes fed to the model are the ACTUAL minutes played (oracle minutes),
so these numbers measure the rate model only, not minutes prediction.

Holdout discipline: TRAIN_SEASONS are used for tuning. HOLDOUT_SEASON may only be scored through
`score_holdout`, which requires frozen parameters and writes a log entry every time it runs.
"""
from __future__ import annotations

import json
import logging
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from . import dist
from .data import History, match_week_blocks, team_matches
from .project import (DistParams, ModelParams, add_distribution, baselines, model_version, project_players,
                      team_projection)
from .share import ShareParams
from .team import TeamModel, TeamParams

log = logging.getLogger("peanut_soccer.model")

TRAIN_SEASONS = ("2024-25", "2025-26")
HOLDOUT_SEASON = "2026-27"
BURN_IN_BLOCKS = 5  # first 5 match-week blocks of 2024-25 are not scored: the DB has no earlier data
PRIMARY_MIN_MINUTES = 60


class HoldoutViolation(RuntimeError):
    pass


def fixture_teams(con, source: str = "fotmob") -> dict:
    """season -> teams in that season's fixture list (published before the season starts)."""
    rows = con.execute("SELECT season, home_team, away_team FROM matches WHERE source=?", [source]).fetchall()
    out: dict = {}
    for s, h, a in rows:
        out.setdefault(s, set()).update((h, a))
    return out


class WalkForward:
    def __init__(self, app: pd.DataFrame, fixture_teams: dict):
        self.app = app
        self.tm = team_matches(app)
        self.fixture_teams = fixture_teams
        blocks = match_week_blocks(self.tm["kickoff"])
        self.tm["block"] = blocks.to_numpy()
        self.app = self.app.merge(self.tm[["match_id", "block"]].drop_duplicates(), on="match_id")
        # scoring flag: skip 2024-25 burn-in
        first = self.tm[self.tm["season"] == TRAIN_SEASONS[0]]["block"].min()
        self.burn_in = set(range(first, first + BURN_IN_BLOCKS))
        self._team_cache: dict = {}

    def blocks(self, season: str) -> list[int]:
        return sorted(self.tm.loc[self.tm["season"] == season, "block"].unique())

    def history(self, block: int) -> History:
        cutoff = self.tm.loc[self.tm["block"] == block, "kickoff"].min()
        return History.at(cutoff, self.app, self.tm)

    # ---- team volume --------------------------------------------------------------------------
    def team_predictions(self, seasons, tp: TeamParams) -> pd.DataFrame:
        key = (tuple(seasons), tp)
        if key in self._team_cache:
            return self._team_cache[key]
        model = TeamModel(tp, self.fixture_teams)
        parts = []
        for season in seasons:
            for b in self.blocks(season):
                hist = self.history(b)
                tgt = self.tm[self.tm["block"] == b]
                parts.append(team_projection(hist, tgt, season, model))
        out = pd.concat(parts, ignore_index=True)
        out["scored"] = ~out["block"].isin(self.burn_in)
        self._team_cache[key] = out
        return out

    # ---- players ------------------------------------------------------------------------------
    def player_predictions(self, seasons, params: ModelParams, with_baselines: bool = False) -> pd.DataFrame:
        tpred = self.team_predictions(seasons, params.team)
        model = TeamModel(params.team, self.fixture_teams)
        parts = []
        for season in seasons:
            for b in self.blocks(season):
                hist = self.history(b)
                tgt = self.app[self.app["block"] == b]
                tp = tpred[tpred["block"] == b]
                pr = project_players(hist, tgt, season, model, params, team_proj=tp)
                if with_baselines:
                    bl = baselines(hist, tgt, season)
                    for c in bl.columns:
                        pr[c] = bl[c].to_numpy()
                pr["cutoff"] = hist.cutoff
                parts.append(pr)
        out = pd.concat(parts, ignore_index=True)
        out["scored"] = ~out["block"].isin(self.burn_in)
        out["primary"] = out["started"] & (out["minutes"] >= PRIMARY_MIN_MINUTES)
        return out


# ---- objectives -------------------------------------------------------------------------------

def team_objective(tpred: pd.DataFrame) -> float:
    s = tpred[tpred["scored"] & tpred["team_proj"].notna()]
    return float(np.mean(np.abs(s["team_proj"] - s["passes"])))


def player_objective(pred: pd.DataFrame) -> tuple[float, float, float]:
    """NB log-loss on the primary set (starters, 60+ min) with ML dispersion; also MAE."""
    s = pred[pred["scored"] & pred["primary"] & pred["mu"].notna()]
    r = dist.fit_size(s["passes"], s["mu"])
    ll = float(dist.log_loss(s["passes"], s["mu"], r).mean())
    return ll, float(np.mean(np.abs(s["mu"] - s["passes"]))), r


# ---- tuning -----------------------------------------------------------------------------------

# Grids were widened after a first pass put short_weight, k_league, beta_GK, beta_DEF and promoted_mult on
# a grid edge (training data only). short_weight excludes 0: the spec requires <20-min appearances to count.
TEAM_GRID = {"decay": [0.7, 0.8, 0.85, 0.9, 0.95, 1.0], "k_prior": [0.5, 1, 2, 4, 8, 16],
             "promoted_mult": [0.5, 1, 2, 4, 8, 16]}
SHARE_GRID = {"decay": [0.7, 0.8, 0.85, 0.9, 0.95, 1.0], "k_long": [0.5, 1, 2, 4, 8],
              "k_role": [0.25, 0.5, 1, 2, 4, 8], "k_league": [3, 10, 30, 100, 300],
              "short_weight": [0.05, 0.1, 0.25, 0.5, 0.75, 1.0]}
BETA_GRID = [-0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75]
# Coordinate descent starts from the optimum of the first (narrower-grid) pass.
SHARE_START = ShareParams(decay=0.85, k_long=2.0, k_role=2.0, k_league=30.0, short_weight=0.1,
                          beta=(("GK", 0.0), ("DEF", 1.25), ("MID", 1.0), ("FWD", 0.75)))


def tune(wf: WalkForward, seasons=TRAIN_SEASONS, passes: int = 2, progress_path: Path | None = None
         ) -> tuple[ModelParams, dict]:
    if HOLDOUT_SEASON in seasons:
        raise HoldoutViolation("tuning may not use the holdout season")
    trace = {"team": [], "share": []}

    # 1) team volume: full grid on team-level MAE
    best_t, best_v = None, np.inf
    for d in TEAM_GRID["decay"]:
        for k in TEAM_GRID["k_prior"]:
            for m in TEAM_GRID["promoted_mult"]:
                tp = TeamParams(d, k, m)
                v = team_objective(wf.team_predictions(seasons, tp))
                trace["team"].append({"decay": d, "k_prior": k, "promoted_mult": m, "mae": v})
                _progress(progress_path, trace)
                if v < best_v:
                    best_t, best_v = tp, v
    log.info("team params %s MAE %.2f", best_t, best_v)

    # 2) share: coordinate descent on primary-set NB log-loss
    params = ModelParams(team=best_t, share=SHARE_START)
    cur_ll, _, _ = player_objective(wf.player_predictions(seasons, params))
    for p in range(passes):
        for name, grid in list(SHARE_GRID.items()) + [(f"beta_{r}", BETA_GRID) for r in ("GK", "DEF", "MID", "FWD")]:
            for v in grid:
                if name.startswith("beta_"):
                    sp = params.share.with_beta(name[5:], v)
                else:
                    sp = replace(params.share, **{name: v})
                if sp == params.share:
                    continue
                cand = replace(params, share=sp)
                ll, mae, r = player_objective(wf.player_predictions(seasons, cand))
                trace["share"].append({"pass": p, "param": name, "value": v, "logloss": ll, "mae": mae})
                _progress(progress_path, trace)
                if ll < cur_ll - 1e-6:
                    params, cur_ll = cand, ll
                    log.info("improved %s=%s logloss %.4f mae %.3f", name, v, ll, mae)
    return params, trace


def _progress(path: Path | None, trace: dict) -> None:
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(trace, default=float))


# ---- distribution choice ----------------------------------------------------------------------

def choose_distribution(pred: pd.DataFrame) -> tuple[DistParams, pd.DataFrame]:
    """Poisson vs NB (one size) vs NB (size per position group), by cross-season validation log-loss.

    Sizes are fit on one training season's walk-forward predictions and scored on the other, both ways.
    """
    s = pred[pred["scored"] & pred["mu"].notna() & (pred["mu"] > 0)]
    seasons = sorted(s["season"].unique())
    rows = []
    for subset in ("primary", "all"):
        ss = s[s["primary"]] if subset == "primary" else s
        for fam in ("poisson", "nb_global", "nb_by_role"):
            lls = []
            for fit_s, ev_s in ((seasons[0], seasons[1]), (seasons[1], seasons[0])):
                fit, ev = ss[ss["season"] == fit_s], ss[ss["season"] == ev_s]
                if fam == "poisson":
                    ll = dist.log_loss(ev["passes"], ev["mu"], None)
                elif fam == "nb_global":
                    ll = dist.log_loss(ev["passes"], ev["mu"], dist.fit_size(fit["passes"], fit["mu"]))
                else:
                    ll = np.empty(len(ev))
                    for role in ev["role"].unique():
                        f, e = fit[fit["role"] == role], (ev["role"] == role).to_numpy()
                        ll[e] = dist.log_loss(ev.loc[e, "passes"], ev.loc[e, "mu"], dist.fit_size(f["passes"], f["mu"]))
                lls.append(ll)
            rows.append({"subset": subset, "family": fam, "logloss": float(np.concatenate(lls).mean()),
                         "n": int(sum(len(x) for x in lls))})
    table = pd.DataFrame(rows)
    prim = table[table["subset"] == "primary"].set_index("family")["logloss"]
    choice = prim.idxmin()
    # final sizes fit on all scored training rows (all appearances, so subs get a size too)
    if choice == "poisson":
        dp = DistParams("poisson", (("ALL", float("inf")),))
    elif choice == "nb_global":
        dp = DistParams("nbinom", (("ALL", dist.fit_size(s["passes"], s["mu"])),))
    else:
        dp = DistParams("nbinom", tuple((r, dist.fit_size(s.loc[s["role"] == r, "passes"], s.loc[s["role"] == r, "mu"]))
                                        for r in ("GK", "DEF", "MID", "FWD")))
    return dp, table


def baseline_sizes(pred: pd.DataFrame) -> dict:
    """NB size for each baseline, fit on its own training walk-forward predictions (all scored rows)."""
    s = pred[pred["scored"]]
    out = {}
    for b in ("base_std", "base_last5", "base_last10"):
        ok = s[b].notna() & (s[b] > 0)
        out[b] = dist.fit_size(s.loc[ok, "passes"], s.loc[ok, b])
    return out


# ---- holdout ----------------------------------------------------------------------------------

def score_holdout(wf: WalkForward, params: ModelParams, log_path: Path) -> pd.DataFrame:
    """Score the holdout season with frozen parameters. Every call is appended to log_path."""
    version = model_version(params)
    entries = json.loads(log_path.read_text()) if log_path.exists() else []
    entries.append({"model_version": version, "scored_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "params": params.to_json()})
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(entries, indent=2))
    pred = wf.player_predictions([HOLDOUT_SEASON], params, with_baselines=True)
    pred["scored"] = True
    return pred
