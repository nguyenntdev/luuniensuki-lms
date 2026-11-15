"""P11 reliability-math tests on clearly-labeled SYNTHETIC TOY matrices.

These matrices never enter results; they verify the math only. Expected values are
hand-computed or cross-checked against the reference `krippendorff` package when available
(skipped gracefully if the package is absent).
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from research_v3.methods.p11.reliability import (
    EmptyMatrixError,
    ReliabilityError,
    cohen_kappa_unweighted,
    cohen_kappa_weighted,
    compute_reliability,
    cronbach_alpha,
    icc_a1,
    krippendorff_alpha,
    load_ratings_csv,
    smoke_toy,
)

# ---------------------------------------------------------------------------
# hand-computed weighted kappa (exact)
# ---------------------------------------------------------------------------


def test_weighted_kappa_hand_computed_systematic():
    """A=[3,3,2,3,2,3], B=[2,2,1,2,1,3]: kappa_w = 0.4 exactly (hand computation)."""
    a = [3, 3, 2, 3, 2, 3]
    b = [2, 2, 1, 2, 1, 3]
    assert math.isclose(cohen_kappa_weighted(a, b), 0.4, rel_tol=1e-12)


def test_unweighted_kappa_hand_computed_systematic():
    a = [3, 3, 2, 3, 2, 3]
    b = [2, 2, 1, 2, 1, 3]
    # p_o = 1/6; p_e = 10/36; kappa = (1/6 - 10/36)/(1 - 10/36) = -0.1538...
    k = cohen_kappa_unweighted(a, b)
    assert math.isclose(k, -0.15384615384615385, rel_tol=1e-9)


def test_perfect_agreement_all_statistics_one():
    m = [[2, 2], [3, 3], [1, 1], [0, 0], [3, 3], [2, 2]]
    assert cohen_kappa_weighted([r[0] for r in m], [r[1] for r in m]) == 1.0
    assert cohen_kappa_unweighted([r[0] for r in m], [r[1] for r in m]) == 1.0
    assert krippendorff_alpha(m, level_of_measurement="nominal") == 1.0
    assert krippendorff_alpha(m, level_of_measurement="ordinal") == 1.0
    assert icc_a1(m) == pytest.approx(1.0)


def test_constant_ratings_kappa_is_one_not_nan():
    """All-identical ratings: observed and expected weighted disagreement both 0."""
    m = [[2, 2], [2, 2], [2, 2], [2, 2]]
    assert cohen_kappa_weighted([r[0] for r in m], [r[1] for r in m]) == 1.0
    assert krippendorff_alpha(m, level_of_measurement="nominal") == 1.0


# ---------------------------------------------------------------------------
# Krippendorff alpha known values
# ---------------------------------------------------------------------------


def test_alpha_krippendorff_textbook_example():
    """Two raters, nominal, data unit1={1,1}, unit2={2,1}, unit3={3,3}, unit4={3,3},
    unit5={3,2}: alpha = 0.4194. Value cross-verified against the reference
    `krippendorff` package (and used in the optional cross-check test below)."""
    data = [[1, 1], [2, 1], [3, 3], [3, 3], [3, 2]]
    assert krippendorff_alpha(data, level_of_measurement="nominal") == pytest.approx(0.4193548387, abs=1e-8)


def test_alpha_systematic_disagreement_is_low():
    """One-level systematic offset: nominal alpha must be low (rater effect), not spuriously high."""
    m = [[3, 2], [3, 2], [2, 1], [3, 2], [2, 1], [3, 3]]
    a = krippendorff_alpha(m, level_of_measurement="nominal")
    assert a is not None and a < 0.2


def test_alpha_handles_missing_data():
    m = [[2, 2, None], [3, None, 3], [None, 1, 1], [0, 0, None], [3, 3, 3], [1, None, 2]]
    for lvl in ("nominal", "ordinal", "interval"):
        assert krippendorff_alpha(m, level_of_measurement=lvl) is not None


def test_alpha_monotone_in_disagreement():
    """More disagreement -> lower interval alpha, same marginals."""
    good = [[1, 1], [2, 2], [3, 3], [0, 0], [3, 2], [1, 1], [2, 2], [0, 0]]
    worse = [[1, 3], [2, 0], [3, 1], [0, 2], [3, 0], [1, 3], [2, 0], [0, 3]]
    a_good = krippendorff_alpha(good, level_of_measurement="interval")
    a_worse = krippendorff_alpha(worse, level_of_measurement="interval")
    assert a_good > a_worse


def test_alpha_nominal_two_raters_reference_verified():
    """Reference-verified value (krippendorff package): 0.4242424... for this matrix.

    Note: for two raters with complete data, nominal alpha is closely related to but not
    identical to Scott's pi (alpha's coincidence normalization differs); we pin the
    reference value rather than a hand-waved pi equivalence.
    """
    data = [
        [1, 1], [1, 1], [1, 1], [1, 2], [1, 2], [2, 2], [2, 2], [2, 2], [2, 1], [1, 1],
    ]
    assert krippendorff_alpha(data, level_of_measurement="nominal") == pytest.approx(0.4242424242, abs=1e-9)


# ---------------------------------------------------------------------------
# cross-check vs reference package (optional dependency)
# ---------------------------------------------------------------------------


def test_alpha_matches_reference_package_if_available():
    krippendorff = pytest.importorskip("krippendorff")
    rng = np.random.default_rng(11)
    for t in range(5):
        n, r = int(rng.integers(6, 14)), int(rng.integers(2, 6))
        m = rng.integers(0, 4, size=(n, r)).astype(float)
        m[rng.random(m.shape) < 0.25] = np.nan
        data = [[None if np.isnan(x) else int(x) for x in row] for row in m]
        ref_data = np.array([[np.nan if v is None else v for v in row] for row in data]).T
        for lvl in ("nominal", "ordinal", "interval"):
            ref = krippendorff.alpha(reliability_data=ref_data, level_of_measurement=lvl)
            mine = krippendorff_alpha(data, level_of_measurement=lvl)
            assert (ref is None) == (mine is None)
            if ref is not None:
                assert mine == pytest.approx(float(ref), abs=1e-9)


# ---------------------------------------------------------------------------
# ICC + Cronbach
# ---------------------------------------------------------------------------


def test_icc_hand_computed_two_raters():
    """ICC(A,1) for the systematic toy = 2/3 / 1.5 = 0.4444 (hand-derived from MS equations)."""
    m = [[3, 2], [3, 2], [2, 1], [3, 2], [2, 1], [3, 3]]
    assert icc_a1(m) == pytest.approx(0.4444444444, abs=1e-6)


def test_icc_needs_two_complete_units():
    with pytest.raises(EmptyMatrixError):
        icc_a1([[1, 2], [None, 2]])


def test_cronbach_alpha_hand_computed():
    """3 respondents x 3 items, hand-computed: item vars (ddof=1) = [4/3, 1, 1],
    total var = 28/3 -> alpha = (3/2)(1 - (10/3)/(28/3)) = (3/2)(18/28) = 0.9643."""
    items = [
        [2, 2, 1],
        [2, 3, 2],
        [4, 4, 3],
    ]
    assert cronbach_alpha(items) == pytest.approx(0.9642857143, abs=1e-9)


def test_cronbach_is_not_inter_rater():
    """A single rater scoring 4 criteria (columns) yields internal consistency only."""
    one_rater = [[1, 2, 0, 3], [2, 2, 1, 2], [3, 3, 2, 3], [0, 1, 0, 1]]
    val = cronbach_alpha(one_rater)
    assert val is None or -1.0 <= val <= 1.0  # computable but must never be labeled inter-rater


# ---------------------------------------------------------------------------
# fail-closed behavior
# ---------------------------------------------------------------------------


def test_empty_matrix_raises_never_returns_number():
    with pytest.raises(EmptyMatrixError):
        krippendorff_alpha([[None, None], [None, None]])
    with pytest.raises(EmptyMatrixError):
        cohen_kappa_weighted([1, None], [None, 2])
    with pytest.raises(EmptyMatrixError):
        krippendorff_alpha([[1, None], [2, None]])


def test_single_rater_rejected():
    with pytest.raises(ReliabilityError):
        krippendorff_alpha([[1], [2], [3]])


def test_out_of_range_rejected():
    with pytest.raises(ReliabilityError):
        cohen_kappa_weighted([4], [0], n_levels=4)


def test_compute_reliability_flags_toy_provenance():
    m = [[1, 1], [2, 2], [3, 3]]
    real = compute_reliability(m, source="real_batch", is_synthetic_toy=False)
    toy = compute_reliability(m, source="toy", is_synthetic_toy=True)
    assert "REAL" in real.provenance_note
    assert "SYNTHETIC" in toy.provenance_note
    d = toy.to_dict()
    assert d["is_synthetic_toy"] is True


# ---------------------------------------------------------------------------
# CSV loader contract (NA/ABSTAIN excluded, never imputed)
# ---------------------------------------------------------------------------


def test_load_ratings_csv_maps_na_and_abstain_to_missing(tmp_path):
    csv_path = tmp_path / "ratings.csv"
    csv_path.write_text(
        "unit_id,rater_A,rater_B\n"
        "u1,2,2\n"
        "u2,ABSTAIN,1\n"
        "u3,NOT_APPLICABLE,3\n"
        "u4,0,\n",
        encoding="utf-8",
    )
    ids, rows = load_ratings_csv(str(csv_path))
    assert ids == ["u1", "u2", "u3", "u4"]
    assert rows == [[2.0, 2.0], [None, 1.0], [None, 3.0], [0.0, None]]


def test_load_ratings_csv_rejects_out_of_range(tmp_path):
    csv_path = tmp_path / "bad.csv"
    csv_path.write_text("unit_id,rater_A,rater_B\nu1,7,2\n", encoding="utf-8")
    with pytest.raises(ReliabilityError, match="outside 0-3"):
        load_ratings_csv(str(csv_path))


# ---------------------------------------------------------------------------
# toy smoke run is labeled and deterministic
# ---------------------------------------------------------------------------


def test_smoke_toy_deterministic_and_labeled():
    a = smoke_toy()
    b = smoke_toy()
    assert a == b
    assert "SYNTHETIC" in a["warning"]
    for key in ("perfect_agreement", "systematic_disagreement", "sparse_missing"):
        assert a[key]["is_synthetic_toy"] is True
    assert a["perfect_agreement"]["kappa_weighted"] == 1.0
    assert a["systematic_disagreement"]["alpha_nominal"] < 0.2
