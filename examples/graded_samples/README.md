# Graded samples

Worked examples of the grading routine in [`docs/annotator_guidelines.md`](../../docs/annotator_guidelines.md),
applied to model responses with the rubrics in [`rubrics/`](../../rubrics/). Each file shows the full
record a reviewer would need: the task, the response(s) verbatim, what a complete answer had to
contain (written *before* reading the response), per-dimension scores with the evidence behind
each, the weighted score, a verdict, and a calibration note on where another grader might differ.

| Sample | Rubric | What it demonstrates |
|---|---|---|
| [01 · pandas performance Q&A](01_general_assistant_pandas_performance.md) | general_assistant_v1 | A fluent answer with embedded factual errors; verifying claims by running them; scoring dimensions independently |
| [02 · SQL monthly revenue](02_data_analysis_sql_monthly_revenue.md) | data_analysis_response_v1 | Join fan-out that reading cannot catch; correctness weighting and the gate; an explanation that misdescribes the code |
| [03 · workplace advice, A vs B](03_pairwise_workplace_advice.md) | pairwise_preference_v1 | Resisting length and formatting bias; substance-first decision; reason codes; position-bias self-check |

The prompts and model responses are written for these examples (they are not taken from any
platform or client). The flaws are the kinds that show up constantly in real grading: confident
wrong parameters, counts inflated by joins, advice that never answers the question.
