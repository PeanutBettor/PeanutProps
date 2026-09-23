"""CLI.

  python -m peanut_soccer backfill      # all seasons, cache-first (safe to re-run)
  python -m peanut_soccer update        # current season only: new finished matches
  python -m peanut_soccer crosscheck    # sample matches vs premierleague.com
  python -m peanut_soccer report        # write reports/data_quality.md
  python -m peanut_soccer tune          # walk-forward tuning on 2024-25 + 2025-26 -> models/params.json
  python -m peanut_soccer holdout       # score 2026-27 ONCE with the frozen params
  python -m peanut_soccer validate-report   # write reports/model_validation.md
  python -m peanut_soccer project --match-id M --player-id P --minutes 90 [--lines 30.5 40.5]
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
    ap.add_argument("command", choices=["backfill", "update", "crosscheck", "report", "tune", "holdout",
                                            "validate-report", "project"])
    ap.add_argument("--seasons", nargs="*", default=config.SEASONS)
    ap.add_argument("--force", action="store_true", help="re-fetch even if a match is cached")
    ap.add_argument("--limit", type=int, default=None, help="max matches per season (testing)")
    ap.add_argument("--per-season", type=int, default=8, help="crosscheck: matches sampled per season")
    ap.add_argument("--db", default=str(config.DB_PATH))
    ap.add_argument("--match-id")
    ap.add_argument("--player-id")
    ap.add_argument("--minutes", type=float)
    ap.add_argument("--lines", type=float, nargs="*", default=[20.5, 30.5, 40.5, 50.5, 60.5, 70.5])
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
    elif a.command in ("tune", "holdout", "validate-report", "project"):
        from .model import cli as mcli
        if a.command == "tune":
            res = mcli.cmd_tune(con)
        elif a.command == "holdout":
            res = mcli.cmd_holdout(con)
        elif a.command == "validate-report":
            from .model import validation
            res = {"wrote": str(validation.write(con))}
        else:
            if not (a.match_id and a.player_id and a.minutes is not None):
                ap.error("project needs --match-id, --player-id and --minutes")
            res = mcli.cmd_project(con, a.match_id, a.player_id, a.minutes, a.lines)
        print(json.dumps(res, indent=2, default=str))
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
