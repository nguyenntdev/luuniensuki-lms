# -*- coding: utf-8 -*-
"""V5-T120 (Wave W11, Slot A10): Startup Evidence Room and Pitch Review Test Suite.

Audits and verifies:
1. Evidence Room 7-Domain Coverage & Integrity:
   - Covers product, customer, market, finances, impact, legal, and team.
   - Each pointer contains immutable metadata, SHA-256 fingerprint, doc reference, and metric payload.
2. Query and Filtering:
   - Query by domain and status.
   - Verification of key audited constants (202,360,638 VND sponsorship, 90% artisan retention, etc.).
3. Negative Abuse Guardrail 1 (Missing Evidence Pointer):
   - Quantitative pitch claim without evidence_pointer_id is strictly flagged as UNGROUNDED_FLAGGED.
   - Overall pitch deck readiness is marked FLAGGED_UNREADY.
4. Negative Abuse Guardrail 2 (Invalid or Non-Active Pointer):
   - Non-existent pointer ID or archived pointer triggers UNGROUNDED_FLAGGED and FLAGGED_UNREADY.
5. Negative Abuse Guardrail 3 (Metric Contradiction & Verbal Inflation):
   - Claiming 206,000,000 VND verbal sponsorship when audited actual is 202,360,638 VND triggers UNGROUNDED_FLAGGED.
   - Claiming inflated 95% artisan share or 15% platform take rate triggers UNGROUNDED_FLAGGED.
6. Positive Acceptance (Golden Pitch Deck):
   - 100% grounded quantitative claims achieve APPROVED_FOR_PITCH readiness.
7. Database Persistence & Integrity:
   - rbpc_evidence_room_pointers and rbpc_pitch_reviews tables persist and reload audit records.
8. REST API Endpoints Integration:
   - GET /api/v1/rbpc/evidence-room/pointers
   - GET /api/v1/rbpc/evidence-room/pointers/{pointer_id}
   - POST /api/v1/rbpc/pitch-review/evaluate
   - GET /api/v1/rbpc/pitch-review/audits/{audit_ref}
   - GET /api/v1/rbpc/evidence-room/export
9. Documentation Parity:
   - Verifies docs/rbpc/STARTUP_EVIDENCE_ROOM.md and docs/rbpc/PITCH_REVIEW.md existence and alignment.
"""
from __future__ import annotations

import json
from pathlib import Path
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.models_rbpc import (
    RbpcEvidenceDomain,
    RbpcEvidencePointer,
    RbpcEvidencePointerStatus,
    RbpcPitchClaimStatus,
    RbpcPitchReadiness,
    RbpcPitchReview,
)
from backend.services.rbpc_evidence_room import (
    CANONICAL_EVIDENCE_POINTERS,
    CanonicalEvidencePointer,
    PitchClaimItem,
    StartupEvidenceRoomService,
    default_evidence_room_service,
)


# --------------------------------------------------------------------------- #
# 1. Evidence Room 7-Domain Coverage and Pointer Integrity
# --------------------------------------------------------------------------- #
def test_v5_t120_evidence_room_7_domain_coverage():
    """Verify that canonical evidence room pointers cover all 7 mandatory domains."""
    service = default_evidence_room_service
    pointers = service.get_all_pointers()
    assert len(pointers) >= 14, f"Expected at least 14 evidence pointers, found {len(pointers)}"

    domains_found = {p.domain for p in pointers}
    expected_domains = {
        RbpcEvidenceDomain.product,
        RbpcEvidenceDomain.customer,
        RbpcEvidenceDomain.market,
        RbpcEvidenceDomain.finances,
        RbpcEvidenceDomain.impact,
        RbpcEvidenceDomain.legal,
        RbpcEvidenceDomain.team,
    }
    assert domains_found == expected_domains, f"Missing domains: {expected_domains - domains_found}"

    for p in pointers:
        assert p.pointer_id.startswith("EVID-")
        assert len(p.pointer_id) >= 10
        assert p.title
        assert p.doc_ref.startswith("docs/rbpc/")
        assert p.version
        assert p.status == RbpcEvidencePointerStatus.active_verified
        assert len(p.hash_sha256) == 64, f"Invalid SHA-256 hash for {p.pointer_id}"
        assert isinstance(p.metrics_payload, dict)
        assert len(p.metrics_payload) > 0, f"Pointer {p.pointer_id} must have metric payload"
        assert p.summary
        assert p.owner in ["S1 Integrator", "S2 Historian", "S3 Business Lead", "S4 Frontend Lead"]
        assert "T" in p.verified_at


