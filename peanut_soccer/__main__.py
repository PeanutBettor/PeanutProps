"""CLI.

  python -m peanut_soccer backfill      # all seasons, cache-first (safe to re-run)
  python -m peanut_soccer update        # current season only: new finished matches
  python -m peanut_soccer crosscheck    # sample matches vs premierleague.com
  python -m peanut_soccer report        # write reports/data_quality.md
"""
from __future__ import annotations

import argparse
import json
import logging
import sys

from . import config, crosscheck, db, ingest, report
from .http import HttpClient
from .sources.fotmob import FotMobAdapter
from .sources.premierleague import HEADERS as PL_HEADERS, PremierLeagueAdapter


def _setup_logging(verbose: bool) -> None:
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    fmt = "%(asctime)s %(levelname)s %(name)s | %(message)s"
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO, format=fmt,
        handlers=[logging.StreamHandler(sys.stdout),
                  logging.FileHandler(config.LOG_DIR / "pipeline.log", encoding="utf-8")],
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="peanut_soccer")
    ap.add_argument("command", choices=["backfill", "update", "crosscheck", "report"])
    ap.add_argument("--seasons", nargs="*", default=config.SEASONS)
    ap.add_argument("--force", action="store_true", help="re-fetch even if a match is cached")
    ap.add_argument("--limit", type=int, default=None, help="max matches per season (testing)")
    ap.add_argument("--per-season", type=int, default=8, help="crosscheck: matches sampled per season")
    ap.add_argument("--db", default=str(config.DB_PATH))
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args(argv)
    _setup_logging(a.verbose)

    con = db.connect(a.db)
    on_fetch = lambda s, u, st, e: db.log_fetch(con, s, u, st, e)  # noqa: E731
    fotmob = FotMobAdapter(HttpClient("fotmob", on_fetch=on_fetch))

    if a.command in ("backfill", "update"):
        res = ingest.run(con, fotmob, a.seasons, incremental=a.command == "update", force=a.force, limit=a.limit)
        print(json.dumps(res, indent=2))
    elif a.command == "crosscheck":
        pl = PremierLeagueAdapter(HttpClient("premierleague", headers=PL_HEADERS, on_fetch=on_fetch))
        print(json.dumps(crosscheck.run(con, fotmob, pl, a.seasons, n_per_season=a.per_season), indent=2, default=str))
    elif a.command == "report":
        print(f"wrote {report.write(con)}")
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
