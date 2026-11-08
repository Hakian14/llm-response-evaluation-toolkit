# Rubrics

| File | Use | Scale | Gate |
|---|---|---|---|
| [`general_assistant_v1.yaml`](general_assistant_v1.yaml) | Single-response grading for chat / Q&A / writing / advice | 1–5 on 6 weighted dimensions | `safety` ≤ 1 caps the total at 2.0 |
| [`data_analysis_response_v1.yaml`](data_analysis_response_v1.yaml) | Single-response grading for SQL, data analysis and statistics prompts | 1–5 on 5 weighted dimensions | `correctness` ≤ 1 caps the total at 2.0 |
| [`pairwise_preference_v1.yaml`](pairwise_preference_v1.yaml) | A-vs-B preference judgements with strength and reason code | −3…+3 | — |

## Rubric format

```yaml
name: ...
version: "1.0"
task_type: ...
scale: {min: 1, max: 5}
instructions: |
  How to apply the rubric.
dimensions:
  - key: snake_case_id
    name: Human name
    weight: 2.0              # relative weight in the overall score
    gate: {threshold: 1, cap: 2.0}   # optional: if score <= threshold, overall is capped
    description: |
      What this dimension measures and what it does NOT measure.
    anchors:                 # one anchor per scale level - every level must be present
      1: ...
      5: ...
metadata: {}                 # free-form: author, calibration notes, reason codes, ...
```

Rules the loader enforces (`python -m llm_eval.cli validate-rubric <file>`):

- every scale level has an anchor on every dimension;
- dimension keys are unique; weights are positive;
- a gate declares its threshold.

## Design principles behind these rubrics

1. **Anchors describe observable evidence, not adjectives.** "Omits a required column" beats
   "somewhat incomplete".
2. **Dimensions are orthogonal.** Instruction following (did it do what was asked) is separated
   from completeness (did it include what an expert would add) and from accuracy (is it true).
   Overlapping dimensions are the main cause of low inter-rater agreement.
3. **The middle of the scale means something.** 3 = acceptable with real flaws. Rubrics whose 3
   means "fine" collapse into a 2-point scale in practice.
4. **Gates for disqualifying failures.** Weighted averages let a harmful or wrong response score
   3.8 because it was well formatted. A gate prevents that.
5. **Weights reflect what the response is for.** Correctness carries 3.0 in the data-analysis
   rubric because a wrong query is worse than an ugly one.

## Scoring in code

```python
from llm_eval.rubric import load_rubric

rub = load_rubric("rubrics/general_assistant_v1.yaml")
scores = {"instruction_following": 4, "factual_accuracy": 2, "reasoning_quality": 3,
          "completeness": 3, "safety": 5, "clarity": 5}
rub.validate_scores(scores)        # -> [] when valid
rub.weighted_score(scores)         # -> 3.44  (weighted mean, weights 2,2,1.5,1.5,1,1)
rub.normalized_score(scores)       # -> 0.61
print(rub.to_markdown())           # render the rubric for a briefing document
```