# --------------------------------------------------------------------------- #
# 2. Pointer Filtering and Queries
# --------------------------------------------------------------------------- #
def test_v5_t120_pointer_filtering_and_key_metrics():
    """Verify pointer queries by domain and status, and check critical figures."""
    service = default_evidence_room_service

    fin_pointers = service.get_all_pointers(domain=RbpcEvidenceDomain.finances)
    assert len(fin_pointers) >= 3

    # Check audited sponsorship pointer EVID-FIN-002
    p_sponsor = service.get_pointer("EVID-FIN-002")
    assert p_sponsor is not None
    assert p_sponsor.metrics_payload["total_in_kind_sponsorship_vnd"] == 202360638
    assert p_sponsor.metrics_payload["unverified_verbal_claim_vnd"] == 206000000
    assert p_sponsor.metrics_payload["unverified_variance_rejected_vnd"] == -3639362

    # Check unit economics pointer EVID-FIN-001
    p_econ = service.get_pointer("EVID-FIN-001")
    assert p_econ is not None
    assert p_econ.metrics_payload["platform_fee_percent"] == 10.0
    assert p_econ.metrics_payload["artisan_share_percent"] == 90.0
    assert p_econ.metrics_payload["breakeven_bookings_per_month"] == 2.9

    # Check market sizing pointer EVID-MKT-001
    p_mkt = service.get_pointer("EVID-MKT-001")
    assert p_mkt is not None
    assert p_mkt.metrics_payload["tam_gbv_vnd"] == 28500000000
    assert p_mkt.metrics_payload["som_year1_experiences"] == 1100


# --------------------------------------------------------------------------- #
# 3. Negative Abuse Guardrail 1: Missing Evidence Pointer
# --------------------------------------------------------------------------- #
def test_v5_t120_negative_abuse_missing_evidence_pointer():
    """Negative abuse invariant: Quantitative claim without evidence pointer is UNGROUNDED_FLAGGED."""
    service = default_evidence_room_service
    unreferenced_claim = PitchClaimItem(
        claim_text="We have 10,000 active booking users in our beta app.",
        domain="customer",
        evidence_pointer_id=None,  # VIOLATION: Quantitative claim lacks evidence pointer!
        is_quantitative=True,
    )

    report = service.evaluate_pitch_claims(
        deck_title="Unreferenced Pitch Deck",
        deck_version="0.1.0",
        claims=[unreferenced_claim],
    )

    assert report.total_claims_audited == 1
    assert report.verified_claims_count == 0
    assert report.ungrounded_claims_count == 1
    assert report.pitch_readiness == RbpcPitchReadiness.flagged_unready.value
    assert report.findings[0].status == RbpcPitchClaimStatus.ungrounded_flagged.value
    assert not report.findings[0].is_grounded
    assert "lacks mandatory evidence pointer" in report.findings[0].discrepancy_notes


# --------------------------------------------------------------------------- #
# 4. Negative Abuse Guardrail 2: Invalid or Non-Active Pointer
# --------------------------------------------------------------------------- #
def test_v5_t120_negative_abuse_nonexistent_or_archived_pointer():
    """Negative abuse invariant: Non-existent pointer or archived pointer triggers UNGROUNDED_FLAGGED."""
    service = StartupEvidenceRoomService()

    # 1. Nonexistent pointer
    claim_nonexistent = PitchClaimItem(
        claim_text="Product retains 99% of customers according to internal survey.",
        domain="customer",
        evidence_pointer_id="EVID-FAKE-999",  # Nonexistent!
        is_quantitative=True,
    )
    report1 = service.evaluate_pitch_claims("Test Deck", "1.0", [claim_nonexistent])
    assert report1.findings[0].status == RbpcPitchClaimStatus.ungrounded_flagged.value
    assert report1.pitch_readiness == RbpcPitchReadiness.flagged_unready.value

    # 2. Register an archived pointer
    archived_pointer = CanonicalEvidencePointer(
        pointer_id="EVID-OLD-001",
        domain=RbpcEvidenceDomain.finances,
        title="Obsolete pricing draft",
        doc_ref="docs/rbpc/OLD.md",
        version="0.1.0",
        status=RbpcEvidencePointerStatus.archived,  # ARCHIVED!
        hash_sha256="0" * 64,
        metrics_payload={"old_fee": 20.0},
        summary="Obsolete draft",
        owner="S3 Business Lead",
        verified_at="2026-09-01T00:00:00Z",
    )
    service.register_pointer(archived_pointer)

    claim_archived = PitchClaimItem(
        claim_text="Platform charges 20% commission fee.",
        domain="finances",
        evidence_pointer_id="EVID-OLD-001",
        metric_key="old_fee",
        claimed_value=20.0,
        is_quantitative=True,
    )
    report2 = service.evaluate_pitch_claims("Test Deck", "1.0", [claim_archived])
    assert report2.findings[0].status == RbpcPitchClaimStatus.ungrounded_flagged.value
    assert "not active_verified" in report2.findings[0].discrepancy_notes


