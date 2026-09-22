"""Parser tests against saved REAL raw responses (no invented JSON)."""
import pytest

from peanut_soccer.sources.fotmob import FotMobAdapter
from peanut_soccer.sources.premierleague import PremierLeagueAdapter

from .conftest import FOTMOB_MATCHES, NoNetworkClient, load


def _fm(mid, season):
    return FotMobAdapter(NoNetworkClient()).parse_match(load(f"fotmob_{mid}.json.gz"), season)


def _by_name(rows, name):
    hits = [r for r in rows if r.player_name == name]
    assert len(hits) == 1, name
    return hits[0]


def test_fotmob_match_header():
    m, _ = _fm("4813374", "2025-26")
    assert (m.home_team, m.away_team, m.home_score, m.away_score) == ("Liverpool", "AFC Bournemouth", 4, 2)
    assert m.status == "finished"
    assert m.date_utc.isoformat() == "2025-08-15T19:00:00"


def test_fotmob_player_values():
    _, rows = _fm("4813374", "2025-26")
    g = _by_name(rows, "Cody Gakpo")  # also 29 / 21 / 90 on premierleague.com
    assert (g.passes_attempted, g.passes_completed, g.minutes_played) == (29, 21, 90)
    assert g.started and g.team == "Liverpool" and g.opponent == "AFC Bournemouth" and g.is_home
    assert g.position == "FWD" and g.opta_player_id == "243298"
    s = _by_name(rows, "Adam Smith")
    assert (s.passes_attempted, s.passes_completed, s.minutes_played, s.subbed_off_minute) == (25, 16, 89, 90)
    assert not s.is_home and s.position == "DEF"
    r = _by_name(rows, "Andrew Robertson")
    assert (r.started, r.subbed_on_minute, r.minutes_played, r.passes_attempted) == (False, 60, 30, 9)


def test_fotmob_explicit_zero_is_zero_not_null():
    _, rows = _fm("4506263", "2024-25")
    j = _by_name(rows, "Jay Stansfield")  # FotMob shows Accurate passes 0/0 in 1 minute
    assert j.passes_attempted == 0 and j.passes_completed == 0 and j.minutes_played == 1
    assert "passes_attempted" not in j.null_reasons


@pytest.mark.parametrize("season,mid,expected", [
    ("2024-25", "4506263", (482, 384)),
    ("2025-26", "4813374", (489, 299)),
    ("2026-27", "5795459", (457, 606)),
])
def test_fotmob_player_sums_equal_team_stat(season, mid, expected):
    raw = load(f"fotmob_{mid}.json.gz")
    assert FotMobAdapter.team_pass_totals(raw) == expected
    _, rows = FotMobAdapter(NoNetworkClient()).parse_match(raw, season)
    home = sum(r.passes_attempted for r in rows if r.is_home and r.passes_attempted is not None)
    away = sum(r.passes_attempted for r in rows if not r.is_home and r.passes_attempted is not None)
    assert (home, away) == expected


@pytest.mark.parametrize("season,mid", list(FOTMOB_MATCHES.items()))
def test_fotmob_structure(season, mid):
    _, rows = _fm(mid, season)
    for home in (True, False):
        assert sum(1 for r in rows if r.is_home == home and r.started) == 11
    for r in rows:
        appeared = r.started or r.subbed_on_minute is not None
        if appeared:
            assert r.minutes_played is not None and r.passes_attempted is not None
        else:
            assert r.minutes_played is None and r.passes_attempted is None
            assert r.null_reasons["passes_attempted"] == "unused_sub"


def test_fotmob_fixture_list():
    fx = FotMobAdapter(NoNetworkClient()).parse_fixtures(load("fotmob_fixtures_2025-26.json.gz"), "2025-26")
    assert len(fx) == 380
    assert all(m.status == "finished" for m in fx)
    first = next(m for m in fx if m.match_id == "4813374")
    assert (first.home_team, first.home_score, first.away_score) == ("Liverpool", 4, 2)


def test_fotmob_fixture_list_rejects_wrong_season():
    with pytest.raises(ValueError):
        FotMobAdapter(NoNetworkClient()).parse_fixtures(load("fotmob_fixtures_2025-26.json.gz"), "2026-27")


def test_premierleague_parser():
    m, rows = PremierLeagueAdapter(NoNetworkClient()).parse_match(load("premierleague_124791.json.gz"), "2025-26")
    assert (m.home_team, m.away_team, m.home_score, m.away_score) == ("Liverpool", "Bournemouth", 4, 2)
    g = _by_name(rows, "Cody Gakpo")
    assert (g.passes_attempted, g.passes_completed, g.minutes_played, g.opta_player_id) == (29, 21, 90, "243298")
    home = sum(r.passes_attempted or 0 for r in rows if r.is_home)
    away = sum(r.passes_attempted or 0 for r in rows if not r.is_home)
    assert (home, away) == (489, 299)  # equals FotMob team totals for the same match
