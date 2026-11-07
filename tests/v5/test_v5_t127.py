# -*- coding: utf-8 -*-
"""V5-T127 (Wave W12, Slot A07): Legal and Creator Agreement Sign-Off Test Suite.

Audits and verifies:
1. 5-Domain Legal & Creator Agreement Coverage:
   - Covers software_ip, photos_3d_rights, school_consent, artisan_agreement, consumer_tax_terms.
   - Each domain contains immutable metadata, signatory role, document reference,
     governing regulations, SHA-256 checksum, and approved status.
2. Master Compliance & Master Fingerprint:
   - All 5 domains evaluate to APPROVED_FOR_PRODUCTION.
   - Deterministic compound master SHA-256 fingerprint generated.
3. Negative Abuse Guardrail 1 (Missing / Unapproved Sign-Off Blocks Commerce):
   - Overriding any domain to pending, rejected, or revoked forces commerce_allowed=False
     and feature_flag_status="OFF" with BLOCKED_LEGAL_DEFECT.
4. Negative Abuse Guardrail 2 (Unapproved Assets Blocked & Barred from Commerce):
   - Speculative/fantasy geometry (SF-020) permanently rejected (status=rejected_accuracy).
   - Third-party 3D models strictly blocked from commercial workshop cards (status=blocked_commercial_context).
   - NoAI assets (SF-017) quarantined from AI ingestion and commercial use (status=blocked_noai).
   - Non-commercial assets (SF-010) blocked from commercial deployment (status=blocked_nc).
   - Unstated/missing licenses trigger needs_rights_review and require 2D fallback.
5. Negative Abuse Guardrail 3 (Unconsented or Revoked Artisan Consent Forces Feature Flag OFF):
   - Creator with pending_review or revoked consent strictly forces feature_flag_status="OFF"
     and commerce_allowed=False.
   - enforce_runtime_feature_flag sets FEATURE_FLAG_RBPC_COMMERCE_ENABLED to False.
6. Negative Abuse Guardrail 4 (Unapproved Assets Force Commerce Flag OFF):
   - Setting has_unapproved_assets=True strictly forces feature_flag_status="OFF".
7. Positive Acceptance Flow:
   - CC BY 4.0 models (SF-009, SF-011, SF-016) clear documentary embed gate.
   - Verified active artisan consent without unapproved assets clears commerce gate and permits feature flag ON.
8. REST API Endpoints Integration:
   - GET /api/v1/rbpc/legal/signoff-audit
   - POST /api/v1/rbpc/legal/evaluate-asset
   - POST /api/v1/rbpc/legal/evaluate-commerce-gate
9. Documentation Parity:
   - Verifies docs/rbpc/CONTENT_RIGHTS.md (§9) and docs/rbpc/LEGAL_COMPLIANCE_SIGN_OFF.md existence and alignment.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.services.feature_flags import (
    clear_runtime_overrides,
    is_feature_flag_enabled,
    set_runtime_override,
)
from backend.services.rbpc_legal_signoff import (
    CANONICAL_LEGAL_SIGNOFFS,
    LegalSignoffDomain,
    LegalSignoffRecord,
    LegalSignoffStatus,
    RbpcLegalSignoffService,
    default_legal_signoff_service,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def cleanup_overrides():
    clear_runtime_overrides()
    yield
    clear_runtime_overrides()


# --------------------------------------------------------------------------- #
# 1. 5-Domain Legal Sign-Off Coverage & Pointer Integrity
# --------------------------------------------------------------------------- #
def test_v5_t127_legal_signoff_5_domain_coverage():
    """Verify that canonical legal sign-offs cover all 5 mandatory domains."""
    service = default_legal_signoff_service
    records = service.get_all_records()
    assert len(records) == 5, f"Expected exactly 5 canonical legal sign-offs, found {len(records)}"

    domains_found = {r.domain for r in records}
    expected_domains = {
        LegalSignoffDomain.software_ip,
        LegalSignoffDomain.photos_3d_rights,
        LegalSignoffDomain.school_consent,
        LegalSignoffDomain.artisan_agreement,
        LegalSignoffDomain.consumer_tax_terms,
    }
    assert domains_found == expected_domains, f"Missing domains: {expected_domains - domains_found}"

    for r in records:
        assert r.signoff_ref.startswith("SIGNOFF-")
        assert len(r.signoff_ref) >= 12
        assert r.title
        assert r.status == LegalSignoffStatus.approved
        assert r.signatory_role
        assert r.signatory_name
        assert r.document_ref.startswith("docs/rbpc/")
        assert len(r.governing_regulations) >= 2
        assert len(r.checksum_sha256) == 64, f"Invalid SHA-256 hash for {r.signoff_ref}"
        assert "T" in r.signed_at
        assert r.summary
        assert len(r.conditions) >= 2


# --------------------------------------------------------------------------- #
# 2. Master Compliance & Fingerprint
# --------------------------------------------------------------------------- #
def test_v5_t127_master_compliance_and_fingerprint():
    """Verify master compliance calculation and compound SHA-256 fingerprint."""
    service = default_legal_signoff_service
    comp = service.verify_overall_legal_compliance()

    assert comp["all_approved"] is True
    assert comp["domains_count"] == 5
    assert comp["expected_domains_count"] == 5
    assert comp["missing_domains"] == []
    assert comp["compliance_verdict"] == "APPROVED_FOR_PRODUCTION"
    assert len(comp["master_fingerprint_sha256"]) == 64
    assert comp["status_by_domain"] == {
        "software_ip": "approved",
        "photos_3d_rights": "approved",
        "school_consent": "approved",
        "artisan_agreement": "approved",
        "consumer_tax_terms": "approved",
    }


# --------------------------------------------------------------------------- #
# 3. Negative Abuse Guardrail 1: Non-Approved Legal Sign-Off Blocks Commerce
# --------------------------------------------------------------------------- #
def test_v5_t127_negative_abuse_unapproved_signoff_blocks_commerce():
    """Negative abuse: If any legal sign-off is pending or revoked, commerce is strictly blocked."""
    service = default_legal_signoff_service

    # Test 1: Artisan agreement pending
    res1 = service.evaluate_commerce_gate(
        creator_consent_status="consented",
        has_unapproved_assets=False,
        signoff_status_override={LegalSignoffDomain.artisan_agreement: LegalSignoffStatus.pending},
    )
    assert res1["commerce_allowed"] is False
    assert res1["feature_flag_status"] == "OFF"
    assert res1["gate_verdict"] == "BLOCKED_LEGAL_DEFECT"
    assert "artisan_agreement" in res1["reason"]

    # Test 2: Consumer/Tax terms revoked
    res2 = service.evaluate_commerce_gate(
        creator_consent_status="consented",
        has_unapproved_assets=False,
        signoff_status_override={LegalSignoffDomain.consumer_tax_terms: LegalSignoffStatus.revoked},
    )
    assert res2["commerce_allowed"] is False
    assert res2["feature_flag_status"] == "OFF"
    assert res2["gate_verdict"] == "BLOCKED_LEGAL_DEFECT"
    assert "consumer_tax_terms" in res2["reason"]


# --------------------------------------------------------------------------- #
# 4. Negative Abuse Guardrail 2: Asset Clearance & Commercial Context
# --------------------------------------------------------------------------- #
def test_v5_t127_negative_abuse_asset_clearance_gates():
    """Negative abuse: Unapproved, NC, NoAI, inaccurate, or commercial 3D assets are rejected."""
    service = default_legal_signoff_service

    # Case A: Fantasy geometry (SF-020)
    sf020 = service.evaluate_asset_clearance({
        "id": "SF-020",
        "accuracy_grade": "rejected_inaccurate",
        "displayed_license": "NOT STATED",
    })
    assert sf020["is_cleared"] is False
    assert sf020["status"] == "rejected_accuracy"
    assert sf020["embed_allowed"] is False
    assert sf020["fallback_required"] is True
    assert "Speculative or fantasy geometry" in sf020["reason"]

    # Case B: Commercial workshop card prohibition (no 3D models on workshop cards)
    comm_3d = service.evaluate_asset_clearance({
        "id": "SF-009",
        "displayed_license": "CC BY",
        "accuracy_grade": "reference_checked_photogrammetry",
        "is_commercial_context": True,
    })
    assert comm_3d["is_cleared"] is False
    assert comm_3d["status"] == "blocked_commercial_context"
    assert comm_3d["commercial_use_allowed"] is False
    assert "Third-party 3D models are prohibited from commercial workshop cards" in comm_3d["reason"]

    # Case C: NoAI tag protection (SF-017)
    sf017 = service.evaluate_asset_clearance({
        "id": "SF-017",
        "displayed_license": "CC BY-NC-SA",
        "accuracy_grade": "reference_checked_lidar",
        "noai": True,
    })
    assert sf017["is_cleared"] is False
    assert sf017["status"] == "blocked_noai"
    assert sf017["ai_training_allowed"] is False

    # Case D: Non-commercial license (SF-010)
    sf010 = service.evaluate_asset_clearance({
        "id": "SF-010",
        "displayed_license": "CC BY-NC-SA",
        "accuracy_grade": "reference_checked_photogrammetry",
    })
    assert sf010["is_cleared"] is False
    assert sf010["status"] == "blocked_nc"

    # Case E: Missing license
    missing = service.evaluate_asset_clearance({
        "id": "SF-001",
        "displayed_license": "NOT STATED",
    })
    assert missing["is_cleared"] is False
    assert missing["status"] == "needs_rights_review"
    assert missing["fallback_required"] is True


# --------------------------------------------------------------------------- #
# 5. Negative Abuse Guardrail 3: Unconsented or Revoked Artisan Consent
# --------------------------------------------------------------------------- #
def test_v5_t127_negative_abuse_unconsented_artisan_keeps_flag_off():
    """Negative abuse: Unconsented or revoked artisan consent strictly keeps feature flag OFF."""
    service = default_legal_signoff_service

    # Revoked consent
    res_revoked = service.evaluate_commerce_gate(
        creator_consent_status="revoked",
        has_unapproved_assets=False,
    )
    assert res_revoked["commerce_allowed"] is False
    assert res_revoked["feature_flag_status"] == "OFF"
    assert res_revoked["gate_verdict"] == "BLOCKED_CONSENT_DEFECT"

    # Pending review consent
    res_pending = service.evaluate_commerce_gate(
        creator_consent_status="pending_review",
        has_unapproved_assets=False,
    )
    assert res_pending["commerce_allowed"] is False
    assert res_pending["feature_flag_status"] == "OFF"

    # Runtime enforcement strictly sets override to False
    allowed = service.enforce_runtime_feature_flag(
        creator_consent_status="revoked",
        has_unapproved_assets=False,
    )
    assert allowed is False
    assert is_feature_flag_enabled("FEATURE_FLAG_RBPC_COMMERCE_ENABLED") is False


# --------------------------------------------------------------------------- #
# 6. Negative Abuse Guardrail 4: Presence of Unapproved Assets Forces Flag OFF
# --------------------------------------------------------------------------- #
def test_v5_t127_negative_abuse_unapproved_assets_force_flag_off():
    """Negative abuse: Commercial listing with unapproved assets strictly keeps feature flag OFF."""
    service = default_legal_signoff_service

    res = service.evaluate_commerce_gate(
        creator_consent_status="consented",
        has_unapproved_assets=True,  # Violation!
    )
    assert res["commerce_allowed"] is False
    assert res["feature_flag_status"] == "OFF"
    assert res["gate_verdict"] == "BLOCKED_UNAPPROVED_ASSETS"

    allowed = service.enforce_runtime_feature_flag(
        creator_consent_status="consented",
        has_unapproved_assets=True,
    )
    assert allowed is False
    assert is_feature_flag_enabled("FEATURE_FLAG_RBPC_COMMERCE_ENABLED") is False


# --------------------------------------------------------------------------- #
# 7. Positive Acceptance: Cleared Asset & Active Consent
# --------------------------------------------------------------------------- #
def test_v5_t127_positive_acceptance_cleared_asset_and_commerce():
    """Positive flow: Approved CC BY asset and verified artisan consent pass all gates."""
    service = default_legal_signoff_service

    # 1. Asset clearance for documentary explore embed (SF-009)
    sf009 = service.evaluate_asset_clearance({
        "id": "SF-009",
        "displayed_license": "CC BY",
        "accuracy_grade": "reference_checked_photogrammetry",
        "noai": False,
        "is_commercial_context": False,
    })
    assert sf009["is_cleared"] is True
    assert sf009["status"] == "candidate_embed"
    assert sf009["embed_allowed"] is True
    assert sf009["fallback_required"] is False

    # 2. Commerce gate with active consent and clean assets
    comm_cleared = service.evaluate_commerce_gate(
        creator_consent_status="consented",
        has_unapproved_assets=False,
    )
    assert comm_cleared["commerce_allowed"] is True
    assert comm_cleared["feature_flag_status"] == "ON"
    assert comm_cleared["gate_verdict"] == "CLEARED_COMMERCE_PERMITTED"

    # 3. Runtime enforcement enables feature flag
    allowed = service.enforce_runtime_feature_flag(
        creator_consent_status="consented",
        has_unapproved_assets=False,
    )
    assert allowed is True
    assert is_feature_flag_enabled("FEATURE_FLAG_RBPC_COMMERCE_ENABLED") is True


# --------------------------------------------------------------------------- #
# 8. REST API Endpoints Integration
# --------------------------------------------------------------------------- #
def test_v5_t127_api_endpoints_integration(client: TestClient):
    """Test full HTTP lifecycle for legal sign-off and gate endpoints."""
    # 1. GET /api/v1/rbpc/legal/signoff-audit
    res_audit = client.get("/api/v1/rbpc/legal/signoff-audit")
    assert res_audit.status_code == 200
    audit_data = res_audit.json()
    assert audit_data["all_approved"] is True
    assert audit_data["domains_count"] == 5
    assert audit_data["compliance_verdict"] == "APPROVED_FOR_PRODUCTION"
    assert len(audit_data["items"]) == 5
    assert any(i["domain"] == "software_ip" for i in audit_data["items"])
    assert any(i["domain"] == "photos_3d_rights" for i in audit_data["items"])
    assert any(i["domain"] == "school_consent" for i in audit_data["items"])
    assert any(i["domain"] == "artisan_agreement" for i in audit_data["items"])
    assert any(i["domain"] == "consumer_tax_terms" for i in audit_data["items"])

    # 2. POST /api/v1/rbpc/legal/evaluate-asset (Positive & Negative)
    # Positive
    res_asset_pos = client.post(
        "/api/v1/rbpc/legal/evaluate-asset",
        json={
            "asset_id": "SF-011",
            "displayed_license": "CC BY",
            "accuracy_grade": "reference_checked_partial",
            "noai": False,
            "is_commercial_context": False,
        },
    )
    assert res_asset_pos.status_code == 200
    assert res_asset_pos.json()["is_cleared"] is True
    assert res_asset_pos.json()["embed_allowed"] is True

    # Negative: Speculative geometry
    res_asset_neg1 = client.post(
        "/api/v1/rbpc/legal/evaluate-asset",
        json={
            "asset_id": "SF-020",
            "displayed_license": "NOT STATED",
            "accuracy_grade": "rejected_inaccurate",
        },
    )
    assert res_asset_neg1.status_code == 200
    assert res_asset_neg1.json()["is_cleared"] is False
    assert res_asset_neg1.json()["status"] == "rejected_accuracy"

    # Negative: 3D model in commercial context
    res_asset_neg2 = client.post(
        "/api/v1/rbpc/legal/evaluate-asset",
        json={
            "asset_id": "SF-009",
            "displayed_license": "CC BY",
            "is_commercial_context": True,
        },
    )
    assert res_asset_neg2.status_code == 200
    assert res_asset_neg2.json()["is_cleared"] is False
    assert res_asset_neg2.json()["status"] == "blocked_commercial_context"

    # 3. POST /api/v1/rbpc/legal/evaluate-commerce-gate (Positive & Negative)
    # Positive
    res_comm_pos = client.post(
        "/api/v1/rbpc/legal/evaluate-commerce-gate",
        json={
            "creator_consent_status": "consented",
            "has_unapproved_assets": False,
        },
    )
    assert res_comm_pos.status_code == 200
    assert res_comm_pos.json()["commerce_allowed"] is True
    assert res_comm_pos.json()["feature_flag_status"] == "ON"

    # Negative: Revoked artisan consent
    res_comm_neg = client.post(
        "/api/v1/rbpc/legal/evaluate-commerce-gate",
        json={
            "creator_consent_status": "revoked",
            "has_unapproved_assets": False,
        },
    )
    assert res_comm_neg.status_code == 200
    assert res_comm_neg.json()["commerce_allowed"] is False
    assert res_comm_neg.json()["feature_flag_status"] == "OFF"


# --------------------------------------------------------------------------- #
# 9. Documentation Parity
# --------------------------------------------------------------------------- #
def test_v5_t127_documentation_parity():
    """Verify documentation parity in docs/rbpc/."""
    # 1. CONTENT_RIGHTS.md
    rights_doc = REPO_ROOT / "docs" / "rbpc" / "CONTENT_RIGHTS.md"
    assert rights_doc.exists(), "docs/rbpc/CONTENT_RIGHTS.md must exist"
    content = rights_doc.read_text(encoding="utf-8")
    assert "Section IX — Final Production Legal & Creator Agreement Sign-Off Matrix" in content
    assert "SIGNOFF-SW-001" in content
    assert "SIGNOFF-3D-002" in content
    assert "SIGNOFF-SCH-003" in content
    assert "SIGNOFF-ART-004" in content
    assert "SIGNOFF-TAX-005" in content
    assert "Decree 13/2023/ND-CP" in content
    assert "Decree 52/2013/ND-CP" in content
    assert "Decree 85/2021/ND-CP" in content
    assert "Artisan Dignity Charter" in content
    assert "FEATURE_FLAG_RBPC_COMMERCE_ENABLED" in content

    # 2. LEGAL_COMPLIANCE_SIGN_OFF.md
    legal_doc = REPO_ROOT / "docs" / "rbpc" / "LEGAL_COMPLIANCE_SIGN_OFF.md"
    assert legal_doc.exists(), "docs/rbpc/LEGAL_COMPLIANCE_SIGN_OFF.md must exist"
    legal_content = legal_doc.read_text(encoding="utf-8")
    assert "DOC-RBPC-LEGAL-001" in legal_content
    assert "SIGNOFF-SW-001" in legal_content
    assert "SIGNOFF-TAX-005" in legal_content
