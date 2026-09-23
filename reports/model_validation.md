# Model Validation — EPL passes attempted (rate + distribution)

Model version **00a8ed082820** (hash of parameters + projection code). Data snapshot 2026-09-22 21:45:30 UTC. Tuned 2026-09-23T00:17:29+00:00.

> **Minutes are ORACLE (actual) minutes** in every backtest number below. These results measure the rate model (team volume × share × distribution) only. Real-world error will be larger once minutes must be predicted (prompt 3).

- Walk-forward: chronological match-week blocks (a new block starts after a >30 h gap between kickoffs). For each block the model is refit on matches completed before the block's first kickoff (kickoff + 3 h), then the block is projected.
- Training / tuning: 2024-25, 2025-26. The first 5 blocks of 2024-25 are not scored (the database has no earlier data to project from).
- Holdout: 2026-27, never used in tuning. Holdout scoring runs so far: **1** (first at 2026-09-23T00:18:04+00:00, version 00a8ed082820).
- Primary evaluation set: starters with ≥ 60 actual minutes. Subs are reported separately.

## 1. Chosen parameters and how each was chosen

| parameter | value | grid searched | how chosen |
|---|---|---|---|
| team: recency decay per match | 0.950 | [0.7, 0.8, 0.85, 0.9, 0.95, 1.0] | full grid, walk-forward team-passes MAE |
| team: prior strength k (matches) | 4 | [0.5, 1, 2, 4, 8, 16] | same grid |
| team: promoted-team prior multiplier | 4 | [0.5, 1, 2, 4, 8, 16] | same grid |
| share: recency decay per appearance | 0.850 | [0.7, 0.8, 0.85, 0.9, 0.95, 1.0] | coordinate descent (2 passes, warm start from a first narrower-grid pass), walk-forward primary-set NB log-loss |
| share: recent→long-term strength k_long | 1 | [0.5, 1, 2, 4, 8] | same |
| share: long-term→role prior strength k_role | 2 | [0.25, 0.5, 1, 2, 4, 8] | same |
| share: team role→league role strength k_league | 100 | [3, 10, 30, 100, 300] | same |
| share: weight of <20-min appearances | 0.050 | [0.05, 0.1, 0.25, 0.5, 0.75, 1.0] | same |
| volume elasticity beta GK | -0.250 | [-0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75] | same |
| volume elasticity beta DEF | 1.250 | [-0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75] | same |
| volume elasticity beta MID | 1.000 | [-0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75] | same |
| volume elasticity beta FWD | 0.750 | [-0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75] | same |
| distribution | nbinom {"GK": 32.8, "DEF": 11.29, "MID": 12.89, "FWD": 12.66} | Poisson / NB one size / NB size per position | cross-season validation log-loss (table below) |
| home effect eta | re-estimated each block |  | half the mean log(home/away passes) of completed matches |

Strengths k are in full-match equivalents (1 = one match of evidence; for shares, one match of 450 team passes). Search traces: `models/tuning_trace_team.csv`, `models/tuning_trace_share.csv`.

### Distribution selection (fit on one training season, scored on the other, both directions)

| subset | family | validation log-loss | n |
|---|---|---|---|
| primary | poisson | 4.374 | 14648 |
| primary | nb_global | 3.762 | 14648 |
| primary | nb_by_role | 3.756 | 14648 |
| all | poisson | 4.058 | 21523 |
| all | nb_global | 3.550 | 21523 |
| all | nb_by_role | 3.545 | 21523 |

Baseline NB sizes (fit on their own training predictions): base_std 9.5, base_last5 9.0, base_last10 9.8

## 2. Team volume

- Walk-forward (train): 1420 team-matches, MAE 63.3, RMSE 79.0, bias -0.7 passes (mean actual 442).
- Holdout: 100 team-matches, MAE 72.6, RMSE 91.1, bias -4.6 passes (mean actual 443).

### Volume-shift flags (possible manager / style change — flagged for manual review, NOT modelled)

Rule: at each block cutoff, a team with ≥ 10 matches this season is flagged when the mean of its last 5 matches deviates from its earlier-season mean by more than 2 standard deviations of its earlier matches. (A looser standard-error rule, SD/√5, produced 141 flags and was too noisy to review.)

1 flagged cutoffs across 1 team-seasons:

| season | team | as of (cutoff) | matches | earlier mean | earlier SD | last-5 mean | deviation (SD) |
|---|---|---|---|---|---|---|---|
| 2024-25 | Brighton & Hove Albion | 2024-11-23 | 11 | 531.0 | 45.712 | 416.4 | -2.507 |

