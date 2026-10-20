# -*- coding: utf-8 -*-
"""Service layer for STTTNNĐ Heritage Audio Guides (STTT-SPEC-AUDIO-PASSPORT-002).

Provides retrieval and caching for:
- Individual monument audio guide tracks with synchronized timed transcripts
- Catalog of all 16 Đại Nội monument audio tracks with aggregate duration
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from ..apischemas.imperial_audio import (
    ImperialAudioCatalogOut,
    ImperialAudioGuideOut,
    TimedTranscriptCue,
)

# Canonical JSON data file location
_AUDIO_GUIDES_FILE = Path(__file__).resolve().parents[2] / "data" / "imperial" / "audio_guides.json"

_audio_guides_cache: Optional[dict[str, ImperialAudioGuideOut]] = None
_all_guides_cache: Optional[ImperialAudioCatalogOut] = None


def _load_audio_guides_data() -> dict[str, ImperialAudioGuideOut]:
    """Parse data/imperial/audio_guides.json and build lookup map keyed by monument_slug."""
    global _audio_guides_cache, _all_guides_cache
    if _audio_guides_cache is not None:
        return _audio_guides_cache

    cache: dict[str, ImperialAudioGuideOut] = {}
    if not _AUDIO_GUIDES_FILE.exists():
        _audio_guides_cache = cache
        return _audio_guides_cache

    try:
        raw_text = _AUDIO_GUIDES_FILE.read_text(encoding="utf-8")
        raw_data = json.loads(raw_text)
    except Exception:
        _audio_guides_cache = cache
        return _audio_guides_cache

    tracks_list = raw_data.get("audio_guides") or raw_data.get("tracks") or []
    out_tracks: list[ImperialAudioGuideOut] = []
    total_seconds = 0

    for item in tracks_list:
        slug = item.get("monument_slug") or item.get("site_slug")
        if not slug:
            continue

        raw_cues = item.get("timed_transcript") or []
        parsed_cues: list[TimedTranscriptCue] = []
        for cue in raw_cues:
            parsed_cues.append(
                TimedTranscriptCue(
                    time_sec=float(cue.get("time_sec", 0.0)),
                    text=cue.get("text", ""),
                    end_time_sec=float(cue.get("end_time_sec")) if cue.get("end_time_sec") is not None else None,
                    speaker=cue.get("speaker") or "Lưu Niên Voice Guide",
                    section_title=cue.get("section_title"),
                )
            )

        duration = int(item.get("duration_seconds") or item.get("duration") or 120)
        total_seconds += duration

        guide_out = ImperialAudioGuideOut(
            monument_slug=slug,
            title_vi=item.get("title_vi") or item.get("site_name_vi") or slug,
            duration_seconds=duration,
            audio_url=item.get("audio_url") or f"/assets/imperial/audio/{slug}.mp3",
            narrator=item.get("narrator") or "Lưu Niên Voice Guide — Giọng Cố Đô",
            script_text=item.get("script_text") or "",
            timed_transcript=parsed_cues,
            credit_text=item.get("credit_text") or "Trung tâm Bảo tồn Di tích Cố đô Huế & Dự án Lưu Niên Sứ Ký",
            summary=item.get("summary"),
            tags=item.get("tags") or [],
        )

        cache[slug] = guide_out
        out_tracks.append(guide_out)

    _audio_guides_cache = cache
    _all_guides_cache = ImperialAudioCatalogOut(
        content_scope=raw_data.get("content_scope", "STTT_IMPERIAL_CITY_AUDIO_GUIDES"),
        version=raw_data.get("version", "1.0.0"),
        total_guides=len(out_tracks),
        total_duration_seconds=total_seconds,
        tracks=out_tracks,
    )

    return _audio_guides_cache


def get_audio_guide_by_slug(monument_slug: str) -> Optional[ImperialAudioGuideOut]:
    """Retrieve narration metadata and timed transcript for a specific monument."""
    data = _load_audio_guides_data()
    return data.get(monument_slug)


def list_all_audio_guides() -> ImperialAudioCatalogOut:
    """Retrieve all available audio guide tracks with aggregate duration statistics."""
    global _all_guides_cache
    if _all_guides_cache is None:
        _load_audio_guides_data()
    if _all_guides_cache is None:
        return ImperialAudioCatalogOut(
            content_scope="STTT_IMPERIAL_CITY_AUDIO_GUIDES",
            version="1.0.0",
            total_guides=0,
            total_duration_seconds=0,
            tracks=[],
        )
    return _all_guides_cache
