import numpy as np
import pytest

from peanut_soccer.model import dist
from peanut_soccer.model.project import DistParams, add_distribution

import pandas as pd

CASES = [(3.0, 5.0), (25.0, 12.0), (48.0, 20.0), (80.0, 30.0), (40.0, None)]


@pytest.mark.parametrize("mu,r", CASES)
def test_probabilities_sum_to_one(mu, r):
    k = np.arange(0, 2000)
    assert dist.pmf(k, mu, r).sum() == pytest.approx(1.0, abs=1e-9)


@pytest.mark.parametrize("mu,r", CASES)
def test_p_over_decreases_with_line(mu, r):
    lines = np.arange(0.5, 150.5, 1.0)
    p = np.array([dist.prob_over(L, mu, r) for L in lines])
    assert np.all(np.diff(p) <= 1e-12)
    assert np.all((p >= 0) & (p <= 1))
    # P(over X.5) + P(under X.5) = 1
    for L in (20.5, 45.5):
        under = dist.pmf(np.arange(0, int(L) + 1), mu, r).sum()
        assert dist.prob_over(L, mu, r) + under == pytest.approx(1.0)


def test_quantiles_ordered_and_nb_wider_than_poisson():
    s_nb = dist.summary(np.array([40.0]), 15.0)
    s_po = dist.summary(np.array([40.0]), None)
    assert s_nb["p10"][0] <= s_nb["median"][0] <= s_nb["p90"][0]
    assert s_nb["p90"][0] - s_nb["p10"][0] > s_po["p90"][0] - s_po["p10"][0]


def test_fit_size_recovers_dispersion():
    rng = np.random.default_rng(1)
    mu = rng.uniform(10, 70, 20000)
    r = 12.0
    y = rng.negative_binomial(r, r / (r + mu))
    assert dist.fit_size(y, mu) == pytest.approx(r, rel=0.1)


def test_crps_and_pit_basic():
    y = np.array([0, 10, 40])
    mu = np.array([5.0, 10.0, 40.0])
    c = dist.crps(y, mu, 10.0)
    assert (c >= 0).all()
    u = dist.randomized_pit(y, mu, 10.0)
    assert ((u >= 0) & (u <= 1)).all()


def test_add_distribution_outputs():
    df = pd.DataFrame({"mu": [35.0, 5.0, np.nan], "role": ["MID", "FWD", "DEF"]})
    out = add_distribution(df, DistParams("nbinom", (("ALL", 15.0),)))
    assert out.loc[0, "p_over_30.5"] > out.loc[0, "p_over_40.5"] > out.loc[0, "p_over_50.5"]
    assert np.isnan(out.loc[2, "median"])