## 3. Walk-forward results (training seasons, oracle minutes)

### Primary: starters ≥ 60 min

Rows: 14648; projectable by model: 14648; comparable (model and all three baselines defined and > 0): 14344. Baselines are undefined for a player's first appearance of a season (season-to-date) or first appearance overall.

| method | n | MAE | RMSE | bias | NB log-loss | CRPS |
|---|---|---|---|---|---|---|
| Model | 14344 | 8.965 | 12.041 | 0.154 | 3.758 | 6.336 |
| Season-to-date per 90 | 14344 | 10.173 | 14.031 | 0.735 | 3.878 | 7.178 |
| Last-5 per 90 | 14344 | 10.462 | 14.402 | 0.842 | 3.900 | 7.376 |
| Last-10 per 90 | 14344 | 10.084 | 13.820 | 0.802 | 3.864 | 7.099 |
| Model, all projectable rows | 14648 | 8.986 | 12.069 | 0.186 | 3.760 | 6.351 |

### Subs (came off the bench)

Rows: 5903; projectable by model: 5903; comparable (model and all three baselines defined and > 0): 5518. Baselines are undefined for a player's first appearance of a season (season-to-date) or first appearance overall.

| method | n | MAE | RMSE | bias | NB log-loss | CRPS |
|---|---|---|---|---|---|---|
| Model | 5518 | 3.592 | 5.256 | -1.671 | 3.069 | 2.691 |
| Season-to-date per 90 | 5518 | 3.987 | 7.046 | -0.935 | 3.074 | 2.951 |
| Last-5 per 90 | 5518 | 3.942 | 6.491 | -0.960 | 3.061 | 2.906 |
| Last-10 per 90 | 5518 | 3.857 | 6.396 | -1.031 | 3.050 | 2.855 |
| Model, all projectable rows | 5903 | 3.575 | 5.261 | -1.647 | 3.055 | 2.678 |

### Starters < 60 min

Rows: 972; projectable by model: 972; comparable (model and all three baselines defined and > 0): 953. Baselines are undefined for a player's first appearance of a season (season-to-date) or first appearance overall.

| method | n | MAE | RMSE | bias | NB log-loss | CRPS |
|---|---|---|---|---|---|---|
| Model | 953 | 5.571 | 7.495 | 0.527 | 3.247 | 3.893 |
| Season-to-date per 90 | 953 | 6.345 | 9.196 | 0.972 | 3.359 | 4.432 |
| Last-5 per 90 | 953 | 6.582 | 9.260 | 0.962 | 3.390 | 4.559 |
| Last-10 per 90 | 953 | 6.283 | 8.827 | 0.940 | 3.351 | 4.355 |
| Model, all projectable rows | 972 | 5.603 | 7.537 | 0.534 | 3.249 | 3.912 |

## 4. HOLDOUT results — 2026-27 (scored once, oracle minutes)

### Primary: starters ≥ 60 min

Rows: 1048; projectable by model: 1048; comparable (model and all three baselines defined and > 0): 814. Baselines are undefined for a player's first appearance of a season (season-to-date) or first appearance overall.

| method | n | MAE | RMSE | bias | NB log-loss | CRPS |
|---|---|---|---|---|---|---|
| Model | 814 | 9.180 | 12.486 | 0.098 | 3.765 | 6.449 |
| Season-to-date per 90 | 814 | 12.945 | 20.398 | 2.098 | 4.096 | 9.173 |
| Last-5 per 90 | 814 | 11.444 | 18.283 | 1.309 | 3.967 | 8.163 |
| Last-10 per 90 | 814 | 11.366 | 18.168 | 0.989 | 3.958 | 8.082 |
| Model, all projectable rows | 1048 | 9.589 | 13.005 | -0.329 | 3.807 | 6.755 |

### Subs (came off the bench)

Rows: 438; projectable by model: 438; comparable (model and all three baselines defined and > 0): 256. Baselines are undefined for a player's first appearance of a season (season-to-date) or first appearance overall.

| method | n | MAE | RMSE | bias | NB log-loss | CRPS |
|---|---|---|---|---|---|---|
| Model | 256 | 3.490 | 4.937 | -1.324 | 3.016 | 2.615 |
| Season-to-date per 90 | 256 | 4.747 | 8.192 | 0.719 | 3.163 | 3.416 |
| Last-5 per 90 | 256 | 3.768 | 5.424 | -0.799 | 3.065 | 2.785 |
| Last-10 per 90 | 256 | 3.770 | 5.328 | -0.943 | 3.069 | 2.767 |
| Model, all projectable rows | 438 | 3.793 | 5.445 | -1.607 | 3.160 | 2.853 |

