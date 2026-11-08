# Agreement metrics — which one, when, and how to read it

Every metric in `llm_eval.agreement` answers the same question — *do the raters agree more
than chance would predict?* — under different assumptions. Picking the wrong one is the most
common reporting mistake in annotation projects.

## Decision table

| Situation | Metric | Function |
|---|---|---|
| 2 raters, categories with no order (reason codes, pass/fail) | Cohen's κ | `cohen_kappa(a, b)` |
| 2 raters, ordered scale (1–5) where being off by one is better than off by four | Weighted κ (quadratic) | `cohen_kappa(a, b, weights="quadratic")` |
| ≥ 3 raters, **every** item rated by the **same number** of raters, nominal | Fleiss' κ | `fleiss_kappa(counts)` |
| ≥ 2 raters, **missing** ratings, any scale (nominal / ordinal / interval) | Krippendorff's α | `krippendorff_alpha(data, level=...)` |
| "How often do they just agree?" (for stakeholders) | Percent agreement — *always alongside a chance-corrected metric* | `percent_agreement(a, b)` |

**Default for rubric-based LLM grading:** Krippendorff's α with `level="ordinal"`. It handles
the realities of annotation pools (raters rotate, items get 2–4 ratings, scales are ordinal) and
has one well-known interpretation guide.

## Interpretation

| Krippendorff's α (Krippendorff's own guidance) | Cohen's / Fleiss' κ (Landis & Koch, 1977) |
|---|---|
| ≥ .800 — rely on the data | .81–1.00 almost perfect |
| .667–.800 — tentative conclusions only | .61–.80 substantial |
| < .667 — do not use for conclusions | .41–.60 moderate |
| | .21–.40 fair · ≤ .20 slight |

These bands are conventions, not laws. Two things change what "good" means:

1. **Scale granularity.** A 1–5 scale will never reach the agreement of a pass/fail decision.
   Weighted κ / ordinal α partly compensate; percent-within-±1 is the stakeholder-friendly companion.
2. **Prevalence (the κ paradox).** When 85% of items get the same score (e.g. *safety* is almost
   always 5), chance agreement is already high, so κ and α are deflated even if raters agree on
   nearly every item. Report the score distribution next to the metric, and look at agreement on
   the minority class specifically before concluding the dimension is "unreliable".

## Percent agreement is not enough

Two raters assigning 5 to 90% of items agree 81% of the time by chance alone. Percent agreement
of 85% in that setting is κ ≈ 0.2. Always report a chance-corrected metric; show percent agreement
(or within-±1) as the plain-language companion.

## Rater-level diagnostics (what `llm_eval.quality` computes)

| Diagnostic | What it detects | Default threshold |
|---|---|---|
| κw vs **leave-one-out consensus** | A rater who disagrees with everyone else (compared with the median of the *other* raters, so the rater is not scored against themselves) | ≥ 0.55 |
| Mean bias vs consensus | Systematic harshness / leniency | \|bias\| ≤ 0.40 |
| Straight-lining share | Same score on every dimension of a task — not grading dimensions independently | ≤ 35% of tasks |
| Score SD | A rater who never uses the scale | ≥ 0.60 |
| Fast-task share | Time per task below the pool's 10th percentile | ≤ 30% |
| Gold accuracy (within ±1) | Disagreement with reference-scored items | ≥ 70% |
| Drift | Deviation from consensus moving between first and last period | change ≤ 0.40 |
| First-position preference (pairwise) | Position bias | 42–58% |
| Tie share (pairwise) | Decision avoidance | ≤ 15% |

Thresholds live in `quality.Thresholds` and should be tuned to the project: a 3-point scale, or a
pool with 5 raters per item, moves every number.

## Dimension-level diagnostics

Mean pairwise κw **per rubric dimension** separates two very different problems:

- *One rater* is low on every dimension → a rater problem (training, attention).
- *Every rater* is low on one dimension → a rubric problem (ambiguous anchors, overlapping
  dimensions). Rewrite the anchors; retraining the raters will not fix it.

## Reporting checklist

A reliability statement for a delivered dataset should include:

1. α (ordinal) overall and per dimension, with n items and raters-per-item.
2. The score distribution per dimension (so the reader can judge the prevalence effect).
3. Percent within ±1 of consensus (plain-language companion).
4. The rater QC summary: how many raters were flagged, for what, and what was done.
5. Gold-item accuracy of the final pool.

## References

- Krippendorff, K. (2011). *Computing Krippendorff's Alpha-Reliability.* University of Pennsylvania.
- Landis, J. R. & Koch, G. G. (1977). The measurement of observer agreement for categorical data. *Biometrics*, 33(1).
- Fleiss, J. L. (1971). Measuring nominal scale agreement among many raters. *Psychological Bulletin*, 76(5).
- Cohen, J. (1968). Weighted kappa. *Psychological Bulletin*, 70(4).
