"""P12 tests — validator rejection paths (claim without source, bad source_id,
missing locator) and pass/abstain behaviour. Fixtures are synthetic; the real
read-only corpus is exercised separately in test_p12_corpus_audit.py."""
from __future__ import annotations

import pytest

from research_v3.methods.p12.ledger import (
    ABSTAIN,
    LedgerError,
    Locator,
    SourceRecord,
    ValidationVerdict,
    audit_corpus,
    validate_claim,
)
from test_p12_helpers import make_claim, make_registry


def test_claim_without_source_is_rejected():
    v = validate_claim(make_claim(source_id=None), make_registry())
    assert v.verdict == "REJECT"
    assert "missing_source" in v.failures


def test_claim_with_empty_source_string_is_rejected():
    v = validate_claim(make_claim(source_id=""), make_registry())
    assert v.verdict == "REJECT" and "missing_source" in v.failures


def test_claim_with_unresolvable_source_id_is_rejected():
    v = validate_claim(make_claim(source_id="src-does-not-exist"), make_registry())
    assert v.verdict == "REJECT"
    assert "unknown_source" in v.failures
    # must NOT also demand a locator for an unresolvable source (no invention)
    assert "missing_locator" not in v.failures


def test_claim_with_missing_locator_is_rejected():
    v = validate_claim(make_claim(locator=None), make_registry())
    assert v.verdict == "REJECT"
    assert "missing_locator" in v.failures


def test_locator_with_any_empty_part_is_rejected():
    with pytest.raises(LedgerError):
        Locator(edition="", volume="Quyển 1", page="Tờ 5a")
    with pytest.raises(LedgerError):
        Locator(edition="E", volume=" ", page="Tờ 5a")
    with pytest.raises(LedgerError):
        Locator(edition="E", volume="Q", page="")


def test_missing_locator_downgrade_mode_passes_only_provisional_claims():
    """fail_on_missing_locator=False models a registry edition that does not
    paginate: a resolvable provisional claim passes, an unknown source still
    rejects. No invention happens in either branch."""
    registry = {
        "src-fixture-primary": SourceRecord(
            "src-fixture-primary", "T", "royal_record", "E", "public_domain", "verified"
        )
    }
    v_unknown = validate_claim(make_claim(locator=None, source_id="src-nope"), {}, fail_on_missing_locator=False)
    v_unlocated = validate_claim(make_claim(locator=None), registry, fail_on_missing_locator=False)
    assert v_unknown.verdict == "REJECT"
    assert v_unlocated.verdict == "PASS"


def test_wellformed_provisional_claim_passes():
    v = validate_claim(make_claim(), make_registry())
    assert v.verdict == "PASS"
    assert v.failures == ()


def test_inherited_verified_status_routes_to_abstain_not_pass():
    """A claim *claiming* archival/expert/editor status is not machine-verified:
    the honest verdict is ABSTAIN routed to human review (P12-T19)."""
    for status in ("archival_primary", "expert_verified", "editor_reviewed"):
        v = validate_claim(make_claim(confidence_status=status), make_registry())
        assert v.verdict == ABSTAIN
        assert any("P12-T19" in n for n in v.notes)


def test_invalid_vocabulary_is_typed_failure():
    with pytest.raises(LedgerError):
        make_claim(stance="proves")
    with pytest.raises(LedgerError):
        make_claim(confidence_status="verified")  # legacy word, not in vocabulary
    with pytest.raises(LedgerError):
        make_claim(evidence_kind="tertiary")


def test_verdict_reject_requires_failure_code():
    with pytest.raises(LedgerError):
        ValidationVerdict("c1", "REJECT", ())


def test_undetermined_stance_never_contradicts():
    """V4: 'undetermined' is a first-class ABSTAIN-like stance, not a vote."""
    claims = [
        make_claim(claim_id="a", claim_text="Same text", stance="undetermined",
                   source_id="src-fixture-primary"),
        make_claim(claim_id="b", claim_text="Same text", stance="supports",
                   source_id="src-fixture-secondary"),
    ]
    report = audit_corpus(claims, make_registry(), timestamp_provider=lambda: "2026-11-15T00:00:00Z")
    assert report["contradiction_count"] == 0
