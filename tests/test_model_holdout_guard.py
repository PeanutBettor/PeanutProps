import pytest

from peanut_soccer.model.backtest import HOLDOUT_SEASON, HoldoutViolation, tune


def test_tuning_refuses_holdout_season():
    with pytest.raises(HoldoutViolation):
        tune(wf=None, seasons=("2025-26", HOLDOUT_SEASON))
