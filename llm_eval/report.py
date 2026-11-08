"""
Build a Markdown quality report from an annotations file (and optionally a
pairwise-judgements file). Used by the CLI:

    python -m llm_eval.cli report data/sample/annotations.csv --pairwise data/sample/pairwise_judgements.csv
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import quality as q
from .agreement import interpret_alpha, interpret_kappa, krippendorff_alpha


def _md(df: pd.DataFrame, floatfmt: str = "{:.2f}") -> str:
    if df is None or len(df) == 0:
        return "_no data_"
    d = df.copy()
    for c in d.columns:
        if d[c].dtype.kind == "f":
            d[c] = d[c].map(lambda v: "" if pd.isna(v) else floatfmt.format(v))
        elif d[c].dtype == object:
            d[c] = d[c].map(lambda v: ", ".join(v) if isinstance(v, list) else v)
    cols = [str(d.index.name or "")] + [str(c) for c in d.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for idx, row in d.iterrows():
        lines.append("| " + " | ".join([str(idx)] + [str(v) for v in row.tolist()]) + " |")
    return "\n".join(lines)


def overall_reliability(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for dim, g in df.groupby("dimension"):
        wide = q.to_wide(g, dimension=dim)
        a_ord = krippendorff_alpha(wide.T.to_numpy(), level="ordinal")
        a_int = krippendorff_alpha(wide.T.to_numpy(), level="interval")
        modal_share = float(g["score"].value_counts(normalize=True).iloc[0])
        rows.append({"dimension": dim, "alpha_ordinal": a_ord, "alpha_interval": a_int, "modal_score_share": modal_share,
                     "verdict": interpret_alpha(a_ord)})
    all_wide = q.to_wide(df)
    rows.append({"dimension": "ALL DIMENSIONS", "alpha_ordinal": krippendorff_alpha(all_wide.T.to_numpy(), "ordinal"),
                 "alpha_interval": krippendorff_alpha(all_wide.T.to_numpy(), "interval"),
                 "modal_score_share": float(df["score"].value_counts(normalize=True).iloc[0]),
                 "verdict": interpret_alpha(krippendorff_alpha(all_wide.T.to_numpy(), "ordinal"))})
    return pd.DataFrame(rows).set_index("dimension")


def build_report(ann: pd.DataFrame, pairwise: pd.DataFrame | None = None, thresholds: q.Thresholds = q.Thresholds(),
                 title: str = "Annotation quality report") -> str:
    n_tasks, n_raters = ann["task_id"].nunique(), ann["rater_id"].nunique()
    per_task = ann.groupby("task_id")["rater_id"].nunique()
    rel = overall_reliability(ann)
    flags = q.flag_raters(ann, thresholds)
    rvc = q.rater_vs_consensus(ann)
    dist = q.score_distribution(ann)
    dims = q.dimension_agreement(ann)
    drift = q.drift_over_time(ann)
    dur = q.duration_outliers(ann, thresholds)
    gold = q.gold_accuracy(ann)

    out = [f"# {title}", "",
           f"**Pool:** {n_tasks} tasks · {n_raters} raters · {ann['dimension'].nunique()} dimensions · "
           f"{per_task.min()}–{per_task.max()} raters per task · {len(ann):,} scores", ""]

    out += ["## 1. Is the dataset reliable? (Krippendorff's α)", "",
            "α is computed per dimension over all raters, treating the 1–5 scale as ordinal (primary) and interval (reference). "
            "Krippendorff's guidance: ≥ .800 reliable, .667–.800 tentative, below .667 unreliable.", "",
            _md(rel, "{:.3f}"), ""]
    worst = rel.drop(index="ALL DIMENSIONS")["alpha_ordinal"].idxmin()
    out += [f"The least reliable dimension is **{worst}** (α = {rel.loc[worst, 'alpha_ordinal']:.3f}). "
            "When one dimension lags the others by a wide margin the fix is usually the rubric anchors, not the raters.", ""]
    skewed = rel.drop(index="ALL DIMENSIONS")
    skewed = skewed[skewed["modal_score_share"] > 0.70]
    if len(skewed):
        names = ", ".join(f"**{d}** ({row['modal_score_share']:.0%} of scores are one value)" for d, row in skewed.iterrows())
        out += [f"Prevalence caveat: {names}. When most items share the same score, α is deflated by low variance even "
                "when raters agree on nearly every item — read the exact-agreement share in the rater profiles alongside α "
                "before concluding the dimension is unreliable.", ""]

    out += ["## 2. Which dimensions are hard to agree on?", "",
            "Mean pairwise quadratic-weighted κ between raters, per dimension (Landis & Koch bands: .41–.60 moderate, .61–.80 substantial).", "",
            _md(dims.assign(band=dims["mean_pairwise_qw_kappa"].map(interpret_kappa))), ""]

    out += ["## 3. Rater flags", "",
            f"Thresholds: κw vs consensus ≥ {thresholds.min_kappa_vs_consensus}, |bias| ≤ {thresholds.max_abs_bias}, "
            f"straight-lining ≤ {thresholds.max_straightline_share:.0%}, score SD ≥ {thresholds.min_score_sd}, "
            f"fast-task share ≤ {thresholds.max_fast_share:.0%}, gold within ±1 ≥ {thresholds.min_gold_accuracy:.0%}.", "",
            _md(flags[["n_tasks", "kappa_vs_consensus", "mean_bias", "n_flags", "flags"]]), ""]
    flagged = flags[flags["n_flags"] > 0]
    if len(flagged):
        out += ["**Recommended actions**", ""]
        for rater, row in flagged.iterrows():
            action = []
            for f in row["flags"]:
                if "drift" in f:
                    action.append("drift detected — schedule a mid-project recalibration and check for fatigue (task volume, time of day)")
                elif "harsh" in f or "lenient" in f:
                    action.append("recalibrate on the 20-item reference set; review anchors for the dimensions driving the bias")
                elif "straight" in f or "variation" in f:
                    action.append("spot-check 10 tasks; if confirmed, pause and retrain on independent dimension scoring")
                elif "rushing" in f:
                    action.append("compare their fast tasks against consensus; if accuracy holds, no action — speed alone is not a fault")
                elif "low agreement" in f:
                    action.append("pair-review 10 disagreements with a lead to find whether it is rubric reading or attention")
                elif "gold" in f:
                    action.append("gold accuracy below bar — hold production tasks until a calibration pass is cleared")
            out.append(f"- **{rater}**: " + "; ".join(dict.fromkeys(action)))
        out.append("")
    else:
        out += ["No rater exceeds any threshold.", ""]

    out += ["## 4. Rater profiles", "", "### Agreement with leave-one-out consensus", "", _md(rvc), "",
            "### Score distributions", "", _md(dist), ""]
    if len(dur):
        out += ["### Time per task", "", f"Fast cut-off: {dur.attrs.get('fast_cut_sec', float('nan')):.0f} s "
                f"(pool {thresholds.fast_duration_quantile:.0%} quantile).", "", _md(dur, "{:.0f}").replace("| nan |", "| |"), ""]
    if len(gold):
        out += ["### Gold-item accuracy", "", _md(gold), ""]
    if len(drift):
        out += ["### Drift: mean deviation from consensus by week", "",
                "Negative = harsher than consensus. A rater whose row trends away from zero is drifting.", "", _md(drift), ""]

    if pairwise is not None and len(pairwise):
        pw = q.pairwise_checks(pairwise, thresholds)
        lo, hi = thresholds.position_bias_band
        out += ["## 5. Pairwise judgements", "",
                f"First-position preference should sit within {lo:.0%}–{hi:.0%}; tie share should stay below {thresholds.max_tie_share:.0%}.", "",
                _md(pw), ""]
        for rater, row in pw.iterrows():
            if row["position_bias_flag"]:
                out.append(f"- **{rater}** prefers the first-shown response {row['first_position_pref_share']:.0%} of the time — position bias. "
                           "Re-brief on reading both responses fully before scoring; re-check after 50 judgements.")
            if row["tie_flag"]:
                out.append(f"- **{rater}** records ties on {row['tie_share']:.0%} of pairs — decision avoidance. Require a reason code for every tie.")
        out.append("")

    out += ["---", "", "_Generated by `llm_eval.report` — metrics defined in `docs/metrics.md`._"]
    return "\n".join(out)
