"""Writes reports/data_quality.md."""
from __future__ import annotations

import random
from pathlib import Path

from . import config
from .sources.fotmob import FotMobAdapter
from .sources.premierleague import PremierLeagueAdapter

LOW, HIGH = 200, 900
APPEARED = "(started OR subbed_on_minute IS NOT NULL)"


def _table(headers, rows) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join("" if v is None else str(v) for v in r) + " |")
    return "\n".join(out)


def build(con, primary: str = "fotmob", other: str = "premierleague", seed: int = 7,
          raw_dir: Path = config.RAW_DIR) -> str:
    L = ["# Data Quality Report — EPL passes attempted", ""]
    L.append(f"Primary source: **{primary}**. Cross-check source: **{other}**.  ")
    gen = con.execute("SELECT max(fetched_at) FROM player_match WHERE source=?", [primary]).fetchone()[0]
    L.append(f"Latest raw fetch in DB: {gen} UTC")
    L += ["", "## Provider definitions of \"passes attempted\"", "",
          f"- **fotmob**: {FotMobAdapter.passes_definition}",
          f"- **premierleague**: {PremierLeagueAdapter.passes_definition}",
          "- Both are Opta (Stats Perform) numbers. PrizePicks' settlement provider for soccer "
          "is NOT verified here — confirm on PrizePicks' official scoring-providers page before "
          "treating either feed as the settlement number.", ""]

    # 1. expected vs fetched
    L += ["## 1. Matches expected vs fetched", ""]
    rows = con.execute(f"""
        SELECT m.season, count(*) AS fixtures,
               count(*) FILTER (WHERE status='finished') AS finished,
               count(DISTINCT pm.match_id) AS fetched,
               count(*) FILTER (WHERE status IN ('postponed','cancelled','abandoned','awarded')) AS irregular
        FROM matches m LEFT JOIN (SELECT DISTINCT match_id, source FROM player_match) pm USING (match_id, source)
        WHERE m.source=? GROUP BY 1 ORDER BY 1""", [primary]).fetchall()
    L.append(_table(["season", "fixtures", "finished (expected)", "fetched", "postponed/cancelled/awarded"], rows))
    missing = con.execute("""
        SELECT m.season, m.match_id, m.date, m.home_team, m.away_team FROM matches m
        WHERE m.source=? AND m.status='finished'
          AND NOT EXISTS (SELECT 1 FROM player_match pm WHERE pm.source=m.source AND pm.match_id=m.match_id)
        ORDER BY m.date""", [primary]).fetchall()
    L += ["", f"Finished matches with no player rows: **{len(missing)}**", ""]
    if missing:
        L.append(_table(["season", "match_id", "date", "home", "away"], missing))
    rc = con.execute(f"""
        SELECT m.season, count(*) AS rows, count(*) FILTER (WHERE {APPEARED}) AS appeared,
               count(DISTINCT player_id) AS players
        FROM player_match pm JOIN matches m USING (match_id, source) WHERE pm.source=? GROUP BY 1 ORDER BY 1""",
                    [primary]).fetchall()
    L += ["", "Row counts (player_match, primary source; `appeared` excludes unused subs):", "",
          _table(["season", "rows", "appeared", "distinct players"], rc), ""]

    # 2. NULLs
    L += ["## 2. NULL passes_attempted / minutes_played (with reason codes)", ""]
    nulls = con.execute(f"""
        SELECT m.season, pm.null_reasons, {APPEARED} AS appeared, count(*) FROM player_match pm
        JOIN matches m USING (match_id, source)
        WHERE pm.source=? AND (passes_attempted IS NULL OR minutes_played IS NULL)
        GROUP BY ALL ORDER BY 1, 4 DESC""", [primary]).fetchall()
    L.append(_table(["season", "null_reasons", "appeared", "rows"], nulls))
    bad = con.execute(f"""
        SELECT pm.match_id, pm.player_name, pm.team, pm.minutes_played, pm.passes_attempted, pm.null_reasons
        FROM player_match pm WHERE pm.source=? AND {APPEARED}
          AND (passes_attempted IS NULL OR minutes_played IS NULL)""", [primary]).fetchall()
    L += ["", f"Players who **appeared** but have NULL passes or minutes: **{len(bad)}**", ""]
    if bad:
        L.append(_table(["match_id", "player", "team", "minutes", "passes_att", "null_reasons"], bad))
    L.append("")

    # 3. minutes > 0, passes = 0
    zero = con.execute("""
        SELECT m.season, pm.match_id, pm.player_name, pm.team, pm.position, pm.started, pm.minutes_played,
               pm.subbed_on_minute, pm.red_card
        FROM player_match pm JOIN matches m USING (match_id, source)
        WHERE pm.source=? AND minutes_played > 0 AND passes_attempted = 0
        ORDER BY pm.minutes_played DESC""", [primary]).fetchall()
    L += ["## 3. minutes > 0 but passes_attempted = 0 (flag for review)", "",
          f"Count: **{len(zero)}**. Mostly late substitutes; anything with high minutes deserves a manual look.", ""]
    if zero:
        L.append(_table(["season", "match_id", "player", "team", "pos", "started", "min", "on_min", "red"], zero))
    L.append("")

    # 4. team totals
    tt = con.execute("""
        SELECT m.season, pm.match_id, pm.team, sum(pm.passes_attempted) AS total,
               count(*) FILTER (WHERE pm.passes_attempted IS NULL AND (pm.started OR pm.subbed_on_minute IS NOT NULL)) AS null_rows
        FROM player_match pm JOIN matches m USING (match_id, source)
        WHERE pm.source=? GROUP BY ALL""", [primary]).fetchall()
    flagged = [r for r in tt if r[3] is None or r[3] < LOW or r[3] > HIGH]
    totals = [r[3] for r in tt if r[3] is not None]
    L += ["## 4. Team totals sanity check", ""]
    if totals:
        L.append(f"Team-matches: **{len(tt)}**; min {min(totals)}, median {sorted(totals)[len(totals)//2]}, "
                 f"max {max(totals)}, mean {sum(totals)/len(totals):.1f}.")
    L += ["", f"Flagged (< {LOW} or > {HIGH}): **{len(flagged)}**", ""]
    if flagged:
        L.append(_table(["season", "match_id", "team", "sum passes_att", "appeared rows w/ NULL"], flagged))

    if primary == "fotmob":
        mism = _fotmob_team_total_check(con, raw_dir)
        L += ["", "Sum of player passes vs FotMob's own team \"Passes\" stat (from cached raw):",
              f"checked **{mism['checked']}** team-matches, mismatches **{len(mism['bad'])}**, "
              f"team stat unavailable **{mism['unavailable']}**.", ""]
        if mism["bad"]:
            L.append(_table(["match_id", "team", "sum players", "team stat"], mism["bad"]))
    L.append("")

    # 5. cross-check
    L += ["## 5. Cross-check vs premierleague.com (Opta)", ""]
    xs = con.execute("""
        SELECT count(*), count(*) FILTER (WHERE outcome IN ('exact','diff')), count(*) FILTER (WHERE outcome='exact'),
               avg(abs_diff) FILTER (WHERE outcome IN ('exact','diff')), count(DISTINCT primary_match_id),
               count(*) FILTER (WHERE primary_minutes IS NOT NULL AND other_minutes IS NOT NULL),
               count(*) FILTER (WHERE primary_minutes = other_minutes)
        FROM crosscheck WHERE primary_source=? AND other_source=?""", [primary, other]).fetchone()
    if xs[0]:
        L.append(f"Matches compared: **{xs[4]}**; player rows: **{xs[0]}**; both sources have a value: **{xs[1]}**; "
                 f"exact passes_attempted match: **{xs[2]}** (**{100*xs[2]/xs[1]:.2f}%**); "
                 f"mean absolute difference: **{xs[3]:.3f}**.  ")
        L.append(f"Minutes agree exactly on {xs[6]}/{xs[5]} rows (reported for information; FotMob and the PL "
                 f"feed round stoppage time differently).")
        oc = con.execute("SELECT outcome, join_method, count(*) FROM crosscheck WHERE primary_source=? AND other_source=? "
                         "GROUP BY 1, 2 ORDER BY 3 DESC", [primary, other]).fetchall()
        L += ["", _table(["outcome", "join_method", "rows"], oc), "",
              "Join: Opta player id. The PL feed omits Opta ids for some 2024-25 fixtures, so those rows fall back "
              "to an exact accent-insensitive name match (same side), then a unique last-name match. Names that "
              "still don't match are left unmatched (`unresolved`), not guessed. `null_in_one` means one source "
              "has the stat and the other doesn't. The PL feed drops zero-valued stats, so FotMob `0` vs "
              "PL absent is expected there.", ""]
        big = con.execute("""
            SELECT primary_match_id, other_match_id, player_name, team, primary_passes, other_passes, abs_diff,
                   primary_minutes, other_minutes
            FROM crosscheck WHERE primary_source=? AND other_source=? AND abs_diff > 3 ORDER BY abs_diff DESC""",
                          [primary, other]).fetchall()
        L.append(f"Disagreements > 3 passes: **{len(big)}**")
        if big:
            L += ["", _table(["fotmob match", "PL fixture", "player", "team", "fotmob", "PL", "abs diff",
                              "fotmob min", "PL min"], big)]
        other_rows = con.execute("""
            SELECT primary_match_id, other_match_id, player_name, team, outcome, join_method, primary_passes,
                   other_passes, primary_minutes, other_minutes
            FROM crosscheck WHERE primary_source=? AND other_source=? AND outcome NOT IN ('exact','diff')""",
                                 [primary, other]).fetchall()
        if other_rows:
            L += ["", "Rows present in only one source or NULL in one:", "",
                  _table(["fotmob match", "PL fixture", "player", "team", "outcome", "join", "fotmob", "PL",
                          "fotmob min", "PL min"], other_rows)]
        xr = con.execute("SELECT primary_match_id, other_match_id, method, note FROM match_xref "
                         "WHERE primary_source=? AND other_source=? AND note IS NOT NULL", [primary, other]).fetchall()
        if xr:
            L += ["", "Match links that failed or were rejected:", "",
                  _table(["fotmob match", "PL fixture", "method", "note"], xr)]
    else:
        L.append("Cross-check has not been run yet (`python -m peanut_soccer crosscheck`).")
    L.append("")

    # 6. fetch log
    fl = con.execute("SELECT source, status, count(*) FROM fetch_log GROUP BY ALL ORDER BY 1, 2").fetchall()
    L += ["## 6. Fetch log summary", "", _table(["source", "status", "requests"], fl), ""]

    # 7. spot checks
    rng = random.Random(seed)
    keys = con.execute(f"SELECT match_id, player_id FROM player_match WHERE source=? AND {APPEARED} "
                       "ORDER BY match_id, player_id", [primary]).fetchall()
    L += ["## 7. Five random player-match rows for manual spot-check", "",
          "Open `https://www.fotmob.com/match/<match_id>` and compare the player's *Accurate passes* "
          "(x/**y**, y = attempted) and minutes.", ""]
    cols = [d[0] for d in con.execute("SELECT * FROM player_match LIMIT 0").description]
    for mid, pid in rng.sample(keys, min(5, len(keys))):
        r = con.execute("SELECT pm.*, m.date, m.home_team, m.away_team FROM player_match pm "
                        "JOIN matches m USING (match_id, source) WHERE pm.source=? AND pm.match_id=? AND pm.player_id=?",
                        [primary, mid, pid]).fetchone()
        names = cols + ["match_date_utc", "home_team", "away_team"]
        L += [f"**{r[3]}** — {r[-2]} v {r[-1]} ({r[-3]})", "", "```"]
        L += [f"{n:18s} {v}" for n, v in zip(names, r)]
        L += ["```", ""]
    return "\n".join(L)


