"""
Annotation quality checks.

Input is a long-format DataFrame of single-response grades with (at least):
    task_id, rater_id, dimension, score
and optionally: timestamp, duration_sec, gold_score (reference score for gold items),
comment.

Pairwise judgements use a separate frame with:
    task_id, rater_id, preference (-3..3), first_position ("A" or "B"), reason_code

Each check returns a DataFrame; `flag_raters` turns them into a per-rater
flag table with plain-language reasons. The thresholds are defaults that work
for 1-5 rubrics with 3 raters per item - tune them in `Thresholds`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .agreement import cohen_kappa


@dataclass
class Thresholds:
    min_kappa_vs_consensus: float = 0.55      # quadratic-weighted kappa, rater vs leave-one-out consensus
    max_abs_bias: float = 0.40                # mean (rater - consensus) across dimensions
    max_straightline_share: float = 0.35      # share of tasks where a rater gave the same score to every dimension
    min_score_sd: float = 0.60                # a rater who never varies is not grading
    fast_duration_quantile: float = 0.10      # durations below this quantile of the pool are "too fast"
    max_fast_share: float = 0.30
    min_gold_accuracy: float = 0.70           # share of gold items within +/-1 of reference
    position_bias_band: tuple = (0.42, 0.58)  # acceptable first-position preference share
    max_tie_share: float = 0.15
    max_drift: float = 0.40                   # change in mean deviation from consensus, first period -> last


# --------------------------------------------------------------------------- helpers

def to_wide(df: pd.DataFrame, dimension: str | None = None) -> pd.DataFrame:
    """Long -> wide (rows: task or task×dimension, columns: raters)."""
    d = df if dimension is None else df[df["dimension"] == dimension]
    idx = ["task_id"] if dimension is not None else ["task_id", "dimension"]
    return d.pivot_table(index=idx, columns="rater_id", values="score", aggfunc="first")


def consensus(df: pd.DataFrame, method: str = "median") -> pd.DataFrame:
    """Consensus score per task × dimension across raters."""
    agg = "median" if method == "median" else "mean"
    return df.groupby(["task_id", "dimension"])["score"].agg(agg).rename("consensus").reset_index()


# --------------------------------------------------------------------------- checks

def rater_vs_consensus(df: pd.DataFrame) -> pd.DataFrame:
    """Per rater: quadratic-weighted kappa and mean bias against the leave-one-out consensus
    (median of the *other* raters), so a rater is not compared with themselves."""
    rows = []
    for rater, g in df.groupby("rater_id"):
        others = df[df["rater_id"] != rater]
        cons = others.groupby(["task_id", "dimension"])["score"].median().rename("loo_consensus").reset_index()
        m = g.merge(cons, on=["task_id", "dimension"], how="inner")
        if len(m) < 10:
            continue
        # kappa needs integer categories: round the median consensus
        kappa = cohen_kappa(m["score"].astype(int), m["loo_consensus"].round().astype(int), weights="quadratic",
                            categories=sorted(set(df["score"].astype(int))))
        rows.append({
            "rater_id": rater, "n_scores": len(m),
            "kappa_vs_consensus": kappa,
            "mean_bias": float((m["score"] - m["loo_consensus"]).mean()),
            "mean_abs_dev": float((m["score"] - m["loo_consensus"]).abs().mean()),
            "share_within_1": float(((m["score"] - m["loo_consensus"]).abs() <= 1).mean()),
        })
    return pd.DataFrame(rows).set_index("rater_id")


def score_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Per rater: mean, SD, share of each score value, straight-lining share."""
    rows = []
    for rater, g in df.groupby("rater_id"):
        per_task = g.groupby("task_id")["score"].agg(["nunique", "size"])
        straight = float(((per_task["nunique"] == 1) & (per_task["size"] >= 3)).mean()) if len(per_task) else np.nan
        dist = g["score"].value_counts(normalize=True).sort_index()
        row = {"rater_id": rater, "n_tasks": g["task_id"].nunique(), "mean_score": g["score"].mean(),
               "score_sd": g["score"].std(ddof=0), "straightline_share": straight}
        row.update({f"share_{int(k)}": float(v) for k, v in dist.items()})
        rows.append(row)
    return pd.DataFrame(rows).set_index("rater_id").fillna(0.0)


def drift_over_time(df: pd.DataFrame, freq: str = "W") -> pd.DataFrame:
    """Per rater and period: mean deviation from consensus. Reveals raters who become
    harsher/laxer over time (fatigue, rubric drift)."""
    if "timestamp" not in df:
        return pd.DataFrame()
    cons = consensus(df)
    m = df.merge(cons, on=["task_id", "dimension"])
    m["period"] = pd.to_datetime(m["timestamp"]).dt.to_period(freq).astype(str)
    m["dev"] = m["score"] - m["consensus"]
    return m.pivot_table(index="rater_id", columns="period", values="dev", aggfunc="mean").round(2)


def duration_outliers(df: pd.DataFrame, thresholds: Thresholds = Thresholds()) -> pd.DataFrame:
    """Per rater: median time per task and share of tasks finished faster than the pool's
    fast quantile. Fast + low kappa = not reading."""
    if "duration_sec" not in df:
        return pd.DataFrame()
    per_task = df.groupby(["rater_id", "task_id"])["duration_sec"].first().reset_index()
    fast_cut = per_task["duration_sec"].quantile(thresholds.fast_duration_quantile)
    out = per_task.groupby("rater_id")["duration_sec"].agg(median_sec="median", p10_sec=lambda s: s.quantile(0.1))
    out["fast_share"] = per_task.assign(fast=per_task["duration_sec"] <= fast_cut).groupby("rater_id")["fast"].mean()
    out.attrs["fast_cut_sec"] = float(fast_cut)
    return out


