"""DuckDB schema and idempotent upserts."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

import duckdb

from . import config
from .sources.base import MatchRecord, PlayerMatchRecord

SCHEMA = """
CREATE TABLE IF NOT EXISTS matches (
    match_id     VARCHAR NOT NULL,
    source       VARCHAR NOT NULL,
    season       VARCHAR NOT NULL,
    date         TIMESTAMP,            -- kickoff, UTC
    home_team    VARCHAR,
    away_team    VARCHAR,
    home_score   INTEGER,
    away_score   INTEGER,
    status       VARCHAR,
    round        VARCHAR,
    PRIMARY KEY (match_id, source)
);

CREATE TABLE IF NOT EXISTS player_match (
    match_id           VARCHAR NOT NULL,
    source             VARCHAR NOT NULL,
    player_id          VARCHAR NOT NULL,
    player_name        VARCHAR,
    team               VARCHAR,
    opponent           VARCHAR,
    is_home            BOOLEAN,
    position           VARCHAR,        -- GK / DEF / MID / FWD
    started            BOOLEAN,
    minutes_played     INTEGER,
    passes_attempted   INTEGER,
    passes_completed   INTEGER,
    subbed_on_minute   INTEGER,
    subbed_off_minute  INTEGER,
    red_card           BOOLEAN,
    opta_player_id     VARCHAR,        -- cross-source join key
    null_reasons       VARCHAR,        -- "field:reason_code;..." for every NULL above
    fetched_at         TIMESTAMP,
    PRIMARY KEY (match_id, source, player_id)
);

CREATE TABLE IF NOT EXISTS players (
    player_id         VARCHAR NOT NULL,
    source            VARCHAR NOT NULL,
    player_name       VARCHAR,
    current_team      VARCHAR,
    primary_position  VARCHAR,
    opta_player_id    VARCHAR,
    PRIMARY KEY (player_id, source)
);

CREATE TABLE IF NOT EXISTS fetch_log (
    source           VARCHAR,
    url_or_endpoint  VARCHAR,
    status           VARCHAR,
    error            VARCHAR,
    fetched_at       TIMESTAMP
);

-- Link between the same real match in two sources (built by the cross-check step).
CREATE TABLE IF NOT EXISTS match_xref (
    primary_source    VARCHAR NOT NULL,
    primary_match_id  VARCHAR NOT NULL,
    other_source      VARCHAR NOT NULL,
    other_match_id    VARCHAR,
    method            VARCHAR,
    note              VARCHAR,
    PRIMARY KEY (primary_source, primary_match_id, other_source)
);

-- One row per compared player-match (primary vs cross-check source).
CREATE TABLE IF NOT EXISTS crosscheck (
    primary_source     VARCHAR NOT NULL,
    primary_match_id   VARCHAR NOT NULL,
    other_source       VARCHAR NOT NULL,
    other_match_id     VARCHAR,
    opta_player_id     VARCHAR NOT NULL,  -- join key (Opta id, or a name key when unresolved)
    player_name        VARCHAR,
    team               VARCHAR,
    primary_passes     INTEGER,
    other_passes       INTEGER,
    primary_minutes    INTEGER,
    other_minutes      INTEGER,
    abs_diff           INTEGER,
    outcome            VARCHAR,   -- exact | diff | missing_in_primary | missing_in_other | null_in_one
    join_method        VARCHAR,   -- opta_id | name_exact | name_lastname | unresolved
    checked_at         TIMESTAMP,
    PRIMARY KEY (primary_source, primary_match_id, other_source, opta_player_id)
);
"""


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def connect(path: Optional[Path] = None) -> duckdb.DuckDBPyConnection:
    path = Path(path or config.DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(path))
    con.execute(SCHEMA)
    return con


def log_fetch(con, source: str, url: str, status: str, error: Optional[str]) -> None:
    con.execute("INSERT INTO fetch_log VALUES (?, ?, ?, ?, ?)", [source, url, status, error, utcnow()])


def upsert_matches(con, matches: Iterable[MatchRecord]) -> int:
    rows = [(m.match_id, m.source, m.season, m.date_utc, m.home_team, m.away_team,
             m.home_score, m.away_score, m.status, m.round) for m in matches]
    if rows:
        con.executemany("INSERT OR REPLACE INTO matches VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
    return len(rows)


def upsert_player_matches(con, recs: Iterable[PlayerMatchRecord], fetched_at: Optional[datetime] = None) -> int:
    ts = fetched_at or utcnow()
    rows = [(r.match_id, r.source, r.player_id, r.player_name, r.team, r.opponent, r.is_home, r.position,
             r.started, r.minutes_played, r.passes_attempted, r.passes_completed, r.subbed_on_minute,
             r.subbed_off_minute, r.red_card, r.opta_player_id, r.null_reason_str(), ts) for r in recs]
    if rows:
        con.executemany("INSERT OR REPLACE INTO player_match VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    return len(rows)


def rebuild_players(con) -> None:
    """Derive the players table from player_match (latest team, most common position)."""
    con.execute("DELETE FROM players")
    con.execute("""
        INSERT INTO players
        WITH apps AS (
            SELECT pm.*, m.date FROM player_match pm
            JOIN matches m USING (match_id, source)
        ),
        latest AS (
            SELECT player_id, source, arg_max(player_name, date) AS player_name,
                   arg_max(team, date) AS current_team, max(opta_player_id) AS opta_player_id
            FROM apps GROUP BY player_id, source
        ),
        pos AS (
            SELECT player_id, source, position, count(*) AS n,
                   row_number() OVER (PARTITION BY player_id, source ORDER BY count(*) DESC, position) AS rk
            FROM apps WHERE position IS NOT NULL GROUP BY player_id, source, position
        )
        SELECT l.player_id, l.source, l.player_name, l.current_team, p.position, l.opta_player_id
        FROM latest l LEFT JOIN pos p ON p.player_id = l.player_id AND p.source = l.source AND p.rk = 1
    """)