### Starters < 60 min

Rows: 52; projectable by model: 52; comparable (model and all three baselines defined and > 0): 40. Baselines are undefined for a player's first appearance of a season (season-to-date) or first appearance overall.

| method | n | MAE | RMSE | bias | NB log-loss | CRPS |
|---|---|---|---|---|---|---|
| Model | 40 | 5.129 | 5.981 | 3.670 | 3.171 | 3.323 |
| Season-to-date per 90 | 40 | 4.732 | 6.050 | 1.515 | 3.136 | 3.279 |
| Last-5 per 90 | 40 | 4.736 | 5.676 | 1.221 | 3.114 | 3.194 |
| Last-10 per 90 | 40 | 4.817 | 5.650 | 1.402 | 3.121 | 3.204 |
| Model, all projectable rows | 52 | 5.103 | 5.984 | 2.848 | 3.157 | 3.321 |

### Verdict (holdout, primary set)

- vs Season-to-date per 90: MAE better (9.180 vs 12.945); log-loss better (3.7646 vs 4.0964).
- vs Last-5 per 90: MAE better (9.180 vs 11.444); log-loss better (3.7646 vs 3.9674).
- vs Last-10 per 90: MAE better (9.180 vs 11.366); log-loss better (3.7646 vs 3.9576).

**The model beats all three baselines on both MAE and log-loss in the holdout.**

## 5. Holdout breakdowns (primary set)

### By role

| role | n | MAE | RMSE | bias (proj - actual) |
|---|---|---|---|---|
| DEF | 401 | 12.462 | 16.012 | -0.163 |
| MID | 305 | 9.993 | 13.587 | -0.668 |
| FWD | 242 | 5.432 | 6.780 | 0.119 |
| GK | 100 | 6.894 | 8.380 | -1.039 |

### By home/away

| home/away | n | MAE | RMSE | bias (proj - actual) |
|---|---|---|---|---|
| home | 525 | 9.762 | 13.402 | -0.790 |
| away | 523 | 9.414 | 12.595 | 0.134 |

### By team

| team | n | MAE | RMSE | bias (proj - actual) |
|---|---|---|---|---|
| AFC Bournemouth | 55 | 6.880 | 7.913 | -0.534 |
| Brighton & Hove Albion | 55 | 12.272 | 16.313 | 0.593 |
| Everton | 55 | 6.806 | 9.049 | -2.595 |
| Fulham | 55 | 9.298 | 12.866 | -4.195 |
| Chelsea | 54 | 12.932 | 16.520 | 6.635 |
| Ipswich Town | 54 | 6.888 | 8.949 | -1.741 |
| Liverpool | 54 | 8.910 | 13.203 | -1.457 |
| Manchester United | 54 | 11.771 | 14.208 | -4.700 |
| Sunderland | 54 | 7.335 | 9.482 | -0.178 |
| Arsenal | 52 | 11.541 | 13.970 | -3.153 |
| Leeds United | 52 | 6.719 | 8.365 | 0.837 |
| Manchester City | 52 | 17.296 | 22.931 | -0.443 |
| Nottingham Forest | 52 | 6.702 | 8.314 | -0.770 |
| Brentford | 51 | 4.524 | 6.081 | -0.289 |
| Coventry City | 51 | 10.414 | 13.804 | 1.909 |
| Tottenham Hotspur | 51 | 11.620 | 15.282 | -7.214 |
| Aston Villa | 50 | 11.991 | 16.582 | 1.971 |
| Crystal Palace | 49 | 8.954 | 11.642 | 1.576 |
| Hull City | 49 | 11.006 | 12.591 | 7.764 |
| Newcastle United | 49 | 8.107 | 10.043 | 0.331 |

## 6. Walk-forward breakdowns (primary set)

### By role

| role | n | MAE | RMSE | bias (proj - actual) |
|---|---|---|---|---|
| DEF | 5321 | 11.739 | 15.091 | 0.129 |
| MID | 4566 | 9.222 | 12.047 | 0.215 |
| FWD | 3351 | 5.461 | 7.126 | 0.382 |
| GK | 1410 | 6.208 | 7.950 | -0.155 |

### By home/away

| home/away | n | MAE | RMSE | bias (proj - actual) |
|---|---|---|---|---|
| home | 7353 | 9.025 | 12.152 | 0.001 |
| away | 7295 | 8.947 | 11.985 | 0.373 |

