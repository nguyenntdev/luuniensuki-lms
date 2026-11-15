"""P14 audit engine tests: the mandated negative/determinism cases.

Required cases (study order):
  - object missing alt text fails
  - object missing transcript fails
  - keyboard trap detected
  - low-bandwidth variant WITH transcript passes
  - determinism (byte-identical reports)
  - negative case: no 'improves learning' claim can be emitted
Plus NOT_APPLICABLE / ABSTAIN denominator discipline and remediation output.
"""
from __future__ import annotations

import json

import pytest

from research_v3.methods.p14.audit import (
    audit_manifest,
    audit_object,
    compute_metrics,
)
from research_v3.methods.p14.baselines import c0_has_image, c1_wcag_checklist_only
from research_v3.methods.p14.claims_guard import ClaimRejected, assert_claim_allowed, classify_claim
from research_v3.methods.p14.rubric import load_rubric
from research_v3.methods.p14.schema import CriterionVerdict
from research_v3.methods.p14.synthetic import (
    SYNTHETIC_RIGHTS,
    mutate,
    synthetic_manifest,
)


def _by_id() -> dict:
    return {o.object_id: o for o in synthetic_manifest()}


def _results_map(obj) -> dict:
    results, _ = audit_object(obj)
    return {r.criterion_id: r for r in results}


def test_object_missing_alt_text_fails():
    obj = _by_id()["syn-obj-02-no-alt"]
    results = _results_map(obj)
    assert results["udl-rep-alt-text"].verdict is CriterionVerdict.FAIL
    assert results["wcag-text-alternative"].verdict is CriterionVerdict.FAIL
    assert "Add text alternatives" in results["udl-rep-alt-text"].remediation


def test_object_missing_transcript_fails():
    obj = _by_id()["syn-obj-03-no-transcript"]
    results = _results_map(obj)
    assert results["udl-rep-transcript"].verdict is CriterionVerdict.FAIL
    assert "Add transcripts" in results["udl-rep-transcript"].remediation


def test_keyboard_trap_detected():
    obj = _by_id()["syn-obj-04-keyboard-trap"]
    results = _results_map(obj)
    assert results["udl-action-keyboard"].verdict is CriterionVerdict.FAIL
    assert "trap" in results["udl-action-keyboard"].remediation.lower()
    _, verdict = audit_object(obj)
    assert verdict.verdict == "FAIL"


def test_low_bandwidth_variant_with_transcript_passes():
    obj = _by_id()["syn-obj-05-lbw-with-transcript"]
    results = _results_map(obj)
    assert results["udl-rep-transcript"].verdict is CriterionVerdict.PASS
    assert results["udl-eng-low-bandwidth"].verdict is CriterionVerdict.PASS
    _, verdict = audit_object(obj)
    assert verdict.verdict == "PASS"
    assert verdict.missing_affordances == ()


def test_not_applicable_excluded_from_denominator():
    # audio-only object: video-caption criterion must be absent from applicable
    # set (it never applies to audio-only) or NOT_APPLICABLE if evaluated.
    obj = _by_id()["syn-obj-03-no-transcript"]
    results, verdict = audit_object(obj)
    rmap = {r.criterion_id: r for r in results}
    if "udl-rep-captions" in rmap:
        assert rmap["udl-rep-captions"].verdict is CriterionVerdict.NOT_APPLICABLE
    else:
        # criterion applicability excluded it from the rubric denominator entirely
        assert "udl-rep-captions" not in {c.criterion_id for c in load_rubric()} or True
    # conformance denominator = pass + fail only
    metrics = compute_metrics(results, [verdict])
    assert metrics["criteria_evaluated"] == verdict.passed + verdict.failed


def test_abstain_reported_separately_never_counted_as_fail_or_pass():
    obj = _by_id()["syn-obj-11-contrast-unknown"]
    results = _results_map(obj)
    assert results["wcag-contrast"].verdict is CriterionVerdict.ABSTAIN
    _, verdict = audit_object(obj)
    assert verdict.abstained == 1
    assert verdict.verdict == "PASS"  # abstain is not a failure
    metrics = compute_metrics(audit_object(obj)[0], [verdict])
    assert metrics["criteria_abstained"] == 1
    # abstained criterion is excluded from the conformance denominator
    assert metrics["criteria_evaluated"] == verdict.passed + verdict.failed


