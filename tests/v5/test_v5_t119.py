# -*- coding: utf-8 -*-
"""V5-T119: Competition Demo Data Truth & Resilience Test Suite.

Ticket: V5-T119 (Wave W11, Slot A09).
Goal:
- Competition demo data truth & resilience in docs/rbpc/DEMO_ENVIRONMENT_RUNBOOK.md,
  frontend/src/app/rbpc/, and backend/services/rbpc_demo.py.
- Demo script using verified heritage + consented test accounts;
  fallback mock data clearly watermarked as DEMO DATA.
- Negative abuse invariant:
  Live network outage does NOT fabricate success or pretend transaction went through.
"""
from __future__ import annotations

import re
from pathlib import Path
import pytest

from backend.services.rbpc_demo import (
    CANONICAL_DEMO_ACCOUNTS,
    CANONICAL_DEMO_HERITAGE,
    CANONICAL_SEED_MOCK_INQUIRIES,
    DemoAccount,
    DemoConsentStatus,
    DemoMockInquiry,
    DemoResilienceEngine,
    InquiryStatusLookupFailure,
    NetworkOutageError,
    default_demo_resilience_engine,
)


def test_v5_t119_verified_test_accounts_and_consent_invariants():
    """Verify that all competition demo test accounts have verified written consent and strict boundaries."""
    engine = default_demo_resilience_engine
    engine.validate_all_accounts()

    assert len(CANONICAL_DEMO_ACCOUNTS) >= 5, "Expected at least 5 canonical demo accounts"

    # Verify key partner and staff accounts
    phuongduc = engine.get_account_by_email("artisan.phuongduc@histolab.icu")
    assert phuongduc is not None
    assert phuongduc.role == "partner"
    assert phuongduc.tenant_id == "prov-phuong-duc-01"
    assert phuongduc.consent_ref == "CONSENT-PD-001"
    assert phuongduc.consent_status == DemoConsentStatus.CONSENTED
    assert "Nguyễn Văn Sinh" in (phuongduc.artisan_name or "")

    phaplam = engine.get_account_by_email("artisan.phaplam@histolab.icu")
    assert phaplam is not None
    assert phaplam.role == "partner"
    assert phaplam.tenant_id == "prov-phap-lam-01"
    assert phaplam.consent_ref == "CONSENT-PL-002"
    assert "Đỗ Hữu Triết" in (phaplam.artisan_name or "")

    thanhtien = engine.get_account_by_email("artisan.thanhtien@histolab.icu")
    assert thanhtien is not None
    assert thanhtien.role == "partner"
    assert thanhtien.tenant_id == "prov-thanh-tien-02"
    assert thanhtien.consent_ref == "CONSENT-TT-003"
    assert "Thân Văn Huy" in (thanhtien.artisan_name or "")

    curator = engine.get_account_by_email("curator@histolab.icu")
    assert curator is not None
    assert curator.role == "staff"
    assert curator.tenant_id == "global"

    visitor = engine.get_account_by_email("visitor.demo@histolab.icu")
    assert visitor is not None
    assert visitor.role == "learner"

    # Negative abuse test: Unconsented account must fail validation
    unconsented_acc = DemoAccount(
        account_id="usr-fake-99",
        email="unconsented@fake.io",
        username="unconsented_user",
        role="partner",
        tenant_id="prov-fake-99",
        artisan_name="Fake Artisan",
        consent_ref="INVALID-REF",
        consent_status=DemoConsentStatus.UNCONFIRMED,
        description="Unconfirmed demo account without written consent.",
    )
    with pytest.raises(ValueError, match="Negative abuse: Account .* does not have verified consent"):
        unconsented_acc.validate_consent()


def test_v5_t119_verified_heritage_and_primary_citations():
    """Verify that heritage entities and citations in the demo script match verified canonical records."""
    heritage = CANONICAL_DEMO_HERITAGE
    assert len(heritage) >= 6

    # Verify UNESCO entities
    kinh_thanh = next(h for h in heritage if h.unesco_code == "678-001")
    assert "Kinh thành Huế" in kinh_thanh.title_vi
    assert "Khâm Định Đại Nam Hội Điển Sự Lệ" in kinh_thanh.citation_locator

    thien_mu = next(h for h in heritage if h.unesco_code == "678-002")
    assert "Chùa Thiên Mụ" in thien_mu.title_vi
    assert "1710" in thien_mu.historical_basis

    ho_quyen = next(h for h in heritage if h.unesco_code == "678-013")
    assert "Hổ Quyền" in ho_quyen.title_vi

    # Verify living craft traditions
    craft_phuong_duc = next(h for h in heritage if h.entity_id == "craft-phuong-duc")
    assert "Cửu Đỉnh" in craft_phuong_duc.historical_basis
    assert "Quyển 223" in craft_phuong_duc.citation_locator