### By team

| team | n | MAE | RMSE | bias (proj - actual) |
|---|---|---|---|---|
| Brentford | 762 | 8.109 | 10.835 | 0.284 |
| Everton | 756 | 7.453 | 9.497 | 0.257 |
| AFC Bournemouth | 750 | 7.622 | 10.215 | -0.193 |
| Manchester City | 747 | 11.364 | 15.259 | -2.508 |
| Fulham | 745 | 8.825 | 11.958 | -0.984 |
| Newcastle United | 744 | 8.705 | 11.763 | -0.213 |
| Liverpool | 742 | 10.434 | 13.756 | -0.496 |
| Crystal Palace | 734 | 7.823 | 10.580 | 0.897 |
| Brighton & Hove Albion | 728 | 8.968 | 12.381 | -0.022 |
| Wolverhampton Wanderers | 727 | 8.851 | 11.616 | 1.072 |
| Aston Villa | 725 | 9.530 | 13.071 | -0.191 |
| Nottingham Forest | 724 | 8.410 | 10.979 | 0.596 |
| West Ham United | 722 | 7.792 | 10.445 | 1.104 |
| Arsenal | 713 | 10.412 | 14.048 | -1.086 |
| Chelsea | 713 | 10.165 | 13.744 | -1.810 |
| Tottenham Hotspur | 711 | 9.181 | 12.399 | 1.259 |
| Manchester United | 708 | 9.334 | 12.354 | 0.486 |
| Leeds United | 401 | 8.598 | 11.257 | 0.888 |
| Burnley | 395 | 8.779 | 11.121 | 0.953 |
| Sunderland | 392 | 8.141 | 10.780 | 1.851 |
| Ipswich Town | 348 | 8.732 | 11.369 | 2.933 |
| Leicester City | 339 | 9.085 | 11.794 | 0.838 |
| Southampton | 322 | 10.713 | 13.891 | 3.563 |

## 7. Calibration of P(over) — holdout, primary set

**Line 20.5**: n=1048, mean predicted P(over) 0.803, actual over rate 0.799, Brier 0.0913

| P(over) bucket | n | mean predicted | actual hit rate | actual - predicted |
|---|---|---|---|---|
| 0-10% | 34 | 0.046 | 0.029 | -0.016 |
| 10-20% | 34 | 0.159 | 0.235 | 0.077 |
| 20-30% | 27 | 0.248 | 0.259 | 0.011 |
| 30-40% | 29 | 0.354 | 0.379 | 0.025 |
| 40-50% | 29 | 0.452 | 0.414 | -0.038 |
| 50-60% | 35 | 0.550 | 0.543 | -0.007 |
| 60-70% | 47 | 0.649 | 0.553 | -0.096 |
| 70-80% | 67 | 0.750 | 0.716 | -0.034 |
| 80-90% | 158 | 0.854 | 0.848 | -0.006 |
| 90-100% | 588 | 0.969 | 0.971 | 0.002 |

**Line 30.5**: n=1048, mean predicted P(over) 0.574, actual over rate 0.568, Brier 0.1370

| P(over) bucket | n | mean predicted | actual hit rate | actual - predicted |
|---|---|---|---|---|
| 0-10% | 141 | 0.028 | 0.021 | -0.007 |
| 10-20% | 65 | 0.148 | 0.123 | -0.025 |
| 20-30% | 56 | 0.248 | 0.268 | 0.020 |
| 30-40% | 62 | 0.354 | 0.371 | 0.017 |
| 40-50% | 71 | 0.449 | 0.380 | -0.069 |
| 50-60% | 88 | 0.551 | 0.500 | -0.051 |
| 60-70% | 96 | 0.655 | 0.688 | 0.033 |
| 70-80% | 108 | 0.749 | 0.759 | 0.010 |
| 80-90% | 162 | 0.849 | 0.840 | -0.009 |
| 90-100% | 199 | 0.958 | 0.960 | 0.001 |

**Line 40.5**: n=1048, mean predicted P(over) 0.363, actual over rate 0.375, Brier 0.1299

| P(over) bucket | n | mean predicted | actual hit rate | actual - predicted |
|---|---|---|---|---|
| 0-10% | 305 | 0.025 | 0.030 | 0.005 |
| 10-20% | 115 | 0.148 | 0.148 | -0.000 |
| 20-30% | 103 | 0.248 | 0.214 | -0.034 |
| 30-40% | 98 | 0.353 | 0.357 | 0.005 |
| 40-50% | 67 | 0.451 | 0.448 | -0.004 |
| 50-60% | 92 | 0.552 | 0.565 | 0.013 |
| 60-70% | 73 | 0.656 | 0.767 | 0.112 |
| 70-80% | 60 | 0.759 | 0.833 | 0.074 |
| 80-90% | 72 | 0.851 | 0.875 | 0.024 |
| 90-100% | 63 | 0.948 | 0.937 | -0.011 |