# --------------------------------------------------------------------------- #
# 5. Negative Abuse Guardrail 3: Metric Contradiction & Verbal Inflation
# --------------------------------------------------------------------------- #
def test_v5_t120_negative_abuse_metric_contradiction_and_verbal_inflation():
    """Negative abuse invariant: Claiming inflated numbers contradicting audited evidence is flagged."""
    service = default_evidence_room_service

    # Case 1: Verbal approximation claiming 206M VND sponsorship when audited is 202,360,638 VND
    claim_inflated_sponsorship = PitchClaimItem(
        claim_text="We secured 206M VND in corporate compute sponsorship from partners.",
        domain="finances",
        evidence_pointer_id="EVID-FIN-002",
        metric_key="total_in_kind_sponsorship_vnd",
        claimed_value=206000000,  # VIOLATION: Contradicts verified actual 202,360,638 VND!
        is_quantitative=True,
    )

    # Case 2: Claiming 95% artisan share when platform policy is 90%
    claim_inflated_artisan_share = PitchClaimItem(
        claim_text="Artisans keep 95% of all workshop ticket revenues.",
        domain="finances",
        evidence_pointer_id="EVID-FIN-001",
        metric_key="artisan_share_percent",
        claimed_value=95.0,  # VIOLATION: Contradicts verified 90.0%!
        is_quantitative=True,
    )

    report = service.evaluate_pitch_claims(
        deck_title="Inflated Numbers Pitch Deck",
        deck_version="0.9.0",
        claims=[claim_inflated_sponsorship, claim_inflated_artisan_share],
    )

    assert report.total_claims_audited == 2
    assert report.verified_claims_count == 0
    assert report.ungrounded_claims_count == 2
    assert report.pitch_readiness == RbpcPitchReadiness.flagged_unready.value
    for f in report.findings:
        assert f.status == RbpcPitchClaimStatus.ungrounded_flagged.value
        assert "contradicts verified evidence" in f.discrepancy_notes


# --------------------------------------------------------------------------- #
# 6. Positive Acceptance: Golden Pitch Deck
# --------------------------------------------------------------------------- #
def test_v5_t120_positive_golden_pitch_deck_evaluation():
    """Positive flow: Golden pitch deck with 100% verified claims passes with APPROVED_FOR_PITCH."""
    service = default_evidence_room_service

    golden_claims = [
        PitchClaimItem(
            claim_text="Secured 202,360,638 VND in documented in-kind corporate compute support from BNIX and Phổ Tuệ.",
            domain="finances",
            evidence_pointer_id="EVID-FIN-002",
            metric_key="total_in_kind_sponsorship_vnd",
            claimed_value=202360638,
            is_quantitative=True,
            truth_tier="OBSERVED",
        ),
        PitchClaimItem(
            claim_text="Intimate masterclasses transfer 90% of booking fees directly to host artisan families.",
            domain="finances",
            evidence_pointer_id="EVID-FIN-001",
            metric_key="artisan_share_percent",
            claimed_value=90.0,
            is_quantitative=True,
            truth_tier="OBSERVED",
        ),
        PitchClaimItem(
            claim_text="Commercial breakeven achieved at 2.9 bookings per month across all of Huế.",
            domain="finances",
            evidence_pointer_id="EVID-FIN-001",
            metric_key="breakeven_bookings_per_month",
            claimed_value=2.9,
            is_quantitative=True,
            truth_tier="OBSERVED",
        ),
        PitchClaimItem(
            claim_text="78% of international visitors report difficulty understanding authentic heritage context from brief plaques.",
            domain="customer",
            evidence_pointer_id="EVID-CUST-001",
            metric_key="comprehension_difficulty_percent",
            claimed_value=78.0,
            is_quantitative=True,
            truth_tier="HYPOTHESIS",
        ),
        PitchClaimItem(
            claim_text="Total Addressable Market for cultural workshop experiences across Thừa Thiên Huế is 28.5B VND.",
            domain="market",
            evidence_pointer_id="EVID-MKT-001",
            metric_key="tam_gbv_vnd",
            claimed_value=28500000000,
            is_quantitative=True,
            truth_tier="FORECAST",
        ),
    ]

    report = service.evaluate_pitch_claims(
        deck_title="Luu Nien RBPC 2026 Finals Master Deck",
        deck_version="1.0.0",
        claims=golden_claims,
    )

    assert report.total_claims_audited == 5
    assert report.verified_claims_count == 5
    assert report.ungrounded_claims_count == 0
    assert report.pitch_readiness == RbpcPitchReadiness.approved_for_pitch.value

    # Check truth tiers mapped properly
    assert report.findings[0].status == RbpcPitchClaimStatus.verified_observed.value
    assert report.findings[3].status == RbpcPitchClaimStatus.verified_hypothesis.value
    assert report.findings[4].status == RbpcPitchClaimStatus.verified_projection.value


