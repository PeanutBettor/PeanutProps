"""Point-in-time enforcement: a projection may only use matches completed before its kickoff."""
import pandas as pd
import pytest

from peanut_soccer.model.data import COMPLETION_BUFFER, History, LeakageError, team_matches
from peanut_soccer.model.project import ModelParams, baselines, project_players
from peanut_soccer.model.team import TeamModel

from .model_fixtures import load_app

TEAMS = {"2024-25": None, "2025-26": None}


def _setup():
    app = load_app()
    fixture_teams = {s: set(g["team"]) | set(g["opponent"]) for s, g in app.groupby("season")}
    # target: Liverpool's 20th match of 2025-26
    liv = app[(app["team"] == "Liverpool") & (app["season"] == "2025-26")]
    mid = liv["match_id"].drop_duplicates().iloc[19]
    tgt = app[app["match_id"] == mid].copy()
    return app, fixture_teams, tgt


def test_history_only_contains_completed_matches():
    app, _, tgt = _setup()
    ko = tgt["kickoff"].iloc[0]
    h = History.at(ko, app)
    assert len(h.app) > 0
    assert (h.app["kickoff"] + COMPLETION_BUFFER <= ko).all()
    assert tgt["match_id"].iloc[0] not in set(h.app["match_id"])


def test_deliberate_leak_of_future_match_is_rejected():
    """Build a history whose cutoff is AFTER the target kickoff (so it contains the target match itself
    and later matches) and try to project the target with it. Must fail."""
    app, ft, tgt = _setup()
    ko = tgt["kickoff"].iloc[0]
    leaky = History.at(ko + pd.Timedelta(days=30), app)
    assert tgt["match_id"].iloc[0] in set(leaky.app["match_id"])  # the leak is really there
    with pytest.raises(LeakageError):
        project_players(leaky, tgt, "2025-26", TeamModel(ModelParams().team, ft), ModelParams())
    with pytest.raises(LeakageError):
        baselines(leaky, tgt, "2025-26")


def test_hand_built_history_with_future_rows_is_rejected():
    app, _, tgt = _setup()
    ko = tgt["kickoff"].iloc[0]
    with pytest.raises(LeakageError):
        History(cutoff=ko, app=app, tm=team_matches(app))  # bypasses History.at filtering


def test_match_just_before_kickoff_is_not_yet_completed():
    app, _, tgt = _setup()
    ko = tgt["kickoff"].iloc[0]
    prev_ko = app.loc[app["kickoff"] < ko, "kickoff"].max()
    h = History.at(prev_ko + pd.Timedelta(hours=1), app)  # previous match still in progress
    assert prev_ko not in set(h.app["kickoff"])


def test_projection_invariant_to_future_data():
    """Deleting everything after the target kickoff must not change the projection."""
    app, ft, tgt = _setup()
    ko = tgt["kickoff"].iloc[0]
    p = ModelParams()
    full = project_players(History.at(ko, app), tgt, "2025-26", TeamModel(p.team, ft), p)
    past_only = app[app["kickoff"] < ko]
    trunc = project_players(History.at(ko, past_only), tgt, "2025-26", TeamModel(p.team, ft), p)
    pd.testing.assert_series_equal(full["mu"], trunc["mu"])
    assert full["mu"].notna().all()
