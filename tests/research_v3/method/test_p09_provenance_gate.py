"""P09 core gate/policy behavior on synthetic fixtures (required negative cases)."""
from __future__ import annotations

import pytest

from p09_helpers import GUID, make_claim, make_corpus, make_source
from research_v3.methods.p09 import (
    Claim,
    Locator,
    ProvenanceCorpus,
    ProvenanceError,
    SourceRef,
    SurfaceDecision,
    propose_surface,
    verify_claim,
)


# ---------------------------------------------------------------- construction


def test_unverified_claim_is_withheld_with_explicit_abstention():
    claim = make_claim(epistemic="unverified")
    corpus = make_corpus()
    decision = propose_surface(claim, corpus)
    assert decision.decision == "abstain_unverified"
    assert decision.epistemic_badge == "unverified"
    assert decision.evidence_ids == ()
    assert decision.citation is None
    assert "fail_closed_gate" in decision.reason_codes


def test_disputed_claim_is_withheld_too():
    claim = make_claim(epistemic="disputed")
    decision = propose_surface(claim, make_corpus())
    assert decision.decision == "abstain_unverified"


def test_claim_with_valid_verified_source_is_surfaced_with_citation():
    claim = make_claim(epistemic="verified")
    corpus = make_corpus()
    decision = propose_surface(claim, corpus)
    assert decision.decision == "surface"
    assert decision.epistemic_badge == "verified"
    assert decision.evidence_ids == ("Q975568",)
    assert decision.citation is not None
    assert decision.citation["source_id"] == "Q975568"
    assert decision.citation["locator_kind"] == "statement_guid"
    assert decision.citation["locator_value"] == GUID
    assert decision.citation["license"] == "CC0-1.0"


def test_nonexistent_source_id_claim_is_rejected():
    ghost = make_source(source_id="Q999999999", title="Non-existent source")
    claim = make_claim(
        source=ghost, locator=Locator("Q999999999", "property", "P571")
    )
    corpus = make_corpus()
    result = verify_claim(claim, corpus)
    assert result.outcome == "invalid"
    assert "nonexistent_source_id" in result.reason_codes
    decision = propose_surface(claim, corpus)
    assert decision.decision == "reject_invalid_source"


def test_malformed_statement_guid_is_rejected():
    # Malformed GUIDs are rejected at construction (belt) and the gate rejects
    # any well-formed-but-unresolvable GUID (braces; see forged-GUID test).
    with pytest.raises(ProvenanceError):
        make_claim(
            locator=Locator("Q975568", "statement_guid", "NOT-A-GUID"), epistemic="verified"
        )


def test_forged_but_wellformed_guid_that_does_not_resolve_is_rejected():
    forged = "Q975568$00000000-0000-0000-0000-000000000000"
    claim = make_claim(
        locator=Locator("Q975568", "statement_guid", forged), epistemic="verified"
    )
    corpus = make_corpus()
    result = verify_claim(claim, corpus)
    assert result.outcome == "invalid"
    assert "unresolvable_statement_guid" in result.reason_codes


def test_guid_qid_prefix_mismatch_is_rejected():
    claim = make_claim(
        locator=Locator("Q975568", "statement_guid", "Q1$11111111-2222-4333-8444-555555555555"),
        epistemic="verified",
    )
    result = verify_claim(claim, make_corpus())
    assert result.outcome == "invalid"
    assert "guid_qid_mismatch" in result.reason_codes


def test_locator_source_mismatch_is_rejected():
    claim = make_claim(
        locator=Locator("Q999999998", "property", "P571"), epistemic="verified"
    )
    result = verify_claim(claim, make_corpus())
    assert result.outcome == "invalid"
    assert result.reason_codes[0] in {"nonexistent_source_id", "claim_source_locator_mismatch", "invalid_locator"}


def test_claim_source_and_locator_source_divergence_is_rejected():
    corpus = make_corpus()
    other = make_source(source_id="Q888888888", title="Other real source")
    corpus.add_source(other, frozenset())
    claim = make_claim(
        source=make_source(),  # declared Q975568
        locator=Locator("Q888888888", "property", "P571"),  # locator points elsewhere
        epistemic="verified",
    )
    result = verify_claim(claim, corpus)
    assert result.outcome == "invalid"
    assert "claim_source_locator_mismatch" in result.reason_codes


def test_missing_rights_statement_fails_gate_never_surfaces():
    no_rights = make_source(license="")
    corpus = ProvenanceCorpus()
    corpus.add_source(no_rights, frozenset({GUID}))
    claim = make_claim(source=no_rights, locator=Locator(no_rights.source_id, "statement_guid", GUID))
    result = verify_claim(claim, corpus)
    assert result.outcome == "invalid"
    assert "missing_rights_statement" in result.reason_codes
    assert propose_surface(claim, corpus).decision == "reject_invalid_source"


def test_tampered_license_in_declared_source_is_rejected():
    corpus = make_corpus()
    tampered = make_source(license="CC-BY-4.0")
    claim = make_claim(source=tampered, epistemic="verified")
    result = verify_claim(claim, corpus)
    assert result.outcome == "invalid"
    assert "source_registry_mismatch" in result.reason_codes


def test_locator_kinds_are_validated_structurally():
    bad = [
        ("property", "not-a-property"),
        ("page", "-3"),
        ("page", "abc"),
        ("section", "   "),
        ("statement_kind_typo", "x"),
    ]
    for kind, value in bad:
        with pytest.raises(ProvenanceError):
            Locator("Q975568", kind, value)
    # Valid structural forms must construct cleanly.
    for kind, value in [("property", "P571"), ("page", "12"), ("section", "Origin")]:
        Locator("Q975568", kind, value)


def test_invalid_epistemic_badge_rejected_at_construction():
    with pytest.raises(ProvenanceError):
        make_claim(epistemic="expert_consensus")  # no fabricated badges


def test_invalid_sha256_rejected_at_construction():
    with pytest.raises(ProvenanceError):
        make_source(sha256="deadbeef")


# ---------------------------------------------------------------- determinism


def test_gate_and_policy_are_deterministic():
    corpus = make_corpus()
    claims = [
        make_claim("D1", epistemic="verified"),
        make_claim("D2", epistemic="unverified"),
        make_claim("D3", epistemic="verified", locator=Locator("Q975568", "property", "P625")),
        make_claim("D4", epistemic="verified", source=make_source(source_id="Q000000")),
    ]
    for claim in claims:
        r1 = verify_claim(claim, corpus)
        r2 = verify_claim(claim, corpus)
        assert r1.to_dict() == r2.to_dict()
        d1 = propose_surface(claim, corpus)
        d2 = propose_surface(claim, corpus)
        assert d1.to_dict() == d2.to_dict()


def test_surface_decision_cannot_carry_unverified_badge():
    with pytest.raises(ProvenanceError):
        SurfaceDecision(
            claim_id="X",
            method_id="proposed",
            method_version="v",
            decision="surface",
            epistemic_badge="unverified",
            reason_codes=(),
            evidence_ids=("Q1",),
        )


def test_abstain_decision_cannot_carry_citation():
    with pytest.raises(ProvenanceError):
        SurfaceDecision(
            claim_id="X",
            method_id="proposed",
            method_version="v",
            decision="abstain_unverified",
            epistemic_badge="unverified",
            reason_codes=(),
            evidence_ids=(),
            citation={"source_id": "Q1"},
        )
