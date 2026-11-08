"""Automated unit and integration tests for Study LN-01 (Spiral Curriculum Progression).

Pedagogical Invariants:
- INV-LN-01-01: Progression edge must increase cognitive complexity (reject_no_progression).
- INV-LN-01-02: Prerequisite edges must form a DAG without cycles (reject_cycle).
- INV-LN-01-03: Every node grade must have a verified curriculum anchor (reject_missing_anchor).
- INV-LN-01-04: Non-decreasing grade sequence must be maintained along edges (reject_grade_order).
- INV-LN-01-05: Nominal spiral progression allows valid sequence across grades 10-11-12.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from research.integrations.ln01 import run_policy
from research.spiral.curriculum_crosswalk import (
    STANDARD_GDDP_ANCHORS,
    check_anchor_coverage,
)
from research.spiral.progression_graph import (
    detect_prerequisite_cycles,
    evaluate_spiral_progression_ablation,
    evaluate_spiral_progression_baseline,
    evaluate_spiral_progression_intervention,
)


FIXTURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "LUU_NIEN_SPEC_10_STUDIES_MODULAR_FULL_2026"
    / "LUU_NIEN_SPEC_MODULAR_10_STUDIES_2026"
    / "04_FIXTURES"
    / "CONCRETE"
    / "LN-01_concrete.jsonl"
)


def _sample_nominal_input():
    return {
        "case_id": "TEST-NOMINAL",
        "content": {"id": "ngo-mon", "label": "Ngọ Môn", "type": "imperial-site"},
        "curriculum_anchor": {
            "grade10": "GDĐP-HUE-10-ART",
            "grade11": "GDĐP-HUE-11-HISTORY",
            "grade12": "GDĐP-HUE-12-HERITAGE",
        },
        "nodes": [
            {"cognitive_level": 1, "content_id": "ngo-mon", "grade": 10, "objective": "motif_observation"},
            {"cognitive_level": 2, "content_id": "ngo-mon", "grade": 11, "objective": "historical_context"},
            {"cognitive_level": 3, "content_id": "ngo-mon", "grade": 12, "objective": "heritage_evaluation"},
        ],
        "prerequisites": [[0, 1], [1, 2]],
    }


def test_nominal_intervention():
    """INV-LN-01-05: Nominal scenario satisfies all constraints and is accepted."""
    inp = _sample_nominal_input()
    res = evaluate_spiral_progression_intervention(inp)
    assert res.decision == "accept"
    assert res.progression_valid is True
    assert "nominal_progression_valid" in res.reason_codes
    assert res.observables["prerequisite_cycle_count"] == 0
    assert res.observables["unmapped_outcome_rate"] == 0.0


def test_prerequisite_cycle_intervention():
    """INV-LN-01-02: Prerequisite cycle is rejected by DFS cycle detection."""
    inp = _sample_nominal_input()
    inp["prerequisites"] = [[0, 1], [1, 2], [2, 0]]
    res = evaluate_spiral_progression_intervention(inp)
    assert res.decision == "reject_cycle"
    assert res.progression_valid is False
    assert "prerequisite_cycle_detected" in res.reason_codes
    assert res.observables["prerequisite_cycle_count"] >= 1
    assert "cycle_detected_in_prerequisites" in res.observables["violations"]


def test_grade_reversed_intervention():
    """INV-LN-01-04: Reversed grade progression is detected and rejected."""
    inp = _sample_nominal_input()
    inp["nodes"][1]["grade"] = 9
    res = evaluate_spiral_progression_intervention(inp)
    assert res.decision == "reject_grade_order"
    assert res.progression_valid is False
    assert "grade_order_reversed" in res.reason_codes
    assert any("Grade" in v for v in res.observables["violations"])


def test_missing_curriculum_intervention():
    """INV-LN-01-03: Missing regulatory curriculum anchor is rejected."""
    inp = _sample_nominal_input()
    del inp["curriculum_anchor"]["grade11"]
    res = evaluate_spiral_progression_intervention(inp)
    assert res.decision == "reject_missing_anchor"
    assert res.progression_valid is False
    assert "missing_curriculum_anchor" in res.reason_codes
    assert res.observables["unmapped_outcome_rate"] > 0.0
    assert 11 in res.observables["missing_anchor_grades"]


def test_repeat_shallow_intervention():
    """INV-LN-01-01: Repeating shallow cognitive level without progression is rejected."""
    inp = _sample_nominal_input()
    inp["nodes"][1]["cognitive_level"] = 1
    inp["nodes"][1]["objective"] = "motif_observation"
    res = evaluate_spiral_progression_intervention(inp)
    assert res.decision == "reject_no_progression"
    assert res.progression_valid is False
    assert "no_cognitive_progression" in res.reason_codes
    assert any("cognitive progression" in v.lower() for v in res.observables["violations"])


def test_baseline_always_allows():
    """Baseline policy ignores cognitive level, cycle, and anchor checks."""
    cycle_inp = _sample_nominal_input()
    cycle_inp["prerequisites"] = [[0, 1], [1, 2], [2, 0]]
    res = evaluate_spiral_progression_baseline(cycle_inp)
    assert res.decision == "accept"
    assert res.progression_valid is True
    assert res.policy_version == "1.0-baseline"


def test_ablation_modes():
    """Ablation mode bypasses configured checks."""
    # 1. Skip cycle check: when cycle check is skipped, subsequent pipeline checks execute
    # If all structural checks on the cyclic edge are bypassed, it accepts
    cycle_inp = _sample_nominal_input()
    cycle_inp["prerequisites"] = [[0, 1], [1, 2], [2, 0]]
    res_cycle_skip = evaluate_spiral_progression_ablation(
        cycle_inp,
        config={"skip_cycle_check": True, "skip_grade_order_check": True, "skip_cognitive_check": True},
    )
    assert res_cycle_skip.decision == "accept"
    assert res_cycle_skip.progression_valid is True

    # When only cycle check is skipped, it proceeds to catch grade reversal on [2, 0]
    res_cycle_partial = evaluate_spiral_progression_ablation(cycle_inp, config={"skip_cycle_check": True})
    assert res_cycle_partial.decision == "reject_grade_order"

    # 2. Skip cognitive check (via ablation_type or disable_depth_gate)
    shallow_inp = _sample_nominal_input()
    shallow_inp["nodes"][1]["cognitive_level"] = 1
    res_cog = evaluate_spiral_progression_ablation(shallow_inp, config={"ablation_type": "no_cognitive_check"})
    assert res_cog.decision == "accept"
    assert res_cog.progression_valid is True

    res_cog_alias = evaluate_spiral_progression_ablation(shallow_inp, config={"disable_depth_gate": True})
    assert res_cog_alias.decision == "accept"
    assert res_cog_alias.progression_valid is True

    # 3. Skip anchor check (via skip_anchor_check, ablation_type, or disable_crosswalk)
    missing_anchor_inp = _sample_nominal_input()
    del missing_anchor_inp["curriculum_anchor"]["grade11"]
    res_anchor = evaluate_spiral_progression_ablation(missing_anchor_inp, config={"skip_anchor_check": True})
    assert res_anchor.decision == "accept"
    assert res_anchor.progression_valid is True

    res_anchor_alias = evaluate_spiral_progression_ablation(missing_anchor_inp, config={"disable_crosswalk": True})
    assert res_anchor_alias.decision == "accept"
    assert res_anchor_alias.progression_valid is True

    # 4. Skip grade order check
    reversed_grade_inp = _sample_nominal_input()
    reversed_grade_inp["nodes"][1]["grade"] = 9
    # When grade order check is skipped, it proceeds to check anchor for grade 9 (which is missing)
    res_grade_partial = evaluate_spiral_progression_ablation(reversed_grade_inp, config={"skip_grade_order_check": True})
    assert res_grade_partial.decision == "reject_missing_anchor"

    # When both grade order and anchor checks are bypassed, it accepts
    res_grade_skip = evaluate_spiral_progression_ablation(
        reversed_grade_inp,
        config={"skip_grade_order_check": True, "skip_anchor_check": True},
    )
    assert res_grade_skip.decision == "accept"
    assert res_grade_skip.progression_valid is True


def test_run_policy_adapter_contract():
    """Adapter returns standardized dictionary matching runner contract."""
    inp = _sample_nominal_input()
    out = run_policy(inp, mode="intervention", config={})
    assert isinstance(out, dict)
    assert out["decision"] == "accept"
    assert out["policy_version"] == "2.0-intervention"
    assert out["progression_valid"] is True
    assert isinstance(out["reason_codes"], list)
    assert "prerequisite_cycle_count" in out
    assert "unmapped_outcome_rate" in out


def test_cycle_detector_unit():
    """Unit test for DFS cycle detection algorithm."""
    # Graph with cycle: 0 -> 1 -> 2 -> 0
    cycles = detect_prerequisite_cycles(3, [[0, 1], [1, 2], [2, 0]])
    assert len(cycles) >= 1

    # Graph without cycle: 0 -> 1 -> 2
    no_cycles = detect_prerequisite_cycles(3, [[0, 1], [1, 2]])
    assert len(no_cycles) == 0


def test_crosswalk_standard_anchors():
    """Check standard GDĐP anchors catalog coverage."""
    assert "GDĐP-HUE-10-ART" in STANDARD_GDDP_ANCHORS
    assert "GDĐP-HUE-11-HISTORY" in STANDARD_GDDP_ANCHORS
    assert "GDĐP-HUE-12-HERITAGE" in STANDARD_GDDP_ANCHORS

    # Anchor coverage helper
    nodes = [{"grade": 10}, {"grade": 11}]
    ok, missing, rate = check_anchor_coverage(nodes, {"grade10": "A", "grade11": "B"})
    assert ok is True
    assert missing == []
    assert rate == 0.0

    ok2, missing2, rate2 = check_anchor_coverage(nodes, {"grade10": "A"})
    assert ok2 is False
    assert missing2 == [11]
    assert rate2 == 0.5


def test_topological_baseline_b1():
    """Verify B1 topological baseline rejects cycles but admits non-cognitive leaps."""
    # 1. Cyclic graph is rejected by B1
    cycle_inp = _sample_nominal_input()
    cycle_inp["prerequisites"] = [[0, 1], [1, 2], [2, 0]]
    res_cycle = run_policy(cycle_inp, mode="baseline", config={"baseline_type": "topological"})
    assert res_cycle["decision"] == "reject_cycle"
    assert res_cycle["progression_valid"] is False

    # 2. Shallow repetition (Bloom level stagnant) is allowed by B1
    shallow_inp = _sample_nominal_input()
    shallow_inp["nodes"][1]["cognitive_level"] = 1
    res_shallow = run_policy(shallow_inp, mode="baseline", config={"baseline_type": "topological"})
    assert res_shallow["decision"] == "accept"
    assert res_shallow["progression_valid"] is True


def test_independent_holdout_120_cases():
    """Verify full intervention I1 against the independent 120-case holdout dataset."""
    holdout_path = Path(__file__).resolve().parents[2] / "research" / "fixtures" / "holdout" / "LN-01_holdout.jsonl"
    assert holdout_path.exists(), f"Holdout fixture missing: {holdout_path}"

    total = 0
    matches = 0
    with open(holdout_path, "r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            total += 1
            res = run_policy(row["input"], mode="intervention", config={})
            expected = row["oracle"]["expected_decision"]
            assert res["decision"] == expected, (
                f"Mismatch on {row['case_id']} ({row['fault_id']}): got {res['decision']}, expected {expected}"
            )
            matches += 1

    assert total == 120
    assert matches == 120


def test_concrete_fixture_conformance_all_720():
    """Verify that intervention matches 100% of the 720 concrete scenarios."""
    assert FIXTURE_PATH.exists(), f"Mandatory fixture missing (fail-closed): {FIXTURE_PATH}"

    matches = 0
    total = 0
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            total += 1
            res = run_policy(row["input"], mode="intervention", config={})
            expected = row["oracle"]["expected_decision"]
            assert res["decision"] == expected, (
                f"Mismatch on {row['case_id']} ({row['fault_id']}): got {res['decision']}, expected {expected}"
            )
            assert "progression_valid" in res
            assert isinstance(res["progression_valid"], bool)
            matches += 1

    assert total == 720
    assert matches == 720


def test_five_study_conditions_configs_experiments():
    """Verify all 5 conditions specified in configs/experiments.json:
    - B0: baseline
    - I1: intervention
    - A1: ablation no_cognitive_check (disable_depth_gate)
    - A2: ablation no_anchor_check (disable_crosswalk)
    - A3: ablation no_cycle_check (allow_cycles)
    """
    # 1. B0: Baseline
    res_b0 = run_policy(_sample_nominal_input(), mode="baseline", config={})
    assert res_b0["decision"] == "accept"
    assert res_b0["policy_version"] == "1.0-baseline"

    # 2. I1: Intervention
    res_i1 = run_policy(_sample_nominal_input(), mode="intervention", config={})
    assert res_i1["decision"] == "accept"
    assert res_i1["policy_version"] == "2.0-intervention"

    # 3. A1: no_cognitive_check / disable_depth_gate
    shallow = _sample_nominal_input()
    shallow["nodes"][1]["cognitive_level"] = 1
    res_a1_spec = run_policy(shallow, mode="ablation", config={"ablation_type": "no_cognitive_check"})
    assert res_a1_spec["decision"] == "accept"
    res_a1_alias = run_policy(shallow, mode="ablation", config={"disable_depth_gate": True})
    assert res_a1_alias["decision"] == "accept"

    # 4. A2: no_anchor_check / disable_crosswalk
    missing_anchor = _sample_nominal_input()
    del missing_anchor["curriculum_anchor"]["grade11"]
    res_a2_spec = run_policy(missing_anchor, mode="ablation", config={"ablation_type": "no_anchor_check"})
    assert res_a2_spec["decision"] == "accept"
    res_a2_alias = run_policy(missing_anchor, mode="ablation", config={"disable_crosswalk": True})
    assert res_a2_alias["decision"] == "accept"

    # 5. A3: no_cycle_check / allow_cycles
    # Under A3, cycle check is skipped; when remaining structural checks are also bypassed, cyclic graph is accepted
    cycle_graph = _sample_nominal_input()
    cycle_graph["prerequisites"] = [[0, 1], [1, 2], [2, 0]]
    res_a3_spec = run_policy(
        cycle_graph,
        mode="ablation",
        config={"ablation_type": "no_cycle_check", "skip_grade_order_check": True, "skip_cognitive_check": True},
    )
    assert res_a3_spec["decision"] == "accept"
    res_a3_alias = run_policy(
        cycle_graph,
        mode="ablation",
        config={"allow_cycles": True, "skip_grade_order_check": True, "skip_cognitive_check": True},
    )
    assert res_a3_alias["decision"] == "accept"

