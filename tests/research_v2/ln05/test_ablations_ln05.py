"""Ablation divergence tests (LN-05-15): each ablation changes a real code path.

Every ablation must diverge from the proposed method on the exact threat
family its removed gate was responsible for, with a unit-level counterexample.
"""
from __future__ import annotations

import copy

from research_v2.contracts.types import StudyInput
from research_v2.methods.ln05 import predict_batch as predict_proposed
from research_v2.methods.ln05.ablations_a1 import predict_batch as predict_a1
from research_v2.methods.ln05.ablations_a2 import predict_batch as predict_a2
from research_v2.methods.ln05.ablations_a3 import predict_batch as predict_a3
from tests.research_v2.ln05.conftest import (
    duplicate_case_inputs,
    load_gold,
    load_rows,
    make_inputs,
    run_config,
)


def _one_row(gold_family: str) -> dict:
    golds = load_gold()
    return next(r for r in load_rows() if golds[r["case_id"]] == gold_family)


def test_a1_xp_only_diverges_on_missing_competency():
    """Without mastery proof, XP alone awards the badge I1 would deny."""
    row = _one_row("deny_mastery_badge")
    inputs = make_inputs([row])
    proposed = predict_proposed(inputs, run_config())[0]
    a1 = predict_a1(inputs, run_config())[0]
    assert proposed.decision == "deny_mastery_badge"
    assert a1.decision == "grant_if_eligible"
    assert "mastery_proof_disabled" in a1.reason_codes


def test_a2_no_anti_replay_awards_every_duplicate():
    """Without the dedup ledger, all 100 deliveries earn independent grants."""
    inputs = duplicate_case_inputs(100)
    proposed = predict_proposed(inputs, run_config())
    a2 = predict_a2(inputs, run_config())
    grants = sum(1 for p in proposed if p.decision == "grant_if_eligible")
    a2_grants = sum(1 for p in a2 if p.decision == "grant_if_eligible")
    assert grants == 1
    assert a2_grants == 100, "A2 must diverge: anti-replay removed means 100 awards"


def test_a3_no_provenance_accepts_forged_client_events():
    """Without the server-actor gate, client-forged XP earns the badge."""
    row = _one_row("reject_forged_event")
    inputs = make_inputs([row])
    proposed = predict_proposed(inputs, run_config())[0]
    a3 = predict_a3(inputs, run_config())[0]
    assert proposed.decision == "reject_forged_event"
    assert a3.decision == "grant_if_eligible"


def test_a2_and_a3_keep_freshness_gate():
    """Ablations only remove their own gate; staleness is still caught."""
    row = _one_row("revalidate_badge")
    inputs = make_inputs([row])
    for ablated in (predict_a2(inputs, run_config())[0], predict_a3(inputs, run_config())[0]):
        assert ablated.decision == "revalidate_badge"


def test_a1_keeps_replay_and_provenance_gates():
    replay_row = _one_row("deduplicate_events")
    forged_row = _one_row("reject_forged_event")
    assert predict_a1(make_inputs([replay_row]), run_config())[0].decision == "deduplicate_events"
    assert predict_a1(make_inputs([forged_row]), run_config())[0].decision == "reject_forged_event"


def test_a1_idempotent_across_duplicates():
    """A1 keeps the atomic ledger even with the mastery gate removed."""
    inputs = duplicate_case_inputs(100)
    a1 = predict_a1(inputs, run_config())
    assert sum(1 for p in a1 if p.decision == "grant_if_eligible") == 1


def test_ablation_divergence_matrix_over_full_dataset():
    """Dataset-level: each ablation diverges from I1 on its target families."""
    inputs = make_inputs(load_rows())
    golds = load_gold()
    base = {p.case_id: p.decision for p in predict_proposed(inputs, run_config())}

    a1 = {p.case_id: p.decision for p in predict_a1(inputs, run_config())}
    a2 = {p.case_id: p.decision for p in predict_a2(inputs, run_config())}
    a3 = {p.case_id: p.decision for p in predict_a3(inputs, run_config())}

    a1_diff = {c for c in base if a1[c] != base[c]}
    a2_diff = {c for c in base if a2[c] != base[c]}
    a3_diff = {c for c in base if a3[c] != base[c]}

    replay_cases = {c for c, d in golds.items() if d == "deduplicate_events"}
    forged_cases = {c for c, d in golds.items() if d == "reject_forged_event"}
    denied_cases = {c for c, d in golds.items() if d == "deny_mastery_badge"}

    assert replay_cases <= a2_diff, "A2 must diverge on replay family"
    assert not (replay_cases & a3_diff), "A3 must not diverge on replay family"
    assert forged_cases <= a3_diff, "A3 must diverge on forged family"
    assert denied_cases <= a1_diff, "A1 must diverge on competency-denied family"
    assert forged_cases & a1_diff == set(), "A1 keeps provenance gate"


def test_stale_policy_cases_are_untouched_by_all_ablations():
    golds = load_gold()
    inputs = make_inputs(load_rows())
    base = {p.case_id: p.decision for p in predict_proposed(inputs, run_config())}
    for preds in (predict_a1(inputs, run_config()), predict_a2(inputs, run_config()), predict_a3(inputs, run_config())):
        for p in preds:
            if golds[p.case_id] == "revalidate_badge":
                assert p.decision == base[p.case_id] == "revalidate_badge"


def test_ablation_inputs_and_budget_match_proposed():
    """No ablation may run on different inputs or a smaller budget (15.C.5)."""
    inputs = make_inputs(load_rows())
    for preds in (
        predict_a1(inputs, run_config()),
        predict_a2(inputs, run_config()),
        predict_a3(inputs, run_config()),
    ):
        assert len(preds) == len(inputs)
        assert all(p.case_id == i.case_id for p, i in zip(preds, inputs))
