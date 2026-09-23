"""Model commands: tune, holdout, validate-report, project."""
from __future__ import annotations

import json
import logging
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .. import config
from . import backtest, dist
from .backtest import HOLDOUT_SEASON, TRAIN_SEASONS, WalkForward, fixture_teams
from .data import History, load_appearances
from .project import ModelParams, add_distribution, model_version, project_players
from .team import TeamModel, volume_shift_flags

log = logging.getLogger("peanut_soccer.model")

MODELS_DIR = config.ROOT / "models"
PARAMS_PATH = MODELS_DIR / "params.json"
HOLDOUT_LOG = MODELS_DIR / "holdout_log.json"
KEEP_COLS = ["match_id", "season", "block", "kickoff", "cutoff", "player_id", "player_name", "team", "opponent",
             "is_home", "role", "started", "minutes", "passes", "team_total", "team_proj", "team_n_matches",
             "share", "share_long", "role_prior", "raw_share", "n_apps_team", "mu", "median", "p10", "p90",
             "nb_size", "base_std", "base_last5", "base_last10", "scored", "primary", "no_proj_reason"]


def _save_predictions(con, pred: pd.DataFrame, phase: str, version: str, snapshot) -> None:
    df = pred[[c for c in KEEP_COLS if c in pred.columns]].copy()
    df["phase"] = phase
    df["model_version"] = version
    df["data_snapshot"] = pd.Timestamp(snapshot)
    df["created_at"] = pd.Timestamp(datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0))
    con.execute("CREATE TABLE IF NOT EXISTS model_backtest AS SELECT * FROM df LIMIT 0")
    con.execute("DELETE FROM model_backtest WHERE phase = ?", [phase])
    con.execute("INSERT INTO model_backtest BY NAME SELECT * FROM df")


def cmd_tune(con) -> dict:
    app = load_appearances(con)
    wf = WalkForward(app, fixture_teams(con))
    params, trace = backtest.tune(wf, TRAIN_SEASONS, progress_path=MODELS_DIR / "tuning_progress.json")
    pred = wf.player_predictions(TRAIN_SEASONS, params, with_baselines=True)
    dp, dist_table = backtest.choose_distribution(pred)
    params = replace(params, dist=dp)
    pred = add_distribution(pred, dp)
    bsizes = backtest.baseline_sizes(pred)
    version = model_version(params)
    ll, mae, _ = backtest.player_objective(pred)
    out = {
        "model_version": version,
        "tuned_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "data_snapshot": str(app.attrs["snapshot"]),
        "train_seasons": list(TRAIN_SEASONS),
        "params": params.to_json(),
        "baseline_nb_size": bsizes,
        "distribution_selection": dist_table.to_dict(orient="records"),
        "train_objective": {"primary_nb_logloss": ll, "primary_mae": mae,
                            "team_mae": backtest.team_objective(wf.team_predictions(TRAIN_SEASONS, params.team))},
    }
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    PARAMS_PATH.write_text(json.dumps(out, indent=2))
    pd.DataFrame(trace["team"]).to_csv(MODELS_DIR / "tuning_trace_team.csv", index=False)
    pd.DataFrame(trace["share"]).to_csv(MODELS_DIR / "tuning_trace_share.csv", index=False)
    _save_predictions(con, pred, "train", version, app.attrs["snapshot"])
    tp = wf.team_predictions(TRAIN_SEASONS, params.team)
    tp.to_csv(MODELS_DIR / "team_predictions_train.csv", index=False)
    return out


def load_frozen() -> tuple[ModelParams, dict]:
    meta = json.loads(PARAMS_PATH.read_text())
    params = ModelParams.from_json(meta["params"])
    if model_version(params) != meta["model_version"]:
        raise RuntimeError(f"model code or params changed since tuning ({model_version(params)} != "
                           f"{meta['model_version']}); re-tune before scoring")
    return params, meta


