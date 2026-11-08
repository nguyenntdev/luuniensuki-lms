import json
import pathlib
import pytest
import numpy as np

from research.tools.statistical_meta_analysis import (
    bootstrap_ci,
    bootstrap_paired_diff_ci,
    compute_mcnemar,
    compute_wilcoxon,
    compute_cohens_d,
    compute_cliffs_delta,
    run_meta_analysis,
    ROOT,
    ARTIFACTS_DIR,
    FIXTURES_DIR,
    CONFIGS_FILE,
)


def test_bootstrap_ci_deterministic():
    rng = np.random.default_rng(42)
    # Constant data
    res_const = bootstrap_ci(np.ones(100), b=500, rng=rng)
    assert res_const["point"] == 1.0
    assert res_const["ci_lower"] == 1.0
    assert res_const["ci_upper"] == 1.0
    assert res_const["se"] == 0.0

    # Normal distribution
    data = rng.normal(loc=10.0, scale=2.0, size=500)
    res = bootstrap_ci(data, b=1000, rng=rng)
    assert 9.5 < res["point"] < 10.5
    assert res["ci_lower"] < res["point"] < res["ci_upper"]
    assert res["se"] > 0.0


def test_bootstrap_paired_diff_ci():
    rng = np.random.default_rng(42)
    x = np.array([1, 1, 1, 0, 0])
    y = np.array([0, 0, 0, 0, 0])
    res = bootstrap_paired_diff_ci(x, y, b=500, rng=rng)
    assert res["diff_point"] == 0.6
    assert 0.0 <= res["diff_ci_lower"] <= res["diff_ci_upper"] <= 1.0


def test_compute_mcnemar_exact_and_cc():
    # Identical
    res_zero = compute_mcnemar(np.array([1, 1, 0]), np.array([1, 1, 0]))
    assert res_zero["p_value"] == 1.0
    assert res_zero["statistic"] == 0.0

    # Small discordant (exact binomial)
    x = np.array([1] * 10 + [0] * 5)
    y = np.array([0] * 10 + [0] * 5)
    res_exact = compute_mcnemar(x, y)
    assert res_exact["method"] == "exact_binomial"
    assert res_exact["p_value"] < 0.01

    # Large discordant (continuity corrected)
    x_large = np.array([1] * 100 + [0] * 10)
    y_large = np.array([0] * 100 + [0] * 10)
    res_cc = compute_mcnemar(x_large, y_large)
    assert res_cc["method"] == "mcnemar_continuity_corrected"
    assert res_cc["p_value"] < 1e-10


def test_compute_wilcoxon():
    # Zero diff
    res_zero = compute_wilcoxon(np.zeros(50), np.zeros(50))
    assert res_zero["p_value"] == 1.0
    assert res_zero["statistic"] == 0.0

    # Significant diff
    x = np.zeros(100)
    y = np.ones(100) * 5.0
    res = compute_wilcoxon(x, y)
    assert res["p_value"] < 1e-10


def test_compute_cohens_d_and_cliffs_delta():
    # Varying differences
    x = np.array([1.0, 2.5, 3.0, 4.2, 5.0])
    y = np.array([0.0, 1.0, 2.0, 3.0, 4.0])

    d_paired, d_pooled, note = compute_cohens_d(x, y)
    assert d_paired is not None and d_paired > 0
    assert d_pooled is not None and d_pooled > 0
    assert note == "standard"

    delta, interp = compute_cliffs_delta(x, y)
    assert 0.0 < delta <= 1.0

    # Total separation zero variance
    x_zero = np.zeros(50)
    y_one = np.ones(50)
    d_p_zero, d_s_zero, note_sep = compute_cohens_d(x_zero, y_one)
    assert d_p_zero is None
    assert "deterministic_separation" in note_sep

    delta_sep, interp_sep = compute_cliffs_delta(x_zero, y_one)
    assert delta_sep == -1.0
    assert interp_sep == "Large"


def test_output_artifacts_exist_and_conform():
    summary_path = ARTIFACTS_DIR / "statistical_summary.json"
    csv_path = ARTIFACTS_DIR / "statistical_comparison_table.csv"

    assert summary_path.is_file(), "statistical_summary.json missing"
    assert csv_path.is_file(), "statistical_comparison_table.csv missing"

    with summary_path.open(encoding="utf-8") as f:
        summary = json.load(f)

    assert summary["metadata"]["total_studies"] == 10
    assert summary["metadata"]["total_conditions"] == 50
    assert summary["metadata"]["total_executions"] == 36000
    assert summary["meta_summary"]["all_10_studies_statistically_significant_i1_vs_b0"] is True

    # Check that all 10 studies are present
    for i in range(1, 11):
        sid = f"LN-{i:02d}"
        assert sid in summary["studies"]
        s_data = summary["studies"][sid]
        assert "I1_vs_B0" in s_data["comparisons"]
        p_comp = s_data["comparisons"]["I1_vs_B0"]["primary_metric"]
        assert p_comp["p_value"] < 1e-20
        assert p_comp["significance"] == "***"
