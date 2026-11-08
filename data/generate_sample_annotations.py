"""
Synthetic annotation dataset with planted quality problems, for demonstrating
and testing the QC checks.

    python data/generate_sample_annotations.py   -> data/sample/*.csv

Pool: 300 tasks, 6 rubric dimensions (general_assistant_v1), 3 raters per task
drawn from 8 raters. Planted issues:
    R03  harsh  (scores ~0.7 below consensus)
    R05  straight-liner (same score on every dimension ~60% of the time)
    R06  rushes (very short durations) and is noisy
    R07  drifts harsher in the last two weeks
Also 30 gold tasks with reference scores, and a pairwise set where R02 shows
position bias.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

SEED = 11
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample")
DIMS = ["instruction_following", "factual_accuracy", "reasoning_quality", "completeness", "safety", "clarity"]
RATERS = [f"R0{i}" for i in range(1, 9)]
RATER_SD = {r: 0.5 for r in RATERS}
RATER_SD["R06"] = 1.1
RATER_BIAS = {r: 0.0 for r in RATERS}
RATER_BIAS["R03"] = -0.7
RATER_BIAS["R04"] = 0.25


def main():
    rng = np.random.default_rng(SEED)
    os.makedirs(OUT, exist_ok=True)
    n_tasks = 300
    start = datetime(2025, 10, 1, 9, 0)

    # latent "true" quality per task and dimension
    task_quality = rng.normal(3.4, 0.8, size=n_tasks)
    dim_offset = {d: rng.normal(0, 0.25) for d in DIMS}
    true = {(t, d): np.clip(task_quality[t] + dim_offset[d] + rng.normal(0, 0.45), 1, 5) for t in range(n_tasks) for d in DIMS}
    # safety is mostly 5 with occasional problems
    for t in range(n_tasks):
        true[(t, "safety")] = 5.0 if rng.random() < 0.85 else rng.choice([2.0, 3.0, 4.0])

    tasks = pd.DataFrame({
        "task_id": [f"T{1000 + t}" for t in range(n_tasks)],
        "prompt_category": rng.choice(["coding", "writing", "advice", "factual_qa", "analysis", "roleplay"], size=n_tasks),
        "is_gold": [t < 30 for t in range(n_tasks)],
    })
    gold_scores = {(t, d): int(round(true[(t, d)])) for t in range(30) for d in DIMS}

    rows = []
    for t in range(n_tasks):
        raters = rng.choice(RATERS, size=3, replace=False)
        ts = start + timedelta(days=int(t / n_tasks * 28), minutes=int(rng.integers(0, 480)))
        for r in raters:
            drift = -0.9 if (r == "R07" and ts >= start + timedelta(days=14)) else 0.0
            straight = r == "R05" and rng.random() < 0.6
            base_all = int(np.clip(round(task_quality[t] + rng.normal(0, 0.4)), 1, 5))
            duration = max(25, rng.lognormal(np.log(45 if r == "R06" else 150), 0.35))
            for d in DIMS:
                if straight:
                    score = base_all
                else:
                    score = int(np.clip(round(true[(t, d)] + RATER_BIAS[r] + drift + rng.normal(0, RATER_SD[r])), 1, 5))
                rows.append({"task_id": f"T{1000 + t}", "rater_id": r, "dimension": d, "score": score,
                             "timestamp": ts.strftime("%Y-%m-%d %H:%M"), "duration_sec": int(duration),
                             "gold_score": gold_scores.get((t, d)) if t < 30 else None})
    ann = pd.DataFrame(rows)

    # pairwise set: 240 comparisons, 4 raters. Presentation order is counter-balanced
    # within each true-preference sign, as a well-designed study would do, so position
    # effects in the data come only from raters (R02 is given a first-position bias).
    n_pairs = 240
    sign = rng.choice([-1, 0, 1], size=n_pairs, p=[0.45, 0.10, 0.45])
    magnitude = rng.choice([1, 2, 3], size=n_pairs, p=[0.45, 0.35, 0.20])
    true_prefs = sign * magnitude
    first_pos = np.empty(n_pairs, dtype=object)
    for sgn in (-1, 0, 1):
        idx = np.where(sign == sgn)[0]
        balanced = np.array(["A", "B"] * (len(idx) // 2 + 1))[:len(idx)]
        first_pos[idx] = rng.permutation(balanced)
    pw_rows = []
    for i in range(n_pairs):
        true_pref, first = int(true_prefs[i]), str(first_pos[i])
        for r in rng.choice(RATERS[:4], size=2, replace=False):
            pref = int(np.clip(round(true_pref + rng.normal(0, 0.7)), -3, 3))
            if r == "R02" and rng.random() < 0.35:                       # position bias toward whatever is first
                pref = -max(abs(pref), 1) if first == "A" else max(abs(pref), 1)
            if r == "R04" and rng.random() < 0.25:                       # avoids decisions: too many ties
                pref = 0
            pw_rows.append({"task_id": f"P{2000 + i}", "rater_id": r, "preference": pref, "first_position": first,
                            "reason_code": rng.choice(["CORRECTNESS", "INSTRUCTION", "COMPLETENESS", "CLARITY", "REASONING", "TONE"])})
    pw = pd.DataFrame(pw_rows)

    tasks.to_csv(os.path.join(OUT, "tasks.csv"), index=False)
    ann.to_csv(os.path.join(OUT, "annotations.csv"), index=False)
    pw.to_csv(os.path.join(OUT, "pairwise_judgements.csv"), index=False)
    print(f"tasks {len(tasks)}, annotations {len(ann)}, pairwise {len(pw)} -> {os.path.relpath(OUT)}")


if __name__ == "__main__":
    main()