def _fotmob_team_total_check(con, raw_dir: Path) -> dict:
    import json
    res = {"checked": 0, "bad": [], "unavailable": 0}
    ms = con.execute("SELECT DISTINCT m.season, m.match_id FROM matches m JOIN player_match pm USING (match_id, source) "
                     "WHERE m.source='fotmob'").fetchall()
    for season, mid in ms:
        p = Path(raw_dir) / "fotmob" / season / f"{mid}.json"
        if not p.exists():
            res["unavailable"] += 2
            continue
        tot = FotMobAdapter.team_pass_totals(json.loads(p.read_text(encoding="utf-8")))
        if tot is None:
            res["unavailable"] += 2
            continue
        sums = dict(con.execute("SELECT is_home, sum(passes_attempted) FROM player_match WHERE source='fotmob' "
                                "AND match_id=? GROUP BY 1", [mid]).fetchall())
        teams = dict(con.execute("SELECT is_home, any_value(team) FROM player_match WHERE source='fotmob' "
                                 "AND match_id=? GROUP BY 1", [mid]).fetchall())
        for is_home, stat in ((True, tot[0]), (False, tot[1])):
            res["checked"] += 1
            if sums.get(is_home) != stat:
                res["bad"].append((mid, teams.get(is_home), sums.get(is_home), stat))
    return res


def write(con, path: Path = config.REPORTS_DIR / "data_quality.md", **kw) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build(con, **kw), encoding="utf-8")
    return path