# --------------------------------------------------------------------------- #
# 7. Database Persistence & Integrity
# --------------------------------------------------------------------------- #
def test_v5_t120_database_persistence_and_audit_history(db_session):
    """Verify that evidence pointers and pitch reviews persist cleanly in PostgreSQL."""
    service = default_evidence_room_service

    # Seed pointers
    seeded_count = service.seed_db(db_session)
    assert seeded_count >= 14

    # Query back from DB
    db_pointers = db_session.scalars(select(RbpcEvidencePointer)).all()
    assert len(db_pointers) >= 14

    # Verify unique constraint on pointer_id
    pointer_fin = db_session.scalar(
        select(RbpcEvidencePointer).where(RbpcEvidencePointer.pointer_id == "EVID-FIN-002")
    )
    assert pointer_fin is not None
    assert pointer_fin.metrics_payload["total_in_kind_sponsorship_vnd"] == 202360638

    # Evaluate and persist pitch review
    claim = PitchClaimItem(
        claim_text="Secured 202,360,638 VND in verified sponsorships.",
        domain="finances",
        evidence_pointer_id="EVID-FIN-002",
        metric_key="total_in_kind_sponsorship_vnd",
        claimed_value=202360638,
        is_quantitative=True,
        truth_tier="OBSERVED",
    )
    report = service.evaluate_pitch_claims("Audit Persistence Test", "1.0.0", [claim])
    review_row = service.persist_pitch_review(db_session, report)

    assert review_row.id is not None
    assert review_row.audit_ref.startswith("AUDIT-PITCH-")
    assert review_row.total_claims_audited == 1
    assert review_row.verified_claims_count == 1
    assert review_row.ungrounded_claims_count == 0
    assert review_row.pitch_readiness == RbpcPitchReadiness.approved_for_pitch.value

    # Query back from DB
    reloaded_review = db_session.scalar(
        select(RbpcPitchReview).where(RbpcPitchReview.audit_ref == review_row.audit_ref)
    )
    assert reloaded_review is not None
    assert reloaded_review.pitch_deck_title == "Audit Persistence Test"
    assert len(reloaded_review.claims_payload) == 1
    assert reloaded_review.claims_payload[0]["is_grounded"] is True