**Line 50.5**: n=1048, mean predicted P(over) 0.216, actual over rate 0.230, Brier 0.0947

| P(over) bucket | n | mean predicted | actual hit rate | actual - predicted |
|---|---|---|---|---|
| 0-10% | 531 | 0.024 | 0.017 | -0.007 |
| 10-20% | 123 | 0.144 | 0.122 | -0.022 |
| 20-30% | 94 | 0.254 | 0.234 | -0.020 |
| 30-40% | 70 | 0.347 | 0.443 | 0.096 |
| 40-50% | 55 | 0.442 | 0.509 | 0.067 |
| 50-60% | 50 | 0.557 | 0.640 | 0.083 |
| 60-70% | 41 | 0.652 | 0.683 | 0.031 |
| 70-80% | 35 | 0.746 | 0.914 | 0.168 |
| 80-90% | 30 | 0.844 | 0.933 | 0.090 |
| 90-100% | 19 | 0.931 | 0.842 | -0.089 |

**Line 60.5**: n=1048, mean predicted P(over) 0.126, actual over rate 0.135, Brier 0.0706

| P(over) bucket | n | mean predicted | actual hit rate | actual - predicted |
|---|---|---|---|---|
| 0-10% | 696 | 0.016 | 0.013 | -0.003 |
| 10-20% | 123 | 0.142 | 0.146 | 0.004 |
| 20-30% | 60 | 0.240 | 0.250 | 0.010 |
| 30-40% | 54 | 0.351 | 0.426 | 0.075 |
| 40-50% | 35 | 0.457 | 0.486 | 0.029 |
| 50-60% | 25 | 0.544 | 0.680 | 0.136 |
| 60-70% | 24 | 0.648 | 0.917 | 0.269 |
| 70-80% | 14 | 0.748 | 0.571 | -0.177 |
| 80-90% | 16 | 0.845 | 0.750 | -0.095 |
| 90-100% | 1 | 0.910 | 1.000 | 0.090 |

**Line 70.5**: n=1048, mean predicted P(over) 0.073, actual over rate 0.074, Brier 0.0477

| P(over) bucket | n | mean predicted | actual hit rate | actual - predicted |
|---|---|---|---|---|
| 0-10% | 837 | 0.013 | 0.010 | -0.004 |
| 10-20% | 77 | 0.142 | 0.195 | 0.053 |
| 20-30% | 47 | 0.244 | 0.213 | -0.032 |
| 30-40% | 28 | 0.334 | 0.393 | 0.058 |
| 40-50% | 23 | 0.444 | 0.565 | 0.122 |
| 50-60% | 13 | 0.539 | 0.692 | 0.154 |
| 60-70% | 13 | 0.654 | 0.462 | -0.192 |
| 70-80% | 9 | 0.756 | 0.556 | -0.200 |
| 80-90% | 1 | 0.822 | 1.000 | 0.178 |


## 8. Calibration of P(over) — walk-forward, primary set

**Line 20.5**: n=14648, mean predicted P(over) 0.816, actual over rate 0.815, Brier 0.0781

| P(over) bucket | n | mean predicted | actual hit rate | actual - predicted |
|---|---|---|---|---|
| 0-10% | 490 | 0.047 | 0.033 | -0.015 |
| 10-20% | 396 | 0.149 | 0.114 | -0.036 |
| 20-30% | 333 | 0.251 | 0.198 | -0.052 |
| 30-40% | 339 | 0.352 | 0.324 | -0.028 |
| 40-50% | 405 | 0.455 | 0.402 | -0.052 |
| 50-60% | 441 | 0.551 | 0.526 | -0.025 |
| 60-70% | 686 | 0.654 | 0.644 | -0.009 |
| 70-80% | 965 | 0.753 | 0.753 | -0.000 |
| 80-90% | 1853 | 0.857 | 0.877 | 0.021 |
| 90-100% | 8740 | 0.970 | 0.974 | 0.005 |

**Line 30.5**: n=14648, mean predicted P(over) 0.593, actual over rate 0.590, Brier 0.1295

