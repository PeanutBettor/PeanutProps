"""Regression test: the data quality report must not confuse player appearances with unique players."""
from peanut_soccer import db, ingest, report
from peanut_soccer.sources.fotmob import FotMobAdapter

from .conftest import NoNetworkClient


def test_appearances_vs_unique_players(tmp_path, raw_dir):
    con = db.connect(tmp_path / "r.duckdb")
    fm = FotMobAdapter(NoNetworkClient(), raw_dir=raw_dir)
    # Real matches: Man Utd v Fulham in 2024-25 and Fulham v Man Utd in 2026-27, so several
    # players appear in both, plus Liverpool v Bournemouth 2025-26.
    for season, mid in (("2024-25", "4506263"), ("2025-26", "4813374"), ("2026-27", "5795459")):
        ingest.ingest_match(con, fm, season, mid)
    rows = {r["season"]: r for r in report.row_counts(con)}

    for season in ("2024-25", "2025-26", "2026-27"):
        r = rows[season]
        appeared = con.execute(
            "SELECT count(*), count(DISTINCT player_id) FROM player_match pm JOIN matches m USING (match_id, source) "
            "WHERE m.season=? AND (started OR subbed_on_minute IS NOT NULL)", [season]).fetchone()
        assert (r["appearances"], r["unique_players"]) == appeared
        # one match per season -> every appearing player appears exactly once
        assert r["appearances"] == r["unique_players"]
        assert r["squad_players"] >= r["unique_players"]

    total = rows["all seasons"]
    assert total["appearances"] == sum(rows[s]["appearances"] for s in ("2024-25", "2025-26", "2026-27"))
    # players who played in both Man Utd/Fulham matches are counted once
    repeaters = con.execute(
        "SELECT count(*) FROM (SELECT player_id FROM player_match WHERE started OR subbed_on_minute IS NOT NULL "
        "GROUP BY 1 HAVING count(*) > 1)").fetchone()[0]
    assert repeaters > 0
    assert total["unique_players"] == total["appearances"] - sum(
        n - 1 for (n,) in con.execute("SELECT count(*) FROM player_match WHERE started OR subbed_on_minute IS NOT NULL "
                                      "GROUP BY player_id").fetchall())
    assert total["unique_players"] < total["appearances"]


def test_report_headers_renamed(tmp_path, raw_dir):
    con = db.connect(tmp_path / "r.duckdb")
    ingest.ingest_match(con, FotMobAdapter(NoNetworkClient(), raw_dir=raw_dir), "2025-26", "4813374")
    text = report.build(con, raw_dir=raw_dir)
    assert "| season | rows | player appearances | unique players | players in squads |" in text
    assert "| appeared |" not in text  # the old ambiguous column header is gone everywhere
