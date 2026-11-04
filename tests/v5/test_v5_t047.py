# -*- coding: utf-8 -*-
"""V5-T047: 360 Virtual Museum Source Links & Panorama Provenance Test Suite.

Audits and verifies (Wave W04, Slot A07 / Ticket V5-T047):
1. Historical Monument Linkage & Primary Citations:
   - Verifies canonical registry of historical monuments (Cửu Đỉnh, Thế Miếu, Ngọ Môn, Điện Thái Hòa, Kinh thành Huế, Hiển Lâm Các).
   - Verifies primary bibliographic citations from authoritative imperial sources:
     * Đại Nam Thực Lục Chính Biên (Quốc Sử Quán Triều Nguyễn)
     * Khâm Định Đại Nam Hội Điển Sự Lệ (Nội Các Triều Nguyễn)
     * Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC) dossier
   - Verifies institutional rights attribution (HMCC) and CC BY 4.0 licensing.
2. Panorama Viewpoints Linkage:
   - Viewpoints link to real verified historical objects/monuments.
   - Enforces bibliographic citations and verification status ('canonical', 'verified', 'probable').
3. Accessibility & Reduced-Motion Enforcement:
   - Accessible roles: role="region", aria-roledescription="toàn cảnh 360 độ" / "toàn cảnh 2D tiếp cận".
   - Descriptive aria-labels and alt texts across all components and hotspots.
   - Reduced-motion support: auto-detection of prefers-reduced-motion, autoRotate suppression,
     damping velocity suppression, and static 2D accessible alternative toggle.
4. Negative Abuse Guardrails:
   - Broken or inaccessible panorama URIs (empty, invalid, missing) fail safely to accessible 2D still
     photographs/rubbings and comprehensive textual descriptions.
   - When 2D fallback images fail, renders high-contrast SVG architectural schematics.
   - Inaccessible panorama URIs without declared fallbacks fail closed with typed exceptions.
   - Generic or missing alt_text (< 10 chars, "image.jpg") fails closed with PanoramaAccessibilityError.
   - Missing rights attribution (credit_text) fails closed.
5. Component & Frontend Contract Audit:
   - Panorama360.tsx, PanoramaViewer.tsx, SelfHostedTour.tsx, and panorama-sources.ts.
6. Database Integration:
   - ImperialLearningMedia with kind="panorama360", ImperialMediaHotspot, ImperialArtDetail,
     and ImperialArtDetailClaimSource.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import uuid
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.imperial_models import CONTENT_SCOPE_IMPERIAL, ImperialSite, ImperialZone
from backend.imperial_v51_models import (
    ImperialArtDetail,
    ImperialArtDetailClaimSource,
    ImperialLearningMedia,
    ImperialMediaHotspot,
)
from backend.services.virtual_museum_panorama import (
    VERIFIED_PANORAMA_MONUMENTS,
    PanoramaAccessibilityError,
    PanoramaInaccessibleWithoutFallbackError,
    PanoramaMissingSourceCitationError,
    audit_virtual_museum_panoramas,
    get_verified_monument_by_slug,
    get_verified_panorama_monuments,
    is_broken_panorama_uri,
    resolve_panorama_2d_fallback,
    validate_panorama_accessibility,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_SRC = REPO_ROOT / "frontend" / "src"
PANORAMA_360_PATH = FRONTEND_SRC / "components" / "vr360" / "Panorama360.tsx"
PANORAMA_VIEWER_PATH = FRONTEND_SRC / "components" / "imperial" / "media" / "PanoramaViewer.tsx"
SELF_HOSTED_TOUR_PATH = FRONTEND_SRC / "components" / "vr360" / "SelfHostedTour.tsx"
PANORAMA_SOURCES_PATH = FRONTEND_SRC / "lib" / "imperial" / "panorama-sources.ts"


# ==============================================================================
# 1. Canonical Verified Monuments & Primary Citations Registry
# ==============================================================================


def test_verified_monuments_registry_completeness():
    """Verify all 6 canonical monuments are registered with primary sources, citations, and licenses."""
    monuments = get_verified_panorama_monuments()
    expected_slugs = {"cuu-dinh", "the-mieu", "ngo-mon", "dien-thai-hoa", "kinh-thanh", "hien-lam-cac"}

    for slug in expected_slugs:
        assert slug in monuments, f"Missing expected monument '{slug}' in verified registry"
        mon = monuments[slug]

        assert mon["slug"] == slug
        assert len(mon["name"]) > 5
        assert len(mon["historical_period"]) > 5
        assert len(mon["provenance"]) > 30
        assert mon["rights_owner"] == "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)"
        assert "CC BY 4.0" in mon["license"]
        assert mon["fallback_2d_image_url"].startswith("/ban-duc-noi/")
        assert mon["verification_status"] in ("canonical", "verified")

        # Verify primary bibliographic sources
        sources = mon["primary_sources"]
        assert len(sources) >= 1, f"Monument '{slug}' has no primary bibliographic sources"
        for src in sources:
            assert len(src["title"]) > 5
            assert len(src["author"]) > 5
            assert src["year"]
            assert src["locator"]
            assert src["evidence_strength"] == "verified"


def test_get_verified_monument_by_slug_and_prefix():
    """Verify slug lookup handles clean slugs, monument- prefixes, and unknown queries."""
    cuu_dinh = get_verified_monument_by_slug("cuu-dinh")
    assert cuu_dinh is not None
    assert "Cửu Đỉnh" in cuu_dinh["name"]

    with_prefix = get_verified_monument_by_slug("monument-the-mieu")
    assert with_prefix is not None
    assert with_prefix["slug"] == "the-mieu"

    unknown = get_verified_monument_by_slug("unknown-pagoda")
    assert unknown is None

    empty = get_verified_monument_by_slug("")
    assert empty is None


# ==============================================================================
# 2. Resilient 2D Fallback Resolution & URI Accessibility Checks
# ==============================================================================


def test_panorama_uri_inaccessibility_detection():
    """Verify accurate detection of broken, missing, or malformed panorama URIs."""
    assert is_broken_panorama_uri("") is True
    assert is_broken_panorama_uri("   ") is True
    assert is_broken_panorama_uri(None) is True
    assert is_broken_panorama_uri("null") is True
    assert is_broken_panorama_uri("undefined") is True
    assert is_broken_panorama_uri("broken://bad-texture.jpg") is True
    assert is_broken_panorama_uri("/panoramas/invalid-file.jpg") is True
    assert is_broken_panorama_uri("/panoramas/missing-pano.jpg") is True

    # Valid URIs
    assert is_broken_panorama_uri("/panoramas/cuu-dinh.jpg") is False
    assert is_broken_panorama_uri("https://example.com/panoramas/the-mieu.jpg") is False


def test_resolve_panorama_2d_fallback_for_broken_uri():
    """Verify that broken panorama URIs resolve seamlessly to authentic 2D still images and descriptions."""
    res = resolve_panorama_2d_fallback(
        uri="broken://inaccessible.jpg",
        fallback_image_url=None,
        slug="cuu-dinh",
    )

    assert res["is_broken_uri"] is True
    assert res["fallback_image_url"] == "/ban-duc-noi/CAO DINH/CAO ĐỈNH.jpg"
    assert res["monument_name"] == "Cửu Đỉnh (Chín Chiếc Đỉnh Đồng Triều Nguyễn)"
    assert "Cửu Đỉnh" in res["accessible_description"]
    assert "Đại Nam Thực Lục Chính Biên" in res["accessible_description"]
    assert "HMCC" in res["accessible_description"]


def test_resolve_panorama_2d_fallback_with_custom_fallback():
    """Verify custom fallback image is respected if valid, or recovered if broken."""
    res = resolve_panorama_2d_fallback(
        uri="/panoramas/the-mieu.jpg",
        fallback_image_url="/assets/imperial/the-mieu-2d.jpg",
        slug="the-mieu",
    )
    assert res["is_broken_uri"] is False
    assert res["fallback_image_url"] == "/assets/imperial/the-mieu-2d.jpg"

    # When custom fallback is broken, recovers to monument 2D rubbing
    res_bad_custom = resolve_panorama_2d_fallback(
        uri="broken://source.jpg",
        fallback_image_url="broken://fallback.jpg",
        slug="ngo-mon",
    )
    assert res_bad_custom["is_broken_uri"] is True
    assert res_bad_custom["fallback_image_url"] == "/ban-duc-noi/CAO DINH/ĐÔNG HẢI.jpg"


# ==============================================================================
# 3. Negative Abuse Guardrails & Accessibility Policy Validation
# ==============================================================================


def test_negative_broken_uri_without_fallback_fails_closed():
    """Negative Abuse Test: Broken panorama URI without an accessible fallback fails closed."""
    broken_payload = {
        "media_url": "broken://texture.jpg",
        "alt_text": "Toàn cảnh 360 độ sân Cửu Đỉnh tại Hoàng thành Huế",
        "credit_text": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
        "thumbnail_url": "",
        "fallback_image_url": None,
    }

    with pytest.raises(PanoramaInaccessibleWithoutFallbackError) as exc_info:
        validate_panorama_accessibility(broken_payload)

    assert "must declare an accessible 2D fallback" in str(exc_info.value)


def test_negative_missing_or_generic_alt_text_fails_closed():
    """Negative Abuse Test: Missing, too short, or generic alt_text fails closed."""
    # Empty alt text
    with pytest.raises(PanoramaAccessibilityError) as exc_info:
        validate_panorama_accessibility({
            "media_url": "/panoramas/cuu-dinh.jpg",
            "alt_text": "",
            "credit_text": "HMCC",
        })
    assert "requires descriptive alt_text" in str(exc_info.value)

    # Generic filename alt text
    with pytest.raises(PanoramaAccessibilityError) as exc_info:
        validate_panorama_accessibility({
            "media_url": "/panoramas/cuu-dinh.jpg",
            "alt_text": "image.jpg",
            "credit_text": "HMCC",
        })
    assert "Generic or unhelpful alt_text" in str(exc_info.value)

    with pytest.raises(PanoramaAccessibilityError) as exc_info:
        validate_panorama_accessibility({
            "media_url": "/panoramas/cuu-dinh.jpg",
            "alt_text": "panorama_photo_final",
            "credit_text": "HMCC",
        })
    assert "Generic or unhelpful alt_text" in str(exc_info.value)


def test_negative_missing_credit_text_fails_closed():
    """Negative Abuse Test: Missing credit_text rights owner attribution fails closed."""
    with pytest.raises(PanoramaAccessibilityError) as exc_info:
        validate_panorama_accessibility({
            "media_url": "/panoramas/cuu-dinh.jpg",
            "alt_text": "Ảnh toàn cảnh 360 độ sân Thế Miếu nhìn từ Hiển Lâm Các",
            "credit_text": "",
        })
    assert "requires authentic credit_text" in str(exc_info.value)


def test_positive_panorama_accessibility_validation():
    """Verify that valid panorama asset with descriptive alt and rights passes validation."""
    valid_payload = {
        "media_url": "/panoramas/cuu-dinh.jpg",
        "alt_text": "Toàn cảnh 360 độ di tích Cửu Đỉnh tại sân Thế Miếu, Hoàng thành Huế",
        "credit_text": "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
        "thumbnail_url": "/ban-duc-noi/CAO DINH/CAO ĐỈNH.jpg",
    }
    result = validate_panorama_accessibility(valid_payload)
    assert result["status"] == "cleared"
    assert result["has_accessible_fallback"] is True


# ==============================================================================
# 4. Database Integration & Virtual Museum Audit
# ==============================================================================


def test_database_virtual_museum_panorama_and_hotspot_linkage(db_session: Session):
    """Verify that panorama360 learning media persists and links to site, hotspots, and primary claim sources."""
    # 1. Create or query zone & site
    zone = db_session.scalar(
        select(ImperialZone).where(ImperialZone.slug == "zone-ancestral-worship-test")
    )
    if not zone:
        zone = ImperialZone(
            slug="zone-ancestral-worship-test",
            title_vi="Không Gian Thờ Tự Hoàng Triều",
            content_scope=CONTENT_SCOPE_IMPERIAL,
            display_order=1,
        )
        db_session.add(zone)
        db_session.flush()

    site = db_session.scalar(
        select(ImperialSite).where(ImperialSite.slug == "site-cuu-dinh-test")
    )
    if not site:
        site = ImperialSite(
            zone_id=zone.id,
            slug="site-cuu-dinh-test",
            name_vi="Sân Cửu Đỉnh & Thế Miếu",
            content_scope=CONTENT_SCOPE_IMPERIAL,
            display_order=1,
            latitude=16.4687,
            longitude=107.5776,
        )
        db_session.add(site)
        db_session.flush()

    # 2. Create Art Detail with Primary Claim Source
    art_detail = ImperialArtDetail(
        site_id=site.id,
        title="Cao Đỉnh - Chiếc Đỉnh Thuần Đồng Biểu Trưng Vương Quyền",
        slug=f"art-cao-dinh-test-{uuid.uuid4().hex[:6]}",
        kind="relief",
        motif="Long vân và hải sản",
        story_type="documented_event",
        review_status="published",
        content_scope=CONTENT_SCOPE_IMPERIAL,
    )
    db_session.add(art_detail)
    db_session.flush()

    claim_source = ImperialArtDetailClaimSource(
        detail_id=art_detail.id,
        section="observation",
        claim_text="Cao Đỉnh được đặt ở vị trí trung tâm, thẳng hàng với gian thờ Thế Tổ Cao Hoàng Đế.",
        source_title="Đại Nam Thực Lục Chính Biên",
        source_locator="Đệ nhị kỷ, Quyển 162",
        evidence_strength="verified",
    )
    db_session.add(claim_source)
    db_session.flush()

    # 3. Create Panorama360 Media Asset
    pano_media = ImperialLearningMedia(
        site_id=site.id,
        kind="panorama360",
        media_url="/panoramas/cuu-dinh.jpg",
        thumbnail_url="/ban-duc-noi/CAO DINH/CAO ĐỈNH.jpg",
        alt_text="Ảnh toàn cảnh 360 độ sân Cửu Đỉnh và gác Hiển Lâm tại Hoàng thành Huế",
        credit_text="Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
        review_status="published",
        content_scope=CONTENT_SCOPE_IMPERIAL,
    )
    db_session.add(pano_media)
    db_session.flush()

    # 4. Create Viewpoint Hotspot placed on Panorama360
    hotspot = ImperialMediaHotspot(
        media_id=pano_media.id,
        point_kind="point",
        u=0.50,
        v=0.45,
        position_payload={"yaw": 0.0, "pitch": -2.5},
        title="Vị trí Cao Đỉnh",
        description="Đỉnh cao nhất và nặng nhất trong Cửu Đỉnh, đặt thẳng hàng gian giữa Thế Miếu.",
        detail_id=art_detail.id,
        review_status="published",
        content_scope=CONTENT_SCOPE_IMPERIAL,
    )
    db_session.add(hotspot)
    db_session.commit()

    # 5. Execute Virtual Museum Panorama Audit
    audit_res = audit_virtual_museum_panoramas(db_session)
    assert audit_res["total_panoramas_audited"] >= 1
    assert audit_res["cleared_panoramas_count"] >= 1


# ==============================================================================
# 5. Frontend Components Contract Audits
# ==============================================================================


def test_frontend_panorama360_component_contract():
    """Audit frontend/src/components/vr360/Panorama360.tsx for accessibility, 2D fallback, and source links."""
    assert PANORAMA_360_PATH.exists(), f"Missing {PANORAMA_360_PATH}"
    content = PANORAMA_360_PATH.read_text(encoding="utf-8")

    # Contract checks
    assert "HistoricalMonumentLink" in content
    assert "HistoricalSourceCitation" in content
    assert "PanoramaViewpoint" in content
    assert "getVerifiedMonumentOrFallback" in content
    assert "isBrokenPanoramaUri" in content
    assert "resolvePanorama2DFallback" in content

    # Props checks
    assert "monument?:" in content
    assert "monumentKey?:" in content
    assert "viewpoints?:" in content
    assert "fallbackImageUrl?:" in content
    assert "fallbackDescription?:" in content
    assert "reducedMotion?:" in content
    assert "ariaLabel?:" in content
    assert "alt?:" in content

    # Accessibility & Semantic markup
    assert 'role="region"' in content
    assert 'aria-roledescription="toàn cảnh 360 độ"' in content
    assert 'aria-roledescription="toàn cảnh 2D thay thế"' in content
    assert "prefers-reduced-motion" in content

    # Reduced motion and 2D mode controls
    assert "enableDamping={!effectiveReducedMotion}" in content
    assert "Chế độ 2D" in content

    # Provenance and primary source citations UI
    assert "Sử liệu & Chứng thực" in content
    assert "Đại Nam Thực Lục" not in content or "monument.sourceCitations" in content
    assert "cite.citationQuote" in content
    assert "cite.evidenceStrength" in content


def test_frontend_panorama_viewer_component_contract():
    """Audit frontend/src/components/imperial/media/PanoramaViewer.tsx for hotspot sources and reduced-motion."""
    assert PANORAMA_VIEWER_PATH.exists(), f"Missing {PANORAMA_VIEWER_PATH}"
    content = PANORAMA_VIEWER_PATH.read_text(encoding="utf-8")

    # PanoramaHotspot provenance linkage
    assert "monument_id?:" in content
    assert "monument_name?:" in content
    assert "source_citation?:" in content
    assert "verification_status?:" in content
    assert "alt_text?:" in content
    assert "aria_label?:" in content

    # PanoramaViewerProps extensions
    assert "monument?:" in content
    assert "monumentKey?:" in content
    assert "altText?:" in content
    assert "ariaLabel?:" in content
    assert "reducedMotion?:" in content
    assert "fallbackDescription?:" in content

    # Reduced motion logic in render loop
    assert "isReducedMotion" in content
    assert "!isReducedMotion && !state.isDragging" in content

    # Accessible 2D still fallback
    assert 'aria-roledescription="toàn cảnh 2D tiếp cận"' in content
    assert "Bản vẽ kiến trúc & tư liệu khảo sát di tích" in content
    assert "fallbackImageFailed" in content
    assert "onError={() => setFallbackImageFailed(true)}" in content

    # Sources & citations modal
    assert "Chứng thực Lịch sử & Thư mục Nguồn gốc" in content
    assert "c.citationQuote" in content
    assert "c.evidenceStrength" in content


def test_frontend_self_hosted_tour_scenes_link_verified_monuments():
    """Audit SelfHostedTour.tsx for scene linkages to verified monuments and 2D rubbings."""
    assert SELF_HOSTED_TOUR_PATH.exists(), f"Missing {SELF_HOSTED_TOUR_PATH}"
    content = SELF_HOSTED_TOUR_PATH.read_text(encoding="utf-8")

    assert "VERIFIED_VIRTUAL_MUSEUM_MONUMENTS" in content
    assert 'monumentKey: "cuu-dinh"' in content
    assert 'monumentKey: "the-mieu"' in content
    assert 'monumentKey: "ngo-mon"' in content
    assert 'monumentKey: "kinh-thanh"' in content

    # Fallback rubbing images
    assert "/ban-duc-noi/CAO DINH/CAO ĐỈNH.jpg" in content
    assert "/ban-duc-noi/NHAN DINH/NHÂN ĐỈNH.jpg" in content
    assert "/ban-duc-noi/CAO DINH/ĐÔNG HẢI.jpg" in content
    assert "/ban-duc-noi/NHAN DINH/NGỰ BÌNH SƠN.jpg" in content


def test_frontend_panorama_sources_registry_contract():
    """Audit panorama-sources.ts for type exports, monument records, and resolvers."""
    assert PANORAMA_SOURCES_PATH.exists(), f"Missing {PANORAMA_SOURCES_PATH}"
    content = PANORAMA_SOURCES_PATH.read_text(encoding="utf-8")

    assert "export interface HistoricalSourceCitation" in content
    assert "export interface HistoricalMonumentLink" in content
    assert "export interface PanoramaViewpoint" in content
    assert "export const VERIFIED_VIRTUAL_MUSEUM_MONUMENTS" in content
    assert "export function getVerifiedMonument" in content
    assert "export function getVerifiedMonumentOrFallback" in content
    assert "export function isBrokenPanoramaUri" in content
    assert "export function generateAccessible2DDescription" in content
    assert "export function resolvePanorama2DFallback" in content
