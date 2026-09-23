"""Team volume-shift flags (reporting only; not used by projections, not part of the model version hash).

Rule (per spec): a team is flagged when the mean of its last 5 matches deviates from its season volume
by more than 2 standard deviations, where "season volume" is the mean and SD of its earlier matches this
season (the 5 being tested are excluded). Needs at least 10 matches (5 earlier + 5 recent).

An earlier version tested the last-5 mean against its standard error (SD / sqrt 5). That rule flagged
37 of 40 team-seasons in 2024-25..2026-27 and was too noisy for manual review; it is kept in
team.volume_shift_flags only because team.py is part of the frozen model hash.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .data import History


def volume_shift_flags(hist: History, season: str, n_sd: float = 2.0) -> pd.DataFrame:
    tm = hist.tm[hist.tm["season"] == season].sort_values("kickoff")
    out = []
    for team, g in tm.groupby("team"):
        if len(g) < 10:
            continue
        last5, before = g["passes"].iloc[-5:], g["passes"].iloc[:-5]
        sd = before.std(ddof=1)
        if not sd or np.isnan(sd):
            continue
        dev = (last5.mean() - before.mean()) / sd
        if abs(dev) > n_sd:
            out.append({"team": team, "season": season, "as_of": hist.cutoff, "earlier_mean": before.mean(),
                        "earlier_sd": sd, "last5_mean": last5.mean(), "sd_units": dev, "n_matches": len(g)})
    return pd.DataFrame(out)
