import json
import pathlib
import pytest

np = pytest.importorskip("numpy")
scipy = pytest.importorskip("scipy")

from research.tools.statistical_meta_analysis import (
    bootstrap_ci,
    bootstrap_paired_diff_ci,
    benjamini_hochberg,
    clopper_pearson_interval,
    compute_mcnemar,
    compute_wilcoxon,
    compute_cohens_d,
    compute_cliffs_delta,
    holm_bonferroni,
    run_meta_analysis,
    summarize_metric,
    wilson_score_interval,
    _sanitize_for_json,
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


# --------------------------------------------------------------------------- #
# Zero-error proportion intervals (LN-01 degenerate bootstrap regression)
# --------------------------------------------------------------------------- #
def test_zero_error_proportion_ci_not_degenerate():
    zero_errors = np.zeros(120, dtype=float)
    summary = summarize_metric(zero_errors, is_proportion=True, b=500)

    # Naive bootstrap collapses to [0, 0]; that must not be the reported CI.
    assert summary["bootstrap_ci_95"] == [0.0, 0.0]
    assert summary["ci_method"] == "wilson_score"
    assert summary["ci_95"] != [0.0, 0.0]
    assert summary["ci_lower"] == 0.0
    assert summary["ci_upper"] > 0.0
    assert summary["wilson_ci_95"] != [0.0, 0.0]
    assert summary["clopper_pearson_ci_95"] != [0.0, 0.0]
    assert 0.0 < summary["wilson_ci_95"][1] < 0.1
    assert 0.0 < summary["clopper_pearson_ci_95"][1] < 0.1


def test_wilson_and_clopper_pearson_zero_success_bounds():
    # 0/120 Wilson upper ~3.1%, CP upper ~3.0%
    w_lo, w_hi = wilson_score_interval(0, 120)
    cp_lo, cp_hi = clopper_pearson_interval(0, 120)
    assert w_lo == 0.0 and 0.02 < w_hi < 0.05
    assert cp_lo == 0.0 and 0.02 < cp_hi < 0.05
    # 120/120 mirrored
    w_lo2, w_hi2 = wilson_score_interval(120, 120)
    cp_lo2, cp_hi2 = clopper_pearson_interval(120, 120)
    assert w_hi2 == 1.0 and 0.95 < w_lo2 < 1.0
    assert cp_hi2 == 1.0 and 0.95 < cp_lo2 < 1.0
    # Zero samples are safe
    assert wilson_score_interval(0, 0) == (0.0, 0.0)
    assert clopper_pearson_interval(0, 0) == (0.0, 0.0)


def test_summarize_metric_continuous_keeps_bootstrap():
    rng = np.random.default_rng(7)
    data = rng.normal(loc=5.0, scale=1.0, size=200)
    summary = summarize_metric(data, is_proportion=False, b=500, rng=rng)
    assert summary["ci_method"] == "bootstrap_percentile"
    assert summary["ci_lower"] < summary["point"] < summary["ci_upper"]
    assert "wilson_ci_95" not in summary
    assert "clopper_pearson_ci_95" not in summary


def test_sanitize_for_json_removes_non_finite():
    payload = {
        "ok": 1.5,
        "inf": float("inf"),
        "neg_inf": float("-inf"),
        "nan": float("nan"),
        "nested": [float("inf"), {"x": float("nan")}],
    }
    cleaned = _sanitize_for_json(payload)
    assert cleaned["ok"] == 1.5
    assert cleaned["inf"] is None
    assert cleaned["neg_inf"] is None
    assert cleaned["nan"] is None
    assert cleaned["nested"][0] is None
    assert cleaned["nested"][1]["x"] is None
    # Must serialize strictly
    text = json.dumps(cleaned, allow_nan=False)
    assert "Infinity" not in text and "NaN" not in text


def test_summary_json_is_strict():
    summary_path = ARTIFACTS_DIR / "statistical_summary.json"
    raw = summary_path.read_text(encoding="utf-8")
    assert "Infinity" not in raw
    assert "NaN" not in raw
    parsed = json.loads(raw)
    # Allow null for undefined quantities but no non-finite floats.
    def walk(node):
        if isinstance(node, float):
            assert node == node  # not NaN
            assert node not in (float("inf"), float("-inf"))
        elif isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(parsed)


def test_generated_proportion_metrics_have_wilson_and_cp():
    summary = json.loads((ARTIFACTS_DIR / "statistical_summary.json").read_text(encoding="utf-8"))
    for sid, sdata in summary["studies"].items():
        pm = sdata["conditions"]["I1"]["primary_metric"]
        if pm.get("ci_method") == "wilson_score":
            assert "wilson_ci_95" in pm and "clopper_pearson_ci_95" in pm
            assert pm["wilson_ci_95"] != [0.0, 0.0] or pm["point"] > 0.0
    # LN-01 I1 zero-error regression: Wilson upper must be > 0.
    ln01_i1 = summary["studies"]["LN-01"]["conditions"]["I1"]["primary_metric"]
    assert ln01_i1["point"] == 0.0
    assert ln01_i1["ci_method"] == "wilson_score"
    assert ln01_i1["wilson_ci_95"][1] > 0.0
    assert ln01_i1["clopper_pearson_ci_95"][1] > 0.0


# --------------------------------------------------------------------------- #
# Multiple-testing correction
# --------------------------------------------------------------------------- #
def test_holm_bonferroni_known_example():
    raw = [0.01, 0.04, 0.03, 0.005]
    adj = holm_bonferroni(raw)
    # Sorted: .005, .01, .03, .04 -> *4, *3, *2, *1 with monotone cummax
    assert adj == [0.03, 0.06, 0.06, 0.02]


def test_benjamini_hochberg_known_example():
    raw = [0.01, 0.04, 0.03, 0.005]
    adj = benjamini_hochberg(raw)
    # BH adjusted p-values are monotone non-decreasing in ranked order.
    order = sorted(range(4), key=lambda i: raw[i])
    ranked = [adj[i] for i in order]
    assert ranked == sorted(ranked)


def test_multiple_testing_adjusted_ge_raw_and_monotonic():
    pvals = [1e-9, 0.001, 0.02, 0.049, 0.2, 0.7, 0.95, 0.999]
    holm = holm_bonferroni(pvals)
    bh = benjamini_hochberg(pvals)
    assert all(h + 1e-12 >= r for h, r in zip(holm, pvals))
    assert all(b + 1e-12 >= r for b, r in zip(bh, pvals))
    assert all(0.0 <= x <= 1.0 for x in holm + bh)


def test_summary_includes_corrected_pvalues_and_family():
    summary = json.loads((ARTIFACTS_DIR / "statistical_summary.json").read_text(encoding="utf-8"))
    mt = summary["metadata"]["multiple_testing_correction"]
    assert set(mt["methods"]) == {"holm_bonferroni", "benjamini_hochberg"}
    assert mt["primary_family"]["n_tests"] >= 40
    assert mt["primary_family"]["holm_monotonic_adjusted_ge_raw"] is True
    assert mt["primary_family"]["bh_monotonic_adjusted_ge_raw"] is True

    for sid, sdata in summary["studies"].items():
        for key, comp in sdata["comparisons"].items():
            pm = comp["primary_metric"]
            assert pm["p_value_raw"] is not None
            assert pm["p_value_holm"] is not None
            assert pm["p_value_bh"] is not None
            assert pm["p_value_holm"] + 1e-15 >= pm["p_value_raw"]
            assert pm["p_value_bh"] + 1e-15 >= pm["p_value_raw"]


# --------------------------------------------------------------------------- #
# Sensitivity analysis
# --------------------------------------------------------------------------- #
def test_sensitivity_analysis_present_and_stable():
    summary = json.loads((ARTIFACTS_DIR / "statistical_summary.json").read_text(encoding="utf-8"))
    sens = summary["sensitivity_analysis"]
    assert "primary_i1_vs_b0_abs_cliffs_delta" in sens
    assert "holdout_accuracy_improvement" in sens

    primary = sens["primary_i1_vs_b0_abs_cliffs_delta"]
    assert primary["n_studies"] == 10
    assert len(primary["drop_one"]) == 10
    assert "conclusions_stable_all_leave_one_out_large" in primary
    assert primary["max_influence_study"] in primary["drop_one"]

    holdout = sens["holdout_accuracy_improvement"]
    assert len(holdout["drop_one"]) == 10
    assert holdout["conclusions_stable_positive_improvement"] is True