def test_v5_t119_fallback_mock_data_watermarking():
    """Verify that all mock/seed inquiries are strictly watermarked with DEMO DATA."""
    engine = default_demo_resilience_engine
    engine.validate_mock_inquiries_watermark()

    for item in CANONICAL_SEED_MOCK_INQUIRIES:
        assert item.is_demo is True
        assert item.watermark == "DEMO DATA"
        assert item.tenant_boundary == "TENANT_DEMO_RBPC"

    # Negative abuse: Unwatermarked mock inquiry must raise ValueError
    unwatermarked = DemoMockInquiry(
        inquiry_id="inq-bad-01",
        reference="INQ-FAKE-01",
        experience_slug="workshop-duc-dong-phuong-duc",
        provider_id="prov-phuong-duc-01",
        contact_name="Fake User",
        status="new",
        is_demo=False,  # VIOLATION
        watermark="LIVE",  # VIOLATION
    )
    with pytest.raises(ValueError, match="Negative abuse"):
        unwatermarked.validate_watermark()


def test_v5_t119_frontend_seed_fixtures_and_watermarking():
    """Verify that frontend seed inquiries and components contain DEMO DATA watermarking."""
    inquiries_lib_path = Path("frontend/src/lib/rbpc/inquiries.ts")
    assert inquiries_lib_path.exists(), "frontend/src/lib/rbpc/inquiries.ts must exist"
    content = inquiries_lib_path.read_text(encoding="utf-8")

    # Check SEED_PARTNER_INQUIRIES watermarking
    assert "export const SEED_PARTNER_INQUIRIES" in content
    assert 'isDemo: true,' in content
    assert 'watermark: "DEMO DATA",' in content

    # Check partner page watermarking banner
    partner_page_path = Path("frontend/src/app/rbpc/partner/page.tsx")
    assert partner_page_path.exists()
    partner_content = partner_page_path.read_text(encoding="utf-8")
    assert 'data-testid="demo-data-watermark"' in partner_content
    assert 'data-testid="demo-badge"' in partner_content
    assert "DEMO DATA" in partner_content
    assert "isDemoMode={isDemoMode}" in partner_content

    # Check inquiries page watermarking banner
    inquiries_page_path = Path("frontend/src/app/rbpc/inquiries/page.tsx")
    assert inquiries_page_path.exists()
    inquiries_content = inquiries_page_path.read_text(encoding="utf-8")
    assert 'data-testid="demo-data-watermark"' in inquiries_content
    assert 'data-testid="demo-badge"' in inquiries_content
    assert "DEMO DATA" in inquiries_content
    assert "TENANT_DEMO_RBPC" in inquiries_content

    # Check PartnerInboxView watermarking
    inbox_view_path = Path("frontend/src/components/rbpc/PartnerInboxView.tsx")
    assert inbox_view_path.exists()
    inbox_content = inbox_view_path.read_text(encoding="utf-8")
    assert 'data-testid="inbox-item-demo-badge"' in inbox_content
    assert 'data-testid="detail-demo-watermark"' in inbox_content


