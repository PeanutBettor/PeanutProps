"""Team pass volume.

    E[team passes] = exp(a_team + d_opponent + eta * side),   side = +1 home, -1 away

a_team      team's own passing level (log), from its recent matches this season
d_opponent  opponent's passes-allowed factor (log): how much teams pass against it relative to their own level
eta         home effect, estimated from all completed matches before the cutoff

a and d are fitted jointly by alternating weighted log-ratio updates over the current season's matches.
Each team's k-th most recent match gets weight decay**k (decay chosen by walk-forward validation).
Both are shrunk toward a prior with strength `k_prior` (in effective matches):
  - returning teams: their own end-of-previous-season rating
  - promoted teams: the average end-of-season rating of the teams relegated from the previous season
    (the closest available proxy for a promoted side), with strength k_prior * promoted_mult
  - first season in the data (no previous season): the league mean
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from .data import History, previous_season

ITERS = 25


@dataclass(frozen=True)
class TeamParams:
    decay: float = 0.9
    k_prior: float = 4.0
    promoted_mult: float = 2.0


@dataclass
class TeamRatings:
    a: dict            # team -> log level
    d: dict            # team -> log passes-allowed factor
    eta: float
    league_log_mean: float
    n_matches: dict    # team -> matches this season used

    def expected(self, team: str, opp: str, is_home: bool) -> float:
        if team not in self.a or opp not in self.d:
            return float("nan")
        return float(np.exp(self.a[team] + self.d[opp] + self.eta * (1 if is_home else -1)))


def estimate_eta(tm: pd.DataFrame) -> float:
    """Half the mean log(home passes / away passes) over completed matches (balanced schedule)."""
    if tm.empty:
        return 0.0
    w = tm.pivot_table(index="match_id", columns="is_home", values="passes", aggfunc="first").dropna()
    if w.empty:
        return 0.0
    return float(0.5 * np.mean(np.log(w[True]) - np.log(w[False])))


def _fit_season(rows: pd.DataFrame, teams: list, prior_a: dict, prior_d: dict, strength: dict,
                eta: float, decay: float) -> tuple[dict, dict]:
    if rows.empty:
        return dict(prior_a), dict(prior_d)
    idx = {t: i for i, t in enumerate(teams)}
    n = len(teams)
    pa = np.array([prior_a[t] for t in teams])
    pdd = np.array([prior_d[t] for t in teams])
    k = np.array([strength[t] for t in teams])
    rows = rows.sort_values("kickoff")
    ti = rows["team"].map(idx).to_numpy()
    oi = rows["opponent"].map(idx).to_numpy()
    side = np.where(rows["is_home"].to_numpy(), 1.0, -1.0)
    y = rows["passes"].to_numpy(dtype=float)
    # recency rank within team (for a) and within opponent (for d); 0 = most recent
    w_a = decay ** rows.groupby("team").cumcount(ascending=False).to_numpy()
    w_d = decay ** rows.groupby("opponent").cumcount(ascending=False).to_numpy()
    W_a = np.bincount(ti, w_a, n)
    W_d = np.bincount(oi, w_d, n)
    num_a = np.bincount(ti, w_a * y, n)
    num_d = np.bincount(oi, w_d * y, n)
    a, d = pa.copy(), pdd.copy()
    for _ in range(ITERS):
        den = np.bincount(ti, w_a * np.exp(d[oi] + eta * side), n)
        obs = np.where(W_a > 0, np.log(np.where(num_a > 0, num_a, 1) / np.where(den > 0, den, 1)), 0.0)
        a = (W_a * obs + k * pa) / (W_a + k)
        den = np.bincount(oi, w_d * np.exp(a[ti] + eta * side), n)
        obs = np.where(W_d > 0, np.log(np.where(num_d > 0, num_d, 1) / np.where(den > 0, den, 1)), 0.0)
        d = (W_d * obs + k * pdd) / (W_d + k)
    return dict(zip(teams, a)), dict(zip(teams, d))


class TeamModel:
    def __init__(self, params: TeamParams, fixture_teams: dict):
        """fixture_teams: season -> set of teams in that season's fixture list (known pre-season)."""
        self.p = params
        self.fixture_teams = fixture_teams
        self._end_cache: dict = {}

    def _end_of_season(self, hist_tm: pd.DataFrame, season: str) -> TeamRatings | None:
        """Ratings after the last match of `season` (a completed season before the target)."""
        if season not in self.fixture_teams:
            return None
        key = (season, len(hist_tm[hist_tm["season"] == season]))
        if key not in self._end_cache:
            rows = hist_tm[hist_tm["season"] == season]
            self._end_cache[key] = self._fit(rows, hist_tm[hist_tm["season"] <= season], season)
        return self._end_cache[key]

    def _priors(self, hist_tm: pd.DataFrame, season: str, league_log_mean: float):
        teams = sorted(self.fixture_teams[season])
        prev = previous_season(season)
        end = self._end_of_season(hist_tm, prev) if prev in self.fixture_teams else None
        prior_a, prior_d, strength = {}, {}, {}
        if end is None:
            for t in teams:
                prior_a[t], prior_d[t], strength[t] = league_log_mean, 0.0, self.p.k_prior
            return teams, prior_a, prior_d, strength
        relegated = sorted(self.fixture_teams[prev] - self.fixture_teams[season])
        rel_a = float(np.mean([end.a[t] for t in relegated])) if relegated else league_log_mean
        rel_d = float(np.mean([end.d[t] for t in relegated])) if relegated else 0.0
        for t in teams:
            if t in end.a:
                prior_a[t], prior_d[t], strength[t] = end.a[t], end.d[t], self.p.k_prior
            else:  # promoted
                prior_a[t], prior_d[t] = rel_a, rel_d
                strength[t] = self.p.k_prior * self.p.promoted_mult
        return teams, prior_a, prior_d, strength

    def _fit(self, rows: pd.DataFrame, hist_tm_upto: pd.DataFrame, season: str) -> TeamRatings:
        eta = estimate_eta(hist_tm_upto)
        pool = hist_tm_upto if len(hist_tm_upto) else rows
        league = float(np.log(pool["passes"]).mean()) if len(pool) else float(np.log(450.0))
        teams, pa, pd_, k = self._priors(hist_tm_upto, season, league)
        a, d = _fit_season(rows, teams, pa, pd_, k, eta, self.p.decay)
        n = rows.groupby("team").size().to_dict()
        return TeamRatings(a, d, eta, league, {t: int(n.get(t, 0)) for t in teams})

    def ratings(self, hist: History, season: str) -> TeamRatings:
        tm = hist.tm
        return self._fit(tm[tm["season"] == season], tm, season)

    def params_dict(self) -> dict:
        return asdict(self.p)


def volume_shift_flags(hist: History, season: str, z_threshold: float = 2.0) -> pd.DataFrame:
    """Teams whose last 5 matches deviate from their earlier season volume by > z_threshold SE.

    SE = sd(earlier matches) / sqrt(5). Needs >= 5 earlier matches. Flag only; not modelled.
    """
    tm = hist.tm[hist.tm["season"] == season].sort_values("kickoff")
    out = []
    for team, g in tm.groupby("team"):
        if len(g) < 10:
            continue
        last5, before = g["passes"].iloc[-5:], g["passes"].iloc[:-5]
        sd = before.std(ddof=1)
        if not sd or np.isnan(sd):
            continue
        z = (last5.mean() - before.mean()) / (sd / np.sqrt(5))
        if abs(z) > z_threshold:
            out.append({"team": team, "season": season, "as_of": hist.cutoff, "earlier_mean": before.mean(),
                        "last5_mean": last5.mean(), "z": z, "n_matches": len(g)})
    return pd.DataFrame(out)
