"""P07 selector unit contract tests: typed failures, tri-state affordances,
device/rights screens, determinism, oracle-free inference.

Mandatory counterexamples (user contract + spec section 5):
  1. raster WITH image but MISSING inscription -> reject_missing_affordance
  2. screen-reader learner, audio WITHOUT transcript -> reject (not select)
  3. low-bandwidth fallback WITH transcript -> accepted (positive control)
  4. rights violation (unknown/NC license) -> reject_rights_violation
  5. determinism: identical inputs -> identical decisions for any seed
"""
from __future__ import annotations

import pytest

from research_v3.methods.p07.affordances import (
    AFFORDANCE_VOCAB,
    DeviceConstraints,
    LearningObject,
    SchemaError,
    SelectionDecision,
    TaskRequirements,
)
from research_v3.methods.p07.selector import select, predict_case


def _obj(oid: str, modality: str = "2d_image", kb: int = 320, **aff) -> LearningObject:
    affordances = {k: None for k in AFFORDANCE_VOCAB}
    affordances.update(aff)
    return LearningObject(
        object_id=oid, modality=modality, kb=kb, affordances=affordances,
        license_status="CC0",
    )


def _task(*req: str, tid: str = "t1") -> TaskRequirements:
    return TaskRequirements(task_id=tid, task_type="test", required_affordances=tuple(req))


DEV = DeviceConstraints(network_kbps=3000)


# ---------------------------------------------------------------- tri-state

def test_not_applicable_is_distinct_from_false():
    o = _obj("o1", relief_depth=None, inscription_text=False)
    assert o.affords("relief_depth") is None
    assert o.affords("inscription_text") is False


def test_unknown_affordance_axis_raises():
    o = _obj("o1")
    with pytest.raises(SchemaError):
        o.affords("nonexistent_axis")


def test_bad_license_status_rejected_at_construction():
    with pytest.raises(SchemaError):
        LearningObject(object_id="o", modality="text", kb=1,
                       affordances={}, license_status="")


def test_invalid_decision_schema():
    with pytest.raises(SchemaError):
        SelectionDecision("select", None)
    with pytest.raises(SchemaError):
        SelectionDecision("bogus_decision", "x")
    with pytest.raises(SchemaError):
        SelectionDecision("reject_missing_affordance", None, ())


# ------------------------------------------------- mandatory counterexample 1

def test_raster_with_image_but_missing_inscription_is_rejected():
    """THE V2 LN-07 lesson: image presence never substitutes for inscription."""
    raster = _obj("raster", inscription_text=False, image=True, visual_detail=True)
    text = _obj("text", modality="text", kb=10, inscription_text=False, visual_detail=True)
    d = select(_task("visual_detail", "inscription_text"), DEV, [raster, text])
    assert d.decision == "reject_missing_affordance"
    assert "inscription_text" in d.missing_affordances


def test_raster_with_inscription_is_selected():
    raster = _obj("raster", inscription_text=True, image=True, visual_detail=True)
    d = select(_task("visual_detail", "inscription_text"), DEV, [raster])
    assert d.decision == "select"
    assert d.selected_object_id == "raster"


def test_not_applicable_inscription_does_not_count_as_coverage():
    """None (NOT_APPLICABLE) on a REQUIRED axis must not satisfy coverage."""
    o = _obj("o1", inscription_text=None, visual_detail=True)
    d = select(_task("inscription_text"), DEV, [o])
    assert d.decision == "reject_missing_affordance"


# ------------------------------------------------- mandatory counterexample 2

def test_screen_reader_audio_without_transcript_is_rejected():
    audio = _obj("audio", modality="audio", kb=480, audio=True, screen_reader_ready=True,
                 audio_transcript=False)
    d = select(_task("audio", "audio_transcript"),
               DeviceConstraints(network_kbps=3000, screen_reader=True), [audio])
    assert d.decision == "reject_missing_affordance"


def test_screen_reader_audio_with_transcript_is_selected():
    audio = _obj("audio", modality="audio", kb=480, audio=True, screen_reader_ready=True,
                 audio_transcript=True)
    d = select(_task("audio", "audio_transcript"),
               DeviceConstraints(network_kbps=3000, screen_reader=True), [audio])
    assert d.decision == "select"


# ------------------------------------------------- mandatory counterexample 3

