# Annotation quality report — sample pool, Oct 2025

**Pool:** 300 tasks · 8 raters · 6 dimensions · 3–3 raters per task · 5,400 scores

## 1. Is the dataset reliable? (Krippendorff's α)

α is computed per dimension over all raters, treating the 1–5 scale as ordinal (primary) and interval (reference). Krippendorff's guidance: ≥ .800 reliable, .667–.800 tentative, below .667 unreliable.

| dimension | alpha_ordinal | alpha_interval | modal_score_share | verdict |
|---|---|---|---|---|
| clarity | 0.475 | 0.487 | 0.342 | unreliable (< .667) - revise rubric or recalibrate raters |
| completeness | 0.448 | 0.456 | 0.398 | unreliable (< .667) - revise rubric or recalibrate raters |
| factual_accuracy | 0.539 | 0.532 | 0.358 | unreliable (< .667) - revise rubric or recalibrate raters |
| instruction_following | 0.549 | 0.554 | 0.309 | unreliable (< .667) - revise rubric or recalibrate raters |
| reasoning_quality | 0.540 | 0.554 | 0.343 | unreliable (< .667) - revise rubric or recalibrate raters |
| safety | 0.352 | 0.490 | 0.587 | unreliable (< .667) - revise rubric or recalibrate raters |
| ALL DIMENSIONS | 0.578 | 0.586 | 0.302 | unreliable (< .667) - revise rubric or recalibrate raters |

The least reliable dimension is **safety** (α = 0.352). When one dimension lags the others by a wide margin the fix is usually the rubric anchors, not the raters.

## 2. Which dimensions are hard to agree on?

Mean pairwise quadratic-weighted κ between raters, per dimension (Landis & Koch bands: .41–.60 moderate, .61–.80 substantial).

| dimension | mean_pairwise_qw_kappa | min_pairwise_qw_kappa | score_sd_across_raters | band |
|---|---|---|---|---|
| completeness | 0.47 | 0.18 | 0.46 | moderate |
| safety | 0.50 | -0.08 | 0.43 | moderate |
| clarity | 0.51 | 0.27 | 0.53 | moderate |
| factual_accuracy | 0.55 | 0.29 | 0.53 | moderate |
| reasoning_quality | 0.56 | 0.05 | 0.48 | moderate |
| instruction_following | 0.57 | 0.26 | 0.50 | moderate |

## 3. Rater flags

Thresholds: κw vs consensus ≥ 0.55, |bias| ≤ 0.4, straight-lining ≤ 35%, score SD ≥ 0.6, fast-task share ≤ 30%, gold within ±1 ≥ 70%.

| rater_id | n_tasks | kappa_vs_consensus | mean_bias | n_flags | flags |
|---|---|---|---|---|---|
| R06 | 119 | 0.53 | 0.13 | 2 | low agreement with consensus (κw=0.53), rushing (74% of tasks below fast cut-off) |
| R05 | 111 | 0.54 | -0.08 | 2 | low agreement with consensus (κw=0.54), straight-lining (57% of tasks) |
| R04 | 116 | 0.60 | 0.42 | 1 | systematic lenient bias (+0.42) |
| R03 | 105 | 0.60 | -0.63 | 1 | systematic harsh bias (-0.63) |
| R07 | 109 | 0.58 | -0.35 | 1 | drift over time (+0.06 -> -0.67 vs consensus) |
| R02 | 123 | 0.72 | 0.15 | 0 |  |
| R01 | 116 | 0.71 | 0.17 | 0 |  |
| R08 | 101 | 0.71 | 0.12 | 0 |  |

**Recommended actions**

- **R06**: pair-review 10 disagreements with a lead to find whether it is rubric reading or attention; compare their fast tasks against consensus; if accuracy holds, no action — speed alone is not a fault
- **R05**: pair-review 10 disagreements with a lead to find whether it is rubric reading or attention; spot-check 10 tasks; if confirmed, pause and retrain on independent dimension scoring
- **R04**: recalibrate on the 20-item reference set; review anchors for the dimensions driving the bias
- **R03**: recalibrate on the 20-item reference set; review anchors for the dimensions driving the bias
- **R07**: drift detected — schedule a mid-project recalibration and check for fatigue (task volume, time of day)

## 4. Rater profiles

### Agreement with leave-one-out consensus

| rater_id | n_scores | kappa_vs_consensus | mean_bias | mean_abs_dev | share_within_1 |
|---|---|---|---|---|---|
| R01 | 696 | 0.71 | 0.17 | 0.55 | 0.91 |
| R02 | 738 | 0.72 | 0.15 | 0.55 | 0.92 |
| R03 | 630 | 0.60 | -0.63 | 0.78 | 0.80 |
| R04 | 696 | 0.60 | 0.42 | 0.66 | 0.85 |
| R05 | 666 | 0.54 | -0.08 | 0.70 | 0.84 |
| R06 | 714 | 0.53 | 0.13 | 0.82 | 0.75 |
| R07 | 654 | 0.58 | -0.35 | 0.76 | 0.81 |
| R08 | 606 | 0.71 | 0.12 | 0.52 | 0.93 |

