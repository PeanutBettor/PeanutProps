import numpy as np
import pandas as pd

from peanut_soccer.model.data import History
from peanut_soccer.model.flags import volume_shift_flags


def _team_history(values, team="T"):
    start = pd.Timestamp("2025-08-16 15:00")
    rows = [{"match_id": f"{team}{i}", "season": "2025-26", "kickoff": start + pd.Timedelta(days=7 * i),
             "team": team, "opponent": "O", "is_home": True, "passes": v} for i, v in enumerate(values)]
    return pd.DataFrame(rows)


def _flags(values):
    tm = _team_history(values)
    app = tm.assign(player_id="p", role="MID", minutes=90, started=True, team_total=tm["passes"])
    h = History(cutoff=tm["kickoff"].max() + pd.Timedelta(days=1), app=app, tm=tm)
    return volume_shift_flags(h, "2025-26")


def test_style_change_is_flagged():
    rng = np.random.default_rng(0)
    steady = list(450 + rng.normal(0, 30, 15).round())
    assert len(_flags(steady + [600, 610, 590, 620, 605])) == 1


def test_normal_noise_is_not_flagged():
    rng = np.random.default_rng(1)
    assert len(_flags(list(450 + rng.normal(0, 30, 20).round()))) == 0


def test_needs_ten_matches():
    assert len(_flags([450] * 4 + [700] * 5)) == 0
