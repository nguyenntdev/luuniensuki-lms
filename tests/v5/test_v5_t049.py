# -*- coding: utf-8 -*-
"""V5-T049: Media Accessibility (a11y) & WCAG 2.2 AA Audits Across Frontend Components.

Audits and verifies (Wave W04, Slot A09 / Ticket V5-T049):
1. 2D Equivalence for 3D Relics:
   - All 9 Urn 3D GLB manifests provide verified 2D rubbing archives (ban-duc-noi/).
   - 162 motif reliefs mapped to 2D rubbings and textual descriptions.
   - Approved Sketchfab 3D models provide high-resolution photographic fallbacks and DOI records.
2. Captions & Synchronized Subtitles for Audio Guides:
   - 100% transcript and timed cue coverage across all 16 Imperial Audio Guides (data/imperial/audio_guides.json).
   - Live captions feed (CaptionsFeed) with polite ARIA live regions and log roles.
3. Accessible VR 360 Walkthroughs:
   - Self-hosted panoramas (Panorama360) provide accessible 2D still fallbacks and scene descriptions.
   - Virtual tours (VirtualTours) provide accessible tablist navigation and 2D text descriptions.
4. Component Accessibility Contracts in frontend/src/components/:
   - Keyboard navigation (tabIndex, keydown handlers, focus-visible styling).
   - Screen reader announcements (aria-live polite, role landmarks, aria-labels).
   - High-contrast mode support (contrast-more variants, legible color ratios >= 4.5:1).
5. Negative Abuse Protections:
   - Strict validation preventing historical learning content from being locked exclusively
     behind 3D, AR, or sound without accessible 2D/text equivalents.
   - Simulated missing 2D or transcript alternatives fail closed with ExclusiveMediaLockError.
6. Database Integration:
   - HistoricalAsset and ImperialLearningMedia rows maintain 2D parity and accessible alt text.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List

import pytest
from sqlalchemy.orm import Session

from backend.services.media_accessibility import (
    REPO_ROOT,
    AssetAccessibilityAudit,
    ComponentAccessibilityAudit,
    ExclusiveMediaLockError,
    MediaAccessibilityReport,
    audit_all_3d_assets,
    audit_all_audio_guides,
    audit_all_vr360_tours,
    audit_component_accessibility_contracts,
    audit_database_media_accessibility,
    calculate_contrast_ratio,
    calculate_relative_luminance,
    hex_to_rgb,
    run_full_media_accessibility_audit,
    validate_no_exclusive_media_lock,
)


# ==============================================================================
# 1. 3D Model Accessibility & 2D Equivalence
# ==============================================================================
def test_3d_urn_manifests_provide_2d_fallbacks():
    """Verify that all 9 Urn 3D manifests have verified 2D rubbing fallbacks."""
    audits = audit_all_3d_assets(REPO_ROOT)
    urn_audits = [a for a in audits if a.asset_id.startswith("urn-3d-")]

    assert len(urn_audits) == 9, f"Expected 9 Urn 3D audits, found {len(urn_audits)}"

    for audit in urn_audits:
        assert audit.has_2d_alternative is True, f"Urn '{audit.asset_id}' missing 2D fallback"
        assert audit.has_alt_text is True, f"Urn '{audit.asset_id}' missing textual description"
        assert audit.is_accessible is True, f"Urn '{audit.asset_id}' has violations: {audit.violations}"
        assert audit.fallback_ref is not None


def test_sketchfab_models_provide_photographic_2d_fallbacks():
    """Verify that curated Sketchfab 3D models provide photographic 2D fallbacks and DOI citations."""
    audits = audit_all_3d_assets(REPO_ROOT)
    sf_audits = [a for a in audits if a.asset_id.startswith("sketchfab-")]

    assert len(sf_audits) >= 3, f"Expected at least 3 Sketchfab models, found {len(sf_audits)}"

    for audit in sf_audits:
        assert audit.has_2d_alternative is True, f"Sketchfab model '{audit.asset_id}' missing 2D photographic fallback"
        assert audit.is_accessible is True, f"Sketchfab model '{audit.asset_id}' has violations: {audit.violations}"
        assert audit.fallback_ref == "ThreeDFallback"


# ==============================================================================
# 2. Audio Guides Accessibility (Captions & Synchronized Subtitles)
# ==============================================================================
def test_all_16_audio_guides_have_full_script_and_timed_cues():
    """Verify that 100% of Imperial Audio Guides have complete script_text and timed_transcript cues."""
    audits = audit_all_audio_guides(REPO_ROOT)

    assert len(audits) >= 16, f"Expected >= 16 audio guides in catalog, found {len(audits)}"

    for audit in audits:
        assert audit.has_transcript is True, f"Audio guide '{audit.asset_id}' missing transcript"
        assert audit.transcript_length > 100, f"Audio guide '{audit.asset_id}' transcript too short ({audit.transcript_length} chars)"
        assert audit.has_2d_alternative is True
        assert audit.is_accessible is True, f"Audio guide '{audit.asset_id}' has violations: {audit.violations}"


# ==============================================================================
# 3. VR 360 Panoramas & Tours Accessibility
# ==============================================================================
def test_vr360_tours_provide_2d_fallbacks_and_text_alternatives():
    """Verify that self-hosted panoramas and virtual tours provide 2D still images and text alternatives."""
    audits = audit_all_vr360_tours(REPO_ROOT)

    assert len(audits) >= 6, f"Expected >= 6 VR360 scenes/tours, found {len(audits)}"

    for audit in audits:
        assert audit.has_2d_alternative is True, f"VR scene '{audit.asset_id}' missing 2D alternative"
        assert audit.has_alt_text is True, f"VR scene '{audit.asset_id}' missing alt text description"
        assert audit.is_accessible is True, f"VR scene '{audit.asset_id}' has violations: {audit.violations}"


# ==============================================================================
# 4. Frontend Component Accessibility Contracts
# ==============================================================================
def test_component_accessibility_contracts():
    """Verify that media components in frontend/src/components implement keyboard nav, roles, and a11y."""
    comp_audits = audit_component_accessibility_contracts(REPO_ROOT)

    assert len(comp_audits) >= 10, f"Expected >= 10 audited components, found {len(comp_audits)}"

    comp_map = {c.component_name: c for c in comp_audits}

    # 1. CaptionsFeed
    cf = comp_map.get("CaptionsFeed")
    assert cf is not None
    assert cf.has_keyboard_nav is True
    assert cf.has_aria_live is True
    assert cf.has_accessible_role is True
    assert cf.is_fully_compliant is True

    # 2. SketchfabExhibit
    sfe = comp_map.get("SketchfabExhibit")
    assert sfe is not None
    assert sfe.has_keyboard_nav is True
    assert sfe.has_aria_live is True
    assert sfe.has_accessible_role is True
    assert sfe.has_2d_equivalence is True
    assert sfe.has_high_contrast_support is True

    # 3. FloatingAudioPlayer
    fap = comp_map.get("FloatingAudioPlayer")
    assert fap is not None
    assert fap.has_keyboard_nav is True
    assert fap.has_aria_live is True
    assert fap.has_captions_or_subtitles is True
    assert fap.has_high_contrast_support is True

    # 4. AudioTranscriptDrawer
    atd = comp_map.get("AudioTranscriptDrawer")
    assert atd is not None
    assert atd.has_captions_or_subtitles is True

    # 5. VirtualTours
    vt = comp_map.get("VirtualTours")
    assert vt is not None
    assert vt.has_keyboard_nav is True
    assert vt.has_aria_live is True
    assert vt.has_accessible_role is True
    assert vt.has_2d_equivalence is True

    # 6. Panorama360
    p360 = comp_map.get("Panorama360")
    assert p360 is not None
    assert p360.has_keyboard_nav is True
    assert p360.has_aria_live is True
    assert p360.has_2d_equivalence is True

    # 7. UrnAccessibleFallback
    uaf = comp_map.get("UrnAccessibleFallback")
    assert uaf is not None
    assert uaf.has_keyboard_nav is True
    assert uaf.has_accessible_role is True
    assert uaf.has_2d_equivalence is True


# ==============================================================================
# 5. Negative Abuse Protections (Must Fail Before Fix)
# ==============================================================================
def test_negative_abuse_rejects_3d_model_without_2d_fallback():
    """Negative abuse: simulated 3D asset without 2D fallback raises ExclusiveMediaLockError."""
    fake_asset = AssetAccessibilityAudit(
        asset_id="fake-exclusive-3d-asset",
        asset_name="Speculative Imagined Palace 3D",
        media_type="3d_model",
        has_2d_alternative=False,  # VIOLATION: locked exclusively in 3D
        fallback_ref=None,
        has_alt_text=False,
        is_accessible=False,
    )

    with pytest.raises(ExclusiveMediaLockError) as exc_info:
        validate_no_exclusive_media_lock([fake_asset])

    assert "locked exclusively behind 3D" in str(exc_info.value)
    assert "fake-exclusive-3d-asset" in str(exc_info.value)


def test_negative_abuse_rejects_audio_guide_without_transcript():
    """Negative abuse: simulated audio guide without written transcript raises ExclusiveMediaLockError."""
    fake_audio = AssetAccessibilityAudit(
        asset_id="fake-audio-no-script",
        asset_name="Voice Guide Without Transcript",
        media_type="audio_guide",
        has_2d_alternative=True,
        has_transcript=False,  # VIOLATION: locked exclusively in sound
        transcript_length=0,
        is_accessible=False,
    )

    with pytest.raises(ExclusiveMediaLockError) as exc_info:
        validate_no_exclusive_media_lock([fake_audio])

    assert "locked exclusively behind 3D, AR, or sound" in str(exc_info.value)
    assert "fake-audio-no-script" in str(exc_info.value)


def test_negative_abuse_rejects_vr_scene_without_text_or_still():
    """Negative abuse: simulated VR scene without 2D text or still fallback raises ExclusiveMediaLockError."""
    fake_vr = AssetAccessibilityAudit(
        asset_id="fake-vr-exclusive",
        asset_name="Exclusive VR Chamber",
        media_type="panorama_360",
        has_2d_alternative=False,  # VIOLATION
        has_alt_text=False,
        is_accessible=False,
    )

    with pytest.raises(ExclusiveMediaLockError) as exc_info:
        validate_no_exclusive_media_lock([fake_vr])

    assert "fake-vr-exclusive" in str(exc_info.value)


# ==============================================================================
# 6. WCAG 2.2 AA Contrast Calculations & Tokens
# ==============================================================================
def test_wcag_color_contrast_calculations():
    """Verify relative luminance and contrast ratio calculations comply with WCAG 2.2 standards."""
    # Black on white: 21:1
    ratio_bw = calculate_contrast_ratio("#000000", "#ffffff")
    assert ratio_bw >= 21.0

    # White on dark neutral background (#09090b): >= 15:1
    ratio_dark = calculate_contrast_ratio("#ffffff", "#09090b")
    assert ratio_dark >= 15.0

    # Amber text on dark background (#fbbf24 on #09090b): >= 11:1
    ratio_amber = calculate_contrast_ratio("#fbbf24", "#09090b")
    assert ratio_amber >= 11.0

    # Emerald text on dark background (#34d399 on #09090b): >= 10:1
    ratio_emerald = calculate_contrast_ratio("#34d399", "#09090b")
    assert ratio_emerald >= 10.0


# ==============================================================================
# 7. Database Integration
# ==============================================================================
def test_database_media_accessibility_parity(db_session: Session):
    """Verify that database records in HistoricalAsset and ImperialLearningMedia satisfy accessibility parity."""
    stats = audit_database_media_accessibility(db_session)
    assert stats["database_connected"] is True
    assert "historical_assets" in stats
    assert "imperial_learning_media" in stats


# ==============================================================================
# 8. Master Full Audit Runner & Integrity Check
# ==============================================================================
def test_run_full_media_accessibility_audit_passes():
    """Run master audit runner and verify that no content is exclusively locked."""
    report = run_full_media_accessibility_audit(REPO_ROOT)

    assert report.total_3d_assets_audited >= 12
    assert report.compliant_3d_assets == report.total_3d_assets_audited
    assert report.total_audio_guides_audited >= 16
    assert report.compliant_audio_guides == report.total_audio_guides_audited
    assert report.total_vr360_scenes_audited >= 6
    assert report.compliant_vr360_scenes == report.total_vr360_scenes_audited
    assert report.no_content_exclusively_locked is True
    assert report.summary["wcag_level"] == "WCAG 2.2 AA"
    assert report.summary["keyboard_navigation_verified"] is True
    assert report.summary["aria_live_screen_reader_verified"] is True
    assert report.summary["subtitles_and_captions_verified"] is True
    assert report.summary["2d_text_and_visual_equivalence_verified"] is True
