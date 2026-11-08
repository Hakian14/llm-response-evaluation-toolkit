"""
Inter-annotator agreement metrics.

All functions accept plain Python / numpy / pandas inputs and return floats, so they
can be dropped into any annotation pipeline. Implementations follow the standard
definitions and are unit-tested against published worked examples (see tests/).

    percent_agreement(a, b)
    cohen_kappa(a, b, weights=None | "linear" | "quadratic")
    fleiss_kappa(count_matrix)
    krippendorff_alpha(data, level="nominal" | "ordinal" | "interval")
    agreement_matrix(wide_df, metric=...)        # pairwise raters -> DataFrame

Which one to use:
    * two raters, categorical          -> cohen_kappa
    * two raters, ordinal (1-5 scale)  -> cohen_kappa(weights="quadratic")
    * many raters, every item rated by the same number of raters -> fleiss_kappa
    * many raters, missing ratings, any scale -> krippendorff_alpha  (the general tool)
"""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np
import pandas as pd


# --------------------------------------------------------------------------- two raters

def percent_agreement(a: Sequence, b: Sequence) -> float:
    a, b = np.asarray(a), np.asarray(b)
    if len(a) != len(b):
        raise ValueError("a and b must have the same length")
    return float(np.mean(a == b))


def cohen_kappa(a: Sequence, b: Sequence, weights: str | None = None, categories: Sequence | None = None) -> float:
    """Cohen's kappa for two raters.

    weights: None (nominal), "linear" or "quadratic" (ordinal scales - categories
    must be numeric or given in order via `categories`).
    """
    a, b = np.asarray(a), np.asarray(b)
    if len(a) != len(b):
        raise ValueError("a and b must have the same length")
    cats = list(categories) if categories is not None else sorted(set(a) | set(b))
    idx = {c: i for i, c in enumerate(cats)}
    k = len(cats)
    observed = np.zeros((k, k))
    for x, y in zip(a, b):
        observed[idx[x], idx[y]] += 1
    n = observed.sum()
    if n == 0:
        return float("nan")
    observed /= n
    expected = np.outer(observed.sum(axis=1), observed.sum(axis=0))
    if weights is None:
        w = 1.0 - np.eye(k)
    else:
        i, j = np.meshgrid(np.arange(k), np.arange(k), indexing="ij")
        if weights == "linear":
            w = np.abs(i - j) / (k - 1)
        elif weights == "quadratic":
            w = ((i - j) / (k - 1)) ** 2
        else:
            raise ValueError("weights must be None, 'linear' or 'quadratic'")
    po_dis = (w * observed).sum()
    pe_dis = (w * expected).sum()
    if pe_dis == 0:
        return 1.0 if po_dis == 0 else float("nan")
    return float(1.0 - po_dis / pe_dis)


# --------------------------------------------------------------------------- many raters

def fleiss_kappa(counts) -> float:
    """Fleiss' kappa.

    counts: items x categories matrix where counts[i, c] = number of raters who put
    item i in category c. Every row must sum to the same number of raters.
    """
    M = np.asarray(counts, dtype=float)
    n_raters = M.sum(axis=1)
    if not np.allclose(n_raters, n_raters[0]):
        raise ValueError("every item must be rated by the same number of raters (use krippendorff_alpha otherwise)")
    n = n_raters[0]
    N = M.shape[0]
    p_cat = M.sum(axis=0) / (N * n)
    P_i = ((M ** 2).sum(axis=1) - n) / (n * (n - 1))
    P_bar = P_i.mean()
    P_e = (p_cat ** 2).sum()
    if P_e == 1:
        return 1.0
    return float((P_bar - P_e) / (1 - P_e))


