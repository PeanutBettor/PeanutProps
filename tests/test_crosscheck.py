"""Cross-check join logic on a real match where the PL feed omits Opta ids (Arsenal v Southampton, 2024-25)."""
from peanut_soccer import crosscheck, db
from peanut_soccer.sources.fotmob import FotMobAdapter
from peanut_soccer.sources.premierleague import PremierLeagueAdapter

from .conftest import NoNetworkClient, load


def _setup(tmp_path):
    con = db.connect(tmp_path / "x.duckdb")
    for adapter, name in ((FotMobAdapter(NoNetworkClient()), "fotmob_4506323.json.gz"),
                          (PremierLeagueAdapter(NoNetworkClient()), "premierleague_115887.json.gz")):
        m, rows = adapter.parse_match(load(name), "2024-25")
        db.upsert_matches(con, [m])
        db.upsert_player_matches(con, rows)
    return con


def test_pl_rows_have_no_opta_ids_in_this_fixture(tmp_path):
    con = _setup(tmp_path)
    assert con.execute("SELECT count(opta_player_id) FROM player_match WHERE source='premierleague'").fetchone()[0] == 0


def test_name_fallback_links_and_values_match(tmp_path):
    con = _setup(tmp_path)
    assert crosscheck._player_overlap(con, "fotmob", "4506323", "premierleague", "115887") >= crosscheck.MIN_PLAYER_OVERLAP
    crosscheck._compare(con, "fotmob", "4506323", "premierleague", "115887")
    out = dict(con.execute("SELECT outcome, count(*) FROM crosscheck GROUP BY 1").fetchall())
    assert out.get("diff", 0) == 0 and out["exact"] >= 28


def test_ambiguous_name_is_not_guessed(tmp_path):
    # FotMob "Gabriel" vs PL "Gabriel Magalhães": not an exact or unique-last-name match -> left unmatched.
    con = _setup(tmp_path)
    crosscheck._compare(con, "fotmob", "4506323", "premierleague", "115887")
    rows = con.execute("SELECT player_name, outcome, join_method FROM crosscheck WHERE player_name LIKE 'Gabriel%'").fetchall()
    assert ("Gabriel", "missing_in_other", "opta_id") in rows
    assert ("Gabriel Magalhães", "missing_in_primary", "unresolved") in rows
