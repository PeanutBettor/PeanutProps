"""FotMob adapter (PRIMARY source).

Endpoints (verified live 2026-09-22):
  fixtures:      https://www.fotmob.com/api/data/leagues?id=47&season=2025%2F2026
  match details: https://www.fotmob.com/api/data/matchDetails?matchId=<id>

Passes attempted = content.playerStats[<pid>].stats[*].stats["Accurate passes"].stat.total
  (stat key "accurate_passes", type "fractionWithPercentage": value=completed, total=attempted).
FotMob's player stats are Opta-sourced (each player carries an `optaId`), and the per-player
totals sum exactly to FotMob's team "Passes" total, which equals the Premier League's
official Opta `total_pass`.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from .base import (
    IncompleteData, MatchRecord, PlayerMatchRecord, SourceAdapter,
    R_FIELD_ABSENT, R_NO_POSITION, R_NOT_SUBBED_OFF, R_NOT_SUBBED_ON, R_STATS_MISSING,
    R_UNPARSEABLE, R_UNUSED_SUB,
)

log = logging.getLogger("peanut_soccer.fotmob")

LEAGUE_ID = 47  # English Premier League
BASE = "https://www.fotmob.com/api/data"

# FotMob `usualPlayingPositionId` codes (verified against lineups: GKs=0, CBs/FBs=1, CMs=2, STs=3).
ROLE = {0: "GK", 1: "DEF", 2: "MID", 3: "FWD"}


def fotmob_season_param(season: str) -> str:
    start = int(season.split("-")[0])
    return f"{start}/{start + 1}"


def _parse_utc(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    s = s.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s).astimezone(timezone.utc).replace(tzinfo=None)
    except ValueError:
        return None


def _int_or_none(v) -> Optional[int]:
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return None


def _fixture_status(st: dict) -> str:
    if st.get("cancelled"):
        reason = (st.get("reason") or {}).get("short", "")
        return "postponed" if reason.lower() in ("pp", "pst", "postp.") else "cancelled"
    if st.get("awarded"):
        return "awarded"
    if st.get("finished"):
        return "finished"
    if st.get("started"):
        return "live"
    return "scheduled"


def _flat_stats(player_stats: dict) -> dict:
    """Map stat key -> stat dict across all stat groups (keys are language-independent)."""
    out = {}
    for group in player_stats.get("stats") or []:
        for title, entry in (group.get("stats") or {}).items():
            key = entry.get("key") or title
            out.setdefault(key, entry.get("stat"))
    return out


class FotMobAdapter(SourceAdapter):
    name = "fotmob"
    passes_definition = (
        "Opta (Stats Perform) via FotMob: 'Accurate passes' total = all pass attempts "
        "(open play + set pieces incl. crosses, long balls, goal kicks and GK throws); "
        "value = successful passes. Verified equal to premierleague.com Opta total_pass."
    )

    # ---- fixtures -----------------------------------------------------------------------
    def list_matches(self, season: str, refresh: bool = False) -> list[MatchRecord]:
        raw = None if refresh else self.read_cache(season, "_fixtures")
        if raw is None:
            res = self.client.get(f"{BASE}/leagues", params={"id": LEAGUE_ID, "season": fotmob_season_param(season)})
            raw = json.loads(res.content)
            self.write_cache(season, "_fixtures", raw)
        return self.parse_fixtures(raw, season)

    def parse_fixtures(self, raw: dict, season: str) -> list[MatchRecord]:
        selected = (raw.get("details") or {}).get("selectedSeason")
        if selected != fotmob_season_param(season):
            raise ValueError(f"FotMob returned season {selected!r}, expected {fotmob_season_param(season)!r}")
        out = []
        for m in raw["fixtures"]["allMatches"]:
            st = m.get("status") or {}
            hs = as_ = None
            score = st.get("scoreStr")
            if score and st.get("finished"):
                try:
                    hs, as_ = (int(x.strip()) for x in score.split("-"))
                except ValueError:
                    hs = as_ = None
            out.append(MatchRecord(
                match_id=str(m["id"]), source=self.name, season=season,
                date_utc=_parse_utc(st.get("utcTime")),
                home_team=m["home"]["name"], away_team=m["away"]["name"],
                home_score=hs, away_score=as_, status=_fixture_status(st),
                round=str(m.get("round")) if m.get("round") is not None else None,
            ))
        return out

    # ---- match details ------------------------------------------------------------------
    def fetch_match_raw(self, season: str, match_id: str, force: bool = False) -> dict:
        if not force:
            cached = self.read_cache(season, str(match_id))
            if cached is not None:
                return cached
        res = self.client.get(f"{BASE}/matchDetails", params={"matchId": match_id})
        raw = json.loads(res.content)
        self.check_complete(raw, match_id)
        self.write_cache(season, str(match_id), raw)
        return raw

    @staticmethod
    def check_complete(raw: dict, match_id) -> None:
        general = raw.get("general") or {}
        if str(general.get("matchId")) != str(match_id):
            raise IncompleteData(f"matchId mismatch: asked {match_id}, got {general.get('matchId')}")
        if not general.get("finished"):
            raise IncompleteData(f"match {match_id} not finished")
        content = raw.get("content") or {}
        if not content.get("playerStats"):
            raise IncompleteData(f"match {match_id} has no playerStats yet")
        lu = content.get("lineup") or {}
        for side in ("homeTeam", "awayTeam"):
            if not (lu.get(side) or {}).get("starters"):
                raise IncompleteData(f"match {match_id} missing {side} starters")

    def parse_match(self, raw: dict, season: str) -> tuple[MatchRecord, list[PlayerMatchRecord]]:
        general = raw["general"]
        header = raw.get("header") or {}
        content = raw["content"]
        match_id = str(general["matchId"])
        teams = header.get("teams") or []
        hst = header.get("status") or {}
        match = MatchRecord(
            match_id=match_id, source=self.name, season=season,
            date_utc=_parse_utc(general.get("matchTimeUTCDate") or hst.get("utcTime")),
            home_team=general["homeTeam"]["name"], away_team=general["awayTeam"]["name"],
            home_score=_int_or_none(teams[0].get("score")) if len(teams) == 2 else None,
            away_score=_int_or_none(teams[1].get("score")) if len(teams) == 2 else None,
            status=_fixture_status(hst) if hst else ("finished" if general.get("finished") else "unknown"),
            round=str(general.get("matchRound")) if general.get("matchRound") is not None else None,
        )

        player_stats = content.get("playerStats") or {}
        red_ids, events_ok = self._red_cards(content)
        lineup = content["lineup"]
        rows: list[PlayerMatchRecord] = []
        for side, is_home in (("homeTeam", True), ("awayTeam", False)):
            team = lineup[side]
            opp = lineup["awayTeam" if is_home else "homeTeam"]
            team_name, opp_name = general[side]["name"], general["awayTeam" if is_home else "homeTeam"]["name"]
            for grp, started in (("starters", True), ("subs", False)):
                for p in team.get(grp) or []:
                    rows.append(self._player_row(
                        p, match_id, team_name, opp_name, is_home, started,
                        player_stats.get(str(p["id"])), red_ids, events_ok,
                    ))
        return match, rows

    @staticmethod
    def _red_cards(content: dict) -> tuple[set, bool]:
        try:
            events = content["matchFacts"]["events"]["events"]
        except (KeyError, TypeError):
            return set(), False
        red = set()
        for e in events:
            if e.get("type") == "Card":
                card = str(e.get("card") or "")
                if "red" in card.lower():
                    red.add(str(e.get("playerId") or (e.get("player") or {}).get("id")))
        return red, True

    def _player_row(self, p, match_id, team, opp, is_home, started, pstats, red_ids, events_ok) -> PlayerMatchRecord:
        reasons: dict = {}
        perf = p.get("performance") or {}
        subs = perf.get("substitutionEvents") or []
        sub_on = next((_int_or_none(s.get("time")) for s in subs if s.get("type") == "subIn"), None)
        sub_off = next((_int_or_none(s.get("time")) for s in subs if s.get("type") == "subOut"), None)
        appeared = started or sub_on is not None

        role = ROLE.get(p.get("usualPlayingPositionId"))
        if role is None:
            reasons["position"] = R_NO_POSITION

        minutes = attempted = completed = None
        if not appeared:
            for f in ("minutes_played", "passes_attempted", "passes_completed"):
                reasons[f] = R_UNUSED_SUB
        elif pstats is None:
            for f in ("minutes_played", "passes_attempted", "passes_completed"):
                reasons[f] = R_STATS_MISSING
        else:
            flat = _flat_stats(pstats)
            mp = flat.get("minutes_played")
            if mp is None:
                reasons["minutes_played"] = R_FIELD_ABSENT
            else:
                minutes = _int_or_none(mp.get("value"))
                if minutes is None:
                    reasons["minutes_played"] = R_UNPARSEABLE
            ap = flat.get("accurate_passes")
            if ap is None:
                reasons["passes_attempted"] = R_FIELD_ABSENT
                reasons["passes_completed"] = R_FIELD_ABSENT
            else:
                attempted = _int_or_none(ap.get("total"))
                completed = _int_or_none(ap.get("value"))
                if attempted is None:
                    reasons["passes_attempted"] = R_FIELD_ABSENT if "total" not in ap else R_UNPARSEABLE
                if completed is None:
                    reasons["passes_completed"] = R_FIELD_ABSENT if "value" not in ap else R_UNPARSEABLE

        if sub_on is None:
            reasons["subbed_on_minute"] = R_NOT_SUBBED_ON if started else R_UNUSED_SUB
        if sub_off is None:
            reasons["subbed_off_minute"] = R_NOT_SUBBED_OFF if appeared else R_UNUSED_SUB

        red: Optional[bool]
        if events_ok:
            red = str(p["id"]) in red_ids
        else:
            red = None
            reasons["red_card"] = R_FIELD_ABSENT

        opta = pstats.get("optaId") if pstats else None
        return PlayerMatchRecord(
            match_id=match_id, source=self.name, player_id=str(p["id"]), player_name=p.get("name") or "",
            team=team, opponent=opp, is_home=is_home, position=role, started=started,
            minutes_played=minutes, passes_attempted=attempted, passes_completed=completed,
            subbed_on_minute=sub_on, subbed_off_minute=sub_off, red_card=red,
            opta_player_id=str(opta) if opta else None, null_reasons=reasons,
        )

    # ---- extra: team totals as reported by the source (for sanity checks) ---------------
    @staticmethod
    def team_pass_totals(raw: dict) -> Optional[tuple[int, int]]:
        try:
            for g in raw["content"]["stats"]["Periods"]["All"]["stats"]:
                for s in g.get("stats") or []:
                    if s.get("key") == "passes" and s["stats"][0] is not None:
                        return int(s["stats"][0]), int(s["stats"][1])
        except (KeyError, TypeError, ValueError):
            return None
        return None