def cmd_holdout(con) -> dict:
    params, meta = load_frozen()
    app = load_appearances(con)
    wf = WalkForward(app, fixture_teams(con))
    pred = backtest.score_holdout(wf, params, HOLDOUT_LOG)
    pred = add_distribution(pred, params.dist)
    _save_predictions(con, pred, "holdout", meta["model_version"], app.attrs["snapshot"])
    wf.team_predictions([HOLDOUT_SEASON], params.team).to_csv(MODELS_DIR / "team_predictions_holdout.csv", index=False)
    return {"model_version": meta["model_version"], "rows": len(pred),
            "holdout_scorings": len(json.loads(HOLDOUT_LOG.read_text()))}


def cmd_project(con, match_id: str, player_id: str, minutes: float, lines: list[float]) -> dict:
    """Project one player in one match (scheduled or past) with the frozen model. Minutes are an input."""
    params, meta = load_frozen()
    app = load_appearances(con)
    m = con.execute("SELECT season, date, home_team, away_team FROM matches WHERE source='fotmob' AND match_id=?",
                    [match_id]).fetchone()
    if m is None:
        raise SystemExit(f"unknown match {match_id}")
    season, kickoff, home, away = m
    pl = con.execute("SELECT player_name, current_team, primary_position FROM players WHERE source='fotmob' "
                     "AND player_id=?", [player_id]).fetchone()
    if pl is None:
        raise SystemExit(f"unknown player {player_id}")
    name, team, role = pl
    if team not in (home, away):
        raise SystemExit(f"{name}'s current team {team} is not in match {home} v {away}")
    is_home = team == home
    hist = History.at(pd.Timestamp(kickoff), app)
    tgt = pd.DataFrame([{"match_id": match_id, "player_id": player_id, "team": team,
                         "opponent": away if is_home else home, "is_home": is_home, "role": role,
                         "kickoff": pd.Timestamp(kickoff), "minutes": minutes}])
    pr = add_distribution(project_players(hist, tgt, season, TeamModel(params.team, fixture_teams(con)), params),
                          params.dist).iloc[0]
    r = params.dist.size_of(role)
    res = {"player": name, "team": team, "opponent": tgt.opponent[0], "is_home": bool(is_home), "role": role,
           "kickoff_utc": str(kickoff), "minutes_input": minutes, "team_passes_proj": round(pr.team_proj, 1),
           "share_proj": round(pr.share, 4), "mean": round(pr.mu, 2), "median": pr["median"], "p10": pr.p10,
           "p90": pr.p90, "p_over": {str(L): round(float(dist.prob_over(L, pr.mu, r)), 4) for L in lines},
           "model_version": meta["model_version"], "data_snapshot": str(app.attrs["snapshot"]),
           "history_cutoff": str(hist.cutoff)}
    con.execute("""CREATE TABLE IF NOT EXISTS projections (
        created_at TIMESTAMP, model_version VARCHAR, data_snapshot TIMESTAMP, history_cutoff TIMESTAMP,
        match_id VARCHAR, player_id VARCHAR, player_name VARCHAR, team VARCHAR, opponent VARCHAR, is_home BOOLEAN,
        role VARCHAR, minutes_input DOUBLE, team_passes_proj DOUBLE, share_proj DOUBLE, mean DOUBLE,
        median DOUBLE, p10 DOUBLE, p90 DOUBLE, nb_size DOUBLE)""")
    con.execute("INSERT INTO projections VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [
        datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0), meta["model_version"], app.attrs["snapshot"],
        hist.cutoff, match_id, player_id, name, team, res["opponent"], bool(is_home), role, minutes,
        float(pr.team_proj), float(pr.share), float(pr.mu), float(pr["median"]), float(pr.p10), float(pr.p90),
        float(r) if r is not None else None])
    return res


def current_volume_flags(con) -> pd.DataFrame:
    app = load_appearances(con)
    hist = History.at(pd.Timestamp.utcnow().tz_localize(None), app)
    return pd.concat([volume_shift_flags(hist, s) for s in (HOLDOUT_SEASON,)], ignore_index=True)
