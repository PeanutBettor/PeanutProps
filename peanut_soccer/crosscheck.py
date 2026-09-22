"""Compare passes_attempted between the primary and cross-check source on a sample of matches.

Disagreements are recorded, never "fixed".
"""
from __future__ import annotations

import difflib
import logging
import random
import unicodedata
from datetime import timedelta
from typing import Optional

from . import db
from .http import FetchError
from .ingest import ingest_match
from .sources.base import IncompleteData, MatchRecord, SourceAdapter

log = logging.getLogger("peanut_soccer.crosscheck")

MIN_PLAYER_OVERLAP = 0.8


def _norm(s: str) -> str:
    s = s.lower().replace("&", "and")
    for junk in ("afc ", " fc", "a.f.c.", "football club"):
        s = s.replace(junk, " ")
    return " ".join(s.split())


def _name_score(a: MatchRecord, b: MatchRecord) -> float:
    r = difflib.SequenceMatcher
    return r(None, _norm(a.home_team), _norm(b.home_team)).ratio() + r(None, _norm(a.away_team), _norm(b.away_team)).ratio()


def find_counterpart(m: MatchRecord, others: list[MatchRecord]) -> tuple[Optional[MatchRecord], str]:
    same_ko = [o for o in others if o.date_utc == m.date_utc]
    method = "same_kickoff+team_names"
    if not same_ko:
        same_ko = [o for o in others if o.date_utc and m.date_utc and abs(o.date_utc - m.date_utc) <= timedelta(days=1)]
        method = "kickoff_within_1d+team_names"
    if not same_ko:
        return None, "no_kickoff_candidate"
    best = max(same_ko, key=lambda o: _name_score(m, o))
    if _name_score(m, best) < 1.2:  # both names must be reasonably similar
        return None, f"no_name_match(best={best.home_team} v {best.away_team})"
    return best, method


def pick_sample(con, primary: str, seasons: list[str], n_per_season: int, seed: int) -> list[tuple[str, str]]:
    rng = random.Random(seed)
    out = []
    for season in seasons:
        ids = [r[0] for r in con.execute(
            "SELECT DISTINCT m.match_id FROM matches m JOIN player_match pm USING (match_id, source) "
            "WHERE m.source=? AND m.season=? AND m.status='finished' ORDER BY m.match_id",
            [primary, season]).fetchall()]
        out += [(season, i) for i in rng.sample(ids, min(n_per_season, len(ids)))]
    return out


def run(con, primary: SourceAdapter, other: SourceAdapter, seasons: list[str],
        n_per_season: int = 8, seed: int = 2026) -> dict:
    sample = pick_sample(con, primary.name, seasons, n_per_season, seed)
    fixtures_by_season = {s: other.list_matches(s) for s in {s for s, _ in sample}}
    db.upsert_matches(con, [m for ms in fixtures_by_season.values() for m in ms])
    linked = 0
    for season, pid in sample:
        pm = con.execute("SELECT * FROM matches WHERE source=? AND match_id=?", [primary.name, pid]).fetchone()
        m = MatchRecord(match_id=pm[0], source=pm[1], season=pm[2], date_utc=pm[3], home_team=pm[4],
                        away_team=pm[5], home_score=pm[6], away_score=pm[7], status=pm[8], round=pm[9])
        cp, method = find_counterpart(m, fixtures_by_season[season])
        note = None
        if cp is None:
            con.execute("INSERT OR REPLACE INTO match_xref VALUES (?,?,?,?,?,?)",
                        [primary.name, pid, other.name, None, method, "UNLINKED"])
            log.warning("XREF-FAIL %s %s: %s", primary.name, pid, method)
            continue
        try:
            ingest_match(con, other, season, cp.match_id)
        except (IncompleteData, FetchError) as exc:
            con.execute("INSERT OR REPLACE INTO match_xref VALUES (?,?,?,?,?,?)",
                        [primary.name, pid, other.name, cp.match_id, method, f"FETCH-FAILED: {exc}"[:500]])
            continue
        overlap = _player_overlap(con, primary.name, pid, other.name, cp.match_id)
        if overlap < MIN_PLAYER_OVERLAP:
            note = f"LOW_PLAYER_OVERLAP={overlap:.2f}"
            log.warning("XREF %s %s -> %s %s: %s", primary.name, pid, other.name, cp.match_id, note)
        con.execute("INSERT OR REPLACE INTO match_xref VALUES (?,?,?,?,?,?)",
                    [primary.name, pid, other.name, cp.match_id, f"{method};overlap={overlap:.2f}", note])
        if note is None:
            _compare(con, primary.name, pid, other.name, cp.match_id)
            linked += 1
    return summarize(con, primary.name, other.name) | {"sampled": len(sample), "linked": linked}


