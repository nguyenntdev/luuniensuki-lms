# -*- coding: utf-8 -*-
"""Pydantic schemas for Low-Bandwidth Printable / Offline Kit (V5-T096).

Spec: Wave W09, Slot A06
Provides typed schemas for:
- Printable student handouts with source excerpts
- High-contrast 2D rubbings with rights attributions
- QR codes for offline verification and digital twin follow-up
- Offline inspection tasks executable 100% on paper
- Verbatim audio guide transcripts (zero streaming bandwidth required)
- Equality guarantee: No AR or smartphone is required to complete learning assignments.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class OfflineKitBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class OfflinePrimarySourceItem(OfflineKitBaseSchema):
    """Bibliographic source excerpt with verified rights attribution."""

    source_title: str = Field(..., description="Title of the primary historical source")
    volume_or_chapter: Optional[str] = Field(None, description="Volume or chapter reference")
    citation: str = Field(..., description="Archival excerpt or citation")
    archival_unit: Optional[str] = Field(None, description="Archival collection or institution")
    reliability_level: str = Field("primary_official", description="Epistemic reliability classification")
    rights_owner: str = Field(
        "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
        description="Legal rights owner or custodian",
    )
    license: str = Field(
        "CC BY 4.0 / Educational Fair Use",
        description="Educational open license terms",
    )


class OfflineRubbingAsset(OfflineKitBaseSchema):
    """High-contrast 2D rubbing asset with print-optimized contrast filters."""

    asset_url: str = Field(..., description="URL of the 2D rubbing image")
    local_path: str = Field(..., description="Relative local filesystem path")
    format: str = Field("image/jpeg", description="MIME image format")
    sha256: Optional[str] = Field(None, description="Cryptographic SHA-256 integrity hash")
    high_contrast_css: str = Field(
        "filter: contrast(160%) grayscale(100%) brightness(95%);",
        description="Print CSS filter to maximize relief legibility on monochrome school printers",
    )
    rights_attribution: str = Field(
        "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC)",
        description="Attribution notice",
    )
    legal_basis: str = Field(
        "Public Domain (1835-1837 Imperial relic) / Academic Educational Fair Use",
        description="Legal basis for reproduction",
    )


class OfflineInspectionTask(OfflineKitBaseSchema):
    """Paper-executable inspection task requiring zero digital devices."""

    task_title_vi: str = Field(..., description="Title of the paper inspection task")
    instructions_vi: str = Field(..., description="Direct paper instructions for students")
    checkpoints: List[str] = Field(
        default_factory=list,
        description="Checkpoints to physically verify on the 2D rubbing or structure",
    )
    sketch_prompt_vi: Optional[str] = Field(
        None,
        description="Prompt for drawing or sketching architectural or relief features",
    )
    paper_achievable: bool = Field(
        True,
        description="Strict invariant: 100% achievable with pencil and paper",
    )
    ar_or_smartphone_required: bool = Field(
        False,
        description="Strict invariant: zero smartphone or AR requirement",
    )


class OfflineAudioTranscript(OfflineKitBaseSchema):
    """Verbatim transcript of the audio guide eliminating audio streaming bandwidth."""

    track_title_vi: str = Field(..., description="Title of the audio narration")
    narrator: str = Field(..., description="Voice narrator attribution")
    duration_seconds: int = Field(..., ge=0, description="Spoken duration in seconds")
    script_text: str = Field(..., description="Full verbatim text of the historical narration")
    key_quotes: List[str] = Field(
        default_factory=list,
        description="Key pedagogical takeaways extracted from the transcript",
    )


class OfflineKitStation(OfflineKitBaseSchema):
    """Complete printable station bundle for low-bandwidth learning."""

    station_index: int = Field(..., ge=1, description="Sequential station number")
    monument_slug: str = Field(..., description="Unique slug of the monument or relic")
    monument_name_vi: str = Field(..., description="Vietnamese name of the monument")
    zone_name_vi: str = Field(..., description="Name of the spatial zone")
    reign: Optional[str] = Field(None, description="Dynastic reign")
    construction_year: Optional[int] = Field(None, description="Year of initial construction")
    observation_prompt_vi: str = Field(..., description="Fieldwork observation prompt")
    observation_sample_answer_vi: str = Field(..., description="Suggested answer for teacher key")
    primary_source: OfflinePrimarySourceItem
    rubbing_asset: OfflineRubbingAsset
    qr_code_url: str = Field(..., description="Destination URL encoded in the printed QR code")
    offline_inspection_task: OfflineInspectionTask
    offline_task: Optional[OfflineInspectionTask] = None
    audio_transcript: OfflineAudioTranscript
    conclusion_guide_vi: str = Field(..., description="Guide for drawing historical conclusions")
    mee_claim_sample_vi: str = Field(..., description="Sample claim (M) for M-E-E framework")
    mee_evidence_sample_vi: str = Field(..., description="Sample evidence (E) for M-E-E framework")
    mee_uncertainty_sample_vi: str = Field(..., description="Sample uncertainty boundary for M-E-E")

    @model_validator(mode="before")
    @classmethod
    def sync_offline_task(cls, data: Any) -> Any:
        if isinstance(data, dict):
            task = data.get("offline_task") or data.get("offline_inspection_task")
            if task is not None:
                data["offline_task"] = task
                data["offline_inspection_task"] = task
        return data


class LowBandwidthOfflineKitResponse(OfflineKitBaseSchema):
    """Server-authoritative low-bandwidth printable kit bundle."""

    kit_id: str = Field(..., description="Unique kit identifier")
    version: str = Field("1.0.0", description="Kit schema version")
    title_vi: str = Field(..., description="Kit title")
    subtitle_vi: str = Field(..., description="Kit subtitle")
    content_scope: str = Field("STTT_IMPERIAL_CITY", description="Monitored content scope")
    target_audience: str = Field(
        "Học sinh THPT (Lớp 10 - Giáo dục địa phương / Lịch sử)",
        description="Intended pedagogical audience",
    )
    zero_device_guarantee: bool = Field(
        True,
        description="Invariant: 100% of learning outcomes achievable with paper and pencil",
    )
    paper_achievable_percent: int = Field(
        100,
        description="Percentage of curriculum achievable offline without smartphone or AR",
    )
    ar_or_smartphone_mandatory: bool = Field(
        False,
        description="Invariant: Zero mandatory requirement for AR, WebXR, or smartphone",
    )
    cluster_id: str = Field(..., description="Station cluster ID (standard_4, all_16, etc.)")
    stations: List[OfflineKitStation] = Field(default_factory=list)
    rubric_dimensions: List[dict[str, Any]] = Field(default_factory=list)
    exit_ticket_questions: List[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
