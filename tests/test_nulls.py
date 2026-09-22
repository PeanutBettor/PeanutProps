"""A missing field must become NULL + reason code, never 0.

Inputs are the saved real responses with one field removed.
"""
import copy

from peanut_soccer.sources.fotmob import FotMobAdapter
from peanut_soccer.sources.premierleague import PremierLeagueAdapter

from .conftest import NoNetworkClient, load

GAKPO_FM = "806552"
GAKPO_PL = "32894"


def _drop_fotmob_stat(raw, pid, key):
    for g in raw["content"]["playerStats"][pid]["stats"]:
        for title in [t for t, e in g["stats"].items() if e.get("key") == key]:
            del g["stats"][title]


def _row(rows, pid):
    return next(r for r in rows if r.player_id == pid)


def test_fotmob_missing_passes_is_null_with_reason():
    raw = copy.deepcopy(load("fotmob_4813374.json.gz"))
    _drop_fotmob_stat(raw, GAKPO_FM, "accurate_passes")
    _, rows = FotMobAdapter(NoNetworkClient()).parse_match(raw, "2025-26")
    r = _row(rows, GAKPO_FM)
    assert r.passes_attempted is None and r.passes_completed is None
    assert r.null_reasons["passes_attempted"] == "field_absent_in_source"
    assert r.minutes_played == 90  # other fields untouched


def test_fotmob_missing_total_only():
    raw = copy.deepcopy(load("fotmob_4813374.json.gz"))
    for g in raw["content"]["playerStats"][GAKPO_FM]["stats"]:
        for e in g["stats"].values():
            if e.get("key") == "accurate_passes":
                del e["stat"]["total"]
    _, rows = FotMobAdapter(NoNetworkClient()).parse_match(raw, "2025-26")
    r = _row(rows, GAKPO_FM)
    assert r.passes_attempted is None and r.passes_completed == 21
    assert r.null_reasons["passes_attempted"] == "field_absent_in_source"


def test_fotmob_missing_minutes_is_null_with_reason():
    raw = copy.deepcopy(load("fotmob_4813374.json.gz"))
    _drop_fotmob_stat(raw, GAKPO_FM, "minutes_played")
    _, rows = FotMobAdapter(NoNetworkClient()).parse_match(raw, "2025-26")
    r = _row(rows, GAKPO_FM)
    assert r.minutes_played is None and r.null_reasons["minutes_played"] == "field_absent_in_source"
    assert r.passes_attempted == 29


def test_fotmob_missing_player_block():
    raw = copy.deepcopy(load("fotmob_4813374.json.gz"))
    del raw["content"]["playerStats"][GAKPO_FM]
    _, rows = FotMobAdapter(NoNetworkClient()).parse_match(raw, "2025-26")
    r = _row(rows, GAKPO_FM)
    assert r.passes_attempted is None and r.minutes_played is None
    assert r.null_reasons["passes_attempted"] == "player_stats_block_missing"


def test_fotmob_missing_events_red_card_null():
    raw = copy.deepcopy(load("fotmob_4813374.json.gz"))
    del raw["content"]["matchFacts"]["events"]
    _, rows = FotMobAdapter(NoNetworkClient()).parse_match(raw, "2025-26")
    r = _row(rows, GAKPO_FM)
    assert r.red_card is None and r.null_reasons["red_card"] == "field_absent_in_source"


def test_premierleague_absent_stat_is_null_not_zero():
    raw = copy.deepcopy(load("premierleague_124791.json.gz"))
    st = raw["player_stats"][GAKPO_PL]["stats"]
    raw["player_stats"][GAKPO_PL]["stats"] = [s for s in st if s["name"] != "total_pass"]
    _, rows = PremierLeagueAdapter(NoNetworkClient()).parse_match(raw, "2025-26")
    r = _row(rows, GAKPO_PL)
    assert r.passes_attempted is None and r.null_reasons["passes_attempted"] == "field_absent_in_source"


def test_null_reasons_serialized_to_db_string():
    _, rows = FotMobAdapter(NoNetworkClient()).parse_match(load("fotmob_4813374.json.gz"), "2025-26")
    unused = next(r for r in rows if r.player_name == "Harvey Elliott")
    assert "passes_attempted:unused_sub" in unused.null_reason_str()
