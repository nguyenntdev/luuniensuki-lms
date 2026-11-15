"""LN-10 T3S stress dataset: explicit same-version concurrent-edit coverage.

Reviewer-finding regression guard: the sealed T3 holdout's 24 conflict-stratum
cases are all stale-CAS only (zero ``concurrent_edits`` rows), so the explicit
two-conflicting-offline-edits detector (INV-LN-10-04) was exercised only in
unit fixtures. The T3S stress cell closes that gap in the matrix run itself.

Legacy fixtures under ``research/fixtures/`` stay READ-ONLY: this module reads
only the V2-authored ``research_v2/data/ln10/t3s_*`` files.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from research_v2.contracts.canonical_hash import canonical_json, sha256_bytes
from research_v2.contracts.types import StudyInput
from research_v2.methods.ln10.labels import NATIVE_DECISIONS
from research_v2.methods.ln10.proposed import predict_batch

REPO_ROOT = Path(__file__).resolve().parents[3]
T3S_INPUTS = REPO_ROOT / "research_v2" / "data" / "ln10" / "t3s_inputs.jsonl"
T3S_GOLD = REPO_ROOT / "research_v2" / "data" / "ln10" / "t3s_gold.jsonl"

CONFLICT = "resolve_revision_conflict"
APPLY = "allow_authorized_transition"


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]


@pytest.fixture(scope="module")
def t3s_inputs() -> list[dict]:
    return _load_jsonl(T3S_INPUTS)


@pytest.fixture(scope="module")
def t3s_gold() -> dict[str, str]:
    return {r["case_id"]: r["expected_decision"] for r in _load_jsonl(T3S_GOLD)}


def _study_inputs(rows: list[dict]) -> list[StudyInput]:
    return [
        StudyInput("LN-10", r["case_id"], "stress", r["group_id"], r["input"])
        for r in rows
    ]


def test_t3s_dataset_loads_with_expected_shape(t3s_inputs, t3s_gold):
    assert len(t3s_inputs) == 24
    assert len(t3s_gold) == 24
    assert [r["case_id"] for r in t3s_inputs] == sorted(t3s_gold)
    for row in t3s_inputs:
        assert row["study_id"] == "LN-10"
        assert row["case_id"].startswith("LN-10-V2S-")
        assert row["group_id"].startswith("LN-10-V2S-grp-")
        assert sha256_bytes(canonical_json(row["input"])) == row["input_sha256"]


def test_t3s_every_case_has_at_least_two_edits_on_same_version(t3s_inputs):
    """Every case carries >=2 offline edits sharing one expected_version (the
    detector-triggering shape); some cases add extra edits at other versions."""
    from collections import Counter

    for row in t3s_inputs:
        edits = row["input"].get("concurrent_edits") or []
        assert len(edits) >= 2, f"{row['case_id']}: fewer than two offline edits"
        per_version = Counter(e["expected_version"] for e in edits)
        assert max(per_version.values()) >= 2, (
            f"{row['case_id']}: no version carries two edits"
        )


def test_t3s_contains_genuine_same_version_divergent_conflicts(t3s_inputs, t3s_gold):
    """At least one case must be a REAL divergent-payload conflict on the
    current version - not a stale-CAS case and not an idempotent redelivery."""
    genuine = []
    for row in t3s_inputs:
        edits = row["input"]["concurrent_edits"]
        first = edits[0]
        divergent = any(
            e["action"] != first["action"]
            or e.get("new_goal") != first.get("new_goal")
            or (e.get("rationale") or "") != (first.get("rationale") or "")
            for e in edits[1:]
        )
        cas_aligned = (
            row["input"]["transition"]["expected_version"]
            == row["input"]["project"]["version"]
        )
        if divergent and cas_aligned:
            genuine.append(row)
    assert len(genuine) >= 12
    # Every genuine same-version divergent case must be gold-labelled conflict.
    assert all(t3s_gold[r["case_id"]] == CONFLICT for r in genuine)


def test_t3s_gold_labels_within_native_space(t3s_gold):
    assert set(t3s_gold.values()) <= set(NATIVE_DECISIONS)
    assert set(t3s_gold.values()) == {CONFLICT, APPLY}


def test_t3s_groups_pair_conflict_families(t3s_inputs):
    """Conflict families are grouped: 12 pair-groups, two cases per group."""
    from collections import Counter

    counts = Counter(r["group_id"] for r in t3s_inputs)
    assert len(counts) == 12
    assert set(counts.values()) == {2}


def test_proposed_resolves_divergent_conflicts_and_never_silently_applies(
    t3s_inputs, t3s_gold
):
    preds = predict_batch(_study_inputs(t3s_inputs), {"seed": 11})
    by_case = {p.case_id: p for p in preds}
    conflict_cases = [c for c, gold in t3s_gold.items() if gold == CONFLICT]
    apply_cases = [c for c, gold in t3s_gold.items() if gold == APPLY]
    # Every divergent conflict is detected with the native conflict label...
    for cid in conflict_cases:
        pred = by_case[cid]
        assert pred.decision == CONFLICT, cid
        assert "concurrent_offline_edits" in pred.reason_codes, cid
        assert pred.score == 0.0, cid  # nothing applied silently
    # ...and every identical-redelivery case applies idempotently (no
    # false rejection of legitimate replays).
    for cid in apply_cases:
        pred = by_case[cid]
        assert pred.decision == APPLY, cid
        assert pred.score == 1.0, cid


def test_proposed_conflict_reason_codes_distinguish_families(t3s_inputs, t3s_gold):
    preds = predict_batch(_study_inputs(t3s_inputs), {"seed": 11})
    by_case = {p.case_id: p for p in preds}
    conflict_ids = [c for c, gold in t3s_gold.items() if gold == CONFLICT]
    assert all(
        "concurrent_offline_edits" in by_case[cid].reason_codes for cid in conflict_ids
    )
    # No stale-CAS reason anywhere: every detection came from the explicit
    # two-conflicting-offline-edits detector, not the compare-and-swap gate.
    assert all("offline_conflict" not in by_case[cid].reason_codes for cid in conflict_ids)


def test_canary_always_apply_b0_fails_stress_dataset(t3s_inputs, t3s_gold):
    from research_v2.methods.ln10.baselines import predict_batch_b0

    preds = predict_batch_b0(_study_inputs(t3s_inputs), {"seed": 11})
    wrong = [p for p in preds if p.decision != t3s_gold[p.case_id]]
    # The unchecked checklist silently applies all 20 conflicts.
    assert len(wrong) >= 18


def test_canary_no_concurrency_check_a2_fails_stress_dataset(t3s_inputs, t3s_gold):
    from research_v2.methods.ln10.ablations import predict_batch_a2

    preds = predict_batch_a2(_study_inputs(t3s_inputs), {"seed": 11})
    wrong = [p for p in preds if p.decision != t3s_gold[p.case_id]]
    # Removing the concurrency control silently applies most conflicts.
    assert len(wrong) >= 18
    applied_conflicts = [
        p for p in preds
        if p.decision == APPLY and t3s_gold[p.case_id] == CONFLICT
    ]
    assert len(applied_conflicts) >= 18


def test_canary_c1_classical_checklist_misses_same_version_conflicts(
    t3s_inputs, t3s_gold
):
    """Documented classical failure mode: CAS aligned, no edit-set detector."""
    from research_v2.methods.ln10.baselines import predict_batch_c1

    preds = predict_batch_c1(_study_inputs(t3s_inputs), {"seed": 11})
    applied_conflicts = [
        p for p in preds
        if p.decision == APPLY and t3s_gold[p.case_id] == CONFLICT
    ]
    assert len(applied_conflicts) >= 18


def test_gate_isolation_a1_a3_stay_correct_on_stress_dataset(t3s_inputs, t3s_gold):
    """Removing reflection/ownership gates must NOT change conflict handling:
    the stress dataset isolates the concurrency mechanism."""
    from research_v2.methods.ln10.ablations import predict_batch_a1, predict_batch_a3

    for fn in (predict_batch_a1, predict_batch_a3):
        preds = fn(_study_inputs(t3s_inputs), {"seed": 11})
        assert all(p.decision == t3s_gold[p.case_id] for p in preds)


def test_t3s_no_oracle_material_in_inputs(t3s_inputs):
    from research_v2.contracts.types import FORBIDDEN_INPUT_KEYS

    for row in t3s_inputs:
        inp = row["input"]
        leaked = set(inp) & FORBIDDEN_INPUT_KEYS
        assert not leaked, f"{row['case_id']}: leaked {leaked}"
        assert set(row) == {"study_id", "case_id", "group_id", "input", "input_sha256"}
