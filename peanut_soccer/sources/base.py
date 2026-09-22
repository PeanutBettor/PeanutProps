"""Common interface every source adapter implements.

Downstream code (database, cross-check, report) only sees MatchRecord / PlayerMatchRecord,
so a source can be swapped without touching anything else.
"""
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from .. import config

log = logging.getLogger("peanut_soccer.sources")


# ---- reason codes for NULL values -------------------------------------------------------
# A NULL value in player_match always carries one of these codes in `null_reasons`,
# formatted as "field:code;field:code".
R_UNUSED_SUB = "unused_sub"                # on the bench, never came on
R_FIELD_ABSENT = "field_absent_in_source"  # player appeared but the source omitted this stat
R_NOT_SUBBED_ON = "not_subbed_on"          # subbed_on_minute for starters
R_NOT_SUBBED_OFF = "not_subbed_off"        # subbed_off_minute for players who finished
R_NO_POSITION = "position_absent_in_source"
R_UNPARSEABLE = "unparseable_value"
R_STATS_MISSING = "player_stats_block_missing"


@dataclass
class MatchRecord:
    match_id: str
    source: str
    season: str
    date_utc: Optional[datetime]
    home_team: str
    away_team: str
    home_score: Optional[int]
    away_score: Optional[int]
    status: str  # finished | scheduled | live | cancelled | postponed | awarded | unknown
    round: Optional[str] = None


@dataclass
class PlayerMatchRecord:
    match_id: str
    source: str
    player_id: str
    player_name: str
    team: str
    opponent: str
    is_home: bool
    position: Optional[str]
    started: bool
    minutes_played: Optional[int]
    passes_attempted: Optional[int]
    passes_completed: Optional[int]
    subbed_on_minute: Optional[int]
    subbed_off_minute: Optional[int]
    red_card: Optional[bool]
    opta_player_id: Optional[str] = None
    null_reasons: dict = field(default_factory=dict)  # field -> reason code

    def null_reason_str(self) -> Optional[str]:
        if not self.null_reasons:
            return None
        return ";".join(f"{k}:{v}" for k, v in sorted(self.null_reasons.items()))


class IncompleteData(Exception):
    """Raised when a response is not complete enough to cache (e.g. stats not yet published)."""


class SourceAdapter(ABC):
    name: str = "base"
    # Human-readable statement of which provider's "passes attempted" this source reports.
    passes_definition: str = ""

    def __init__(self, client=None, raw_dir: Path = config.RAW_DIR):
        self.client = client
        self.raw_dir = Path(raw_dir)

    # ---- cache helpers ------------------------------------------------------------------
    def cache_path(self, season: str, key: str) -> Path:
        return self.raw_dir / self.name / season / f"{key}.json"

    def read_cache(self, season: str, key: str) -> Optional[dict]:
        p = self.cache_path(season, key)
        if p.exists():
            log.info("CACHE-HIT %s %s", self.name, p)
            return json.loads(p.read_text(encoding="utf-8"))
        return None

    def write_cache(self, season: str, key: str, payload: dict) -> Path:
        p = self.cache_path(season, key)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        tmp.replace(p)
        return p

    # ---- interface ----------------------------------------------------------------------
    @abstractmethod
    def list_matches(self, season: str, refresh: bool = False) -> list[MatchRecord]:
        """All league fixtures for a season (any status)."""

    @abstractmethod
    def fetch_match_raw(self, season: str, match_id: str, force: bool = False) -> dict:
        """Return raw payload for one match; cache-first unless force=True."""

    @abstractmethod
    def parse_match(self, raw: dict, season: str) -> tuple[MatchRecord, list[PlayerMatchRecord]]:
        """Pure function: raw payload -> records. No network access."""
