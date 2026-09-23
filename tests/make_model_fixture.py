"""Regenerate tests/fixtures/appearances_liv_bou.csv.gz from data/soccer.duckdb.

Every appearance (both teams) in 2024-25 and 2025-26 matches involving Liverpool or AFC Bournemouth.
Run: python -m tests.make_model_fixture
"""
import duckdb

from peanut_soccer import config
from peanut_soccer.model.data import load_appearances

from .model_fixtures import FIX

COLS = ["match_id", "season", "kickoff", "player_id", "player_name", "team", "opponent", "is_home", "role",
        "started", "minutes", "passes", "team_total"]

if __name__ == "__main__":
    import sys
    con = duckdb.connect(sys.argv[1] if len(sys.argv) > 1 else str(config.DB_PATH), read_only=True)
    app = load_appearances(con)
    teams = {"Liverpool", "AFC Bournemouth"}
    mids = app.loc[app["team"].isin(teams) & app["season"].isin(["2024-25", "2025-26"]), "match_id"].unique()
    app[app["match_id"].isin(mids)][COLS].to_csv(FIX, index=False, compression="gzip")
    print(FIX, len(mids), "matches")
