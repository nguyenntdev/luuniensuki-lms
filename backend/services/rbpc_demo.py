# -*- coding: utf-8 -*-
"""Competition Demo Data Truth & Demonstration Resilience Service for RBPC 2026.

Ticket: V5-T119 (Wave W11, Slot A09).
Goal:
- Competition demo data truth & resilience in docs/rbpc/DEMO_ENVIRONMENT_RUNBOOK.md,
  frontend/src/app/rbpc/, and backend/services/rbpc_demo.py.
- Demo script using verified heritage + consented test accounts.
- Fallback mock data clearly watermarked as DEMO DATA.
- Negative abuse invariant:
  Live network outage does NOT fabricate success or pretend transaction went through.
  Under connection drop, 502/503/504, or timeout, systems fail closed with typed error,
  never returning fake tracking codes (INQ-XXXX) or synthetic confirmation screens.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class DemoConsentStatus(str, Enum):
    CONSENTED = "CONSENTED"
    WITHDRAWN = "WITHDRAWN"
    UNCONFIRMED = "UNCONFIRMED"


@dataclass(frozen=True)
class DemoAccount:
    account_id: str
    email: str
    username: str
    role: str  # partner | staff | admin | learner
    tenant_id: str  # prov-phuong-duc-01, prov-phap-lam-01, prov-thanh-tien-02, global, demo-visitor
    artisan_name: Optional[str]
    consent_ref: str
    consent_status: DemoConsentStatus
    description: str

    def validate_consent(self) -> None:
        """Validate that test account has verified consent reference and status."""
        if self.consent_status != DemoConsentStatus.CONSENTED:
            raise ValueError(
                f"Negative abuse: Account '{self.email}' does not have verified consent ({self.consent_status.value})."
            )
        if not self.consent_ref or not self.consent_ref.startswith("CONSENT-"):
            raise ValueError(
                f"Negative abuse: Account '{self.email}' lacks canonical consent reference ({self.consent_ref})."
            )


@dataclass(frozen=True)
class DemoVerifiedHeritageEntity:
    entity_id: str
    unesco_code: Optional[str]
    title_vi: str
    title_en: str
    entity_type: str  # unesco_component | monument | craft_community | artisan | primary_source
    historical_basis: str
    citation_locator: str


@dataclass(frozen=True)
class DemoMockInquiry:
    inquiry_id: str
    reference: str
    experience_slug: str
    provider_id: str
    contact_name: str
    status: str
    is_demo: bool = True
    watermark: str = "DEMO DATA"
    tenant_boundary: str = "TENANT_DEMO_RBPC"

    def validate_watermark(self) -> None:
        """Validate that mock or fallback item is strictly watermarked as DEMO DATA."""
        if not self.is_demo:
            raise ValueError(
                f"Negative abuse: Mock inquiry '{self.inquiry_id}' is missing is_demo=True flag."
            )
        if self.watermark != "DEMO DATA":
            raise ValueError(
                f"Negative abuse: Mock inquiry '{self.inquiry_id}' has invalid watermark '{self.watermark}'."
            )


class NetworkOutageError(RuntimeError):
    """Raised when an operation fails due to simulated or actual network outage."""
    pass


class InquiryStatusLookupFailure(RuntimeError):
    """Raised when status lookup fails due to network outage or unreachable service."""
    pass


# ============================================================================
# CANONICAL CATALOG: Verified Test Accounts (100% Consented)
# ============================================================================

CANONICAL_DEMO_ACCOUNTS: List[DemoAccount] = [
    DemoAccount(
        account_id="usr-demo-artisan-pd-01",
        email="artisan.phuongduc@histolab.icu",
        username="artisan_phuongduc",
        role="partner",
        tenant_id="prov-phuong-duc-01",
        artisan_name="Nghệ nhân Nhân dân Nguyễn Văn Sinh",
        consent_ref="CONSENT-PD-001",
        consent_status=DemoConsentStatus.CONSENTED,
        description="Bronze casting workshop coordinator at Phường Đúc.",
    ),
    DemoAccount(
        account_id="usr-demo-artisan-pl-02",
        email="artisan.phaplam@histolab.icu",
        username="artisan_phaplam",
        role="partner",
        tenant_id="prov-phap-lam-01",
        artisan_name="Thạc sĩ - Nghệ nhân Đỗ Hữu Triết",
        consent_ref="CONSENT-PL-002",
        consent_status=DemoConsentStatus.CONSENTED,
        description="Vitreous enamel workshop director at Huế.",
    ),
    DemoAccount(
        account_id="usr-demo-artisan-tt-03",
        email="artisan.thanhtien@histolab.icu",
        username="artisan_thanhtien",
        role="partner",
        tenant_id="prov-thanh-tien-02",
        artisan_name="Nghệ nhân Ưu tú Thân Văn Huy",
        consent_ref="CONSENT-TT-003",
        consent_status=DemoConsentStatus.CONSENTED,
        description="Thanh Tiên paper lotus craft master.",
    ),
    DemoAccount(
        account_id="usr-demo-curator-04",
        email="curator@histolab.icu",
        username="staff_curator",
        role="staff",
        tenant_id="global",
        artisan_name=None,
        consent_ref="CONSENT-CURATOR-001",
        consent_status=DemoConsentStatus.CONSENTED,
        description="Staff historical researcher and editorial verifier.",
    ),
    DemoAccount(
        account_id="usr-demo-visitor-05",
        email="visitor.demo@histolab.icu",
        username="visitor_demo",
        role="learner",
        tenant_id="demo-visitor",
        artisan_name=None,
        consent_ref="CONSENT-VISITOR-DEMO",
        consent_status=DemoConsentStatus.CONSENTED,
        description="Consented demonstration cultural traveler account.",
    ),
]


# ============================================================================
# CANONICAL CATALOG: Verified Heritage Entities (UNESCO & Primary Citations)
# ============================================================================

CANONICAL_DEMO_HERITAGE: List[DemoVerifiedHeritageEntity] = [
    DemoVerifiedHeritageEntity(
        entity_id="heritage-kinh-thanh-001",
        unesco_code="678-001",
        title_vi="Kinh thành Huế",
        title_en="Huế Imperial Citadel",
        entity_type="unesco_component",
        historical_basis="Quần thể Di tích Cố đô Huế (UNESCO World Heritage Site 1993)",
        citation_locator="UNESCO Decision 678; Khâm Định Đại Nam Hội Điển Sự Lệ",
    ),
    DemoVerifiedHeritageEntity(
        entity_id="heritage-thien-mu-002",
        unesco_code="678-002",
        title_vi="Chùa Thiên Mụ",
        title_en="Thien Mu Pagoda",
        entity_type="unesco_component",
        historical_basis="Tháp Phước Duyên & Đại hồng chung đúc thời chúa Nguyễn Phúc Chu (1710)",
        citation_locator="Đại Nam Thực Lục Tiền Biên; Văn bia chùa Thiên Mụ",
    ),
    DemoVerifiedHeritageEntity(
        entity_id="heritage-ho-quyen-013",
        unesco_code="678-013",
        title_vi="Đấu Xảo / Hổ Quyền - Đền Voi Ré",
        title_en="Ho Quyen Royal Colosseum & Voi Re Temple",
        entity_type="unesco_component",
        historical_basis="Đấu trường voi hổ triều Nguyễn xây dựng năm Minh Mạng 11 (1830)",
        citation_locator="Đại Nam Thực Lục Chính Biên; Quyển 67",
    ),
    DemoVerifiedHeritageEntity(
        entity_id="heritage-dien-kien-trung",
        unesco_code=None,
        title_vi="Điện Kiến Trung",
        title_en="Kien Trung Palace",
        entity_type="monument",
        historical_basis="Cung điện kết hợp kiến trúc Phục Hưng Pháp và mỹ thuật khảm sành sứ hoàng cung",
        citation_locator="Bảo tàng Cổ vật Cung đình Huế (HMFA) Hồ sơ phục dựng 2024",
    ),
    DemoVerifiedHeritageEntity(
        entity_id="craft-phuong-duc",
        unesco_code=None,
        title_vi="Làng Đúc Đồng Phường Đúc",
        title_en="Phuong Duc Bronze Casting Village",
        entity_type="craft_community",
        historical_basis="Phường thợ đúc đồng thuộc Bác Công Bộ triều Nguyễn, nơi đúc Cửu Đỉnh (1835-1837)",
        citation_locator="Khâm Định Đại Nam Hội Điển Sự Lệ, Quyển 223",
    ),
    DemoVerifiedHeritageEntity(
        entity_id="craft-phap-lam",
        unesco_code=None,
        title_vi="Nghệ thuật Pháp Lam Huế",
        title_en="Hue Vitreous Enamel Art",
        entity_type="craft_community",
        historical_basis="Nghệ thuật vẽ men màu trên cốt đồng được khởi xướng thời vua Minh Mạng (1827)",
        citation_locator="Đại Nam Thực Lục Chính Biên; Pháp Lam Tượng Cục",
    ),
    DemoVerifiedHeritageEntity(
        entity_id="craft-thanh-tien",
        unesco_code=None,
        title_vi="Hoa Giấy Làng Thanh Tiên",
        title_en="Thanh Tien Paper Flower Village",
        entity_type="craft_community",
        historical_basis="Làng nghề hoa giấy thờ tự hơn 300 năm ven sông Hương",
        citation_locator="Địa chí Văn hóa Thừa Thiên Huế; Làng nghề truyền thống",
    ),
]


# ============================================================================
# CANONICAL FALLBACK SEED MOCK INQUIRIES (Watermarked)
# ============================================================================

CANONICAL_SEED_MOCK_INQUIRIES: List[DemoMockInquiry] = [
    DemoMockInquiry(
        inquiry_id="inq-001",
        reference="INQ-7F89-A23C",
        experience_slug="workshop-duc-dong-phuong-duc",
        provider_id="prov-phuong-duc-01",
        contact_name="Nguyễn An Nhiên",
        status="new",
        is_demo=True,
        watermark="DEMO DATA",
        tenant_boundary="TENANT_DEMO_RBPC",
    ),
    DemoMockInquiry(
        inquiry_id="inq-002",
        reference="INQ-6E21-B44D",
        experience_slug="workshop-duc-dong-phuong-duc",
        provider_id="prov-phuong-duc-01",
        contact_name="David Miller",
        status="contacted",
        is_demo=True,
        watermark="DEMO DATA",
        tenant_boundary="TENANT_DEMO_RBPC",
    ),
    DemoMockInquiry(
        inquiry_id="inq-003",
        reference="INQ-5B10-C89E",
        experience_slug="workshop-phap-lam-hue",
        provider_id="prov-phap-lam-01",
        contact_name="Trần Bảo Ngọc",
        status="confirmed",
        is_demo=True,
        watermark="DEMO DATA",
        tenant_boundary="TENANT_DEMO_RBPC",
    ),
    DemoMockInquiry(
        inquiry_id="inq-004",
        reference="INQ-4A02-D11F",
        experience_slug="workshop-duc-dong-phuong-duc",
        provider_id="prov-phuong-duc-01",
        contact_name="Jean Dupont",
        status="declined",
        is_demo=True,
        watermark="DEMO DATA",
        tenant_boundary="TENANT_DEMO_RBPC",
    ),
    DemoMockInquiry(
        inquiry_id="inq-005",
        reference="INQ-3C98-E52A",
        experience_slug="workshop-hoa-giay-thanh-tien",
        provider_id="prov-thanh-tien-02",
        contact_name="Phạm Hải Đăng",
        status="new",
        is_demo=True,
        watermark="DEMO DATA",
        tenant_boundary="TENANT_DEMO_RBPC",
    ),
]


# ============================================================================
# RESILIENCE ENGINE & NEGATIVE ABUSE VALIDATORS
# ============================================================================

class DemoResilienceEngine:
    """Engine enforcing demonstration truth, watermarking, and fail-closed network resilience."""

    def __init__(self, accounts: Optional[List[DemoAccount]] = None):
        self.accounts = accounts or list(CANONICAL_DEMO_ACCOUNTS)
        self.heritage_catalog = list(CANONICAL_DEMO_HERITAGE)
        self.mock_inquiries = list(CANONICAL_SEED_MOCK_INQUIRIES)

    def validate_all_accounts(self) -> None:
        """Ensure all registered demo accounts have verified written consent."""
        for acc in self.accounts:
            acc.validate_consent()

    def get_account_by_email(self, email: str) -> Optional[DemoAccount]:
        return next((a for a in self.accounts if a.email == email), None)

    def get_account_by_provider(self, provider_id: str) -> Optional[DemoAccount]:
        return next((a for a in self.accounts if a.tenant_id == provider_id), None)

    def validate_mock_inquiries_watermark(self) -> None:
        """Verify that every mock inquiry is tagged with is_demo=True and watermark='DEMO DATA'."""
        for inq in self.mock_inquiries:
            inq.validate_watermark()

    def simulate_inquiry_submission(
        self,
        payload: Dict[str, Any],
        network_available: bool = True,
        simulate_503: bool = False,
    ) -> Dict[str, Any]:
        """Simulate inquiry submission with network outage guardrail.

        NEGATIVE ABUSE INVARIANT:
        If network_available is False or simulate_503 is True:
        - Must raise NetworkOutageError.
        - Must NOT return a reference code (INQ-XXXX).
        - Must NOT report success or create a transaction.
        """
        if not network_available:
            raise NetworkOutageError(
                "Mất kết nối mạng đến máy chủ LƯU NIÊN. Giao dịch không được tạo và không có mã tham chiếu nào được cấp."
            )
        if simulate_503:
            raise NetworkOutageError(
                "Máy chủ cổng giao dịch đang bảo trì hoặc quá tải (HTTP 503). Vui lòng thử lại sau."
            )

        # Successful submission simulation with valid inputs
        if not payload.get("experience_slug"):
            raise ValueError("Thiếu mã trải nghiệm (experience_slug).")
        contact = payload.get("contact", {})
        if not contact.get("name") or not contact.get("value"):
            raise ValueError("Thông tin liên hệ không đầy đủ.")

        import uuid
        part1 = uuid.uuid4().hex[:4].upper()
        part2 = uuid.uuid4().hex[:4].upper()
        return {
            "status": "success",
            "reference": f"INQ-{part1}-{part2}",
            "status_token": f"tok_{uuid.uuid4().hex}",
            "message": "Yêu cầu trải nghiệm văn hóa đã được gửi thành công.",
        }

    def simulate_inquiry_status_lookup(
        self,
        token: str,
        network_available: bool = True,
    ) -> Dict[str, Any]:
        """Simulate status lookup with network outage guardrail.

        NEGATIVE ABUSE INVARIANT:
        If network_available is False:
        - Must raise InquiryStatusLookupFailure.
        - Must NOT synthesize fake status.
        """
        if not network_available:
            raise InquiryStatusLookupFailure(
                "Không thể kết nối máy chủ để tra cứu trạng thái hồ sơ lúc này."
            )
        token_clean = token.strip()
        if not token_clean:
            raise ValueError("Mã tra cứu không được để trống.")
        
        # Check against seed references
        matched = next((m for m in self.mock_inquiries if m.reference == token_clean), None)
        if not matched:
            raise KeyError(f"Không tìm thấy hồ sơ với mã tra cứu '{token_clean}'.")
        return {
            "reference": matched.reference,
            "status": matched.status,
            "is_demo": matched.is_demo,
            "watermark": matched.watermark,
        }

    def validate_production_tenant_isolation(
        self,
        inquiries: List[Dict[str, Any]],
        is_live_production: bool = True,
    ) -> None:
        """Ensure live production tenant queries never leak synthetic mock items.

        NEGATIVE ABUSE INVARIANT:
        In live production tenant mode, inquiries list must have ZERO mock items.
        """
        if is_live_production:
            for item in inquiries:
                if item.get("is_demo") is True or item.get("watermark") == "DEMO DATA":
                    raise ValueError(
                        f"Negative abuse: Synthetic demo item '{item.get('reference', item.get('id'))}' "
                        f"leaked into live production tenant!"
                    )


default_demo_resilience_engine = DemoResilienceEngine()
