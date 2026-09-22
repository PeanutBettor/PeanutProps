"""Running ingestion twice must produce identical row counts and identical rows."""
from peanut_soccer import db, ingest
from peanut_soccer.sources.fotmob import FotMobAdapter

from .conftest import NoNetworkClient


def _snapshot(con):
    counts = {t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
              for t in ("matches", "player_match", "players")}
    rows = con.execute("SELECT * FROM player_match ORDER BY match_id, player_id").fetchall()
    return counts, rows


def test_ingest_twice_is_idempotent(tmp_path, raw_dir):
    con = db.connect(tmp_path / "t.duckdb")
    fm = FotMobAdapter(NoNetworkClient(), raw_dir=raw_dir)  # cache-only: any network call fails
    ingest.run(con, fm, ["2025-26"], incremental=False, limit=1)
    first = _snapshot(con)
    ingest.run(con, fm, ["2025-26"], incremental=False, limit=1)
    second = _snapshot(con)
    assert first == second
    assert first[0]["matches"] == 380 and first[0]["player_match"] == 40


def test_ingest_match_twice_all_seasons(tmp_path, raw_dir):
    con = db.connect(tmp_path / "t.duckdb")
    fm = FotMobAdapter(NoNetworkClient(), raw_dir=raw_dir)
    for _ in range(2):
        for season, mid in (("2024-25", "4506263"), ("2025-26", "4813374"), ("2026-27", "5795459")):
            ingest.ingest_match(con, fm, season, mid)
        db.rebuild_players(con)
    n = con.execute("SELECT count(*) FROM player_match").fetchone()[0]
    dup = con.execute("SELECT count(*) FROM (SELECT match_id, source, player_id FROM player_match "
                      "GROUP BY ALL HAVING count(*) > 1)").fetchone()[0]
    assert dup == 0 and n == con.execute("SELECT count(DISTINCT (match_id, player_id)) FROM player_match").fetchone()[0]


def test_primary_key_rejects_plain_duplicate(tmp_path):
    import duckdb
    import pytest
    con = db.connect(tmp_path / "t.duckdb")
    con.execute("INSERT INTO player_match (match_id, source, player_id) VALUES ('1','x','p')")
    with pytest.raises(duckdb.ConstraintException):
        con.execute("INSERT INTO player_match (match_id, source, player_id) VALUES ('1','x','p')")


def test_cached_match_not_refetched(raw_dir):
    fm = FotMobAdapter(NoNetworkClient(), raw_dir=raw_dir)
    raw = fm.fetch_match_raw("2025-26", "4813374")  # would raise if it hit the network
    assert raw["general"]["matchId"] == "4813374"
