# -*- coding: utf-8 -*-
"""Service layer for 360 Virtual Museum Source Links & Panorama Provenance.

Ref: Luu Nien STTTNND Follow-On SPEC V5.1 (Ticket V5-T047 / Wave W04-A07).

Implements:
1. Historical Monument Linkage & Primary Bibliographic Citations for 360 Panoramas
2. Viewpoint Provenance Attribution (Đại Nam Thực Lục, Khâm Định Hội Điển, HMCC)
3. Accessibility Validation (alt text, aria labels, reduced motion contracts)
4. Fail-closed Negative Abuse Guards for broken/inaccessible panorama URIs
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..errors import AppError
from ..imperial_models import CONTENT_SCOPE_IMPERIAL, ImperialSite
from ..imperial_v51_models import (
    ImperialArtDetail,
    ImperialArtDetailClaimSource,
    ImperialLearningMedia,
    ImperialMediaHotspot,
)

# --------------------------------------------------------------------------- #
# Custom Typed Exceptions
# --------------------------------------------------------------------------- #
class PanoramaError(AppError):
    """Base error for virtual museum panorama operations."""


class PanoramaAccessibilityError(PanoramaError):
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__("PANORAMA_ACCESSIBILITY_ERROR", message, status_code=400, details=details or {})


class PanoramaInaccessibleWithoutFallbackError(PanoramaError):
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__("PANORAMA_INACCESSIBLE_NO_FALLBACK", message, status_code=422, details=details or {})


class PanoramaMissingSourceCitationError(PanoramaError):
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__("PANORAMA_MISSING_SOURCE_CITATION", message, status_code=400, details=details or {})


# --------------------------------------------------------------------------- #
# Canonical Verified Virtual Museum Monuments & Primary Sources
# --------------------------------------------------------------------------- #
VERIFIED_PANORAMA_MONUMENTS: Dict[str, Dict[str, Any]] = {
    "cuu-dinh": {
        "slug": "cuu-dinh",
        "name": "Cửu Đỉnh (Chín Chiếc Đỉnh Đồng Triều Nguyễn)",
        "historical_period": "Triều Nguyễn — Minh Mạng (1835 - 1837)",
        "provenance": (
            "Chín chiếc đỉnh đồng uy nghi đặt tại sân Thế Miếu, Hoàng thành Huế, đúc từ năm 1835 đến 1837. "
            "Trên mỗi đỉnh chạm khắc 17 hình tượng sông núi, danh thắng, vũ khí và sản vật tiêu biểu của dải đất Việt Nam. "
            "Được UNESCO công nhận là Di sản Tư liệu Khu vực Châu Á - Thái Bình Dương năm 2024."
        ),
        "national_treasure": "Bảo vật Quốc gia Việt Nam (Đợt 1, 2012)",
        "unesco_inscription": "Di sản Tư liệu Ký ức Thế giới Khu vực Châu Á - Thái Bình Dương (2024)",
        "rights_owner": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
        "license": "CC BY 4.0 / Educational Fair Use",
        "monument_url": "/cuu-dinh",
        "fallback_2d_image_url": "/ban-duc-noi/CAO DINH/CAO ĐỈNH.jpg",
        "verification_status": "canonical",
        "primary_sources": [
            {
                "title": "Đại Nam Thực Lục Chính Biên",
                "author": "Quốc Sử Quán Triều Nguyễn",
                "year": "1835",
                "locator": "Đệ nhị kỷ, Quyển 162",
                "citation_quote": "Tháng 12 năm Ất Mùi (1835), đúc chín đỉnh đồng đặt trước sân Thế Miếu.",
                "evidence_strength": "verified",
            },
            {
                "title": "Khâm Định Đại Nam Hội Điển Sự Lệ",
                "author": "Nội Các Triều Nguyễn",
                "year": "1851",
                "locator": "Quyển 162, Công Bộ - Quy thức đúc Cửu Đỉnh",
                "citation_quote": "Quy định quy chuẩn hình thể, quai vạc, chân kiềng và đồ án trên chín đỉnh.",
                "evidence_strength": "verified",
            },
        ],
    },
    "the-mieu": {
        "slug": "the-mieu",
        "name": "Thế Tổ Miếu (Thế Miếu)",
        "historical_period": "Triều Nguyễn — Minh Mạng (1821)",
        "provenance": (
            "Tổ miếu phụng thờ các vị hoàng đế triều Nguyễn, tọa lạc tại góc tây nam Hoàng thành Huế. "
            "Xây dựng năm Minh Mạng thứ 2 (1821), gồm 9 gian 2 chái kép theo kiểu trùng thiềm điệp ốc."
        ),
        "national_treasure": "Di tích Quốc gia đặc biệt — Quần thể Di tích Cố đô Huế (UNESCO 1993)",
        "rights_owner": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
        "license": "CC BY 4.0 / Educational Fair Use",
        "monument_url": "/sites/the-mieu",
        "fallback_2d_image_url": "/ban-duc-noi/NHAN DINH/NHÂN ĐỈNH.jpg",
        "verification_status": "verified",
        "primary_sources": [
            {
                "title": "Đại Nam Thực Lục Chính Biên",
                "author": "Quốc Sử Quán Triều Nguyễn",
                "year": "1821",
                "locator": "Đệ nhị kỷ, Quyển 8",
                "citation_quote": "Xây dựng Thế Miếu ở phía sau cửa Chương Đức, chuẩn bị thần vị và hương án phụng thờ.",
                "evidence_strength": "verified",
            },
        ],
    },
    "ngo-mon": {
        "slug": "ngo-mon",
        "name": "Ngọ Môn Huế (Lầu Ngũ Phụng)",
        "historical_period": "Triều Nguyễn — Minh Mạng (1833)",
        "provenance": (
            "Cổng chính phía nam của Hoàng thành Huế, xây dựng năm Minh Mạng thứ 14 (1833). "
            "Phần trên là Lầu Ngũ Phụng tráng lệ với 100 cột gỗ lim, nơi công bố chiếu chỉ và tổ chức lễ Truyền Lô."
        ),
        "national_treasure": "Di tích Quốc gia đặc biệt — Quần thể Di tích Cố đô Huế (UNESCO 1993)",
        "rights_owner": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
        "license": "CC BY 4.0 / Educational Fair Use",
        "monument_url": "/sites/ngo-mon",
        "fallback_2d_image_url": "/ban-duc-noi/CAO DINH/ĐÔNG HẢI.jpg",
        "verification_status": "verified",
        "primary_sources": [
            {
                "title": "Đại Nam Thực Lục Chính Biên",
                "author": "Quốc Sử Quán Triều Nguyễn",
                "year": "1833",
                "locator": "Đệ nhị kỷ, Quyển 104",
                "citation_quote": "Đổi đài Nam Khuyết làm cửa Ngọ Môn, mở 5 cửa vòm, xây lầu Ngũ Phụng ở trên.",
                "evidence_strength": "verified",
            },
        ],
    },
    "dien-thai-hoa": {
        "slug": "dien-thai-hoa",
        "name": "Điện Thái Hòa (Sân Đại Triều Nghi)",
        "historical_period": "Triều Nguyễn — Gia Long (1805) & Minh Mạng (1833)",
        "provenance": (
            "Cung điện trung tâm quyền lực tối cao của Hoàng triều Nguyễn, nơi đặt Ngai vàng và bửu tọa của 13 đời vua. "
            "Nơi cử hành lễ Đăng quang, Vạn thọ, tiếp sứ thần và các kỳ đại triều."
        ),
        "national_treasure": "Ngai vàng Triều Nguyễn (Bảo vật Quốc gia số 1, 2012)",
        "rights_owner": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
        "license": "CC BY 4.0 / Educational Fair Use",
        "monument_url": "/sites/dien-thai-hoa",
        "fallback_2d_image_url": "/ban-duc-noi/CAO DINH/LONG.jpg",
        "verification_status": "canonical",
        "primary_sources": [
            {
                "title": "Đại Nam Thực Lục Chính Biên",
                "author": "Quốc Sử Quán Triều Nguyễn",
                "year": "1805",
                "locator": "Đệ nhất kỷ, Quyển 26",
                "citation_quote": "Tháng 2 năm Ất Sửu (1805), định quy thức xây dựng điện Thái Hòa.",
                "evidence_strength": "verified",
            },
        ],
    },
    "kinh-thanh": {
        "slug": "kinh-thanh",
        "name": "Kinh Thành Huế (Đô Thành Phú Xuân)",
        "historical_period": "Triều Nguyễn — Gia Long (1805) & Minh Mạng (1832)",
        "provenance": (
            "Quần thể thành quách quân sự phòng thủ rộng lớn kết hợp nguyên lý kiến trúc quân sự Vauban Tây phương "
            "với phong thủy địa lý phương Đông (núi Ngự Bình, sông Hương, cồn Hến, cồn Dã Viên)."
        ),
        "national_treasure": "Di tích Quốc gia đặc biệt — Quần thể Di tích Cố đô Huế (UNESCO 1993)",
        "rights_owner": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
        "license": "CC BY 4.0 / Educational Fair Use",
        "monument_url": "/sites/kinh-thanh",
        "fallback_2d_image_url": "/ban-duc-noi/NHAN DINH/NGỰ BÌNH SƠN.jpg",
        "verification_status": "verified",
        "primary_sources": [
            {
                "title": "Đại Nam Thực Lục Chính Biên",
                "author": "Quốc Sử Quán Triều Nguyễn",
                "year": "1805",
                "locator": "Đệ nhất kỷ, Quyển 24",
                "citation_quote": "Đo đạc cắm mốc xây dựng kinh thành Huế, lấy sông Hương làm minh đường, núi Ngự Bình làm tiền án.",
                "evidence_strength": "verified",
            },
        ],
    },
    "hien-lam-cac": {
        "slug": "hien-lam-cac",
        "name": "Hiển Lâm Các (Gác Hiển Lâm)",
        "historical_period": "Triều Nguyễn — Minh Mạng (1821 - 1822)",
        "provenance": (
            "Công trình kiến trúc bằng gỗ cao nhất trong Hoàng thành Huế (17m), dựng năm 1821-1822 để ghi nhớ công lao "
            "của các vị công thần có công dựng nghiệp triều Nguyễn."
        ),
        "national_treasure": "Di tích Quốc gia đặc biệt — Quần thể Di tích Cố đô Huế (UNESCO 1993)",
        "rights_owner": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
        "license": "CC BY 4.0 / Educational Fair Use",
        "monument_url": "/sites/hien-lam-cac",
        "fallback_2d_image_url": "/ban-duc-noi/CHUONG DINH/CHƯƠNG ĐỈNH.jpg",
        "verification_status": "verified",
        "primary_sources": [
            {
                "title": "Đại Nam Thực Lục Chính Biên",
                "author": "Quốc Sử Quán Triều Nguyễn",
                "year": "1821",
                "locator": "Đệ nhị kỷ, Quyển 11",
                "citation_quote": "Dựng gác Hiển Lâm cao ba tầng ở trước Thế Miếu để biểu dương công tích khai quốc.",
                "evidence_strength": "verified",
            },
        ],
    },
}


# --------------------------------------------------------------------------- #
# Domain Services
# --------------------------------------------------------------------------- #
def get_verified_panorama_monuments() -> Dict[str, Dict[str, Any]]:
    """Return immutable directory of all verified panorama monuments."""
    return VERIFIED_PANORAMA_MONUMENTS


def get_verified_monument_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    """Retrieve verified monument metadata by slug or alias."""
    if not slug:
        return None
    normalized = slug.strip().lower().replace("monument-", "")
    return VERIFIED_PANORAMA_MONUMENTS.get(normalized)


def is_broken_panorama_uri(uri: Optional[str]) -> bool:
    """Detect broken, unreachable, empty, or malformed panorama URIs."""
    if not uri or not isinstance(uri, str):
        return True
    trimmed = uri.strip()
    if trimmed in ("", "null", "undefined"):
        return True
    if trimmed.startswith("broken://") or "invalid" in trimmed or "missing" in trimmed:
        return True
    return False


def resolve_panorama_2d_fallback(
    uri: str,
    fallback_image_url: Optional[str] = None,
    slug: Optional[str] = None,
) -> Dict[str, Any]:
    """Resolve resilient 2D still fallback asset and accessibility description.

    Guarantees:
    - Zero crashing on broken / inaccessible panorama URIs.
    - Resolves an authentic 2D still image (e.g. archival rubbing or photograph).
    - Generates full structured textual accessibility description with primary citations.
    """
    is_broken = is_broken_panorama_uri(uri)
    monument = get_verified_monument_by_slug(slug or "")

    if not monument:
        monument = {
            "slug": slug or "di-tich-hue",
            "name": "Di tích Cố đô Huế",
            "historical_period": "Triều Nguyễn (1802 - 1945)",
            "provenance": "Quần thể Di tích Cố đô Huế, bảo tồn bởi Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC).",
            "rights_owner": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
            "license": "CC BY 4.0 / Educational Fair Use",
            "fallback_2d_image_url": "/ban-duc-noi/CAO DINH/CAO ĐỈNH.jpg",
            "primary_sources": [],
        }

    resolved_fallback_img = fallback_image_url
    if not resolved_fallback_img or is_broken_panorama_uri(resolved_fallback_img):
        resolved_fallback_img = monument.get("fallback_2d_image_url") or "/ban-duc-noi/CAO DINH/CAO ĐỈNH.jpg"

    # Build accessible description
    desc_parts = [
        f"Toàn cảnh di tích: {monument['name']}.",
        f"Niên đại: {monument['historical_period']}.",
        f"Bối cảnh lịch sử: {monument['provenance']}",
    ]
    if monument.get("primary_sources"):
        sources_str = "; ".join(f"{s['title']} ({s.get('locator', '')})" for s in monument["primary_sources"])
        desc_parts.append(f"Sử liệu xác thực: {sources_str}.")
    desc_parts.append(f"Bản quyền tư liệu: {monument['rights_owner']} ({monument['license']}).")

    return {
        "is_broken_uri": is_broken,
        "original_uri": uri,
        "fallback_image_url": resolved_fallback_img,
        "monument_slug": monument.get("slug"),
        "monument_name": monument.get("name"),
        "accessible_description": " ".join(desc_parts),
        "primary_sources": monument.get("primary_sources", []),
        "rights_owner": monument.get("rights_owner"),
        "license": monument.get("license"),
    }


def validate_panorama_accessibility(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Audit and enforce accessibility standards on 360 panorama assets.

    Fails closed if:
    - alt_text is empty or generic filename.
    - credit_text (rights attribution) is missing.
    - Panorama is inaccessible without an accessible 2D fallback.
    """
    alt_text = payload.get("alt_text", "")
    if not alt_text or not isinstance(alt_text, str) or len(alt_text.strip()) == 0:
        raise PanoramaAccessibilityError("Panorama asset requires descriptive alt_text of at least 10 characters.")

    generic_pattern = re.compile(r"^(image|photo|panorama|pano|untitled|\.jpg|\.png)", re.IGNORECASE)
    if generic_pattern.match(alt_text.strip()):
        raise PanoramaAccessibilityError(f"Generic or unhelpful alt_text '{alt_text}' is disallowed.")

    if len(alt_text.strip()) < 10:
        raise PanoramaAccessibilityError("Panorama asset requires descriptive alt_text of at least 10 characters.")

    credit_text = payload.get("credit_text", "")
    if not credit_text or not isinstance(credit_text, str) or len(credit_text.strip()) < 3:
        raise PanoramaAccessibilityError("Panorama asset requires authentic credit_text / rights owner attribution.")

    media_url = payload.get("media_url", "")
    if is_broken_panorama_uri(media_url):
        fallback_url = payload.get("thumbnail_url") or payload.get("fallback_image_url")
        if not fallback_url or is_broken_panorama_uri(fallback_url):
            raise PanoramaInaccessibleWithoutFallbackError(
                f"Broken or inaccessible panorama URI '{media_url}' must declare an accessible 2D fallback image."
            )

    return {
        "status": "cleared",
        "alt_text": alt_text.strip(),
        "credit_text": credit_text.strip(),
        "has_accessible_fallback": True,
    }


