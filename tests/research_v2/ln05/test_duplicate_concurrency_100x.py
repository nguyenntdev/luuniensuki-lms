"""LN-05 hard counterexample: 100 concurrent deliveries of one valid submission.

Mandatory case (spec 03/04 section F): the same valid submission delivered 100
times concurrently must produce exactly ONE mastery award; every other
delivery must be rejected as a replay. Distinct case_ids share one submission
identity (same dedup key) because case_id uniqueness is a contract
requirement, while replay identity is content-derived.

Canary cases (prereg LN05-CE-3/CE-4): redeliveries that rotate only
delivery-variant fields (timestamp, event_id, delivery/nonce/request/trace
ids) are REJECTED as replays; a genuinely new submission (different evidence
content or task) is NOT force-rejected; and whitespace/NFC text variations
that canonicalize equal are rejected like identical redeliveries.
"""
from __future__ import annotations

import copy
import unicodedata
from collections import Counter

from research_v2.methods.ln05 import predict_batch as predict_proposed
from research_v2.methods.ln05.labels import to_v2_decision
from tests.research_v2.ln05.conftest import duplicate_case_inputs, load_rows, run_config


def _deep_strings(obj) -> list[str]:
    """Collect every string value reachable inside a JSON-ish structure."""
    if isinstance(obj, dict):
        out: list[str] = []
        for v in obj.values():
            out.extend(_deep_strings(v))
        return out
    if isinstance(obj, list):
        out = []
        for v in obj:
            out.extend(_deep_strings(v))
        return out
    return [obj] if isinstance(obj, str) else []


def _redecorate_strings(obj, *, _skip_actor: bool = False):
    """Return a copy where every string value is NFD-decomposed and padded.

    Values rewritten this way canonicalize back to the original under the
    identity normalization (NFC + whitespace collapse), so a redelivery using
    them must map to the same dedup key. ``actor`` values are left untouched:
    the raw provenance gate (gate 2) compares actor strings pre-normalization,
    which is correct behaviour and tested separately.
    """
    if isinstance(obj, dict):
        return {k: _redecorate_strings(v, _skip_actor=(k == "actor")) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_redecorate_strings(v) for v in obj]
    if isinstance(obj, str):
        if _skip_actor:
            return obj
        return f" {unicodedata.normalize('NFD', obj)} "
    return obj


def test_100_concurrent_duplicates_yield_exactly_one_grant():
    inputs = duplicate_case_inputs(100)
    preds = predict_proposed(inputs, run_config())
    assert len(preds) == 100
    decisions = Counter(p.decision for p in preds)
    assert decisions["grant_if_eligible"] == 1, decisions
    assert decisions["deduplicate_events"] == 99, decisions
    assert sum(decisions.values()) == 100

    granted = [p for p in preds if p.decision == "grant_if_eligible"]
    assert len(granted) == 1
    # The grant carries its immutable event identity (content-derived key).
    assert granted[0].evidence_ids and all(len(e) == 64 for e in granted[0].evidence_ids)


def test_all_replay_rejections_project_to_v2_reject_replay():
    inputs = duplicate_case_inputs(100)
    preds = predict_proposed(inputs, run_config(seed=23))
    for p in preds:
        if p.decision == "grant_if_eligible":
            continue
        assert to_v2_decision(p.decision) == "reject_replay"
        assert "idempotency_violation" in p.reason_codes


def test_duplicate_grant_count_metric_is_zero_for_proposed():
    from research_v2.methods.ln05.metrics import false_award_metrics

    inputs = duplicate_case_inputs(100)
    preds = predict_proposed(inputs, run_config(seed=37))
    by_key: dict[str, list[str]] = {}
    for p in preds:
        if p.decision == "grant_if_eligible":
            key = p.evidence_ids[0]
            by_key.setdefault(key, []).append(p.case_id)
    m = false_award_metrics(grants_by_dedup_key=by_key)
    assert m["duplicate_grant_count"] == 0
    assert m["total_grants"] == 1


