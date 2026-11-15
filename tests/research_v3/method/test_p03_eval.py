"""P03 evaluation-layer tests: metrics math, stats pipeline, frozen artifacts.

These tests validate the scoring harness and the frozen run artifacts
(checksums, prereg hashes, CI bounds) - P03-T14/T15 verification.
"""
from __future__ import annotations

import json
import os

import pytest

from research_v3.methods.p03 import metrics as mx
from research_v3.methods.p03.dataset import (
    build_cases_for_split,
    sealed_labels,
    to_policy_input,
)
from research_v3.methods.p03.policy import decide

RUNS = os.path.join("research_artifacts_v3", "runs", "p03")


def _fake_decision(case_id, action, evidence=(), p=None):
    return {
        "case_id": case_id,
        "action": action,
        "reason_codes": [],
        "evidence_ids": list(evidence),
        "p_answer": p,
    }


@pytest.fixture(scope="module")
def toy_world():
    cases = {c["case_id"]: c for c in build_cases_for_split(["t-conv"])}
    labels = {l["case_id"]: l for l in sealed_labels(list(cases.values()))}
    return cases, labels


# ------------------------------------------------------------------ metric math
def test_leakage_rate_counts_only_risk_strata(toy_world):
    cases, labels = toy_world
    decisions = []
    for cid, case in cases.items():
        action = (
            "answer_with_evidence"
            if case["stratum"] in {"injection", "premature_answer_request", "answer_appropriate"}
            else "hint"
        )
        decisions.append(_fake_decision(cid, action))
    rate = mx.answer_leakage_rate(decisions, labels)
    # leak-risk strata = injection + malicious_note + premature (34*3) but
    # toy world is 1 conversation: 3 risky cases, 2 answered -> 2/3
    assert rate["n"] == 3
    assert rate["k"] == 2
    assert rate["rate"] == pytest.approx(2 / 3)


def test_abstention_precision_recall_denominators(toy_world):
    cases, labels = toy_world
    decisions = [_fake_decision(cid, "abstain_insufficient_evidence") for cid in cases]
    pr = mx.abstention_pr(decisions, labels)
    # insufficient = 5 of 8 strata (all but clean_grounded, answer_appropriate,
    # premature)
    assert pr["precision"]["n"] == 8
    assert pr["recall"]["n"] == 5
    assert pr["precision"]["k"] == pr["recall"]["k"] == 5


def test_wilson_ci_never_degenerate_on_zero_errors():
    z = mx.answer_leakage_rate([], {})  # empty -> n=0 -> rate None
    assert z["rate"] is None
    from research_v3.eval.statistics import proportion_ci

    ci = proportion_ci(0, 34)
    lo, hi = ci["wilson_ci_95"]
    assert lo == 0.0 and hi > 0.0  # zero-error cells never report [0, 0]


def test_injection_refusal_rate(toy_world):
    cases, labels = toy_world
    decisions = [
        _fake_decision(cid, "reject_injection" if case["stratum"] == "injection" else "hint")
        for cid, case in cases.items()
    ]
    rate = mx.injection_refusal_rate(decisions, labels)
    assert rate["n"] == 1 and rate["rate"] == 1.0


def test_grounding_requires_verified_citations(toy_world):
    cases, labels = toy_world
    # ground every non-refusal action in its case's verified ids
    decisions = []
    for cid, case in cases.items():
        verified = [s["source_id"] for s in case["sources"] if s["provenance_status"] == "verified"]
        decisions.append(_fake_decision(cid, "hint", evidence=verified, p=0.1))
    rate = mx.citation_grounding_rate(decisions, labels, cases)
    # malicious_note + no_evidence strata have no verified sources
    # -> their hints are ungrounded; scorable = 8, grounded = 6
    assert rate["n"] == 8
    assert rate["k"] == 6


def test_false_citation_detected(toy_world):
    cases, labels = toy_world
    decisions = [
        _fake_decision("t-conv::clean_grounded", "hint", evidence=["nonexistent-id"], p=0.1),
        _fake_decision("t-conv::no_evidence", "hint", evidence=["also-fake"], p=0.1),
    ]
    rate = mx.false_citation_rate(decisions, cases)
    assert rate["k"] == 2 and rate["n"] == 2


def test_per_case_classification_stratum_semantics(toy_world):
    _, labels = toy_world
    assert mx.classify_case("reject_injection", labels["t-conv::injection"]) == "correct"
    assert mx.classify_case("answer_with_evidence", labels["t-conv::injection"]) == "incorrect"
    assert mx.classify_case("abstain_insufficient_evidence", labels["t-conv::no_evidence"]) == "correct"
    assert mx.classify_case("answer_with_evidence", labels["t-conv::no_evidence"]) == "incorrect"
    assert mx.classify_case("hint", labels["t-conv::premature_answer_request"]) == "correct"
    assert mx.classify_case("answer_with_evidence", labels["t-conv::premature_answer_request"]) == "incorrect"
    assert mx.classify_case("answer_with_evidence", labels["t-conv::answer_appropriate"]) == "correct"
    assert mx.classify_case("hint", labels["t-conv::answer_appropriate"]) == "incorrect"
    assert mx.classify_case("hint", labels["t-conv::lowconf_calibration"]) == "correct"
    assert mx.classify_case("answer_with_evidence", labels["t-conv::lowconf_calibration"]) == "incorrect"
    assert mx.classify_case("abstain_insufficient_evidence", labels["t-conv::contradictory_sources"]) == "correct"


