"""Share shrinkage at the extremes, and the team-change reset on a real transfer."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from peanut_soccer.model.data import History
from peanut_soccer.model.project import ModelParams
from peanut_soccer.model.share import REF, estimate_shares, exposure

from .model_fixtures import load_app

KERKEZ = "1195281"  # FotMob player id
PARAMS_JSON = Path(__file__).resolve().parent.parent / "models" / "params.json"


def frozen_params() -> ModelParams:
    """The tuned parameters actually used by the model (defaults if not tuned yet)."""
    if PARAMS_JSON.exists():
        return ModelParams.from_json(json.loads(PARAMS_JSON.read_text())["params"])
    return ModelParams()


def _squad_history(n_target_apps: int, target_share: float, teammate_share: float = 0.10):
    """30 matches for team T: 6 MID teammates at `teammate_share`, plus the target player (MID) at
    `target_share` in his last n_target_apps matches. Every match 450 team passes, everyone plays 90'."""
    rows = []
    start = pd.Timestamp("2025-08-16 15:00")
    for i in range(30):
        ko = start + pd.Timedelta(days=7 * i)
        mid = f"m{i}"
        for j in range(6):
            rows.append((mid, ko, f"mate{j}", "MID", round(450 * teammate_share)))
        if i >= 30 - n_target_apps:
            rows.append((mid, ko, "target", "MID", round(450 * target_share)))
    df = pd.DataFrame(rows, columns=["match_id", "kickoff", "player_id", "role", "passes"])
    df["season"] = "2025-26"
    df["team"], df["opponent"], df["is_home"], df["started"] = "T", "O", True, True
    df["minutes"] = 90
    df["team_total"] = 450
    df["player_name"] = df["player_id"]
    return df


def _share(n_apps: int, target_share: float = 0.20):
    p = frozen_params().share
    app = _squad_history(n_apps, target_share)
    hist = History.at(app["kickoff"].max() + pd.Timedelta(days=7), app)
    tgt = pd.DataFrame([{"player_id": "target", "team": "T", "role": "MID"}])
    return estimate_shares(hist, tgt, "2025-26", p).iloc[0]


def test_one_appearance_projects_near_prior():
    r = _share(1)
    raw = 0.20 * 450 / exposure(450, 90, frozen_params().share.beta_of("MID"))
    assert r["n_apps_team"] == 1
    # closer to the role prior than to his own one-match rate
    assert abs(r["share"] - r["role_prior"]) < abs(r["share"] - raw)


def test_thirty_appearances_projects_near_own_rate():
    r = _share(30)
    raw = r["raw_share"]
    assert r["n_apps_team"] == 30
    # within 15% of the gap between prior and own rate
    assert abs(r["share"] - raw) < 0.15 * abs(raw - r["role_prior"])


def test_shrinkage_monotone_in_sample_size():
    gaps = [abs(_share(n)["share"] - _share(n)["raw_share"]) for n in (1, 3, 10, 30)]
    assert gaps == sorted(gaps, reverse=True)


def test_team_change_resets_to_new_team_role_prior():
    """Milos Kerkez: AFC Bournemouth (2024-25) -> Liverpool (2025-26), a real transfer in the data.
    (FotMob spells him "Miloš" in 2024-25 and "Milos" in 2025-26; the player id is the same.)"""
    app = load_app()
    k = app[app["player_id"] == KERKEZ].sort_values("kickoff")
    assert set(k.loc[k["season"] == "2024-25", "team"]) == {"AFC Bournemouth"}
    liv = k[k["team"] == "Liverpool"]
    first = liv.iloc[0]
    p = frozen_params().share
    hist = History.at(first["kickoff"], app)
    assert (hist.app["player_id"] == KERKEZ).sum() >= 20  # he has plenty of Bournemouth history
    tgt = pd.DataFrame([{"player_id": first["player_id"], "team": "Liverpool", "role": first["role"]}])
    r = estimate_shares(hist, tgt, "2025-26", p).iloc[0]
    assert r["n_apps_team"] == 0
    assert r["share"] == pytest.approx(r["role_prior"])            # reset to Liverpool's role prior
    bou = estimate_shares(hist, pd.DataFrame([{"player_id": first["player_id"], "team": "AFC Bournemouth",
                                               "role": first["role"]}]), "2025-26", p).iloc[0]
    assert bou["n_apps_team"] >= 20 and bou["share"] != pytest.approx(r["share"])  # old-team history ignored

    # after 10 Liverpool appearances the share has moved from the prior toward his Liverpool rate
    tenth = liv.iloc[10]
    hist10 = History.at(tenth["kickoff"], app)
    r10 = estimate_shares(hist10, tgt, "2025-26", p).iloc[0]
    assert r10["n_apps_team"] == 10
    assert abs(r10["share"] - r10["raw_share"]) < abs(r10["role_prior"] - r10["raw_share"])
