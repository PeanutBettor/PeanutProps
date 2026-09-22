"""Backfill / incremental ingestion for the primary source."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Iterable, Optional

from . import config, db
from .http import FetchError
from .sources.base import IncompleteData, SourceAdapter

log = logging.getLogger("peanut_soccer.ingest")


def raw_mtime(adapter: SourceAdapter, season: str, match_id: str) -> Optional[datetime]:
    p = adapter.cache_path(season, match_id)
    if not p.exists():
        return None
    return datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).replace(tzinfo=None, microsecond=0)


def ingest_match(con, adapter: SourceAdapter, season: str, match_id: str, force: bool = False) -> int:
    raw = adapter.fetch_match_raw(season, match_id, force=force)
    match, players = adapter.parse_match(raw, season)
    db.upsert_matches(con, [match])
    # fetched_at = when the raw response was saved, so re-ingesting cached data is byte-identical.
    return db.upsert_player_matches(con, players, fetched_at=raw_mtime(adapter, season, match_id))


def ingest_season(con, adapter: SourceAdapter, season: str, refresh_fixtures: bool = False,
                  force: bool = False, limit: Optional[int] = None) -> dict:
    fixtures = adapter.list_matches(season, refresh=refresh_fixtures)
    db.upsert_matches(con, fixtures)
    todo = [m for m in fixtures if m.status == "finished"]
    if limit:
        todo = todo[:limit]
    stats = {"season": season, "fixtures": len(fixtures), "finished": len(todo),
             "ingested": 0, "rows": 0, "incomplete": 0, "failed": 0}
    for i, m in enumerate(todo, 1):
        try:
            n = ingest_match(con, adapter, season, m.match_id, force=force)
            stats["ingested"] += 1
            stats["rows"] += n
        except IncompleteData as exc:
            stats["incomplete"] += 1
            log.warning("INCOMPLETE %s %s: %s (not cached; will retry next run)", adapter.name, m.match_id, exc)
            db.log_fetch(con, adapter.name, f"match:{m.match_id}", "incomplete", str(exc))
        except FetchError as exc:
            stats["failed"] += 1
            log.error("FAILED %s %s: %s", adapter.name, m.match_id, exc)
        if i % 25 == 0:
            log.info("progress %s %s: %d/%d", adapter.name, season, i, len(todo))
    return stats


def run(con, adapter: SourceAdapter, seasons: Iterable[str], incremental: bool, force: bool = False,
        limit: Optional[int] = None) -> list[dict]:
    results = []
    for season in seasons:
        # Completed seasons use the cached fixture list; the current season is always refreshed
        # so new results are picked up.
        refresh = season == config.CURRENT_SEASON
        if incremental and season != config.CURRENT_SEASON:
            continue
        results.append(ingest_season(con, adapter, season, refresh_fixtures=refresh, force=force, limit=limit))
    db.rebuild_players(con)
    return results
