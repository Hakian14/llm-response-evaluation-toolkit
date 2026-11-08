"""Agreement metrics checked against published worked examples and scikit-learn."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_eval.agreement import cohen_kappa, fleiss_kappa, krippendorff_alpha, percent_agreement  # noqa: E402


def test_cohen_kappa_matches_sklearn():
    from sklearn.metrics import cohen_kappa_score
    rng = np.random.default_rng(0)
    a = rng.integers(1, 6, 200)
    b = np.clip(a + rng.integers(-1, 2, 200), 1, 5)
    assert abs(cohen_kappa(a, b) - cohen_kappa_score(a, b)) < 1e-12
    assert abs(cohen_kappa(a, b, "linear") - cohen_kappa_score(a, b, weights="linear")) < 1e-12
    assert abs(cohen_kappa(a, b, "quadratic") - cohen_kappa_score(a, b, weights="quadratic")) < 1e-12


def test_cohen_kappa_perfect_and_chance():
    assert cohen_kappa([1, 2, 3, 1], [1, 2, 3, 1]) == 1.0
    assert percent_agreement([1, 2, 3], [1, 2, 0]) == 2 / 3


def test_fleiss_kappa_wikipedia_example():
    # 10 subjects, 14 raters, 5 categories -> kappa = 0.210
    counts = [[0, 0, 0, 0, 14], [0, 2, 6, 4, 2], [0, 0, 3, 5, 6], [0, 3, 9, 2, 0], [2, 2, 8, 1, 1],
              [7, 7, 0, 0, 0], [3, 2, 6, 3, 0], [2, 5, 3, 2, 2], [6, 5, 2, 1, 0], [0, 2, 2, 3, 7]]
    assert abs(fleiss_kappa(counts) - 0.210) < 0.001


def test_krippendorff_alpha_hand_computed_example():
    # 3 coders x 12 units, 2 units with a single rating (dropped). Hand computation:
    # coincidence matrix o11=3, o22=7, o33=6, o44=3, o55=2, o12=o21=1.5, o13=o31=0.5, o23=o32=1.5
    # n_c = (5, 10, 8, 3, 2), n = 28
    # nominal:  D_o = 7,  sum_{c!=k} n_c n_k = 582  -> alpha = 1 - 27*7/582   = 0.6753
    # interval: D_o = 10, sum n_c n_k (c-k)^2 = 1958 -> alpha = 1 - 27*10/1958 = 0.8621
    nan = np.nan
    data = [
        [1, 2, 3, 3, 2, 1, 4, 1, 2, nan, nan, nan],
        [1, 2, 3, 3, 2, 2, 4, 1, 2, 5, nan, 3],
        [nan, 3, 3, 3, 2, 3, 4, 2, 2, 5, 1, nan],
    ]
    assert abs(krippendorff_alpha(data, "nominal") - (1 - 27 * 7 / 582)) < 1e-9
    assert abs(krippendorff_alpha(data, "interval") - (1 - 27 * 10 / 1958)) < 1e-9
    ordinal = krippendorff_alpha(data, "ordinal")
    assert 0.75 < ordinal < 0.85


def test_krippendorff_two_raters_complete_equals_closed_form():
    # Two raters, no missing data, nominal level: alpha = 1 - D_o / D_e where
    # D_o = 1 - percent agreement and D_e = (n/(n-1)) * (1 - sum_c p_c^2) over the n pooled values.
    rng = np.random.default_rng(4)
    a = rng.integers(0, 3, 150)
    b = np.where(rng.random(150) < 0.7, a, rng.integers(0, 3, 150))
    alpha = krippendorff_alpha([a, b], "nominal")
    values = np.concatenate([a, b])
    n = len(values)
    p_c = np.array([(values == c).mean() for c in range(3)])
    d_o = 1 - percent_agreement(a, b)
    d_e = (n / (n - 1)) * (1 - (p_c ** 2).sum())
    assert abs(alpha - (1 - d_o / d_e)) < 1e-9
    assert 0.3 < alpha < 1.0


def test_krippendorff_handles_missing_and_perfect():
    data = [[1, 2, 3, np.nan], [1, 2, 3, 4], [1, 2, np.nan, 4]]
    assert abs(krippendorff_alpha(data, "nominal") - 1.0) < 1e-12


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok ", name)