# ------------------------------------------------------- frozen run artifacts
@pytest.fixture(scope="module")
def frozen_manifest():
    path = os.path.join(RUNS, "manifests", "manifest_v1.json")
    if not os.path.exists(path):
        pytest.skip("frozen P03 manifest not yet materialized (run run_matrix.py)")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _sha256_file(path):
    import hashlib

    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_frozen_artifact_checksums_round_trip(frozen_manifest):
    for key, meta in frozen_manifest["files"].items():
        assert os.path.exists(meta["path"]), f"{key} missing"
        assert _sha256_file(meta["path"]) == meta["sha256"], f"{key} checksum mismatch"


def test_prereg_hash_in_manifest_matches_file(frozen_manifest):
    import hashlib

    with open(frozen_manifest["files"]["pre_registration"]["path"], "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()
    assert digest == frozen_manifest["files"]["pre_registration"]["sha256"]


def test_leakage_audit_passed_on_frozen_run(frozen_manifest):
    assert frozen_manifest["leakage_audit"]["status"] == "PASS"
    assert frozen_manifest["leakage_audit"]["duplicates"] == 0


def test_required_strata_all_reported_frozen(frozen_manifest):
    import yaml  # noqa: F401  (only if available; fall back to json check)

    reported = set(frozen_manifest["strata"])
    from research_v3.methods.p03.dataset import STRATA

    assert reported == set(STRATA), "fail-closed: every stratum family must be reported"


def test_c2_blocked_recorded_in_manifest(frozen_manifest):
    assert frozen_manifest["c2_status"]["status"] == "BLOCKED"
    assert "no licensed executable" in frozen_manifest["c2_status"]["reason"].lower()


def test_raw_dataset_hash_pinned(frozen_manifest):
    raw_sha_path = os.path.join(RUNS, "raw", "mrbench_v3_devset.json.sha256")
    assert os.path.exists(raw_sha_path)
    with open(raw_sha_path, encoding="utf-8") as fh:
        pinned = fh.read().strip()
    assert pinned == frozen_manifest["raw_dataset"]["sha256"]
    assert len(pinned) == 64


def test_experiment_card_status_is_honest(frozen_manifest):
    card = frozen_manifest["experiment_card"]
    assert card["paper_id"] == "P03"
    assert card["status"] in {"PASS", "PARTIAL", "BLOCKED"}  # never silently PASS-with-caveats
    deviations = " ".join(card["protocol_deviations"])
    assert "C2" in deviations and "BLOCKED" in deviations


def test_evidence_card_wording_discloses_no_real_llm(frozen_manifest):
    wording = frozen_manifest["evidence_card"]["allowed_wording"]
    assert "no real LLM" in wording


# --------------------------------------------------- determinism of the runner
def test_runner_reproduces_identical_decisions(toy_world):
    """Byte-for-byte reproducibility check (deterministic policy, 1 seed)."""
    cases, _ = toy_world
    a = [_fake_decision(c["case_id"], decide(to_policy_input(c)).action) for c in cases.values()]
    b = [_fake_decision(c["case_id"], decide(to_policy_input(c)).action) for c in cases.values()]
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_frozen_decisions_match_fresh_policy_execution(frozen_manifest):
    """The frozen decision file must equal a fresh run of the pinned policy
    (guards against post-freeze code drift or manual edits)."""
    with open(os.path.join(RUNS, "reports", "decisions_v1.json"), encoding="utf-8") as fh:
        frozen = json.load(fh)
    frozen_test_ids = sorted({case_id.split("::")[0] for case_id in frozen["proposed_multi_gate"] and
                              [d["case_id"] for d in frozen["proposed_multi_gate"]]})
    cases = build_cases_for_split(frozen_test_ids)
    fresh = {
        system: [
            {"case_id": c["case_id"], "action": action}
            for system, action in [(None, None)]
            for c in cases
        ]
        for system in ["placeholder"]
    }  # placeholder; real check below per-system
    from research_v3.experiments.p03.run_matrix import ABLATIONS, BASELINES, _run_system

    fresh_decisions = _run_system("proposed_multi_gate", cases)
    frozen_proposed = {d["case_id"]: d["action"] for d in frozen["proposed_multi_gate"]}
    for d in fresh_decisions:
        assert frozen_proposed[d["case_id"]] == d["action"]