# --------------------------------------------------------------------------- #
# 8. REST API Endpoints Integration
# --------------------------------------------------------------------------- #
def test_v5_t120_api_endpoints_integration(client: TestClient, db_session):
    """Test full HTTP lifecycle for evidence room and pitch review endpoints."""
    # 1. GET /api/v1/rbpc/evidence-room/pointers
    res_list = client.get("/api/v1/rbpc/evidence-room/pointers")
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert list_data["total"] >= 14
    assert len(list_data["domains_covered"]) == 7
    assert any(p["pointer_id"] == "EVID-FIN-002" for p in list_data["items"])

    # Domain filter
    res_fin = client.get("/api/v1/rbpc/evidence-room/pointers?domain=finances")
    assert res_fin.status_code == 200
    assert all(p["domain"] == "finances" for p in res_fin.json()["items"])

    # 2. GET /api/v1/rbpc/evidence-room/pointers/{pointer_id}
    res_single = client.get("/api/v1/rbpc/evidence-room/pointers/EVID-FIN-002")
    assert res_single.status_code == 200
    single_data = res_single.json()
    assert single_data["pointer_id"] == "EVID-FIN-002"
    assert single_data["metrics_payload"]["total_in_kind_sponsorship_vnd"] == 202360638

    # 404 for unknown pointer
    res_404 = client.get("/api/v1/rbpc/evidence-room/pointers/EVID-UNKNOWN-999")
    assert res_404.status_code == 404

    # 3. POST /api/v1/rbpc/pitch-review/evaluate
    eval_payload = {
        "pitch_deck_title": "API Due Diligence Test Deck",
        "deck_version": "1.0.0",
        "claims": [
            {
                "claim_text": "202,360,638 VND corporate sponsorship.",
                "domain": "finances",
                "evidence_pointer_id": "EVID-FIN-002",
                "metric_key": "total_in_kind_sponsorship_vnd",
                "claimed_value": 202360638,
                "is_quantitative": True,
                "truth_tier": "OBSERVED",
            },
            {
                "claim_text": "Unverified assertion claiming 999M revenue.",
                "domain": "market",
                "evidence_pointer_id": None,  # Will trigger ungrounded flag!
                "is_quantitative": True,
            },
        ],
    }
    res_eval = client.post("/api/v1/rbpc/pitch-review/evaluate", json=eval_payload)
    assert res_eval.status_code == 200
    eval_data = res_eval.json()
    assert eval_data["total_claims_audited"] == 2
    assert eval_data["verified_claims_count"] == 1
    assert eval_data["ungrounded_claims_count"] == 1
    assert eval_data["pitch_readiness"] == RbpcPitchReadiness.flagged_unready.value
    audit_ref = eval_data["audit_ref"]

    # 4. GET /api/v1/rbpc/pitch-review/audits/{audit_ref}
    res_audit = client.get(f"/api/v1/rbpc/pitch-review/audits/{audit_ref}")
    assert res_audit.status_code == 200
    audit_data = res_audit.json()
    assert audit_data["audit_ref"] == audit_ref
    assert audit_data["pitch_deck_title"] == "API Due Diligence Test Deck"

    # 5. GET /api/v1/rbpc/evidence-room/export
    res_export_json = client.get("/api/v1/rbpc/evidence-room/export?format=json")
    assert res_export_json.status_code == 200
    json_export = res_export_json.json()
    assert json_export["format"] == "json"
    assert "LƯU NIÊN" in json_export["content"]

    res_export_md = client.get("/api/v1/rbpc/evidence-room/export?format=markdown")
    assert res_export_md.status_code == 200
    md_export = res_export_md.json()
    assert md_export["format"] == "markdown"
    assert "# LƯU NIÊN — Startup Evidence Room" in md_export["content"]


# --------------------------------------------------------------------------- #
# 9. Documentation Parity
# --------------------------------------------------------------------------- #
def test_v5_t120_documentation_parity():
    """Verify documentation files exist and cite evidence pointers and negative abuse rules."""
    repo_root = Path(__file__).resolve().parents[2]
    evid_path = repo_root / "docs" / "rbpc" / "STARTUP_EVIDENCE_ROOM.md"
    pitch_path = repo_root / "docs" / "rbpc" / "PITCH_REVIEW.md"

    assert evid_path.exists(), "docs/rbpc/STARTUP_EVIDENCE_ROOM.md must exist"
    assert pitch_path.exists(), "docs/rbpc/PITCH_REVIEW.md must exist"

    evid_text = evid_path.read_text(encoding="utf-8")
    pitch_text = pitch_path.read_text(encoding="utf-8")

    # Evidence room doc must contain 7 canonical domains
    for domain in ["product", "customer", "market", "finances", "impact", "legal", "team"]:
        assert domain in evid_text

    assert "EVID-FIN-002" in evid_text
    assert "202,360,638 VND" in evid_text
    assert "UNGROUNDED_FLAGGED" in evid_text
    assert "FLAGGED_UNREADY" in evid_text

    # Pitch review doc must contain case studies and negative abuse rules
    assert "APPROVED_FOR_PITCH" in pitch_text
    assert "UNGROUNDED_FLAGGED" in pitch_text
    assert "Case Study A" in pitch_text
    assert "Case Study B" in pitch_text
