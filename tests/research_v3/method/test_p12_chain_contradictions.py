"""P12 tests — stance contradiction detection (V4) and append-only hash-chain
tamper detection (V5), plus adversarial mutations (spec §3.5)."""
from __future__ import annotations

import copy

import pytest

from research_v3.methods.p12.ledger import (
    ClaimLedger,
    LedgerError,
    LedgerEvent,
    audit_corpus,
    verify_chain,
)
from test_p12_helpers import make_claim, make_registry, ts_provider  # noqa: F401


def _two_source_contradiction_claims():
    text = "Contradictory fixture claim (test only)."
    return [
        make_claim(claim_id="c-sup", claim_text=text, stance="supports",
                   source_id="src-fixture-primary"),
        make_claim(claim_id="c-ref", claim_text=text, stance="refutes",
                   source_id="src-fixture-secondary"),
    ]


def test_support_vs_refute_from_different_sources_is_contradiction():
    report = audit_corpus(
        _two_source_contradiction_claims(), make_registry(),
        timestamp_provider=ts_provider,
    )
    assert report["contradiction_count"] == 1
    finding = report["contradictions"][0]
    assert finding["type"] == "cross_source_conflict"
    assert finding["supporting_sources"] == ["src-fixture-primary"]
    assert finding["refuting_sources"] == ["src-fixture-secondary"]
    assert finding["resolution"] == "HUMAN_ADJUDICATION_BLOCKED"


def test_same_source_support_and_refute_is_transcription_defect():
    """The same resolvable source carrying both stances for one claim_text is a
    transcription defect: detected and routed to human adjudication, never
    silently ignored (it is NOT a cross-source conflict)."""
    text = "Same-source opposite stances (test only)."
    claims = [
        make_claim(claim_id="c1", claim_text=text, stance="supports",
                   source_id="src-fixture-primary"),
        make_claim(claim_id="c2", claim_text=text, stance="refutes",
                   source_id="src-fixture-primary"),
    ]
    report = audit_corpus(claims, make_registry(), timestamp_provider=ts_provider)
    assert report["contradiction_count"] == 1
    finding = report["contradictions"][0]
    assert finding["type"] == "same_source_transcription_defect"
    assert finding["conflicted_sources"] == ["src-fixture-primary"]
    assert finding["resolution"] == "HUMAN_ADJUDICATION_BLOCKED"


def test_contradiction_with_unresolvable_refuting_source_is_ignored():
    text = "Contradiction attempt with bad source (test only)."
    claims = [
        make_claim(claim_id="c-sup", claim_text=text, stance="supports",
                   source_id="src-fixture-primary"),
        make_claim(claim_id="c-ref", claim_text=text, stance="refutes",
                   source_id="src-unknown"),
    ]
    report = audit_corpus(claims, make_registry(), timestamp_provider=ts_provider)
    assert report["contradiction_count"] == 0
    assert "c-ref" in report["rejected_claims"]  # bad source still rejected


# ---------------------------------------------------------------------------
# Append-only hash chain
# ---------------------------------------------------------------------------

def _build_ledger(n: int = 3):
    ledger_claims = [make_claim(claim_id=f"claim-{i:02d}", claim_text=f"fixture {i}") for i in range(n)]
    report = audit_corpus(ledger_claims, make_registry(), timestamp_provider=ts_provider)
    return report


def _to_events(exported: list[dict]) -> list[LedgerEvent]:
    return [LedgerEvent(**e) for e in exported]


def test_chain_verifies_when_intact():
    report = _build_ledger()
    chain = verify_chain(_to_events(report["ledger_events"]))
    assert chain["status"] == "PASS"
    assert chain["chain_head"] == report["chain"]["chain_head"]


def test_tampered_payload_is_detected():
    report = _build_ledger()
    events = copy.deepcopy(report["ledger_events"])
    events[1]["payload"]["claim_text"] = "TAMPERED HISTORY"
    with pytest.raises(LedgerError, match="entry_hash mismatch"):
        verify_chain(_to_events(events))


def test_tampered_hash_link_is_detected():
    report = _build_ledger()
    events = copy.deepcopy(report["ledger_events"])
    events[2]["prev_hash"] = "0" * 64
    with pytest.raises(LedgerError, match="does not link"):
        verify_chain(_to_events(events))


def test_sequence_break_is_detected():
    report = _build_ledger()
    events = copy.deepcopy(report["ledger_events"])
    events[1]["seq"] = 99
    with pytest.raises(LedgerError, match="sequence break"):
        verify_chain(_to_events(events))


def test_deleted_middle_event_is_detected():
    report = _build_ledger(4)
    events = copy.deepcopy(report["ledger_events"])
    del events[1]
    with pytest.raises(LedgerError):
        verify_chain(_to_events(events))


def test_ledger_append_is_monotonic_and_rejection_of_time_travel():
    ledger = ClaimLedger(timestamp_provider=lambda: "2026-11-15T00:00:05Z")
    ledger.append(make_claim(claim_id="a"))
    ledger.timestamp_provider = lambda: "2026-11-15T00:00:01Z"  # time travel
    with pytest.raises(LedgerError, match="monotonic"):
        ledger.append(make_claim(claim_id="b"))


def test_chain_digest_changes_on_any_mutation():
    r1 = _build_ledger()
    r2 = _build_ledger()
    assert r1["chain_digest"] == r2["chain_digest"]  # determinism
    events = copy.deepcopy(r1["ledger_events"])
    events[0]["timestamp_utc"] = "2026-01-01T00:00:00Z"
    ledger = ClaimLedger()
    for e in events:
        ledger.events.append(LedgerEvent(**e))
    assert ledger.chain_digest() != r1["chain_digest"]


def test_invalid_action_rejected_at_event_level():
    with pytest.raises(LedgerError):
        LedgerEvent(seq=1, timestamp_utc="2026-11-15T00:00:00Z", action="rewrite",
                    payload={}, prev_hash="GENESIS")


def test_claim_entry_mutation_attempts_fail_frozen():
    """frozen dataclass: history cannot be rewritten in place."""
    claim = make_claim()
    with pytest.raises(Exception):
        claim.claim_text = "rewritten"
