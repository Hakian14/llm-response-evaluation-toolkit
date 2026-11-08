# LLM Response Evaluation Toolkit

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](requirements.txt)
[![tests](https://github.com/Hakian14/llm-response-evaluation-toolkit/actions/workflows/tests.yml/badge.svg)](https://github.com/Hakian14/llm-response-evaluation-toolkit/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Rubrics, inter-annotator agreement metrics and annotation quality control for grading large-language-model
outputs — the measurement layer behind RLHF-style evaluation work.

Three things in one small package:

1. **Rubrics** ([`rubrics/`](rubrics/)) — versioned YAML rubrics with evidence-based anchors, weights and
   *gates* (a harmful or wrong response cannot average its way to a good score). General assistant,
   data-analysis/SQL, and pairwise preference.
2. **Agreement metrics** ([`llm_eval/agreement.py`](llm_eval/agreement.py)) — Cohen's κ (nominal, linear,
   quadratic), Fleiss' κ, **Krippendorff's α** (nominal / ordinal / interval, with missing data), percent
   agreement, pairwise agreement matrices. Pure numpy/pandas, unit-tested against published worked examples.
3. **Annotation QC** ([`llm_eval/quality.py`](llm_eval/quality.py), [`report.py`](llm_eval/report.py)) —
   per-rater diagnostics (agreement with leave-one-out consensus, bias, straight-lining, rushing, drift,
   gold accuracy, position bias, tie avoidance) rolled into a Markdown report with recommended actions.

> Written from my work as an AI trainer / evaluator. Everything here is generic practice — no
> client, platform or project material. The sample annotations are synthetic with planted problems.

## See it work

```bash
git clone https://github.com/Hakian14/llm-response-evaluation-toolkit.git
cd llm-response-evaluation-toolkit
pip install -r requirements.txt            # numpy, pandas, scipy, pyyaml

python data/generate_sample_annotations.py # 300 tasks x 3 raters x 6 dimensions, with planted issues
python -m llm_eval.cli report data/sample/annotations.csv \
       --pairwise data/sample/pairwise_judgements.csv --out examples/quality_report.md
```

The report ([`examples/quality_report.md`](examples/quality_report.md)) catches every planted problem:

| Rater | Planted problem | What the report says |
|---|---|---|
| R03 | scores ~0.7 below everyone else | `systematic harsh bias (-0.63)` |
| R04 | mild leniency | `systematic lenient bias (+0.42)` |
| R05 | same score on every dimension 60% of the time | `straight-lining (57% of tasks)` |
| R06 | rushes and is noisy | `rushing (74% of tasks below fast cut-off)`, `low agreement with consensus (κw=0.53)` |
| R07 | turns harsher in weeks 3–4 | `drift over time (+0.06 -> -0.67 vs consensus)` |
| R02 (pairwise) | prefers whichever response is shown first | `prefers the first-shown response 76% of the time — position bias` |
| R04 (pairwise) | avoids decisions | `records ties on 36% of pairs` |

…and separates *rater* problems from *rubric* problems: a dimension on which every rater disagrees
points at the anchors, not the people. It also flags the prevalence caveat — when 85% of items get the
same `safety` score, α is deflated even if raters agree on nearly every item.

## Using the library

```python
import pandas as pd
from llm_eval import krippendorff_alpha, cohen_kappa, load_rubric
from llm_eval.quality import flag_raters, to_wide

ann = pd.read_csv("data/sample/annotations.csv")

# Dataset reliability on one dimension, 1-5 treated as ordinal
wide = to_wide(ann, dimension="factual_accuracy")          # rows: tasks, cols: raters, NaN where unrated
krippendorff_alpha(wide.T.to_numpy(), level="ordinal")     # -> 0.54

# Two raters on an ordinal scale
cohen_kappa(wide["R01"].dropna(), wide["R02"].dropna(), weights="quadratic")   # align on shared items first

# Who needs recalibration?
flag_raters(ann)[["kappa_vs_consensus", "mean_bias", "flags"]]

# Score a response against a rubric (gate applied automatically)
rub = load_rubric("rubrics/general_assistant_v1.yaml")
rub.weighted_score({"instruction_following": 4, "factual_accuracy": 2, "reasoning_quality": 3,
                    "completeness": 3, "safety": 5, "clarity": 5})           # -> 3.44
```

CLI: `report`, `alpha`, `validate-rubric`, `rubric-md` — see `python -m llm_eval.cli -h`.

## Which agreement metric, when

| Situation | Metric |
|---|---|
| 2 raters, unordered categories | Cohen's κ |
| 2 raters, ordered scale | quadratic-weighted κ |
| ≥ 3 raters, same number of raters per item, nominal | Fleiss' κ |
| ≥ 2 raters, missing ratings, any scale — **the default for rubric grading** | Krippendorff's α (ordinal) |

Interpretation thresholds, the prevalence paradox, and a reporting checklist: [`docs/metrics.md`](docs/metrics.md).

## Annotator guidelines

[`docs/annotator_guidelines.md`](docs/annotator_guidelines.md) is the day-one briefing I use: the
grading routine, the seven biases that show up in QC (length, confidence, formatting, position,
sycophancy blindness, domain over-reach, fatigue drift) and how to counter each, calibration gates
(κw ≥ 0.70 on 20 reference items before production), and when to stop grading and fix the rubric instead.

## Repository layout

```
├── rubrics/                 # 3 versioned YAML rubrics + README on rubric design
├── llm_eval/
│   ├── agreement.py         # kappa family, Krippendorff's alpha, agreement matrices
│   ├── quality.py           # rater & dimension diagnostics, pairwise checks, flags
│   ├── report.py            # Markdown QC report
│   ├── rubric.py            # rubric loading, validation, weighted/gated scoring
│   └── cli.py
├── data/
│   ├── generate_sample_annotations.py
│   └── sample/              # annotations.csv, pairwise_judgements.csv, tasks.csv
├── docs/                    # metrics.md, annotator_guidelines.md
├── examples/                # generated quality report, rendered rubric
└── tests/                   # 11 tests incl. published worked examples
```

## Tests

```bash
python tests/test_agreement.py && python tests/test_rubric_and_quality.py   # or: python -m pytest
```

Agreement metrics are checked against scikit-learn (κ, weighted κ), the standard Fleiss' κ worked
example (κ = 0.210), a hand-derived Krippendorff's α example (nominal and interval), and closed-form
two-rater identities.

## About

Built by **Ha Kieu Anh** — AI trainer / evaluator (Outlier, Mercor, Micro1) with a B.Sc. in Statistics and
5+ years as a Data Analyst. [GitHub](https://github.com/Hakian14) · [LinkedIn](https://www.linkedin.com/in/kieu-anh-ha-6249a3172/) · hakieuanh662@gmail.com

License: [MIT](LICENSE)
