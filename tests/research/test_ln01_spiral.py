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

    # 2. Skip cognitive check
    shallow_inp = _sample_nominal_input()
    shallow_inp["nodes"][1]["cognitive_level"] = 1
    res_cog = evaluate_spiral_progression_ablation(shallow_inp, config={"ablation_type": "no_cognitive_check"})
    assert res_cog.decision == "accept"
    assert res_cog.progression_valid is True

    # 3. Skip anchor check
    missing_anchor_inp = _sample_nominal_input()
    del missing_anchor_inp["curriculum_anchor"]["grade11"]
    res_anchor = evaluate_spiral_progression_ablation(missing_anchor_inp, config={"skip_anchor_check": True})
    assert res_anchor.decision == "accept"
    assert res_anchor.progression_valid is True

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


def test_metamorphic_property_content_invariance():
    """Metamorphic test: changing content label/type does not change progression validity."""
    inp = _sample_nominal_input()
    res1 = run_policy(inp, mode="intervention", config={})

    inp_mutated = dict(inp)
    inp_mutated["content"] = {"id": "the-mieu", "label": "Thế Miếu", "type": "shrine"}
    res2 = run_policy(inp_mutated, mode="intervention", config={})

    assert res1["decision"] == res2["decision"]
    assert res1["progression_valid"] == res2["progression_valid"]


def test_concrete_fixture_conformance_all_720():
    """Verify that intervention matches 100% of the 720 concrete scenarios."""
    if not FIXTURE_PATH.exists():
        pytest.skip("Concrete fixtures not found")

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
