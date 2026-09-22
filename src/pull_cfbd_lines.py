"""Pull 2026 regular-season betting lines from CollegeFootballData (weeks 1-4)."""

import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

BASE_URL = "https://api.collegefootballdata.com/lines"
YEAR = 2026
SEASON_TYPE = "regular"
WEEKS = range(1, 5)
SLEEP_SECONDS = 0.5
TIMEOUT_SECONDS = 30

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "data" / f"lines_{YEAR}.csv"

COLUMNS = [
    "season",
    "week",
    "gameId",
    "startDate",
    "homeTeam",
    "awayTeam",
    "provider",
    "spreadOpen",
    "spreadClose",
    "totalOpen",
    "totalClose",
    "homeMoneylineOpen",
    "homeMoneylineClose",
    "awayMoneylineOpen",
    "awayMoneylineClose",
]


def load_api_key() -> str:
    load_dotenv(ROOT / ".env")
    load_dotenv()  # also honor a .env in the current working directory
    key = os.getenv("CFBD_API_KEY", "").strip()
    if not key:
        sys.exit("ERROR: CFBD_API_KEY not found. Add CFBD_API_KEY=<your key> to .env")
    return key


def fetch_week(session: requests.Session, week: int) -> list:
    params = {"year": YEAR, "seasonType": SEASON_TYPE, "week": week}
    resp = session.get(BASE_URL, params=params, timeout=TIMEOUT_SECONDS)

    if resp.status_code == 401:
        sys.exit(
            "ERROR: 401 Unauthorized from CFBD. Your CFBD_API_KEY is missing, "
            "invalid, or expired. Check .env and your key at "
            "https://collegefootballdata.com/key"
        )
    if resp.status_code == 429:
        sys.exit("ERROR: 429 Too Many Requests. CFBD rate limit / monthly quota hit.")
    resp.raise_for_status()

    data = resp.json()
    if not isinstance(data, list):
        raise ValueError(f"Unexpected response for week {week}: {str(data)[:200]}")
    return data


def flatten(games: list) -> list:
    rows = []
    for g in games:
        base = {
            "season": g.get("season"),
            "week": g.get("week"),
            "gameId": g.get("id"),
            "startDate": g.get("startDate"),
            "homeTeam": g.get("homeTeam"),
            "awayTeam": g.get("awayTeam"),
        }
        for line in g.get("lines") or []:
            rows.append(
                {
                    **base,
                    "provider": line.get("provider"),
                    "spreadOpen": line.get("spreadOpen"),
                    "spreadClose": line.get("spread"),
                    "totalOpen": line.get("overUnderOpen"),
                    "totalClose": line.get("overUnder"),
                    "homeMoneylineOpen": line.get("homeMoneylineOpen"),
                    "homeMoneylineClose": line.get("homeMoneyline"),
                    "awayMoneylineOpen": line.get("awayMoneylineOpen"),
                    "awayMoneylineClose": line.get("awayMoneyline"),
                }
            )
    return rows


def main() -> None:
    key = load_api_key()

    session = requests.Session()
    session.headers.update(
        {"Authorization": f"Bearer {key}", "Accept": "application/json"}
    )

    all_rows = []
    for i, week in enumerate(WEEKS):
        if i > 0:
            time.sleep(SLEEP_SECONDS)
        games = fetch_week(session, week)
        rows = flatten(games)
        print(f"Week {week:>2}: {len(games):>3} games, {len(rows):>4} lines")
        all_rows.extend(rows)

    df = pd.DataFrame(all_rows, columns=COLUMNS)
    numeric_cols = COLUMNS[7:]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    df = df.sort_values(["week", "startDate", "gameId", "provider"]).reset_index(drop=True)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)

    print(f"\nSaved {len(df)} rows to {OUT_PATH}")
    print("\nSample (5 rows):")
    with pd.option_context("display.max_columns", None, "display.width", 200):
        print(df.head(5).to_string(index=False) if not df.empty else "(no rows)")


if __name__ == "__main__":
    main()