| P(over) bucket | n | mean predicted | actual hit rate | actual - predicted |
|---|---|---|---|---|
| 0-10% | 1864 | 0.030 | 0.019 | -0.010 |
| 10-20% | 764 | 0.147 | 0.101 | -0.046 |
| 20-30% | 796 | 0.249 | 0.230 | -0.019 |
| 30-40% | 801 | 0.351 | 0.330 | -0.021 |
| 40-50% | 948 | 0.452 | 0.426 | -0.026 |
| 50-60% | 1126 | 0.553 | 0.528 | -0.025 |
| 60-70% | 1320 | 0.651 | 0.653 | 0.002 |
| 70-80% | 1720 | 0.752 | 0.757 | 0.005 |
| 80-90% | 2167 | 0.853 | 0.870 | 0.017 |
| 90-100% | 3142 | 0.952 | 0.964 | 0.012 |

**Line 40.5**: n=14648, mean predicted P(over) 0.380, actual over rate 0.380, Brier 0.1289

| P(over) bucket | n | mean predicted | actual hit rate | actual - predicted |
|---|---|---|---|---|
| 0-10% | 4040 | 0.027 | 0.022 | -0.005 |
| 10-20% | 1542 | 0.147 | 0.111 | -0.036 |
| 20-30% | 1329 | 0.249 | 0.236 | -0.013 |
| 30-40% | 1174 | 0.350 | 0.311 | -0.039 |
| 40-50% | 1177 | 0.449 | 0.445 | -0.004 |
| 50-60% | 1133 | 0.550 | 0.552 | 0.001 |
| 60-70% | 1152 | 0.650 | 0.688 | 0.037 |
| 70-80% | 1195 | 0.751 | 0.776 | 0.025 |
| 80-90% | 1131 | 0.850 | 0.893 | 0.043 |
| 90-100% | 775 | 0.938 | 0.960 | 0.022 |

**Line 50.5**: n=14648, mean predicted P(over) 0.227, actual over rate 0.224, Brier 0.1022

| P(over) bucket | n | mean predicted | actual hit rate | actual - predicted |
|---|---|---|---|---|
| 0-10% | 6982 | 0.023 | 0.018 | -0.005 |
| 10-20% | 1719 | 0.148 | 0.114 | -0.034 |
| 20-30% | 1291 | 0.248 | 0.230 | -0.018 |
| 30-40% | 1099 | 0.349 | 0.344 | -0.005 |
| 40-50% | 937 | 0.449 | 0.446 | -0.003 |
| 50-60% | 851 | 0.549 | 0.571 | 0.022 |
| 60-70% | 683 | 0.650 | 0.697 | 0.047 |
| 70-80% | 579 | 0.748 | 0.784 | 0.036 |
| 80-90% | 386 | 0.845 | 0.873 | 0.028 |
| 90-100% | 121 | 0.926 | 0.983 | 0.058 |

**Line 60.5**: n=14648, mean predicted P(over) 0.130, actual over rate 0.131, Brier 0.0718

| P(over) bucket | n | mean predicted | actual hit rate | actual - predicted |
|---|---|---|---|---|
| 0-10% | 9407 | 0.018 | 0.011 | -0.006 |
| 10-20% | 1703 | 0.146 | 0.140 | -0.005 |
| 20-30% | 1088 | 0.248 | 0.244 | -0.004 |
| 30-40% | 812 | 0.347 | 0.351 | 0.004 |
| 40-50% | 592 | 0.449 | 0.485 | 0.036 |
| 50-60% | 445 | 0.547 | 0.584 | 0.037 |
| 60-70% | 308 | 0.647 | 0.698 | 0.051 |
| 70-80% | 200 | 0.744 | 0.815 | 0.071 |
| 80-90% | 88 | 0.839 | 0.966 | 0.127 |
| 90-100% | 5 | 0.936 | 1.000 | 0.064 |

**Line 70.5**: n=14648, mean predicted P(over) 0.072, actual over rate 0.071, Brier 0.0470

| P(over) bucket | n | mean predicted | actual hit rate | actual - predicted |
|---|---|---|---|---|
| 0-10% | 11390 | 0.014 | 0.014 | -0.001 |
| 10-20% | 1396 | 0.144 | 0.122 | -0.021 |
| 20-30% | 745 | 0.247 | 0.239 | -0.008 |
| 30-40% | 460 | 0.345 | 0.350 | 0.005 |
| 40-50% | 307 | 0.444 | 0.472 | 0.028 |
| 50-60% | 188 | 0.544 | 0.596 | 0.051 |
| 60-70% | 107 | 0.644 | 0.654 | 0.010 |
| 70-80% | 50 | 0.739 | 0.840 | 0.101 |
| 80-90% | 5 | 0.863 | 1.000 | 0.137 |