def gold_accuracy(df: pd.DataFrame) -> pd.DataFrame:
    """Per rater on gold (reference-scored) items: exact match and within-±1 share."""
    if "gold_score" not in df:
        return pd.DataFrame()
    g = df.dropna(subset=["gold_score"])
    if g.empty:
        return pd.DataFrame()
    dev = (g["score"] - g["gold_score"])
    return g.assign(exact=dev == 0, within_1=dev.abs() <= 1, signed=dev).groupby("rater_id").agg(
        n_gold=("task_id", "nunique"), exact_match=("exact", "mean"), within_1=("within_1", "mean"), gold_bias=("signed", "mean"))


def dimension_agreement(df: pd.DataFrame) -> pd.DataFrame:
    """Which rubric dimensions are the hardest to agree on? Mean pairwise quadratic kappa
    per dimension — low values point at a rubric problem, not a rater problem."""
    rows = []
    for dim, g in df.groupby("dimension"):
        wide = to_wide(g, dimension=dim)
        raters = list(wide.columns)
        ks = []
        for i, r1 in enumerate(raters):
            for r2 in raters[i + 1:]:
                both = wide[[r1, r2]].dropna()
                if len(both) >= 10:
                    ks.append(cohen_kappa(both[r1].astype(int), both[r2].astype(int), weights="quadratic",
                                          categories=sorted(set(df["score"].astype(int)))))
        rows.append({"dimension": dim, "mean_pairwise_qw_kappa": float(np.mean(ks)) if ks else np.nan,
                     "min_pairwise_qw_kappa": float(np.min(ks)) if ks else np.nan,
                     "score_sd_across_raters": float(wide.std(axis=1, ddof=0).mean())})
    return pd.DataFrame(rows).set_index("dimension").sort_values("mean_pairwise_qw_kappa")


def pairwise_checks(pw: pd.DataFrame, thresholds: Thresholds = Thresholds()) -> pd.DataFrame:
    """Position bias, tie share and decisiveness for pairwise preference data."""
    rows = []
    for rater, g in pw.groupby("rater_id"):
        decided = g[g["preference"] != 0]
        prefers_first = ((decided["preference"] < 0) & (decided["first_position"] == "A")) | \
                        ((decided["preference"] > 0) & (decided["first_position"] == "B"))
        rows.append({
            "rater_id": rater, "n_judgements": len(g),
            "tie_share": float((g["preference"] == 0).mean()),
            "first_position_pref_share": float(prefers_first.mean()) if len(decided) else np.nan,
            "mean_abs_strength": float(g["preference"].abs().mean()),
            "share_extreme": float((g["preference"].abs() == 3).mean()),
        })
    out = pd.DataFrame(rows).set_index("rater_id")
    lo, hi = thresholds.position_bias_band
    out["position_bias_flag"] = ~out["first_position_pref_share"].between(lo, hi)
    out["tie_flag"] = out["tie_share"] > thresholds.max_tie_share
    return out


# --------------------------------------------------------------------------- flags

def flag_raters(df: pd.DataFrame, thresholds: Thresholds = Thresholds()) -> pd.DataFrame:
    """Combine checks into one table: rater, flags (list), summary metrics."""
    rvc = rater_vs_consensus(df)
    dist = score_distribution(df)
    dur = duration_outliers(df, thresholds)
    gold = gold_accuracy(df)
    drift = drift_over_time(df)
    rows = []
    for rater in dist.index:
        flags = []
        if len(drift) and rater in drift.index and drift.shape[1] >= 3:
            series = drift.loc[rater].dropna()
            if len(series) >= 3 and abs(series.iloc[-1] - series.iloc[0]) > thresholds.max_drift:
                flags.append(f"drift over time ({series.iloc[0]:+.2f} -> {series.iloc[-1]:+.2f} vs consensus)")
        k = rvc["kappa_vs_consensus"].get(rater, np.nan)
        b = rvc["mean_bias"].get(rater, np.nan)
        if not np.isnan(k) and k < thresholds.min_kappa_vs_consensus:
            flags.append(f"low agreement with consensus (κw={k:.2f})")
        if not np.isnan(b) and abs(b) > thresholds.max_abs_bias:
            flags.append(f"systematic {'harsh' if b < 0 else 'lenient'} bias ({b:+.2f})")
        if dist.loc[rater, "straightline_share"] > thresholds.max_straightline_share:
            flags.append(f"straight-lining ({dist.loc[rater, 'straightline_share']:.0%} of tasks)")
        if dist.loc[rater, "score_sd"] < thresholds.min_score_sd:
            flags.append(f"too little variation (sd={dist.loc[rater, 'score_sd']:.2f})")
        if len(dur) and dur["fast_share"].get(rater, 0) > thresholds.max_fast_share:
            flags.append(f"rushing ({dur['fast_share'][rater]:.0%} of tasks below fast cut-off)")
        if len(gold) and rater in gold.index and gold.loc[rater, "within_1"] < thresholds.min_gold_accuracy:
            flags.append(f"gold accuracy {gold.loc[rater, 'within_1']:.0%}")
        rows.append({"rater_id": rater, "n_tasks": dist.loc[rater, "n_tasks"], "kappa_vs_consensus": k,
                     "mean_bias": b, "flags": flags, "n_flags": len(flags)})
    return pd.DataFrame(rows).set_index("rater_id").sort_values("n_flags", ascending=False)
