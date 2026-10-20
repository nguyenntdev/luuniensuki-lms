# -*- coding: utf-8 -*-
"""Comprehensive test suite for Heritage Audio Guide Dataset & Backend API (STTT-SPEC-AUDIO-PASSPORT-002).

Validates:
1. Dataset Integrity (data/imperial/audio_guides.json):
   - All 16 required monuments are present.
   - Required fields (monument_slug, title_vi, duration_seconds, narrator, audio_url, script_text, timed_transcript).
   - Duration bounds: 60s <= duration_seconds <= 300s (specifically 90 - 150s).
   - Timed transcript cues: ascending timestamps, non-empty text, valid structure.
2. Data Isolation & Policy Compliance:
   - Strictly zero forbidden legacy terms across entire audio dataset.
3. Service Layer (backend.services.imperial_audio):
   - get_audio_guide_by_slug retrieves valid schema for all 16 monuments.
   - get_audio_guide_by_slug returns None for non-existent monuments.
   - list_all_audio_guides returns catalog with total_guides == 16 and positive total duration.
4. FastAPI Endpoints (backend.routers.imperial):
   - GET /api/v1/imperial/audio-guides returns 200 OK with full catalog.
   - GET /api/v1/imperial/sites/{slug}/audio returns 200 OK with accurate track details for all 16 monuments.
   - GET /api/v1/imperial/sites/{invalid_slug}/audio returns 404 with AUDIO_GUIDE_NOT_FOUND error code.
5. Audio Asset Delivery:
   - Static audio files exist in backend/assets/imperial/audio/.
   - Static mount GET /assets/imperial/audio/{slug}.mp3 serves valid MPEG audio (audio/mpeg).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services import imperial_audio
from backend.apischemas.imperial_audio import ImperialAudioCatalogOut, ImperialAudioGuideOut
from scripts.imperial.audit_no_legacy_content import FORBIDDEN_TERMS
from scripts.imperial.validate_imperial_content import REQUIRED_SITES

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIO_GUIDES_FILE = REPO_ROOT / "data" / "imperial" / "audio_guides.json"
AUDIO_ASSETS_DIR = REPO_ROOT / "backend" / "assets" / "imperial" / "audio"


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="module")
def audio_raw_data() -> dict:
    assert AUDIO_GUIDES_FILE.exists(), f"Missing audio dataset file: {AUDIO_GUIDES_FILE}"
    return json.loads(AUDIO_GUIDES_FILE.read_text(encoding="utf-8"))


# =========================================================================== #
# 1. Dataset Integrity & Schema Checks
# =========================================================================== #
def test_audio_dataset_presence_and_monument_coverage(audio_raw_data: dict):
    """Ensure all 16 monuments defined in REQUIRED_SITES have audio guides."""
    tracks = audio_raw_data.get("audio_guides") or audio_raw_data.get("tracks") or []
    assert len(tracks) == 16, f"Expected 16 audio tracks, found {len(tracks)}"

    track_slugs = {t.get("monument_slug") or t.get("site_slug") for t in tracks}
    for site_slug in REQUIRED_SITES:
        assert site_slug in track_slugs, f"Monument '{site_slug}' is missing from audio_guides.json"


def test_audio_guide_metadata_and_duration_bounds(audio_raw_data: dict):
    """Validate metadata fields, duration bounds (60-300s, target 90-150s), and transcripts."""
    tracks = audio_raw_data.get("audio_guides") or audio_raw_data.get("tracks") or []

    for track in tracks:
        slug = track.get("monument_slug") or track.get("site_slug")
        assert slug, "Missing monument_slug in track"
        assert track.get("title_vi"), f"Missing title_vi for {slug}"
        assert track.get("narrator") == "Lưu Niên Voice Guide — Giọng Cố Đô", f"Invalid narrator for {slug}"
        assert track.get("audio_url") == f"/assets/imperial/audio/{slug}.mp3", f"Invalid audio_url for {slug}"

        duration = track.get("duration_seconds") or track.get("duration")
        assert duration is not None, f"Missing duration for {slug}"
        assert 60 <= duration <= 300, f"Duration {duration}s outside bounds [60, 300] for {slug}"
        assert 90 <= duration <= 150, f"Duration {duration}s outside target range [90, 150] for {slug}"

        script_text = track.get("script_text")
        assert script_text and len(script_text) >= 100, f"Script text too short for {slug}"

        cues = track.get("timed_transcript") or []
        assert len(cues) >= 3, f"Track {slug} must have at least 3 timed transcript cues"

        prev_time = -0.001
        for cue in cues:
            time_sec = cue.get("time_sec")
            assert time_sec is not None, f"Missing time_sec in cue for {slug}"
            assert time_sec >= 0.0, f"Negative time_sec in cue for {slug}"
            assert time_sec >= prev_time, f"Cues not in ascending chronological order for {slug}"
            prev_time = time_sec

            text = cue.get("text")
            assert text and len(text.strip()) > 5, f"Empty or tiny cue text for {slug}"


# =========================================================================== #
# 2. Zero Forbidden Terms Audit
# =========================================================================== #
def test_audio_guides_zero_forbidden_terms(audio_raw_data: dict):
    """Verify that zero forbidden legacy terms exist across all narration texts, summaries, and tags."""
    content_str = json.dumps(audio_raw_data, ensure_ascii=False).lower()

    found_violations = []
    for term in FORBIDDEN_TERMS:
        if term in content_str:
            found_violations.append(term)

    assert found_violations == [], f"Found forbidden term violations in audio guides dataset: {found_violations}"


# =========================================================================== #
# 3. Service Layer Tests
# =========================================================================== #
def test_imperial_audio_service_get_by_slug():
    """Verify service retrieval by slug for all 16 monuments."""
    for slug in REQUIRED_SITES:
        guide = imperial_audio.get_audio_guide_by_slug(slug)
        assert guide is not None, f"Service returned None for valid monument slug '{slug}'"
        assert isinstance(guide, ImperialAudioGuideOut)
        assert guide.monument_slug == slug
        assert guide.title_vi
        assert 60 <= guide.duration_seconds <= 300
        assert guide.audio_url == f"/assets/imperial/audio/{slug}.mp3"
        assert guide.narrator == "Lưu Niên Voice Guide — Giọng Cố Đô"
        assert len(guide.timed_transcript) >= 3

    # Unknown slug should return None
    assert imperial_audio.get_audio_guide_by_slug("non-existent-palace") is None


def test_imperial_audio_service_list_all():
    """Verify service retrieval of full catalog with aggregation."""
    catalog = imperial_audio.list_all_audio_guides()
    assert isinstance(catalog, ImperialAudioCatalogOut)
    assert catalog.total_guides == 16
    assert catalog.total_duration_seconds >= 16 * 90  # At least 1440 seconds
    assert len(catalog.tracks) == 16


# =========================================================================== #
# 4. REST API Endpoint Tests
# =========================================================================== #
def test_api_list_all_audio_guides(client: TestClient):
    """GET /api/v1/imperial/audio-guides returns 200 OK with full list."""
    response = client.get("/api/v1/imperial/audio-guides")
    assert response.status_code == 200, response.text
    data = response.json()

    assert data.get("total_guides") == 16
    assert data.get("total_duration_seconds") > 1400
    assert len(data.get("tracks", [])) == 16

    first_track = data["tracks"][0]
    assert "monument_slug" in first_track
    assert "title_vi" in first_track
    assert "audio_url" in first_track
    assert "duration_seconds" in first_track
    assert "timed_transcript" in first_track


def test_api_get_site_audio_guide_success(client: TestClient):
    """GET /api/v1/imperial/sites/{slug}/audio returns 200 OK for each monument."""
    for slug in REQUIRED_SITES:
        response = client.get(f"/api/v1/imperial/sites/{slug}/audio")
        assert response.status_code == 200, f"Failed for {slug}: {response.text}"
        data = response.json()

        assert data["monument_slug"] == slug
        assert data["audio_url"] == f"/assets/imperial/audio/{slug}.mp3"
        assert 90 <= data["duration_seconds"] <= 150
        assert data["narrator"] == "Lưu Niên Voice Guide — Giọng Cố Đô"
        assert len(data["timed_transcript"]) >= 3
        assert len(data["script_text"]) > 50


def test_api_get_site_audio_guide_not_found(client: TestClient):
    """GET /api/v1/imperial/sites/{slug}/audio returns 404 for unknown monument."""
    response = client.get("/api/v1/imperial/sites/unknown-monument-xyz/audio")
    assert response.status_code == 404
    data = response.json()
    assert data.get("error", {}).get("code") == "AUDIO_GUIDE_NOT_FOUND"


# =========================================================================== #
# 5. Audio Asset Serving & Static Routing Tests
# =========================================================================== #
def test_audio_assets_exist_on_disk():
    """Verify all 16 MP3 files are present in backend/assets/imperial/audio/."""
    for slug in REQUIRED_SITES:
        mp3_file = AUDIO_ASSETS_DIR / f"{slug}.mp3"
        assert mp3_file.exists(), f"Missing audio asset file: {mp3_file}"
        assert mp3_file.stat().st_size > 0, f"Empty audio asset file: {mp3_file}"


def test_api_static_audio_stream_routing(client: TestClient):
    """GET /assets/imperial/audio/{slug}.mp3 serves audio/mpeg with proper content."""
    for slug in ("ngo-mon", "dien-thai-hoa", "the-to-mieu"):
        response = client.get(f"/assets/imperial/audio/{slug}.mp3")
        assert response.status_code == 200, f"Failed to stream /assets/imperial/audio/{slug}.mp3"
        assert response.headers.get("content-type") == "audio/mpeg"
        assert len(response.content) > 0
