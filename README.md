# PeanutProps Soccer — Passes Attempted: Data Layer

Prompt 1 of 3: the raw data layer only. There's no projection math, no minutes model, and no odds or PrizePicks lines here.

Scope: English Premier League, seasons **2024-25**, **2025-26** (complete) and **2026-27** (in progress).

## Sources

| Role | Source | What it gives | Provider of the number |
|---|---|---|---|
| **Primary** | FotMob (`fotmob.com/api/data/...`) | Per-player per-match *Accurate passes* `value/total` (total = **attempted**), minutes, lineup (starter/bench), sub minutes, cards, position group. One request per match. | **Opta (Stats Perform).** Players carry `optaId`, and player totals sum exactly to the team `total_pass` on premierleague.com. |
| **Cross-check** | Premier League official API (`footballapi.pulselive.com`) | Opta stat names `total_pass`, `accurate_pass`, `mins_played` per player per fixture. About 30 requests per match, so it's only used on samples. | **Opta (Stats Perform)**, the league's official feed |
| Rejected | Sofascore | HTTP 403 from Sofascore's own edge (Varnish) on every endpoint from this environment. It could not be verified, so nothing was built on it. | (Sofascore's own data, not Opta) |
| Rejected | FBref | The Cloudflare challenge blocks automated access. Opta advanced stats (including passes) were removed in Jan 2026 and are no longer updated. | n/a |

Both working sources use the **Opta** definition of a pass attempt. That covers every attempted pass: open play and set pieces, including crosses, long balls, goal kicks and GK throws.
> ⚠️ **PrizePicks settlement provider is not verified.** PrizePicks lists its official scoring partners on its help center (Sportradar, Genius, Stats Perform, …). Confirm which one settles soccer passes before trusting either feed as the settlement number. If it's Sportradar, the numbers can differ slightly from Opta.

## Setup (Windows, `C:\peanut_soccer`)

```powershell
git clone <this repo> C:\peanut_soccer
cd C:\peanut_soccer
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

(macOS/Linux: `python3 -m venv .venv && source .venv/bin/activate`.)

## Run

| Task | Command |
|---|---|
| **Full backfill** (all seasons; cache-first, safe to re-run) | `python -m peanut_soccer backfill` |
| **Incremental update** (current season: fetches only newly finished matches) | `python -m peanut_soccer update` |
| Cross-check vs premierleague.com (8 random matches per season) | `python -m peanut_soccer crosscheck` |
| Data quality report → `reports/data_quality.md` | `python -m peanut_soccer report` |
| Tests | `python -m pytest` |

Options: `--seasons 2025-26 2026-27`, `--force` (re-fetch cached matches), `--limit N` (first N matches per season), `--per-season N` (cross-check sample size), `-v`.

A full backfill is about 810 requests at 3 s spacing, roughly 45 minutes. Re-runs only fetch what isn't cached.

## Layout

```
peanut_soccer/
  config.py            paths, seasons, rate-limit settings
  http.py              RateLimiter (>=3 s between requests), retries w/ exponential backoff, FETCH log line per request
  sources/base.py      SourceAdapter interface + MatchRecord / PlayerMatchRecord + NULL reason codes
  sources/fotmob.py    primary adapter
  sources/premierleague.py  cross-check adapter
  db.py                DuckDB schema + idempotent upserts (INSERT OR REPLACE on primary keys)
  ingest.py            backfill / update
  crosscheck.py        link matches across sources, compare passes_attempted
  report.py            reports/data_quality.md