def test_low_bandwidth_fallback_with_transcript_is_acceptable():
    """Positive control: constrained device still gets a feasible object."""
    text = _obj("text", modality="text", kb=10, inscription_text=True,
                visual_detail=True, screen_reader_ready=True, keyboard_accessible=True)
    heavy = _obj("heavy", modality="3d", kb=1850, visual_detail=True, inscription_text=True)
    dev = DeviceConstraints(network_kbps=120, max_payload_kb=100)
    d = select(_task("visual_detail", "inscription_text"), dev, [heavy, text])
    assert d.decision == "select"
    assert d.selected_object_id == "text"


def test_heavy_3d_blocked_on_low_bandwidth():
    heavy = _obj("heavy", modality="3d", kb=1850, visual_detail=True, inscription_text=True)
    dev = DeviceConstraints(network_kbps=120, max_payload_kb=100)
    d = select(_task("visual_detail", "inscription_text"), dev, [heavy])
    # affordances are covered; the failure axis is device feasibility only
    assert d.decision == "reject_infeasible"
    assert "bandwidth_budget_exceeded" in d.reason_codes


def test_3d_requires_webgl():
    obj3d = _obj("m3d", modality="3d", kb=100, visual_detail=True)
    d = select(_task("visual_detail"), DeviceConstraints(network_kbps=3000, webgl=False), [obj3d])
    assert d.decision == "reject_infeasible"
    assert "webgl_unavailable" in d.reason_codes


# ------------------------------------------------- mandatory counterexample 4

def test_rights_violation_rejected_when_all_candidates_forbidden():
    nc = LearningObject(object_id="nc", modality="2d_image", kb=100, affordances={},
                        license_status="CC-BY-NC-4.0")
    d = select(_task("visual_detail"), DEV, [nc])
    assert d.decision == "reject_rights_violation"


def test_ambiguous_unknown_license_is_rejected_not_guessed():
    unk = LearningObject(object_id="unk", modality="2d_image", kb=100, affordances={},
                         license_status="unknown")
    d = select(_task("visual_detail"), DEV, [unk])
    assert d.decision == "reject_rights_violation"


def test_cc0_among_forbidden_is_still_selectable():
    unk = LearningObject(object_id="unk", modality="2d_image", kb=100,
                         affordances={"visual_detail": True}, license_status="unknown")
    cc0 = _obj("cc0", visual_detail=True, kb=50)
    d = select(_task("visual_detail"), DEV, [unk, cc0])
    assert d.decision == "select"
    assert d.selected_object_id == "cc0"


# ------------------------------------------------- mandatory counterexample 5

def test_determinism_identical_inputs_identical_outputs():
    objs = [
        _obj("a", inscription_text=True, visual_detail=True, kb=100),
        _obj("b", inscription_text=True, visual_detail=True, kb=50),
    ]
    task = _task("inscription_text")
    d1 = select(task, DEV, objs)
    d2 = select(task, DEV, list(reversed(objs)))
    assert d1.decision == d2.decision
    assert d1.selected_object_id == d2.selected_object_id == "b"  # minimal kb, tie by id


def test_predict_case_deterministic_across_repeats():
    from research_v3.methods.p07.synthetic_generator import generate_stress_cases
    rows = generate_stress_cases(seed=999)
    r1 = [predict_case(row) for row in rows]
    r2 = [predict_case(row) for row in rows]
    assert r1 == r2


def test_predict_case_never_reads_gold_keys():
    """Oracle-free inference: a row containing gold material still works, and
    the prediction cannot change because of it."""
    from research_v3.methods.p07.synthetic_generator import generate_stress_cases
    row = generate_stress_cases(seed=7)[0]
    clean = predict_case(row)
    polluted = dict(row)
    polluted["oracle"] = "select"
    polluted["expected_decision"] = "select"
    assert predict_case(polluted) == clean


# ------------------------------------------------------------- misc contract

def test_empty_pool_is_explicit_abstain():
    d = select(_task("visual_detail"), DEV, [])
    assert d.decision == "abstain"
    assert d.selected_object_id is None


def test_selection_prefers_smallest_feasible_payload():
    big = _obj("big", inscription_text=True, kb=500)
    small = _obj("small", inscription_text=True, kb=10)
    d = select(_task("inscription_text"), DEV, [big, small])
    assert d.selected_object_id == "small"
    assert d.kb_used == 10


def test_keyboard_only_learner_gets_accessible_object():
    nk = _obj("no_keyboard", visual_detail=True, keyboard_accessible=False)
    ok = _obj("keyboard_ok", visual_detail=True, keyboard_accessible=True, kb=200)
    d = select(_task("visual_detail"),
               DeviceConstraints(network_kbps=3000, keyboard_only=True), [nk, ok])
    assert d.decision == "select"
    assert d.selected_object_id == "keyboard_ok"