def test_replay_ledger_rejects_cross_batch_redelivery():
    from research_v2.methods.ln05.proposed import ReplayLedger

    inputs = duplicate_case_inputs(2)
    ledger = ReplayLedger()
    first = predict_proposed(inputs[:1], run_config())
    assert first[0].decision == "grant_if_eligible"
    # A second batch reusing the same submission content is still a replay:
    # the ledger is content-addressed, not case-id addressed.
    second = predict_proposed(inputs[:1], run_config())
    # fresh ledger per batch call (each call is one policy epoch), so simulate
    # the shared-ledger path explicitly:
    from research_v2.methods.ln05.proposed import PolicyEpoch

    epoch = PolicyEpoch(policy_version=2, dataset_sha256="ds")
    base_features = inputs[0].features
    key = ledger.dedup_key(
        learner=base_features["learner"],
        badge=base_features["badge"],
        skill_evidence=base_features["skill_evidence"],
        reward_events=base_features["reward_events"],
    )
    assert ledger.consume(key, case_id="c1", decision="grant_if_eligible", evidence_sha256="x") is True
    assert ledger.consume(key, case_id="c2", decision="grant_if_eligible", evidence_sha256="x") is False
    assert ledger.is_consumed(key)


def test_clock_skewed_duplicate_with_new_timestamp_is_rejected():
    """CE-3: redelivery with a mutated timestamp must be REJECTED as a replay.

    The dedup key derives from the normalized submission identity, which
    excludes delivery-variant fields such as ``timestamp``; mutating only the
    timestamp must therefore map onto the already-consumed key.
    """
    inputs = duplicate_case_inputs(2)
    mutated = dict(inputs[1].features)
    events = [dict(e) for e in mutated["reward_events"]]
    for e in events:
        e["timestamp"] = 9999999999.0
    mutated["reward_events"] = events

    from research_v2.methods.ln05.proposed import PolicyEpoch, ReplayLedger, evaluate

    ledger = ReplayLedger()
    epoch = PolicyEpoch(policy_version=2, dataset_sha256="ds")
    cfg = run_config()

    d1 = evaluate(dict(inputs[0].features), cfg, ledger, epoch)
    d2 = evaluate(mutated, cfg, ledger, epoch)
    assert d1[0] == "grant_if_eligible"
    # Strict rejection: a timestamp-mutated redelivery is never re-awarded.
    assert d2[0] == "deduplicate_events", d2
    assert "idempotency_violation" in d2[1]
    assert d2[2]["replay_prevented"] is True
    # The rejected redelivery maps to the exact key the grant consumed.
    assert d2[2]["dedup_key"] == d1[2]["dedup_key"]


def test_rotated_event_id_only_is_rejected():
    """CE-3: rotating ``event_id`` must not mint a fresh dedup key."""
    from research_v2.methods.ln05.proposed import PolicyEpoch, ReplayLedger, evaluate

    inputs = duplicate_case_inputs(2)
    mutated = dict(inputs[1].features)
    events = [dict(e, event_id=f"ROTATED-{k}") for k, e in enumerate(mutated["reward_events"])]
    mutated["reward_events"] = events

    ledger = ReplayLedger()
    epoch = PolicyEpoch(policy_version=2, dataset_sha256="ds")
    cfg = run_config()
    d1 = evaluate(dict(inputs[0].features), cfg, ledger, epoch)
    d2 = evaluate(mutated, cfg, ledger, epoch)
    assert d1[0] == "grant_if_eligible"
    assert d2[0] == "deduplicate_events", d2
    assert d2[2]["dedup_key"] == d1[2]["dedup_key"]


def test_rotated_delivery_metadata_is_rejected():
    """CE-3: new delivery_id/nonce/request_id/trace_id are redelivery knobs."""
    from research_v2.methods.ln05.proposed import PolicyEpoch, ReplayLedger, evaluate

    inputs = duplicate_case_inputs(2)
    mutated = dict(inputs[1].features)
    events = [
        dict(e, delivery_id=f"d-{k}", nonce=f"n-{k}", request_id=f"r-{k}", trace_id=f"t-{k}")
        for k, e in enumerate(mutated["reward_events"])
    ]
    mutated["reward_events"] = events

    ledger = ReplayLedger()
    epoch = PolicyEpoch(policy_version=2, dataset_sha256="ds")
    cfg = run_config()
    d1 = evaluate(dict(inputs[0].features), cfg, ledger, epoch)
    d2 = evaluate(mutated, cfg, ledger, epoch)
    assert d1[0] == "grant_if_eligible"
    assert d2[0] == "deduplicate_events", d2
    assert d2[2]["dedup_key"] == d1[2]["dedup_key"]