## 9. PIT histograms (primary set)

### Holdout (n=1048)

| PIT bin | n | fraction (0.100 = uniform) |  |
|---|---|---|---|
| 0.0-0.1 | 100 | 0.095 | ################### |
| 0.1-0.2 | 104 | 0.099 | #################### |
| 0.2-0.3 | 97 | 0.093 | ################### |
| 0.3-0.4 | 106 | 0.101 | #################### |
| 0.4-0.5 | 106 | 0.101 | #################### |
| 0.5-0.6 | 93 | 0.089 | ################## |
| 0.6-0.7 | 119 | 0.114 | ####################### |
| 0.7-0.8 | 106 | 0.101 | #################### |
| 0.8-0.9 | 110 | 0.105 | ##################### |
| 0.9-1.0 | 107 | 0.102 | #################### |

A calibrated forecast gives a flat histogram. U-shape = too narrow (overconfident); hump = too wide; slope = biased mean.

### Walk-forward (n=14648)

| PIT bin | n | fraction (0.100 = uniform) |  |
|---|---|---|---|
| 0.0-0.1 | 1269 | 0.087 | ################# |
| 0.1-0.2 | 1429 | 0.098 | #################### |
| 0.2-0.3 | 1539 | 0.105 | ##################### |
| 0.3-0.4 | 1541 | 0.105 | ##################### |
| 0.4-0.5 | 1634 | 0.112 | ###################### |
| 0.5-0.6 | 1534 | 0.105 | ##################### |
| 0.6-0.7 | 1552 | 0.106 | ##################### |
| 0.7-0.8 | 1542 | 0.105 | ##################### |
| 0.8-0.9 | 1452 | 0.099 | #################### |
| 0.9-1.0 | 1156 | 0.079 | ################ |

A calibrated forecast gives a flat histogram. U-shape = too narrow (overconfident); hump = too wide; slope = biased mean.

## 10. The 20 largest holdout misses (primary set)

Diagnosis splits log(actual / projected) into a team-volume part (β·log(actual team passes / projected)) and a share part (log(actual on-pitch share / projected share)); these sum exactly. Misses within 2 SD of the forecast distribution are labelled variance.

