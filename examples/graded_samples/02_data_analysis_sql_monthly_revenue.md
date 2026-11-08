# Graded sample 02 — Data analysis / SQL

Rubric: [`data_analysis_response_v1`](../../rubrics/data_analysis_response_v1.yaml) · Grader: Ha Kieu Anh

## Task

**User prompt**

> I have two tables in PostgreSQL: `orders(order_id, customer_id, order_ts, status)` and `order_items(order_id, product_id, quantity, unit_price)`. Write a query that returns, for each month of 2025, the number of delivered orders and the revenue from those orders. Please explain what the query does.

**Model response (graded verbatim)**

> ```sql
> SELECT
>     DATE_TRUNC('month', o.order_ts)      AS month,
>     COUNT(o.order_id)                    AS delivered_orders,
>     SUM(oi.quantity * oi.unit_price)     AS revenue
> FROM orders o
> JOIN order_items oi ON oi.order_id = o.order_id
> WHERE o.status = 'delivered'
>   AND o.order_ts >= '2025-01-01'
> GROUP BY 1
> ORDER BY 1;
> ```
>
> **How it works:** the query joins each order to its line items so we can compute revenue as quantity × unit price. It keeps only delivered orders placed in 2025, groups them by month using `DATE_TRUNC`, counts the orders in each month, and sums the revenue. The result is one row per month with the order count and revenue.

## Before reading the response: what a complete answer needs

- Revenue needs the join to `order_items`; the order **count** must not be inflated by that join → `COUNT(DISTINCT o.order_id)`.
- "2025" means a closed interval: `>= '2025-01-01' AND < '2026-01-01'`.
- `status = 'delivered'` — fine if the status values are known; a careful answer notes the assumption about casing/values.
- Months with zero delivered orders will be missing (acceptable unless the user asks for a full calendar; worth a sentence).
- The explanation should describe what the query *actually* does, including how the join affects the count.

## Verification

Run on a sample schema with 3 delivered orders in January 2025 totalling 7 line items:

| Query | delivered_orders (Jan) |
|---|---|
| As written | **7** |
| `COUNT(DISTINCT o.order_id)` | 3 |

The order count is inflated by the average number of lines per order. On a real e-commerce dataset (~1.7 lines/order) every monthly order count would be ~70% too high, while revenue would be correct — a mismatch that would surface the first time someone computes average order value from this output.

## Scores

| Dimension (weight) | Score | Evidence |
|---|---|---|
| Technical correctness (3.0) · GATE | **2** | Runs, and revenue is right, but `COUNT(o.order_id)` after a one-to-many join counts **lines, not orders** — a subtle, consequential error (verified above). Secondary: no upper bound on the date, so any 2026 rows would be included. Not a 1: the query is not materially wrong on its main metric (revenue), and the fix is one keyword. |
| Analytical soundness (2.0) | **4** | No conclusions are drawn, so little to assess; the response does not over-claim. Loses a point for not stating the assumption that `status = 'delivered'` is the only delivered state. |
| Requirement coverage (1.5) | **3** | Returns month, order count and revenue for delivered orders as asked, with an explanation. The year filter is open-ended rather than "2025". |
| Explanation (1.5) | **2** | The explanation says the query "counts the orders in each month" — it describes what the author *intended*, not what the code does. An explanation that misdescribes the code is worse than none, because it reassures the reader. |
| Presentation (1.0) | **4** | Clean formatting, aligned aliases, sensible column names. Could state that revenue is in the table's currency unit and that `month` is a timestamp, not a label. |

**Weighted score: 2.83 / 5 (normalised 0.46)** — no gate triggered (correctness is 2, the gate fires at 1).

## Overall verdict

A query that "looks right" and returns a wrong number for one of the two things asked. The rubric weights correctness at 3.0 for exactly this case: formatting and explanation cannot rescue a result the user cannot trust. The explanation compounds the problem by asserting the wrong behaviour as fact.

Corrected query, for the record:

```sql
SELECT DATE_TRUNC('month', o.order_ts)                       AS month,
       COUNT(DISTINCT o.order_id)                            AS delivered_orders,
       SUM(oi.quantity * oi.unit_price)                      AS revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.status = 'delivered'
  AND o.order_ts >= DATE '2025-01-01' AND o.order_ts < DATE '2026-01-01'
GROUP BY 1
ORDER BY 1;
```

## Calibration note

The disagreement I expect: **correctness 2 vs 1.** The rubric anchors put "returns a materially wrong result" at 1 and "wrong in a subtle but consequential way (e.g. join fan-out inflating a sum)" at 2 — this is the textbook example of the 2 anchor, and the revenue column is right, so I stay at 2. If the prompt had asked only for the order count, the same bug would be a 1 and the gate would cap the response at 2.0.

Graders who did not run the query would likely give correctness 4 or 5. That is the point of the rubric's instruction to trace or run code before scoring: this bug is invisible to reading.