APPEARED_Q = ("SELECT opta_player_id, player_name, team, passes_attempted, minutes_played, is_home FROM player_match "
              "WHERE source=? AND match_id=? AND (started OR subbed_on_minute IS NOT NULL)")


def _name_key(name: str) -> str:
    s = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode().lower()
    return " ".join(s.replace("-", " ").replace(".", " ").replace("'", "").split())


def _keyed_rows(con, ps, pid, os_, oid) -> tuple[dict, dict, dict]:
    """Return (primary_by_key, other_by_key, join_method_by_key).

    Join on Opta player id. If the other source omits the Opta id for a player (the PL feed does
    this for some 2024-25 fixtures), fall back to an exact accent-insensitive name match on the
    same side of the match, then to a unique last-name match. Anything else stays unmatched.
    """
    a_rows = con.execute(APPEARED_Q, [ps, pid]).fetchall()
    b_rows = con.execute(APPEARED_Q, [os_, oid]).fetchall()
    a = {r[0] or f"noopta:{ps}:{r[1]}": r for r in a_rows}
    method = {k: "opta_id" for k in a}
    b = {}
    for r in b_rows:
        if r[0]:
            b[r[0]] = r
            continue
        side = [(k, x) for k, x in a.items() if x[5] == r[5]]
        exact = [k for k, x in side if _name_key(x[1]) == _name_key(r[1])]
        last = [k for k, x in side if _name_key(x[1]).split()[-1:] == _name_key(r[1]).split()[-1:]]
        if len(exact) == 1 and exact[0] not in b:
            b[exact[0]] = r
            method[exact[0]] = "name_exact"
        elif not exact and len(last) == 1 and last[0] not in b:
            b[last[0]] = r
            method[last[0]] = "name_lastname"
        else:
            key = f"unresolved:{os_}:{r[1]}"
            b[key] = r
            method[key] = "unresolved"
    return a, b, method


def _player_overlap(con, ps, pid, os_, oid) -> float:
    a, b, _ = _keyed_rows(con, ps, pid, os_, oid)
    ka, kb = set(a), set(b)
    return len(ka & kb) / len(ka | kb) if (ka | kb) else 0.0


def _compare(con, ps, pid, os_, oid) -> None:
    a, b, method = _keyed_rows(con, ps, pid, os_, oid)
    now = db.utcnow()
    rows = []
    for key in sorted(set(a) | set(b)):
        ra, rb = a.get(key), b.get(key)
        pa, pb = (ra[3] if ra else None), (rb[3] if rb else None)
        if ra is None:
            outcome = "missing_in_primary"
        elif rb is None:
            outcome = "missing_in_other"
        elif pa is None or pb is None:
            outcome = "null_in_one"
        else:
            outcome = "exact" if pa == pb else "diff"
        ref = ra or rb
        rows.append((ps, pid, os_, oid, key, ref[1], ref[2], pa, pb, ra[4] if ra else None, rb[4] if rb else None,
                     abs(pa - pb) if pa is not None and pb is not None else None, outcome,
                     method.get(key, "opta_id"), now))
    con.executemany("INSERT OR REPLACE INTO crosscheck VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)


def summarize(con, ps: str, os_: str) -> dict:
    r = con.execute("""
        SELECT count(DISTINCT primary_match_id), count(*),
               count(*) FILTER (WHERE outcome IN ('exact','diff')),
               count(*) FILTER (WHERE outcome='exact'),
               avg(abs_diff) FILTER (WHERE outcome IN ('exact','diff')),
               count(*) FILTER (WHERE abs_diff > 3)
        FROM crosscheck WHERE primary_source=? AND other_source=?""", [ps, os_]).fetchone()
    compared = r[2] or 0
    return {"matches_compared": r[0], "player_rows": r[1], "both_present": compared, "exact": r[3],
            "exact_rate": (r[3] / compared) if compared else None, "mean_abs_diff": r[4], "diff_gt_3": r[5]}