def test_v5_t119_negative_abuse_network_outage_does_not_fabricate_success():
    """Negative abuse invariant:
    Live network outage does NOT fabricate success or pretend transaction went through.
    """
    engine = default_demo_resilience_engine

    valid_payload = {
        "experience_slug": "workshop-duc-dong-phuong-duc",
        "contact": {
            "name": "Nguyễn An Nhiên",
            "method": "phone",
            "value": "0912345678",
        },
        "party_size": 2,
    }

    # Case 1: Live network outage (network_available=False)
    with pytest.raises(NetworkOutageError) as exc_info:
        engine.simulate_inquiry_submission(valid_payload, network_available=False)
    assert "Mất kết nối mạng" in str(exc_info.value)
    assert "không có mã tham chiếu nào được cấp" in str(exc_info.value)

    # Case 2: Gateway 503 outage (simulate_503=True)
    with pytest.raises(NetworkOutageError) as exc_info503:
        engine.simulate_inquiry_submission(valid_payload, network_available=True, simulate_503=True)
    assert "HTTP 503" in str(exc_info503.value)

    # Normal success path when network is available
    res = engine.simulate_inquiry_submission(valid_payload, network_available=True)
    assert res["status"] == "success"
    assert res["reference"].startswith("INQ-")
    assert res["status_token"].startswith("tok_")


def test_v5_t119_negative_abuse_status_lookup_network_outage():
    """Negative abuse invariant:
    Status lookup during network outage fails closed, never synthesizing fake inquiry status.
    """
    engine = default_demo_resilience_engine

    # Outage must fail closed
    with pytest.raises(InquiryStatusLookupFailure, match="Không thể kết nối máy chủ"):
        engine.simulate_inquiry_status_lookup("INQ-7F89-A23C", network_available=False)

    # When network is available, valid reference returns watermarked mock record
    res = engine.simulate_inquiry_status_lookup("INQ-7F89-A23C", network_available=True)
    assert res["reference"] == "INQ-7F89-A23C"
    assert res["is_demo"] is True
    assert res["watermark"] == "DEMO DATA"


def test_v5_t119_negative_abuse_production_tenant_isolation():
    """Negative abuse invariant:
    Production live tenant queries must never leak synthetic mock inquiry items.
    """
    engine = default_demo_resilience_engine

    # Real inquiries in live production tenant
    clean_live_inquiries = [
        {
            "id": "real-inq-101",
            "reference": "INQ-8888-9999",
            "is_demo": False,
            "status": "new",
        }
    ]
    # Clean list should pass
    engine.validate_production_tenant_isolation(clean_live_inquiries, is_live_production=True)

    # If mock inquiry is leaked into production tenant
    leaked_inquiries = [
        {
            "id": "inq-001",
            "reference": "INQ-7F89-A23C",
            "is_demo": True,  # MOCK LEAK
            "watermark": "DEMO DATA",
        }
    ]
    with pytest.raises(ValueError, match="Negative abuse: Synthetic demo item .* leaked into live production tenant"):
        engine.validate_production_tenant_isolation(leaked_inquiries, is_live_production=True)


def test_v5_t119_runbook_documentation_parity():
    """Verify that docs/rbpc/DEMO_ENVIRONMENT_RUNBOOK.md contains all required sections and specifications."""
    runbook_path = Path("docs/rbpc/DEMO_ENVIRONMENT_RUNBOOK.md")
    assert runbook_path.exists(), "DEMO_ENVIRONMENT_RUNBOOK.md must exist"
    text = runbook_path.read_text(encoding="utf-8")

    # Required Section headers
    assert "### 5.5 Consented Test Accounts & Production Tenant Baseline" in text
    assert "#### 5.5.1 Canonical Competition Demo Script Walkthrough" in text
    assert "#### 5.5.2 Fallback Mock Data Watermarking Standard" in text
    assert "### 7.4 Live Network Outage & Non-Fabrication Resiliency (Negative Invariant)" in text

    # Required accounts and artisans
    assert "artisan.phuongduc@histolab.icu" in text
    assert "artisan.phaplam@histolab.icu" in text
    assert "artisan.thanhtien@histolab.icu" in text
    assert "curator@histolab.icu" in text
    assert "visitor.demo@histolab.icu" in text
    assert "CONSENT-PD-001" in text
    assert "CONSENT-PL-002" in text
    assert "CONSENT-TT-003" in text

    # Required heritage and sources
    assert "Kinh thành Huế" in text
    assert "678-001" in text
    assert "Khâm Định Đại Nam Hội Điển Sự Lệ" in text
    assert "Quyển 223" in text

    # Watermark and negative abuse terms
    assert "DEMO DATA" in text
    assert "data-testid=\"demo-data-watermark\"" in text
    assert "data-testid=\"demo-badge\"" in text
    assert "data-testid=\"inbox-item-demo-badge\"" in text
    assert "tests/v5/test_v5_t119.py" in text