def krippendorff_alpha(data, level: str = "nominal", value_domain: Sequence | None = None) -> float:
    """Krippendorff's alpha.

    data: raters x items array (or DataFrame) with NaN / None for missing ratings.
    level: "nominal", "ordinal" or "interval". Ordinal and interval require numeric values
           (ordinal uses the rank distances implied by the observed value domain).

    Implemented through the coincidence matrix, following Krippendorff (2011),
    "Computing Krippendorff's Alpha-Reliability".
    """
    arr = np.asarray(pd.DataFrame(data).to_numpy(dtype=object))
    # keep only items with at least two ratings
    cols = []
    for j in range(arr.shape[1]):
        vals = [v for v in arr[:, j] if not _is_missing(v)]
        if len(vals) >= 2:
            cols.append(vals)
    if not cols:
        return float("nan")
    domain = list(value_domain) if value_domain is not None else sorted({v for col in cols for v in col})
    idx = {v: i for i, v in enumerate(domain)}
    k = len(domain)

    # coincidence matrix: each ordered pair of values within an item adds 1/(m_u - 1)
    o = np.zeros((k, k))
    for vals in cols:
        m_u = len(vals)
        for i_a, a in enumerate(vals):
            for i_b, b in enumerate(vals):
                if i_a != i_b:
                    o[idx[a], idx[b]] += 1.0 / (m_u - 1)
    n_c = o.sum(axis=1)
    n = n_c.sum()
    if n <= 1:
        return float("nan")

    # distance metric
    delta = np.zeros((k, k))
    for c in range(k):
        for g in range(k):
            if level == "nominal":
                delta[c, g] = 0.0 if c == g else 1.0
            elif level == "interval":
                delta[c, g] = (float(domain[c]) - float(domain[g])) ** 2
            elif level == "ordinal":
                lo, hi = min(c, g), max(c, g)
                delta[c, g] = (n_c[lo:hi + 1].sum() - (n_c[lo] + n_c[hi]) / 2.0) ** 2 if c != g else 0.0
            else:
                raise ValueError("level must be 'nominal', 'ordinal' or 'interval'")

    d_o = (o * delta).sum()
    d_e = (np.outer(n_c, n_c) * delta).sum() / (n - 1)
    if d_e == 0:
        return 1.0 if d_o == 0 else float("nan")
    return float(1.0 - d_o / d_e)


def _is_missing(v) -> bool:
    if v is None:
        return True
    try:
        return bool(np.isnan(v))
    except (TypeError, ValueError):
        return False


# --------------------------------------------------------------------------- convenience

def agreement_matrix(wide: pd.DataFrame, metric: str = "quadratic_kappa") -> pd.DataFrame:
    """Pairwise rater agreement from a wide table (rows = items, columns = raters).

    metric: "percent", "kappa", "linear_kappa", "quadratic_kappa".
    Pairs are computed on items both raters scored.
    """
    raters = list(wide.columns)
    out = pd.DataFrame(np.nan, index=raters, columns=raters)
    for i, r1 in enumerate(raters):
        out.loc[r1, r1] = 1.0
        for r2 in raters[i + 1:]:
            both = wide[[r1, r2]].dropna()
            if len(both) == 0:
                continue
            a, b = both[r1].to_numpy(), both[r2].to_numpy()
            if metric == "percent":
                v = percent_agreement(a, b)
            elif metric == "kappa":
                v = cohen_kappa(a, b)
            elif metric == "linear_kappa":
                v = cohen_kappa(a, b, weights="linear")
            elif metric == "quadratic_kappa":
                v = cohen_kappa(a, b, weights="quadratic")
            else:
                raise ValueError(metric)
            out.loc[r1, r2] = out.loc[r2, r1] = v
    return out


def interpret_kappa(value: float) -> str:
    """Landis & Koch (1977) bands - a convention, not a law. Use with judgement."""
    if np.isnan(value):
        return "undefined"
    if value < 0:
        return "worse than chance"
    bands = [(0.20, "slight"), (0.40, "fair"), (0.60, "moderate"), (0.80, "substantial"), (1.01, "almost perfect")]
    for upper, label in bands:
        if value < upper:
            return label
    return "almost perfect"


def interpret_alpha(value: float) -> str:
    """Krippendorff's own guidance: >= .800 reliable, .667-.800 tentative, below .667 unreliable."""
    if np.isnan(value):
        return "undefined"
    if value >= 0.800:
        return "reliable (>= .800)"
    if value >= 0.667:
        return "tentative (.667-.800) - draw only cautious conclusions"
    return "unreliable (< .667) - revise rubric or recalibrate raters"
