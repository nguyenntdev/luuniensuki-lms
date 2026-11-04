# -*- coding: utf-8 -*-
"""Domain logic, schemas, and invariants for Live AI Provenance Visibility (V5-T065 / W06-A05).

Core invariants enforced:
1. NEVER mislabel demo, synthetic, or fallback as live AI audio/text.
2. Synthetic or fallback responses always contain visible fallback indicators.
3. Strict telemetry & audit recording of provider mode, guardrail status, and fallback flags.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, Field


# Canonical provider modes
PROVIDER_MODE_LIVE = "live"
PROVIDER_MODE_FALLBACK = "fallback"
PROVIDER_MODE_GUARDRAIL = "guardrail"
PROVIDER_MODE_MOCK = "mock"
PROVIDER_MODE_DEMO = "demo"

VALID_PROVIDER_MODES = {
    PROVIDER_MODE_LIVE,
    PROVIDER_MODE_FALLBACK,
    PROVIDER_MODE_GUARDRAIL,
    PROVIDER_MODE_MOCK,
    PROVIDER_MODE_DEMO,
}

# Guardrail evaluation statuses
GUARDRAIL_STATUS_PASSED = "passed"
GUARDRAIL_STATUS_BLOCKED = "blocked"
GUARDRAIL_STATUS_BYPASSED = "bypassed"
GUARDRAIL_STATUS_NOT_EVALUATED = "not_evaluated"

VALID_GUARDRAIL_STATUSES = {
    GUARDRAIL_STATUS_PASSED,
    GUARDRAIL_STATUS_BLOCKED,
    GUARDRAIL_STATUS_BYPASSED,
    GUARDRAIL_STATUS_NOT_EVALUATED,
}

# Standardized fallback indicators visible in output text
FALLBACK_INDICATOR_HERITAGE = "[Phản hồi dự phòng ngoại tuyến / Offline Heritage Guidance]"
FALLBACK_INDICATOR_GUARDRAIL = "[Nội dung được lọc bởi bộ kiểm duyệt an toàn / Safety Guardrail]"
FALLBACK_INDICATOR_MOCK = "[Nội dung mô phỏng / Synthetic Demo]"
FALLBACK_INDICATOR_STT = "[Phiên âm ngoại tuyến / Offline STT]"
FALLBACK_INDICATOR_TTS = "[Giọng đọc dự phòng / Offline TTS]"

KNOWN_FALLBACK_PROVIDERS = {
    "fallback_policy",
    "guardrail",
    "mock",
    "demo",
    "synthetic",
    "canned",
    "edge-tts",
    "gtts",
}


class LiveAIProvenanceRecord(BaseModel):
    """Immutable record of AI provenance for audit and client transparency."""

    provider_mode: str = Field(
        ...,
        description="Mode of generation: 'live', 'fallback', 'guardrail', 'mock', or 'demo'",
    )
    provider: str = Field(
        ...,
        description="Underlying AI service provider, e.g. 'deepseek', 'fallback_policy', 'guardrail', 'whisper-1'",
    )
    model: Optional[str] = Field(
        None,
        description="Model identifier, e.g. 'deepseek-chat', 'heritage-guidance-v1', 'live-safety-v1'",
    )
    guardrail_status: str = Field(
        GUARDRAIL_STATUS_PASSED,
        description="Status of safety guardrail evaluation ('passed', 'blocked', 'bypassed', 'not_evaluated')",
    )
    guardrail_categories: list[str] = Field(
        default_factory=list,
        description="Content safety categories triggered if guardrail blocked or flagged",
    )
    is_fallback: bool = Field(
        False,
        description="True if generation fell back to static policy, secondary provider, or canned answer",
    )
    is_synthetic: bool = Field(
        False,
        description="True if response is pre-generated, synthetic, mock, or canned",
    )
    used_mock: bool = Field(
        False,
        description="True if synthetic mock data was returned instead of upstream API",
    )
    fallback_indicator: Optional[str] = Field(
        None,
        description="Visible text indicator tag prepended to response if fallback or synthetic",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of response generation",
    )


def ensure_visible_fallback_indicator(text: str, indicator: str) -> str:
    """Prepend the visible fallback indicator to the text if not already present."""
    clean_text = str(text or "").strip()
    clean_indicator = str(indicator or "").strip()
    if not clean_indicator:
        return clean_text
    if clean_indicator in clean_text:
        return clean_text
    return f"{clean_indicator}\n\n{clean_text}".strip()


def validate_live_provenance(
    *,
    provider_mode: str,
    provider: str,
    is_fallback: bool,
    is_synthetic: bool,
    used_mock: bool,
    text: Optional[str] = None,
    fallback_indicator: Optional[str] = None,
) -> None:
    """Enforce negative abuse invariants on live AI responses.

    Rules:
    1. NEVER mislabel demo, mock, or fallback as live AI audio/text.
    2. Synthetic or fallback responses always contain visible fallback indicators.
    """
    prov_mode = str(provider_mode or "").lower().strip()
    prov = str(provider or "").lower().strip()

    # Rule 1: No synthetic / fallback response can claim provider_mode == "live"
    is_non_live = (
        is_fallback
        or is_synthetic
        or used_mock
        or prov in KNOWN_FALLBACK_PROVIDERS
        or prov_mode in (PROVIDER_MODE_FALLBACK, PROVIDER_MODE_GUARDRAIL, PROVIDER_MODE_MOCK, PROVIDER_MODE_DEMO)
    )

    if is_non_live and prov_mode == PROVIDER_MODE_LIVE:
        raise ValueError(
            f"Provenance violation (V5-T065): Response with provider={provider!r}, "
            f"is_fallback={is_fallback}, is_synthetic={is_synthetic}, used_mock={used_mock} "
            f"cannot be mislabeled as provider_mode='live'."
        )

    # Rule 2: Non-live responses must have a visible fallback indicator
    if is_non_live:
        expected_indicator = fallback_indicator or FALLBACK_INDICATOR_HERITAGE
        if text is not None and text.strip():
            has_indicator = any(
                ind in text
                for ind in [
                    expected_indicator,
                    FALLBACK_INDICATOR_HERITAGE,
                    FALLBACK_INDICATOR_GUARDRAIL,
                    FALLBACK_INDICATOR_MOCK,
                    FALLBACK_INDICATOR_STT,
                    FALLBACK_INDICATOR_TTS,
                    "[Dự phòng",
                    "[Phản hồi dự phòng",
                    "[Nội dung được lọc",
                    "[Nội dung mô phỏng",
                    "[Phiên âm ngoại tuyến",
                    "[Giọng đọc dự phòng",
                ]
            )
            if not has_indicator:
                raise ValueError(
                    f"Provenance violation (V5-T065): Synthetic or fallback response must contain "
                    f"a visible fallback indicator. Text preview: {text[:80]!r}"
                )


def resolve_live_ai_provenance(
    *,
    provider: str,
    model: Optional[str] = None,
    requested_mode: str = "hint-first",
    guardrail_safe: bool = True,
    guardrail_categories: Optional[list[str]] = None,
    is_live_call_successful: bool = False,
    forced_mock: bool = False,
    is_demo: bool = False,
    text: Optional[str] = None,
) -> tuple[LiveAIProvenanceRecord, str]:
    """Resolve and validate the canonical provenance record and ensure visible text tagging."""
    cats = list(guardrail_categories or [])

    if not guardrail_safe:
        provider_mode = PROVIDER_MODE_GUARDRAIL
        resolved_provider = "guardrail"
        resolved_model = model or "live-safety-v1"
        guardrail_status = GUARDRAIL_STATUS_BLOCKED
        is_fallback = True
        is_synthetic = True
        used_mock = True
        fallback_indicator = FALLBACK_INDICATOR_GUARDRAIL
    elif is_demo:
        provider_mode = PROVIDER_MODE_DEMO
        resolved_provider = provider or "demo_provider"
        resolved_model = model or "demo-v1"
        guardrail_status = GUARDRAIL_STATUS_PASSED
        is_fallback = True
        is_synthetic = True
        used_mock = True
        fallback_indicator = FALLBACK_INDICATOR_MOCK
    elif forced_mock or not is_live_call_successful:
        provider_mode = PROVIDER_MODE_FALLBACK
        resolved_provider = "fallback_policy"
        resolved_model = model or "heritage-guidance-v1"
        guardrail_status = GUARDRAIL_STATUS_PASSED
        is_fallback = True
        is_synthetic = True
        used_mock = True
        fallback_indicator = FALLBACK_INDICATOR_HERITAGE
    else:
        provider_mode = PROVIDER_MODE_LIVE
        resolved_provider = provider
        resolved_model = model
        guardrail_status = GUARDRAIL_STATUS_PASSED
        is_fallback = False
        is_synthetic = False
        used_mock = False
        fallback_indicator = None

    tagged_text = str(text or "")
    if fallback_indicator and tagged_text.strip():
        tagged_text = ensure_visible_fallback_indicator(tagged_text, fallback_indicator)

    # Validate invariants
    validate_live_provenance(
        provider_mode=provider_mode,
        provider=resolved_provider,
        is_fallback=is_fallback,
        is_synthetic=is_synthetic,
        used_mock=used_mock,
        text=tagged_text if tagged_text.strip() else None,
        fallback_indicator=fallback_indicator,
    )

    provenance = LiveAIProvenanceRecord(
        provider_mode=provider_mode,
        provider=resolved_provider,
        model=resolved_model,
        guardrail_status=guardrail_status,
        guardrail_categories=cats,
        is_fallback=is_fallback,
        is_synthetic=is_synthetic,
        used_mock=used_mock,
        fallback_indicator=fallback_indicator,
    )

    return provenance, tagged_text
