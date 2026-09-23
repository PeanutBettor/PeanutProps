"""Writes reports/model_validation.md from the stored walk-forward (train) and holdout predictions."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .. import config
from . import dist
from .backtest import (BETA_GRID, BURN_IN_BLOCKS, HOLDOUT_SEASON, PRIMARY_MIN_MINUTES, SHARE_GRID, TEAM_GRID,
                       TRAIN_SEASONS)
from .share import REF

LINES = (20.5, 30.5, 40.5, 50.5, 60.5, 70.5)
METHODS = {"model": "Model", "base_std": "Season-to-date per 90", "base_last5": "Last-5 per 90",
           "base_last10": "Last-10 per 90"}
MODELS_DIR = config.ROOT / "models"


def _t(headers, rows) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join(_f(v) for v in r) + " |")
    return "\n".join(out)


def _f(v) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return ""
    if isinstance(v, (float, np.floating)):
        return f"{v:.3f}" if abs(v) < 100 else f"{v:.1f}"
    return str(v)


def load(con, phase: str) -> pd.DataFrame:
    return con.execute("SELECT * FROM model_backtest WHERE phase = ?", [phase]).df()


def _sizes(meta: dict) -> dict:
    s = meta["params"]["dist"]["size"]
    return s


def _model_size(df: pd.DataFrame, meta: dict):
    if meta["params"]["dist"]["family"] == "poisson":
        return None
    s = _sizes(meta)
    return df["role"].map(lambda r: s.get(r, s.get("ALL"))).to_numpy(float)


def comparable(df: pd.DataFrame) -> pd.DataFrame:
    ok = df["mu"].notna() & (df["mu"] > 0)
    for b in ("base_std", "base_last5", "base_last10"):
        ok &= df[b].notna() & (df[b] > 0)
    return df[ok]


def score(df: pd.DataFrame, meta: dict) -> list:
    rows = []
    for key, label in METHODS.items():
        mu = df["mu"] if key == "model" else df[key]
        r = _model_size(df, meta) if key == "model" else meta["baseline_nb_size"][key]
        err = mu - df["passes"]
        rows.append([label, len(df), float(np.mean(np.abs(err))), float(np.sqrt(np.mean(err ** 2))),
                     float(np.mean(err)), float(dist.log_loss(df["passes"], mu, r).mean()),
                     float(dist.crps(df["passes"].to_numpy(), mu.to_numpy(), r).mean())])
    return rows


def breakdown(df: pd.DataFrame, by: str) -> list:
    out = []
    for k, g in df.groupby(by):
        e = g["mu"] - g["passes"]
        out.append([k, len(g), float(np.mean(np.abs(e))), float(np.sqrt(np.mean(e ** 2))), float(np.mean(e))])
    return sorted(out, key=lambda r: -r[1])


def calibration(df: pd.DataFrame, meta: dict) -> str:
    r = _model_size(df, meta)
    parts = []
    for L in LINES:
        p = dist.prob_over(L, df["mu"].to_numpy(), r)
        hit = (df["passes"].to_numpy() > L).astype(float)
        b = np.minimum((p * 10).astype(int), 9)
        rows = []
        for i in range(10):
            m = b == i
            if m.sum():
                rows.append([f"{10*i}-{10*i+10}%", int(m.sum()), float(p[m].mean()), float(hit[m].mean()),
                             float(hit[m].mean() - p[m].mean())])
        brier = float(np.mean((p - hit) ** 2))
        parts += [f"**Line {L}**: n={len(df)}, mean predicted P(over) {p.mean():.3f}, actual over rate "
                  f"{hit.mean():.3f}, Brier {brier:.4f}", "",
                  _t(["P(over) bucket", "n", "mean predicted", "actual hit rate", "actual - predicted"], rows), ""]
    return "\n".join(parts)


def pit_hist(df: pd.DataFrame, meta: dict) -> str:
    u = dist.randomized_pit(df["passes"].to_numpy(), df["mu"].to_numpy(), _model_size(df, meta))
    counts, _ = np.histogram(u, bins=10, range=(0, 1))
    frac = counts / counts.sum()
    rows = [[f"{i/10:.1f}-{(i+1)/10:.1f}", int(c), float(f), "#" * int(round(f * 200))] for i, (c, f) in
            enumerate(zip(counts, frac))]
    return (_t(["PIT bin", "n", "fraction (0.100 = uniform)", ""], rows) +
            "\n\nA calibrated forecast gives a flat histogram. U-shape = too narrow (overconfident); hump = too wide; "
            "slope = biased mean.")


def diagnose(row, beta: dict, r) -> str:
    b = beta[row["role"]]
    team_part = b * np.log(row["team_total"] / row["team_proj"])
    exp_act = REF * (row["team_total"] / REF) ** b * row["minutes"] / 90.0
    s_act = row["passes"] / exp_act
    share_part = np.log(max(s_act, 1e-9) / row["share"])
    sd = np.sqrt(row["mu"] + (row["mu"] ** 2 / r if r else 0))
    z = (row["passes"] - row["mu"]) / sd
    detail = (f"team passes {row['team_total']:.0f} vs proj {row['team_proj']:.0f} ({np.exp(team_part / b if b else 0) - 1:+.0%}); "
              f"on-pitch share {s_act:.3f} vs proj {row['share']:.3f} ({np.exp(share_part) - 1:+.0%}); z={z:+.1f}")
    if abs(z) <= 2:
        kind = "Variance (within 2 SD of the forecast)"
    elif abs(team_part) >= abs(share_part):
        kind = "Team volume miss"
    else:
        kind = "Share miss"
    return f"{kind}: {detail}"


def volume_flag_section(con) -> list:
    """Teams whose last 5 matches deviate > 2 SE from their earlier season volume, at every block cutoff."""
    from .backtest import WalkForward, fixture_teams
    from .data import load_appearances
    from .team import volume_shift_flags
    app = load_appearances(con)
    wf = WalkForward(app, fixture_teams(con))
    events = []
    for season in (*TRAIN_SEASONS, HOLDOUT_SEASON):
        for b in wf.blocks(season):
            f = volume_shift_flags(wf.history(b), season)
            if len(f):
                events.append(f)
    out = ["### Volume-shift flags (possible manager / style change — flagged for manual review, NOT modelled)", "",
           "Rule: at a block cutoff, a team with ≥ 10 matches this season is flagged when the mean of its last 5 "
           "matches differs from its earlier-season mean by more than 2 standard errors "
           "(SE = SD of earlier matches / √5).", ""]
    if not events:
        return out + ["No flags.", ""]
    ev = pd.concat(events, ignore_index=True).sort_values(["season", "team", "as_of"])
    rows = []
    for _, r in ev.iterrows():
        rows.append([r["season"], r["team"], str(pd.Timestamp(r["as_of"]).date()), int(r["n_matches"]),
                     float(r["earlier_mean"]), float(r["last5_mean"]), float(r["z"])])
    out += [f"Every flagged cutoff is listed. {len(ev)} team-cutoff flags across {ev.groupby(['season', 'team']).ngroups} team-seasons:", "",
            _t(["season", "team", "as of (cutoff)", "matches", "earlier mean", "last-5 mean", "z"], rows), ""]
    return out


def build(con) -> str:
    meta = json.loads((MODELS_DIR / "params.json").read_text())
    hl = MODELS_DIR / "holdout_log.json"
    holdout_runs = json.loads(hl.read_text()) if hl.exists() else []
    train = load(con, "train")
    hold = load(con, "holdout") if holdout_runs else pd.DataFrame()
    P = meta["params"]
    beta = P["share"]["beta"]
    L = ["# Model Validation — EPL passes attempted (rate + distribution)", ""]
    L += [f"Model version **{meta['model_version']}** (hash of parameters + projection code). "
          f"Data snapshot {meta['data_snapshot']} UTC. Tuned {meta['tuned_at']}.", "",
          "> **Minutes are ORACLE (actual) minutes** in every backtest number below. These results measure the "
          "rate model (team volume × share × distribution) only. Real-world error will be larger once minutes "
          "must be predicted (prompt 3).", "",
          f"- Walk-forward: chronological match-week blocks (a new block starts after a >30 h gap between kickoffs). "
          f"For each block the model is refit on matches completed before the block's first kickoff "
          f"(kickoff + 3 h), then the block is projected.",
          f"- Training / tuning: {', '.join(TRAIN_SEASONS)}. The first {BURN_IN_BLOCKS} blocks of 2024-25 are not "
          f"scored (the database has no earlier data to project from).",
          f"- Holdout: {HOLDOUT_SEASON}, never used in tuning. Holdout scoring runs so far: **{len(holdout_runs)}**"
          + (f" (first at {holdout_runs[0]['scored_at']}, version {holdout_runs[0]['model_version']})." if holdout_runs else "."),
          f"- Primary evaluation set: starters with ≥ {PRIMARY_MIN_MINUTES} actual minutes. Subs are reported "
          "separately.", ""]

    # ---- parameters
    tp, sp = P["team"], P["share"]
    L += ["## 1. Chosen parameters and how each was chosen", "",
          _t(["parameter", "value", "grid searched", "how chosen"], [
              ["team: recency decay per match", tp["decay"], TEAM_GRID["decay"], "full grid, walk-forward team-passes MAE"],
              ["team: prior strength k (matches)", tp["k_prior"], TEAM_GRID["k_prior"], "same grid"],
              ["team: promoted-team prior multiplier", tp["promoted_mult"], TEAM_GRID["promoted_mult"], "same grid"],
              ["share: recency decay per appearance", sp["decay"], SHARE_GRID["decay"], "coordinate descent (2 passes, warm start from a first narrower-grid pass), walk-forward primary-set NB log-loss"],
              ["share: recent→long-term strength k_long", sp["k_long"], SHARE_GRID["k_long"], "same"],
              ["share: long-term→role prior strength k_role", sp["k_role"], SHARE_GRID["k_role"], "same"],
              ["share: team role→league role strength k_league", sp["k_league"], SHARE_GRID["k_league"], "same"],
              ["share: weight of <20-min appearances", sp["short_weight"], SHARE_GRID["short_weight"], "same"],
              *[[f"volume elasticity beta {r}", beta[r], BETA_GRID, "same"] for r in ("GK", "DEF", "MID", "FWD")],
              ["distribution", P["dist"]["family"] + " " + json.dumps({k: round(v, 2) for k, v in P["dist"]["size"].items()}),
               "Poisson / NB one size / NB size per position", "cross-season validation log-loss (table below)"],
              ["home effect eta", "re-estimated each block", "", "half the mean log(home/away passes) of completed matches"],
          ]), "",
          "Strengths k are in full-match equivalents (1 = one match of evidence; for shares, one match of "
          f"{REF:.0f} team passes). Search traces: `models/tuning_trace_team.csv`, `models/tuning_trace_share.csv`.", ""]
    dsel = pd.DataFrame(meta["distribution_selection"])
    L += ["### Distribution selection (fit on one training season, scored on the other, both directions)", "",
          _t(["subset", "family", "validation log-loss", "n"], dsel[["subset", "family", "logloss", "n"]].values.tolist()),
          "", f"Baseline NB sizes (fit on their own training predictions): "
          + ", ".join(f"{k} {v:.1f}" for k, v in meta["baseline_nb_size"].items()), ""]

    # ---- team volume
    L += ["## 2. Team volume", ""]
    for name, f in (("Walk-forward (train)", "team_predictions_train.csv"), ("Holdout", "team_predictions_holdout.csv")):
        p = MODELS_DIR / f
        if not p.exists():
            continue
        t = pd.read_csv(p)
        t = t[t["scored"] & t["team_proj"].notna()] if "scored" in t else t[t["team_proj"].notna()]
        e = t["team_proj"] - t["passes"]
        L.append(f"- {name}: {len(t)} team-matches, MAE {np.abs(e).mean():.1f}, RMSE {np.sqrt((e**2).mean()):.1f}, "
                 f"bias {e.mean():+.1f} passes (mean actual {t['passes'].mean():.0f}).")
    L.append("")
    L += volume_flag_section(con)

    # ---- walk-forward
    def section(title, df):
        out = [f"## {title}", ""]
        if df.empty:
            return out + ["Not scored yet.", ""]
        df = df[df["scored"]]
        for label, sub in (("Primary: starters ≥ 60 min", df[df["primary"]]),
                           ("Subs (came off the bench)", df[~df["started"]]),
                           ("Starters < 60 min", df[df["started"] & ~df["primary"]])):
            c = comparable(sub)
            out += [f"### {label}", "",
                    f"Rows: {len(sub)}; projectable by model: {int(sub['mu'].notna().sum())}; "
                    f"comparable (model and all three baselines defined and > 0): {len(c)}.", "",
                    _t(["method", "n", "MAE", "RMSE", "bias", "NB log-loss", "CRPS"], score(c, meta)), ""]
        return out

    L += section("3. Walk-forward results (training seasons, oracle minutes)", train)
    L += section("4. HOLDOUT results — 2026-27 (scored once, oracle minutes)", hold)

    if not hold.empty:
        h = comparable(hold[hold["primary"]])
        sc = {r[0]: r for r in score(h, meta)}
        m = sc["Model"]
        beats = {lab: (m[2] < sc[lab][2], m[5] < sc[lab][5]) for lab in list(METHODS.values())[1:]}
        all_ok = all(a and b for a, b in beats.values())
        L += ["### Verdict (holdout, primary set)", ""]
        for lab, (a, b) in beats.items():
            L.append(f"- vs {lab}: MAE {'better' if a else 'NOT better'} ({m[2]:.3f} vs {sc[lab][2]:.3f}); "
                     f"log-loss {'better' if b else 'NOT better'} ({m[5]:.4f} vs {sc[lab][5]:.4f}).")
        L += ["", f"**The model {'beats' if all_ok else 'does NOT beat'} all three baselines on both MAE and log-loss "
              f"in the holdout.**", ""]

    # ---- breakdowns
    for title, df in (("5. Holdout breakdowns (primary set)", hold), ("6. Walk-forward breakdowns (primary set)", train)):
        if df.empty:
            continue
        d = df[df["scored"] & df["primary"] & df["mu"].notna()].copy()
        d["home/away"] = np.where(d["is_home"], "home", "away")
        L += [f"## {title}", ""]
        for by in ("role", "home/away", "team"):
            L += [f"### By {by}", "", _t([by, "n", "MAE", "RMSE", "bias (proj - actual)"], breakdown(d, by)), ""]

    # ---- calibration
    for title, df in (("7. Calibration of P(over) — holdout, primary set", hold),
                      ("8. Calibration of P(over) — walk-forward, primary set", train)):
        if df.empty:
            continue
        d = df[df["scored"] & df["primary"] & df["mu"].notna()]
        L += [f"## {title}", "", calibration(d, meta), ""]

    # ---- PIT
    L += ["## 9. PIT histograms (primary set)", ""]
    for name, df in (("Holdout", hold), ("Walk-forward", train)):
        if df.empty:
            continue
        d = df[df["scored"] & df["primary"] & df["mu"].notna()]
        L += [f"### {name} (n={len(d)})", "", pit_hist(d, meta), ""]

    # ---- misses
    if not hold.empty:
        d = hold[hold["primary"] & hold["mu"].notna()].copy()
        d["abs_err"] = (d["mu"] - d["passes"]).abs()
        top = d.sort_values("abs_err", ascending=False).head(20)
        sizes = P["dist"]["size"]
        rows = []
        for _, r in top.iterrows():
            size = None if P["dist"]["family"] == "poisson" else sizes.get(r["role"], sizes.get("ALL"))
            rows.append([f"{r['player_name']} ({r['team']} v {r['opponent']}, {pd.Timestamp(r['kickoff']).date()})",
                         r["role"], int(r["minutes"]), int(r["passes"]), round(r["mu"], 1),
                         f"{int(r['p10'])}–{int(r['p90'])}", int(r["team_total"]), round(r["team_proj"], 0),
                         diagnose(r, beta, size)])
        L += ["## 10. The 20 largest holdout misses (primary set)", "",
              "Diagnosis splits log(actual / projected) into a team-volume part (β·log(actual team passes / "
              "projected)) and a share part (log(actual on-pitch share / projected share)); these sum exactly. "
              "Misses within 2 SD of the forecast distribution are labelled variance.", "",
              _t(["player (match)", "role", "actual min", "actual passes", "proj mean", "p10–p90",
                  "team actual", "team proj", "diagnosis"], rows), ""]
        kinds = pd.Series([r[-1].split(":")[0] for r in rows]).value_counts()
        L += ["Summary: " + ", ".join(f"{k}: {v}" for k, v in kinds.items()), ""]
    return "\n".join(L)


def write(con, path: Path = config.REPORTS_DIR / "model_validation.md") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build(con), encoding="utf-8")
    return path