### Score distributions

| rater_id | n_tasks | mean_score | score_sd | straightline_share | share_1 | share_2 | share_3 | share_4 | share_5 |
|---|---|---|---|---|---|---|---|---|---|
| R01 | 116 | 3.69 | 1.06 | 0.00 | 0.03 | 0.10 | 0.28 | 0.32 | 0.27 |
| R02 | 123 | 3.70 | 1.05 | 0.02 | 0.02 | 0.11 | 0.27 | 0.33 | 0.27 |
| R03 | 105 | 3.11 | 1.12 | 0.00 | 0.09 | 0.20 | 0.34 | 0.27 | 0.11 |
| R04 | 116 | 3.92 | 1.00 | 0.01 | 0.02 | 0.07 | 0.23 | 0.35 | 0.34 |
| R05 | 111 | 3.52 | 1.05 | 0.57 | 0.03 | 0.15 | 0.30 | 0.33 | 0.20 |
| R06 | 119 | 3.67 | 1.24 | 0.00 | 0.07 | 0.12 | 0.22 | 0.26 | 0.33 |
| R07 | 109 | 3.33 | 1.18 | 0.01 | 0.07 | 0.18 | 0.28 | 0.28 | 0.19 |
| R08 | 101 | 3.65 | 1.06 | 0.01 | 0.02 | 0.12 | 0.31 | 0.29 | 0.26 |

### Time per task

Fast cut-off: 57 s (pool 10% quantile).

| rater_id | median_sec | p10_sec | fast_share |
|---|---|---|---|
| R01 | 148 | 102 | 0 |
| R02 | 147 | 103 | 0 |
| R03 | 146 | 99 | 0 |
| R04 | 150 | 101 | 0 |
| R05 | 143 | 94 | 0 |
| R06 | 46 | 32 | 1 |
| R07 | 148 | 80 | 0 |
| R08 | 152 | 97 | 0 |

### Gold-item accuracy

| rater_id | n_gold | exact_match | within_1 | gold_bias |
|---|---|---|---|---|
| R01 | 13 | 0.65 | 1.00 | -0.01 |
| R02 | 9 | 0.67 | 1.00 | -0.04 |
| R03 | 15 | 0.39 | 0.90 | -0.71 |
| R04 | 10 | 0.63 | 0.93 | 0.27 |
| R05 | 11 | 0.59 | 0.91 | -0.24 |
| R06 | 11 | 0.42 | 0.86 | 0.03 |
| R07 | 13 | 0.62 | 1.00 | -0.03 |
| R08 | 8 | 0.73 | 1.00 | -0.02 |

### Drift: mean deviation from consensus by week

Negative = harsher than consensus. A rater whose row trends away from zero is drifting.

| rater_id | 2025-09-29/2025-10-05 | 2025-10-06/2025-10-12 | 2025-10-13/2025-10-19 | 2025-10-20/2025-10-26 | 2025-10-27/2025-11-02 |
|---|---|---|---|---|---|
| R01 | 0.12 | 0.01 | 0.10 | 0.06 | 0.08 |
| R02 | 0.00 | -0.01 | 0.07 | 0.05 | 0.08 |
| R03 | -0.52 | -0.49 | -0.47 | -0.41 | -0.43 |
| R04 | 0.18 | 0.19 | 0.24 | 0.23 | 0.20 |
| R05 | -0.25 | -0.27 | -0.06 | -0.06 | -0.17 |
| R06 | 0.09 | -0.01 | 0.01 | 0.04 | 0.14 |
| R07 | 0.06 | 0.00 | -0.42 | -0.66 | -0.67 |
| R08 | -0.02 | -0.02 | 0.03 | 0.11 | 0.05 |

## 5. Pairwise judgements

First-position preference should sit within 42%–58%; tie share should stay below 15%.

| rater_id | n_judgements | tie_share | first_position_pref_share | mean_abs_strength | share_extreme | position_bias_flag | tie_flag |
|---|---|---|---|---|---|---|---|
| R01 | 125 | 0.13 | 0.50 | 1.71 | 0.28 | False | False |
| R02 | 113 | 0.12 | 0.76 | 1.58 | 0.20 | True | False |
| R03 | 124 | 0.13 | 0.49 | 1.69 | 0.27 | False | False |
| R04 | 118 | 0.36 | 0.49 | 1.10 | 0.14 | False | True |

- **R02** prefers the first-shown response 76% of the time — position bias. Re-brief on reading both responses fully before scoring; re-check after 50 judgements.
- **R04** records ties on 36% of pairs — decision avoidance. Require a reason code for every tie.

---

_Generated by `llm_eval.report` — metrics defined in `docs/metrics.md`._