import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from llm_eval import quality as q  # noqa: E402
from llm_eval.rubric import load_rubric, validate_rubric_dict  # noqa: E402

SCORES = {"instruction_following": 4, "factual_accuracy": 2, "reasoning_quality": 3,
          "completeness": 3, "safety": 5, "clarity": 5}


def test_rubrics_load_and_validate():
    for f in os.listdir(os.path.join(ROOT, "rubrics")):
        if f.endswith(".yaml"):
            rub = load_rubric(os.path.join(ROOT, "rubrics", f))
            assert rub.dimensions and all(set(d.anchors) == set(range(rub.scale_min, rub.scale_max + 1)) for d in rub.dimensions)


def test_weighted_score_and_gate():
    rub = load_rubric(os.path.join(ROOT, "rubrics", "general_assistant_v1.yaml"))
    assert rub.validate_scores(SCORES) == []
    assert abs(rub.weighted_score(SCORES) - 31 / 9) < 1e-9       # (2*4 + 2*2 + 1.5*3 + 1.5*3 + 1*5 + 1*5) / 9
    gated = dict(SCORES, safety=1)
    assert rub.weighted_score(gated) == 2.0            # safety gate caps the total
    assert rub.validate_scores({"instruction_following": 6}) != []


def test_validate_rubric_dict_catches_missing_anchor():
    bad = {"name": "x", "version": "1", "scale": {"min": 1, "max": 3},
           "dimensions": [{"key": "a", "name": "A", "anchors": {1: "x", 2: "y"}}]}
    assert any("anchors" in p for p in validate_rubric_dict(bad))


def _pool(seed=0):
    """5 raters, 3 dimensions with independent true scores; C is harsh by 1, B is fast."""
    rng = np.random.default_rng(seed)
    rows = []
    for t in range(150):
        true = {d: rng.integers(1, 6) for d in ["d1", "d2", "d3"]}
        for r in ["A", "B", "C", "D", "E"]:
            bias = -1 if r == "C" else 0
            for d in ["d1", "d2", "d3"]:
                noise = int(rng.integers(-1, 2)) if rng.random() < 0.3 else 0
                s = int(np.clip(true[d] + bias + noise, 1, 5))
                rows.append({"task_id": f"T{t}", "rater_id": r, "dimension": d, "score": s,
                             "timestamp": f"2025-10-{1 + t // 6:02d}", "duration_sec": 30 if r == "B" else 120})
    return pd.DataFrame(rows)


def test_quality_flags_planted_problems():
    df = _pool()
    flags = q.flag_raters(df)
    assert any("harsh" in f for f in flags.loc["C", "flags"])
    assert any("rushing" in f for f in flags.loc["B", "flags"])
    assert flags.loc["A", "n_flags"] == 0


def test_pairwise_position_bias_detected():
    rng = np.random.default_rng(1)
    rows = []
    for i in range(200):
        first = rng.choice(["A", "B"])
        rows.append({"task_id": i, "rater_id": "fair", "preference": int(rng.choice([-2, -1, 1, 2])), "first_position": first, "reason_code": "X"})
        rows.append({"task_id": i, "rater_id": "biased", "preference": -2 if first == "A" else 2, "first_position": first, "reason_code": "X"})
    pw = q.pairwise_checks(pd.DataFrame(rows))
    assert bool(pw.loc["biased", "position_bias_flag"]) is True
    assert bool(pw.loc["fair", "position_bias_flag"]) is False


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok ", name)
