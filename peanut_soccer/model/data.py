"""Model inputs and point-in-time enforcement.

Everything the model knows about the past goes through `History`. A History has a cutoff time and
holds only matches that were *completed* before it (kickoff + COMPLETION_BUFFER <= cutoff).
Projection code refuses to project a match whose kickoff is before the history's cutoff, so a
future match can never leak into a projection.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd

# A match counts as completed 3h after kickoff (90' + half-time + stoppage + margin).
COMPLETION_BUFFER = pd.Timedelta(hours=3)
# Consecutive kickoffs more than this far apart start a new match-week block.
BLOCK_GAP = pd.Timedelta(hours=30)

ROLES = ("GK", "DEF", "MID", "FWD")


class LeakageError(RuntimeError):
    """Raised when data from at/after a projection's kickoff would be used."""


APPEARANCES_SQL = """
    SELECT pm.match_id, m.season, m.date AS kickoff, pm.player_id, pm.player_name, pm.team, pm.opponent,
           pm.is_home, pm.position AS role, pm.started, pm.minutes_played AS minutes,
           pm.passes_attempted AS passes, pm.fetched_at
    FROM player_match pm JOIN matches m USING (match_id, source)
    WHERE pm.source = ? AND m.status = 'finished'
      AND (pm.started OR pm.subbed_on_minute IS NOT NULL)
"""


def load_appearances(con, source: str = "fotmob") -> pd.DataFrame:
    """One row per player appearance, with the team's total passes in that match attached.

    Fails closed: a match where any appearing player has NULL passes or minutes is dropped entirely
    (its team total would be wrong), and the count is returned in df.attrs['dropped_matches'].
    """
    df = con.execute(APPEARANCES_SQL, [source]).df()
    bad = df.loc[df["passes"].isna() | df["minutes"].isna(), "match_id"].unique()
    df = df[~df["match_id"].isin(bad)].copy()
    df["passes"] = df["passes"].astype(int)
    df["minutes"] = df["minutes"].astype(int)
    df["kickoff"] = pd.to_datetime(df["kickoff"])
    tt = df.groupby(["match_id", "team"], as_index=False)["passes"].sum().rename(columns={"passes": "team_total"})
    df = df.merge(tt, on=["match_id", "team"])
    df = df.sort_values(["kickoff", "match_id", "team", "player_id"], kind="stable").reset_index(drop=True)
    df.attrs["dropped_matches"] = list(bad)
    df.attrs["snapshot"] = pd.to_datetime(df["fetched_at"]).max()
    return df


def team_matches(app: pd.DataFrame) -> pd.DataFrame:
    """One row per team per match: team, opponent, home flag, team passes."""
    tm = (app.groupby(["match_id", "season", "kickoff", "team", "opponent", "is_home"], as_index=False)
             .agg(passes=("passes", "sum")))
    return tm.sort_values(["kickoff", "match_id", "is_home"], ascending=[True, True, False]).reset_index(drop=True)


def match_week_blocks(kickoffs: pd.Series) -> pd.Series:
    """Label each kickoff with a chronological match-week block id.

    A new block starts when the gap to the previous kickoff exceeds BLOCK_GAP (so a midweek round and
    the following weekend are separate blocks). FotMob's `round` is not used because rescheduled
    matches keep their original round number.
    """
    ko = pd.Series(sorted(pd.to_datetime(kickoffs).unique()))
    new = ko.diff() > BLOCK_GAP
    block_of = dict(zip(ko, new.cumsum()))
    return pd.to_datetime(kickoffs).map(block_of).astype(int)


@dataclass(frozen=True)
class History:
    """Appearances and team-matches completed before `cutoff`. Constructed only via `History.at`."""
    cutoff: pd.Timestamp
    app: pd.DataFrame
    tm: pd.DataFrame

    def __post_init__(self):
        for name, df in (("appearances", self.app), ("team matches", self.tm)):
            if len(df) and (df["kickoff"] + COMPLETION_BUFFER > self.cutoff).any():
                late = df.loc[df["kickoff"] + COMPLETION_BUFFER > self.cutoff, "match_id"].unique()[:5]
                raise LeakageError(f"History({self.cutoff}) contains {name} not completed before cutoff: {list(late)}")

    @classmethod
    def at(cls, cutoff, app: pd.DataFrame, tm: Optional[pd.DataFrame] = None) -> "History":
        cutoff = pd.Timestamp(cutoff)
        tm = team_matches(app) if tm is None else tm
        ok_a = app["kickoff"] + COMPLETION_BUFFER <= cutoff
        ok_t = tm["kickoff"] + COMPLETION_BUFFER <= cutoff
        return cls(cutoff, app[ok_a], tm[ok_t])

    def check_target(self, kickoffs) -> None:
        """Every projected match must kick off at or after the cutoff."""
        ko = pd.to_datetime(pd.Series(kickoffs))
        if (ko < self.cutoff).any():
            raise LeakageError(
                f"projection target kicks off {ko.min()} before history cutoff {self.cutoff}: "
                "history may contain matches played after the target")
        # Belt and braces: no history row may be at/after the earliest target kickoff.
        latest = max(self.app["kickoff"].max() if len(self.app) else pd.Timestamp.min,
                     self.tm["kickoff"].max() if len(self.tm) else pd.Timestamp.min)
        if len(self.app) and latest + COMPLETION_BUFFER > ko.min():
            raise LeakageError(f"history has a match at {latest}, not completed before target {ko.min()}")


def previous_season(season: str) -> str:
    a = int(season.split("-")[0]) - 1
    return f"{a}-{str(a + 1)[-2:]}"


def season_teams(tm: pd.DataFrame, season: str) -> set:
    return set(tm.loc[tm["season"] == season, "team"])