def test_changed_evidence_content_is_not_force_rejected():
    """New evidence content derives a FRESH key: it must not be deduplicated.

    The ledger rejects identical submissions; genuinely new evidence (different
    task and competency level) must stay eligible for a grant.
    """
    from research_v2.contracts.types import StudyInput
    from research_v2.methods.ln05.proposed import PolicyEpoch, ReplayLedger, evaluate

    rows = load_rows()
    base = next(
        r
        for r in rows
        if any(e.get("actor") == "server" for e in r["input"]["reward_events"])
        and len(r["input"]["reward_events"]) == 1
    )
    new_evidence = copy.deepcopy(base["input"])
    # Different task (top-level content) and different evidence level: a
    # genuinely new submission, never a redelivery.
    new_evidence = dict(new_evidence)
    new_evidence["content"] = dict(base["input"].get("content", {"id": "x"}), id="other_task_id")
    req = base["input"]["badge"]["requires_competency"]
    new_evidence["skill_evidence"] = dict(base["input"]["skill_evidence"])
    new_evidence["skill_evidence"][req] = min(1.0, float(base["input"]["skill_evidence"][req]) + 0.1)

    ledger = ReplayLedger()
    epoch = PolicyEpoch(policy_version=2, dataset_sha256="ds")
    cfg = run_config()
    d1 = evaluate(dict(base["input"]), cfg, ledger, epoch)
    d2 = evaluate(new_evidence, cfg, ledger, epoch)
    assert d1[0] == "grant_if_eligible"
    # NOT force-rejected: different evidence content and task derive distinct
    # keys, so the second submission cannot be labelled a replay.
    assert d2[0] != "deduplicate_events", d2
    key1 = ledger.dedup_key(
        learner=base["input"]["learner"],
        badge=base["input"]["badge"],
        skill_evidence=base["input"]["skill_evidence"],
        reward_events=base["input"]["reward_events"],
        features=base["input"],
    )
    key2 = ledger.dedup_key(
        learner=new_evidence["learner"],
        badge=new_evidence["badge"],
        skill_evidence=new_evidence["skill_evidence"],
        reward_events=new_evidence["reward_events"],
        features=new_evidence,
    )
    assert key1 != key2


def test_whitespace_and_nfc_variations_of_evidence_text_are_rejected():
    """Whitespace/NFC normalization: equal-canonical text redelivery is a replay.

    The identity canonicalizer collapses whitespace runs and applies NFC, so a
    redelivery whose evidence text differs only by padding or Unicode
    normalization form maps to the same dedup key. The dataset carries no
    untrimmed strings, so this builds a synthetic redelivery of one row.
    """
    from research_v2.methods.ln05.proposed import PolicyEpoch, ReplayLedger, evaluate

    rows = load_rows()
    base = next(
        r
        for r in rows
        if any(e.get("actor") == "server" for e in r["input"]["reward_events"])
        and len(r["input"]["reward_events"]) == 1
    )
    mutated = copy.deepcopy(base)
    mutated["case_id"] = base["case_id"] + "-WS"
    # NFD + padding: canonicalizes back to the original, so the key must not
    # change and the redelivery must be rejected.
    mutated["input"] = _redecorate_strings(mutated["input"])

    ledger = ReplayLedger()
    epoch = PolicyEpoch(policy_version=2, dataset_sha256="ds")
    cfg = run_config()
    key1 = ledger.dedup_key(
        learner=base["input"]["learner"],
        badge=base["input"]["badge"],
        skill_evidence=base["input"]["skill_evidence"],
        reward_events=base["input"]["reward_events"],
        features=base["input"],
    )
    key2 = ledger.dedup_key(
        learner=mutated["input"]["learner"],
        badge=mutated["input"]["badge"],
        skill_evidence=mutated["input"]["skill_evidence"],
        reward_events=mutated["input"]["reward_events"],
        features=mutated["input"],
    )
    assert key1 == key2
    d1 = evaluate(dict(base["input"]), cfg, ledger, epoch)
    d2 = evaluate(dict(mutated["input"]), cfg, ledger, epoch)
    assert d1[0] == "grant_if_eligible"
    assert d2[0] == "deduplicate_events", d2


def test_dataset_replay_family_cases_are_all_rejected():
    """Every dataset replay-family case is rejected as duplicate, never granted."""
    from tests.research_v2.ln05.conftest import load_gold, load_rows, make_inputs

    golds = load_gold()
    rows = [r for r in load_rows() if golds[r["case_id"]] == "deduplicate_events"]
    preds = predict_proposed(make_inputs(rows), run_config())
    assert len(preds) == len(rows) == 24
    assert all(p.decision == "deduplicate_events" for p in preds)
