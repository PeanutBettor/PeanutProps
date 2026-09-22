"""Premier League official stats API adapter (CROSS-CHECK source).

Endpoints (verified live 2026-09-22; unauthenticated JSON behind premierleague.com):
  seasons:      https://footballapi.pulselive.com/football/competitions/1/compseasons
  fixtures:     https://footballapi.pulselive.com/football/fixtures?comps=1&compSeasons=<id>&page=N&pageSize=100&sort=asc
  fixture:      https://footballapi.pulselive.com/football/fixtures/<fixtureId>   (lineups, subs, cards)
  player-match: https://footballapi.pulselive.com/football/stats/player/<playerId>?fixtures=<fixtureId>

Passes attempted = stat "total_pass"; completed = "accurate_pass"; minutes = "mins_played".
These are raw Opta F9/F24 stat names. Opta omits zero-valued stats from these payloads, so an
absent stat is recorded as NULL with reason `field_absent_in_source`, never assumed to be 0.

Cost: one request per fixture + one per player who appeared (~30 per match), so this source
is used for sampled cross-checks, not full backfills.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from .base import (
    IncompleteData, MatchRecord, PlayerMatchRecord, SourceAdapter,
    R_FIELD_ABSENT, R_NO_POSITION, R_NOT_SUBBED_OFF, R_NOT_SUBBED_ON, R_STATS_MISSING, R_UNKNOWN_CARD, R_UNUSED_SUB,
)

log = logging.getLogger("peanut_soccer.premierleague")

BASE = "https://footballapi.pulselive.com/football"
HEADERS = {"Origin": "https://www.premierleague.com", "Referer": "https://www.premierleague.com/"}
ROLE = {"G": "GK", "D": "DEF", "M": "MID", "F": "FWD"}
# Booking ('B') event codes. 'Y' and 'R' verified on real fixtures (124791, 124792); any other code
# (e.g. a second-yellow code) makes red_card NULL for that player until it is verified.
YELLOW_CODES = {"Y"}
RED_CODES = {"R"}
STATUS = {"C": "finished", "U": "scheduled", "L": "live", "A": "abandoned", "P": "postponed"}


def pl_season_label(season: str) -> str:
    """'2025-26' -> '2025/26' (PL compSeason label)."""
    a, b = season.split("-")
    return f"{a}/{b}"


def _to_int(v) -> Optional[int]:
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return int(f) if f.is_integer() else None


def _minute(clock: Optional[dict]) -> Optional[int]:
    if not clock or clock.get("secs") is None:
        return None
    return int(clock["secs"]) // 60


class PremierLeagueAdapter(SourceAdapter):
    name = "premierleague"
    passes_definition = (
        "Opta (Stats Perform) via premierleague.com: stat 'total_pass' = all pass attempts; "
        "'accurate_pass' = successful passes. This is the league's official Opta feed."
    )

    # ---- seasons / fixtures -------------------------------------------------------------
    def comp_season_id(self, season: str, refresh: bool = False) -> int:
        raw = None if refresh else self.read_cache("_meta", "compseasons")
        if raw is None:
            res = self.client.get(f"{BASE}/competitions/1/compseasons", params={"page": 0, "pageSize": 100})
            raw = json.loads(res.content)
            self.write_cache("_meta", "compseasons", raw)
        start = season.split("-")[0]
        want = {pl_season_label(season), f"English Premier League Season {start}/{int(start) + 1}"}
        hits = [int(c["id"]) for c in raw["content"] if c["label"] in want]
        if len(hits) != 1:
            raise ValueError(f"Could not uniquely resolve PL compSeason for {season}: {hits}")
        return hits[0]

    def list_matches(self, season: str, refresh: bool = False) -> list[MatchRecord]:
        raw = None if refresh else self.read_cache(season, "_fixtures")
        if raw is None:
            cs = self.comp_season_id(season)
            pages, page = [], 0
            while True:
                res = self.client.get(f"{BASE}/fixtures", params={
                    "comps": 1, "compSeasons": cs, "page": page, "pageSize": 100, "sort": "asc",
                    "statuses": "A,C,U,L",
                })
                d = json.loads(res.content)
                pages.extend(d["content"])
                page += 1
                if page >= d["pageInfo"]["numPages"]:
                    break
            raw = {"compSeason": cs, "content": pages}
            self.write_cache(season, "_fixtures", raw)
        return [self._match_from_fixture(f, season) for f in raw["content"]]

    def _match_from_fixture(self, f: dict, season: str) -> MatchRecord:
        t = f["teams"]
        ko = (f.get("kickoff") or {}).get("millis")
        return MatchRecord(
            match_id=str(_to_int(f["id"])), source=self.name, season=season,
            date_utc=datetime.fromtimestamp(ko / 1000, tz=timezone.utc).replace(tzinfo=None) if ko else None,
            home_team=t[0]["team"]["name"], away_team=t[1]["team"]["name"],
            home_score=_to_int(t[0].get("score")), away_score=_to_int(t[1].get("score")),
            status=STATUS.get(f.get("status"), "unknown"),
            round=str(_to_int((f.get("gameweek") or {}).get("gameweek"))),
        )

    # ---- match --------------------------------------------------------------------------
    def fetch_match_raw(self, season: str, match_id: str, force: bool = False) -> dict:
        if not force:
            cached = self.read_cache(season, str(match_id))
            if cached is not None:
                return cached
        res = self.client.get(f"{BASE}/fixtures/{match_id}")
        fixture = json.loads(res.content)
        if fixture.get("status") != "C":
            raise IncompleteData(f"PL fixture {match_id} status={fixture.get('status')}")
        if not fixture.get("teamLists"):
            raise IncompleteData(f"PL fixture {match_id} has no teamLists")
        player_stats = {}
        for pid in sorted(self._appeared_ids(fixture)):
            sub_key = f"{match_id}_players/{pid}"
            ps = None if force else self.read_cache(season, sub_key)
            if ps is None:
                r = self.client.get(f"{BASE}/stats/player/{pid}", params={"fixtures": match_id})
                ps = json.loads(r.content)
                self.write_cache(season, sub_key, ps)
            player_stats[str(pid)] = ps
        raw = {"fixture": fixture, "player_stats": player_stats}
        self.write_cache(season, str(match_id), raw)
        return raw

    @staticmethod
    def _appeared_ids(fixture: dict) -> set:
        ids = set()
        subs_on = {int(e["personId"]) for e in fixture.get("events") or []
                   if e.get("type") == "S" and e.get("description") == "ON" and e.get("personId") is not None}
        for tl in fixture["teamLists"]:
            ids.update(int(p["id"]) for p in tl.get("lineup") or [])
            ids.update(int(p["id"]) for p in tl.get("substitutes") or [] if int(p["id"]) in subs_on)
        return ids

    def parse_match(self, raw: dict, season: str) -> tuple[MatchRecord, list[PlayerMatchRecord]]:
        f = raw["fixture"]
        match = self._match_from_fixture(f, season)
        team_name = {int(t["team"]["id"]): t["team"]["name"] for t in f["teams"]}
        home_id = int(f["teams"][0]["team"]["id"])
        events = f.get("events") or []
        sub_on, sub_off, red, unknown_card = {}, {}, set(), set()
        for e in events:
            pid = e.get("personId")
            if pid is None:
                continue
            pid = int(pid)
            if e.get("type") == "S":
                (sub_on if e.get("description") == "ON" else sub_off).setdefault(pid, _minute(e.get("clock")))
            elif e.get("type") == "B":
                code = e.get("description")
                if code in RED_CODES:
                    red.add(pid)
                elif code not in YELLOW_CODES:
                    log.warning("unrecognized PL booking code %r for player %s", code, pid)
                    unknown_card.add(pid)

        rows = []
        for tl in f["teamLists"]:
            tid = int(tl["teamId"])
            is_home = tid == home_id
            opp = next(n for k, n in team_name.items() if k != tid)
            for grp, started in (("lineup", True), ("substitutes", False)):
                for p in tl.get(grp) or []:
                    pid = int(p["id"])
                    reasons = {}
                    appeared = started or pid in sub_on
                    role = ROLE.get(p.get("matchPosition"))
                    if role is None:
                        reasons["position"] = R_NO_POSITION
                    minutes = att = comp = None
                    if not appeared:
                        for k in ("minutes_played", "passes_attempted", "passes_completed"):
                            reasons[k] = R_UNUSED_SUB
                    else:
                        ps = (raw.get("player_stats") or {}).get(str(pid))
                        if ps is None:
                            for k in ("minutes_played", "passes_attempted", "passes_completed"):
                                reasons[k] = R_STATS_MISSING
                        else:
                            s = {x["name"]: x.get("value") for x in ps.get("stats") or []}
                            minutes, att, comp = _to_int(s.get("mins_played")), _to_int(s.get("total_pass")), _to_int(s.get("accurate_pass"))
                            if minutes is None:
                                reasons["minutes_played"] = R_FIELD_ABSENT
                            if att is None:
                                reasons["passes_attempted"] = R_FIELD_ABSENT
                            if comp is None:
                                reasons["passes_completed"] = R_FIELD_ABSENT
                    on, off = sub_on.get(pid), sub_off.get(pid)
                    if on is None:
                        reasons["subbed_on_minute"] = R_NOT_SUBBED_ON if started else R_UNUSED_SUB
                    if off is None:
                        reasons["subbed_off_minute"] = R_NOT_SUBBED_OFF if appeared else R_UNUSED_SUB
                    if pid in red:
                        red_card = True
                    elif pid in unknown_card:
                        red_card = None
                        reasons["red_card"] = R_UNKNOWN_CARD
                    else:
                        red_card = False
                    opta = (p.get("altIds") or {}).get("opta")
                    rows.append(PlayerMatchRecord(
                        match_id=match.match_id, source=self.name, player_id=str(pid),
                        player_name=(p.get("name") or {}).get("display", ""),
                        team=team_name[tid], opponent=opp, is_home=is_home, position=role, started=started,
                        minutes_played=minutes, passes_attempted=att, passes_completed=comp,
                        subbed_on_minute=on, subbed_off_minute=off, red_card=red_card,
                        opta_player_id=opta.lstrip("p") if opta else None, null_reasons=reasons,
                    ))
        return match, rows