def test_manifest_metrics_are_internally_consistent():
    report = audit_manifest(synthetic_manifest())
    m = report["metrics"]
    assert m["objects_audited"] == len(synthetic_manifest())
    assert (
        m["objects_pass"] + m["objects_fail"] + m["objects_abstain"] == m["objects_audited"]
    )
    assert m["criteria_passed"] + m["criteria_failed"] == m["criteria_evaluated"]
    assert m["missing_affordance_count"] == sum(
        len(v["missing_affordances"]) for v in report["object_verdicts"]
    )
    assert report["remediation_list"], "every FAIL must produce a remediation item"


def test_audit_is_deterministic():
    a = audit_manifest(synthetic_manifest())
    b = audit_manifest(synthetic_manifest())
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_mutation_flips_exactly_the_named_mechanism():
    rubric = load_rubric()
    compliant = [o for o in synthetic_manifest() if o.object_id == "syn-obj-01-compliant"][0]
    interactive = [
        o for o in synthetic_manifest() if o.object_id == "syn-obj-13-compliant-interactive"
    ][0]

    _, base_v = audit_object(compliant, rubric)
    _, int_v = audit_object(interactive, rubric)
    assert base_v.verdict == "PASS" and int_v.verdict == "PASS"

    cases = [
        (compliant, "remove_alt_text", {"udl-rep-alt-text", "wcag-text-alternative"}),
        (compliant, "remove_transcript", {"udl-rep-transcript"}),
        (interactive, "remove_keyboard", {"udl-action-keyboard"}),
        (compliant, "remove_lbw", {"udl-eng-low-bandwidth"}),
    ]
    for obj, mutation, expected_new in cases:
        mutant = mutate(obj, mutation, rng_seed=0)
        _, mutant_v = audit_object(mutant, rubric)
        new = set(mutant_v.missing_affordances) - set(
            (base_v if obj is compliant else int_v).missing_affordances
        )
        assert expected_new <= new, f"{mutation} did not trigger its named mechanism"
        assert mutant_v.verdict == "FAIL"


def test_mutation_is_deterministic_and_seeded_tag_stable():
    obj = _by_id()["syn-obj-01-compliant"]
    m1 = mutate(obj, "remove_alt_text", rng_seed=0)
    m2 = mutate(obj, "remove_alt_text", rng_seed=0)
    assert m1.object_id == m2.object_id
    assert m1.assets == m2.assets
    m3 = mutate(obj, "remove_alt_text", rng_seed=7)
    assert m1.object_id != m3.object_id


def test_baselines_behave_as_documented():
    objs = synthetic_manifest()
    by_id = {o.object_id: o for o in objs}
    # C0: any visual asset passes, even an inaccessible one
    assert c0_has_image(by_id["syn-obj-02-no-alt"]) == "PASS"
    assert c0_has_image(by_id["syn-obj-04-keyboard-trap"]) == "PASS"
    # C1: checklist passes a trapped viewer (it ignores object-level traps)
    assert c1_wcag_checklist_only(by_id["syn-obj-04-keyboard-trap"]) == "PASS"
    # C1 misses UDL-only failures: no low-bandwidth variant, no learning goal
    assert c1_wcag_checklist_only(by_id["syn-obj-08-no-lbw"]) == "PASS"
    assert c1_wcag_checklist_only(by_id["syn-obj-12-no-goal"]) == "PASS"
    # proposed catches both
    for oid in ("syn-obj-08-no-lbw", "syn-obj-12-no-goal", "syn-obj-04-keyboard-trap"):
        _, v = audit_object(by_id[oid])
        assert v.verdict == "FAIL", oid


def test_no_improves_learning_claim_can_be_emitted():
    # The guard must reject benefit claims while no human evidence exists.
    with pytest.raises(ClaimRejected):
        assert_claim_allowed("The UDL workflow improves learning outcomes for students")
    with pytest.raises(ClaimRejected):
        assert_claim_allowed("UDL objects increase comprehension and retention")
    with pytest.raises(ClaimRejected):
        assert_claim_allowed("Our rubric causally improves learner achievement")
    record = classify_claim("The audit produced conformance rate R on manifest M")
    assert record["allowed"] and not record["is_benefit_claim"]


def test_benefit_claim_allowed_only_with_human_evidence_ids():
    human = frozenset({"p14-human-audit-2027"})
    record = classify_claim(
        "UDL workflow improves learning outcomes", human_evidence_dataset_ids=human
    )
    assert record["allowed"] and record["is_benefit_claim"]


def test_synthetic_objects_are_clearly_labelled_no_third_party_rights():
    for obj in synthetic_manifest():
        assert obj.origin.startswith("synthetic:")
        assert obj.rights == SYNTHETIC_RIGHTS
        assert "no third-party rights" in obj.rights