| player (match) | role | actual min | actual passes | proj mean | p10–p90 | team actual | team proj | diagnosis |
|---|---|---|---|---|---|---|---|---|
| Elliot Anderson (Manchester City v Coventry City, 2026-09-05) | MID | 90 | 158 | 90.300 | 58–126 | 819 | 706.0 | Share miss: team passes 819 vs proj 706 (+16%); on-pitch share 0.193 vs proj 0.128 (+51%); z=+2.5 |
| Rúben Dias (Manchester City v AFC Bournemouth, 2026-08-23) | DEF | 90 | 128 | 70.500 | 43–100 | 658 | 566.0 | Share miss: team passes 658 vs proj 566 (+16%); on-pitch share 0.177 vs proj 0.118 (+51%); z=+2.5 |
| Ross Barkley (Aston Villa v Hull City, 2026-09-05) | MID | 90 | 103 | 46.300 | 29–66 | 694 | 476.0 | Share miss: team passes 694 vs proj 476 (+46%); on-pitch share 0.148 vs proj 0.097 (+52%); z=+3.9 |
| Rúben Dias (Manchester City v Sunderland, 2026-09-20) | DEF | 90 | 31 | 84.800 | 53–120 | 475 | 618.0 | Share miss: team passes 475 vs proj 618 (-23%); on-pitch share 0.064 vs proj 0.127 (-49%); z=-2.0 |
| Luka Vuskovic (Brighton & Hove Albion v Aston Villa, 2026-08-23) | DEF | 90 | 103 | 49.700 | 30–71 | 647 | 437.0 | Team volume miss: team passes 647 vs proj 437 (+48%); on-pitch share 0.145 vs proj 0.115 (+27%); z=+3.3 |
| Matt Grimes (Coventry City v Hull City, 2026-08-29) | MID | 90 | 108 | 56.800 | 36–80 | 584 | 444.0 | Share miss: team passes 584 vs proj 444 (+32%); on-pitch share 0.185 vs proj 0.128 (+45%); z=+2.9 |
| Ronald Araujo (Liverpool v Ipswich Town, 2026-09-04) | DEF | 90 | 37 | 86.700 | 54–123 | 531 | 585.0 | Variance (within 2 SD of the forecast): team passes 531 vs proj 585 (-9%); on-pitch share 0.067 vs proj 0.139 (-52%); z=-1.8 |
| Lewis Dunk (Brighton & Hove Albion v Aston Villa, 2026-08-23) | DEF | 90 | 114 | 67.300 | 41–96 | 647 | 437.0 | Team volume miss: team passes 647 vs proj 437 (+48%); on-pitch share 0.161 vs proj 0.155 (+4%); z=+2.2 |
| Victor Nilsson Lindelöf (Aston Villa v Hull City, 2026-09-05) | DEF | 90 | 110 | 63.600 | 39–91 | 694 | 476.0 | Team volume miss: team passes 694 vs proj 476 (+46%); on-pitch share 0.142 vs proj 0.132 (+8%); z=+2.3 |
| Levi Colwill (Chelsea v Fulham, 2026-08-24) | DEF | 90 | 30 | 75.500 | 47–107 | 394 | 531.0 | Variance (within 2 SD of the forecast): team passes 394 vs proj 531 (-26%); on-pitch share 0.079 vs proj 0.136 (-42%); z=-1.9 |
| Boubacar Kamara (Aston Villa v Hull City, 2026-09-05) | MID | 90 | 97 | 55.300 | 35–78 | 694 | 476.0 | Team volume miss: team passes 694 vs proj 476 (+46%); on-pitch share 0.140 vs proj 0.116 (+20%); z=+2.4 |
| Virgil van Dijk (Liverpool v Nottingham Forest, 2026-08-29) | DEF | 90 | 114 | 73.200 | 45–104 | 631 | 538.0 | Variance (within 2 SD of the forecast): team passes 631 vs proj 538 (+17%); on-pitch share 0.166 vs proj 0.130 (+28%); z=+1.7 |
| Jérémy Jacquet (Liverpool v Nottingham Forest, 2026-08-29) | DEF | 77 | 94 | 54.100 | 33–78 | 631 | 538.0 | Share miss: team passes 631 vs proj 538 (+17%); on-pitch share 0.160 vs proj 0.112 (+42%); z=+2.3 |
| Elliot Anderson (Manchester City v Manchester United, 2026-09-13) | MID | 90 | 54 | 93.400 | 60–130 | 403 | 613.0 | Variance (within 2 SD of the forecast): team passes 403 vs proj 613 (-34%); on-pitch share 0.134 vs proj 0.152 (-12%); z=-1.4 |
| Marcos Senesi (Tottenham Hotspur v Brentford, 2026-08-22) | DEF | 90 | 83 | 43.800 | 26–63 | 549 | 399.0 | Team volume miss: team passes 549 vs proj 399 (+38%); on-pitch share 0.144 vs proj 0.113 (+27%); z=+2.7 |
| Lisandro Martínez (Manchester United v Everton, 2026-09-06) | DEF | 90 | 44 | 82.600 | 51–117 | 527 | 562.0 | Variance (within 2 SD of the forecast): team passes 527 vs proj 562 (-6%); on-pitch share 0.080 vs proj 0.139 (-42%); z=-1.5 |
| Alex Iwobi (Fulham v Chelsea, 2026-08-24) | MID | 90 | 92 | 53.600 | 34–76 | 639 | 453.0 | Team volume miss: team passes 639 vs proj 453 (+41%); on-pitch share 0.144 vs proj 0.118 (+22%); z=+2.3 |
| Ezri Konsa (Arsenal v Brighton & Hove Albion, 2026-09-19) | DEF | 90 | 67 | 29.300 | 17–43 | 511 | 340.0 | Team volume miss: team passes 511 vs proj 340 (+50%); on-pitch share 0.127 vs proj 0.093 (+37%); z=+3.7 |
| Jan Paul van Hecke (Tottenham Hotspur v Newcastle United, 2026-08-29) | DEF | 90 | 82 | 44.300 | 27–64 | 498 | 415.0 | Share miss: team passes 498 vs proj 415 (+20%); on-pitch share 0.161 vs proj 0.109 (+47%); z=+2.5 |
| Sandro Tonali (Tottenham Hotspur v Everton, 2026-09-12) | MID | 90 | 88 | 51.600 | 32–73 | 644 | 526.0 | Share miss: team passes 644 vs proj 526 (+23%); on-pitch share 0.137 vs proj 0.098 (+39%); z=+2.3 |

Summary: Share miss: 8, Team volume miss: 7, Variance (within 2 SD of the forecast): 5
