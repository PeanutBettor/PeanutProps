"""Count distributions for passes attempted.

Negative binomial parameterised by mean mu and size r:  Var = mu + mu^2 / r.  r = inf is Poisson.
"""
from __future__ import annotations

import numpy as np
from scipy import optimize, stats

KMAX = 260  # support cap for CRPS / PIT sums (max observed player passes is well below this)


def _frozen(mu, r):
    mu = np.asarray(mu, float)
    if r is None or (np.isscalar(r) and np.isinf(r)):
        return stats.poisson(mu)
    r = np.asarray(r, float)
    if np.isinf(r).any():
        raise ValueError("mixed Poisson/NB sizes in one call are not supported")
    return stats.nbinom(r, r / (r + mu))


def pmf(k, mu, r=None):
    return _frozen(mu, r).pmf(k)


def cdf(k, mu, r=None):
    return _frozen(mu, r).cdf(k)


def quantile(q, mu, r=None):
    return _frozen(mu, r).ppf(q)


def prob_over(line: float, mu, r=None):
    """P(X > line). Lines are X.5, so this is P(X >= ceil(line))."""
    return 1.0 - _frozen(mu, r).cdf(np.floor(line))


def summary(mu, r=None) -> dict:
    f = _frozen(mu, r)
    return {"mean": np.asarray(mu, float), "median": f.ppf(0.5), "p10": f.ppf(0.10), "p90": f.ppf(0.90)}


def log_loss(y, mu, r=None) -> np.ndarray:
    """Negative log probability of the observed count (per row)."""
    return -_frozen(mu, r).logpmf(np.asarray(y))


def crps(y, mu, r=None, kmax: int = KMAX) -> np.ndarray:
    """Discrete CRPS: sum_k (F(k) - 1{y <= k})^2 over k = 0..kmax."""
    y = np.asarray(y)
    mu = np.asarray(mu, float)
    ks = np.arange(kmax + 1)
    out = np.empty(len(y))
    chunk = 4000
    for s in range(0, len(y), chunk):
        sl = slice(s, s + chunk)
        rr = r if (r is None or np.isscalar(r)) else np.asarray(r)[sl]
        F = _frozen(mu[sl][:, None], rr if (rr is None or np.isscalar(rr)) else rr[:, None]).cdf(ks[None, :])
        ind = (y[sl][:, None] <= ks[None, :]).astype(float)
        out[sl] = ((F - ind) ** 2).sum(axis=1)
    return out


def randomized_pit(y, mu, r=None, seed: int = 0) -> np.ndarray:
    """Randomised PIT for a discrete distribution: F(y-1) + U * p(y). Uniform if calibrated."""
    rng = np.random.default_rng(seed)
    f = _frozen(mu, r)
    y = np.asarray(y)
    lo = np.where(y > 0, f.cdf(y - 1), 0.0)
    return lo + rng.uniform(size=len(y)) * f.pmf(y)


def fit_size(y, mu) -> float:
    """Maximum-likelihood NB size r for fixed means."""
    y, mu = np.asarray(y), np.asarray(mu, float)

    def nll(logr):
        return log_loss(y, mu, np.exp(logr)).sum()

    res = optimize.minimize_scalar(nll, bounds=(np.log(0.5), np.log(5000.0)), method="bounded")
    return float(np.exp(res.x))