raw/<source>/<season>/<match_id>.json   raw responses cached before parsing (git-ignored)
data/soccer.duckdb                      database (git-ignored)
logs/pipeline.log                       run log (git-ignored)
tests/fixtures/                         real saved raw responses used by the parser tests
```

To add or swap a source, write a new `SourceAdapter` subclass with `list_matches`, `fetch_match_raw` and `parse_match`. The database and downstream code don't change.

## Database (`data/soccer.duckdb`)

- `matches(match_id, source, season, date [UTC], home_team, away_team, home_score, away_score, status, round)`, PK `(match_id, source)`
- `player_match(match_id, source, player_id, player_name, team, opponent, is_home, position, started, minutes_played, passes_attempted, passes_completed, subbed_on_minute, subbed_off_minute, red_card, opta_player_id, null_reasons, fetched_at)`, PK `(match_id, source, player_id)`
- `players(player_id, source, player_name, current_team, primary_position, opta_player_id)`, derived from `player_match`
- `fetch_log(source, url_or_endpoint, status, error, fetched_at)`: one row per network request
- `match_xref`, `crosscheck`: cross-source links and per-player comparison results

Columns beyond the spec: `round`, `opta_player_id` (the cross-source join key; both sources expose Opta IDs) and `null_reasons`.

### NULL handling (fail closed)

A value is never defaulted. Every NULL in `player_match` has an entry in `null_reasons` (`field:code;field:code`):

| code | meaning |
|---|---|
| `unused_sub` | named on the bench, never came on. Minutes and passes are NULL, **not 0** |
| `field_absent_in_source` | player appeared but the source omitted this stat |
| `player_stats_block_missing` | player in the lineup but the source has no stats block for them |
| `unparseable_value` | the field exists but isn't an integer |
| `not_subbed_on` / `not_subbed_off` | structural: a starter has no sub-on minute; a player who finished has no sub-off minute |
| `position_absent_in_source` | no position code |
| `unrecognized_card_code` | `red_card` only: a card code we have not verified (known: FotMob `Yellow`/`Red`/`YellowRed`; PL `Y`/`R`) |

FotMob reports explicit zeros (`0/0`) for players who appeared and made no passes, so a stored `0` is a real source zero.

Other conventions:
- `position` is the player's position group from FotMob's `usualPlayingPositionId` (GK/DEF/MID/FWD). FotMob's per-match slot codes aren't decoded yet.
- `subbed_on_minute` and `subbed_off_minute` are the source's minute. For stoppage-time subs FotMob reports 90.
- Matches whose stats aren't published yet (finished but no `playerStats`) are **not cached**. They're logged as `incomplete` and retried on the next run.

## Current state (as of 2026-09-22 build)

| season | fixtures | finished | fetched | player_match rows | player appearances | unique players |
|---|---|---|---|---|---|---|
| 2024-25 | 380 | 380 | 380 | 15,188 | 11,567 | 562 |
| 2025-26 | 380 | 380 | 380 | 15,189 | 11,492 | 537 |
| 2026-27 | 380 | 50 | 50 | 1,999 | 1,538 | 421 |
| all seasons | | 810 | 810 | 32,376 | 24,597 | 862 |

Cross-check (24 matches, 8 per season): 718/718 comparable player rows have exact passes_attempted matches, with 0 disagreements > 3. Every team-match's summed player passes equals FotMob's own team pass total (1,620/1,620). Details are in `reports/data_quality.md`.

## Open issues

1. **PrizePicks settlement provider not confirmed.** Both feeds here are Opta. If PrizePicks settles soccer on Sportradar or Genius, their pass counts can differ from Opta.
2. **Sofascore and FBref not usable from the build environment** (403 / Cloudflare). If an independent (non-Opta) cross-check is wanted, re-probe Sofascore from a residential connection before building an adapter.
3. **FotMob is an unofficial, undocumented API.** Endpoints and fields can change without notice, and its terms of use don't grant scraping rights. Keep request volume low (3 s spacing, cache-first) and use it for personal research only. The parser fails closed if the response shape changes.
4. **The PL feed omits Opta player IDs for some 2024-25 fixtures and drops zero-valued stats.** The cross-check handles this with a name fallback and `null_in_one` outcomes. Two name variants (`Gabriel` / `Gabriel Magalhães`, `Hwang Hee-Chan` / `Hee-Chan Hwang`) stay unmatched on purpose.
5. **Minutes differ by 1 on 2/727 cross-checked rows** (stoppage-time rounding). Passes agree on those rows.
6. **378 player-matches have minutes > 0 but 0 passes.** Almost all are late subs. The two 30-minute cases (Nathan Collins 2025-26 v Aston Villa, Darwin Núñez 2024-25 v Man Utd) were checked against the official PL feed, which also shows no passes (6 and 3 touches).
7. **5 team-matches are under 200 passes** (low 168, Burnley 2025-26). They match the source team totals, so they're recorded as real rather than treated as errors.
8. `position` is a coarse group (GK/DEF/MID/FWD) from the player's usual position, not the in-match slot.