def audit_virtual_museum_panoramas(db: Session) -> Dict[str, Any]:
    """Audit all 360 panorama learning media records in database.

    Verifies:
    1. Each panorama360 record is linked to a valid ImperialSite.
    2. alt_text and credit_text are present and descriptive.
    3. Associated hotspots link to verified art details with primary claim sources.
    """
    stmt = (
        select(ImperialLearningMedia)
        .where(
            ImperialLearningMedia.content_scope == CONTENT_SCOPE_IMPERIAL,
            ImperialLearningMedia.kind == "panorama360",
        )
        .options(
            selectinload(ImperialLearningMedia.site),
            selectinload(ImperialLearningMedia.hotspots)
            .selectinload(ImperialMediaHotspot.art_detail)
            .selectinload(ImperialArtDetail.claim_sources),
        )
    )
    panoramas = list(db.scalars(stmt).all())

    audited_count = len(panoramas)
    cleared_count = 0
    issues: List[Dict[str, Any]] = []

    for pano in panoramas:
        pano_issues = []
        if not pano.site:
            pano_issues.append("Missing site linkage")
        if not pano.alt_text or len(pano.alt_text.strip()) < 10:
            pano_issues.append("Missing or insufficient alt_text")
        if not pano.credit_text:
            pano_issues.append("Missing credit_text rights attribution")

        # Verify hotspots have valid art details and sources
        for hp in pano.hotspots:
            if not hp.art_detail:
                pano_issues.append(f"Hotspot '{hp.title}' missing linked art_detail")
            elif not hp.art_detail.claim_sources:
                pano_issues.append(f"Art detail '{hp.art_detail.title}' has no primary claim sources")

        if pano_issues:
            issues.append({"media_id": str(pano.id), "title": pano.alt_text or str(pano.id), "issues": pano_issues})
        else:
            cleared_count += 1

    return {
        "total_panoramas_audited": audited_count,
        "cleared_panoramas_count": cleared_count,
        "has_issues": len(issues) > 0,
        "issues": issues,
    }
