# -*- coding: utf-8 -*-
"""Pydantic v2 schemas for STTTNNĐ Heritage Audio Guides (STTT-SPEC-AUDIO-PASSPORT-002).

DTOs for:
- TimedTranscriptCue: Synchronized text cue with start/end time
- ImperialAudioGuideOut: Detailed audio guide narration for a specific monument
- ImperialAudioGuideSummary: Summary info for audio playlist / track catalog
- ImperialAudioCatalogOut: Aggregated audio catalog response with total listening time
"""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class ImperialAudioBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TimedTranscriptCue(ImperialAudioBaseSchema):
    time_sec: float = Field(..., ge=0.0, description="Start time cue in seconds")
    text: str = Field(..., min_length=1, description="Narration sentence or segment text")
    end_time_sec: Optional[float] = Field(default=None, ge=0.0, description="Optional cue end time in seconds")
    speaker: Optional[str] = Field(default="Lưu Niên Voice Guide", description="Speaker identity")
    section_title: Optional[str] = Field(default=None, description="Subtitle or thematic section title")


class ImperialAudioGuideOut(ImperialAudioBaseSchema):
    monument_slug: str = Field(..., min_length=1, max_length=100, description="Unique monument slug identifier")
    title_vi: str = Field(..., min_length=1, max_length=255, description="Vietnamese monument name")
    duration_seconds: int = Field(..., ge=60, le=300, description="Total audio track duration in seconds (90 - 150s target)")
    audio_url: str = Field(..., min_length=1, max_length=1000, description="Relative URL to the audio file asset")
    narrator: str = Field(default="Lưu Niên Voice Guide — Giọng Cố Đô", description="Narrator description or attribution")
    script_text: str = Field(..., min_length=20, description="Full narration script text in Vietnamese")
    timed_transcript: list[TimedTranscriptCue] = Field(default_factory=list, description="Array of time-coded narration cues")
    credit_text: Optional[str] = Field(default=None, description="Source credit and archival attribution")
    summary: Optional[str] = Field(default=None, description="Brief synopsis of the narration")
    tags: list[str] = Field(default_factory=list, description="Curated discovery tags")


class ImperialAudioGuideSummary(ImperialAudioBaseSchema):
    monument_slug: str = Field(..., min_length=1, max_length=100)
    title_vi: str = Field(..., min_length=1, max_length=255)
    duration_seconds: int = Field(..., ge=1)
    audio_url: str = Field(..., min_length=1, max_length=1000)
    narrator: str = Field(default="Lưu Niên Voice Guide — Giọng Cố Đô")
    summary: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class ImperialAudioCatalogOut(ImperialAudioBaseSchema):
    content_scope: str = Field(default="STTT_IMPERIAL_CITY_AUDIO_GUIDES")
    version: str = Field(default="1.0.0")
    total_guides: int = Field(..., ge=0, description="Total number of audio guide tracks")
    total_duration_seconds: int = Field(..., ge=0, description="Total listening duration across all tracks")
    tracks: list[ImperialAudioGuideOut] = Field(default_factory=list, description="All audio guide tracks")
