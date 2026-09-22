"""Project-wide paths and constants."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(os.environ.get("PEANUT_SOCCER_ROOT", Path(__file__).resolve().parent.parent))
RAW_DIR = ROOT / "raw"
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "soccer.duckdb"
REPORTS_DIR = ROOT / "reports"
LOG_DIR = ROOT / "logs"

# Seasons in scope. Label format used everywhere in this project: "YYYY-YY".
SEASONS = ["2024-25", "2025-26", "2026-27"]
CURRENT_SEASON = "2026-27"

# Politeness: minimum seconds between any two network requests to the same source.
MIN_REQUEST_INTERVAL_S = 3.0
MAX_RETRIES = 4
BACKOFF_BASE_S = 5.0  # 5, 10, 20, 40 seconds

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"
)


def season_start_year(season: str) -> int:
    """'2025-26' -> 2025."""
    return int(season.split("-")[0])
