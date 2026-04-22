"""
Backend voice helpers for live AI teacher (STT/TTS).
"""

from __future__ import annotations

from typing import Any

import httpx

from ..config import settings


def _voice_api_key() -> str | None:
    return (settings.voice_api_key or settings.deepseek_api_key or "").strip() or None


def _voice_base_v1() -> str:
    raw_base = (settings.voice_base_url or settings.deepseek_base_url or "").strip().rstrip("/")
    if not raw_base:
        raise RuntimeError("Voice API base URL not configured")
    if raw_base.endswith("/v1"):
        return raw_base
    return f"{raw_base}/v1"


def _extract_error_text(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        payload = None
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str) and message.strip():
                return message.strip()
        detail = payload.get("detail")
        if isinstance(detail, str) and detail.strip():
            return detail.strip()
    text = response.text.strip()
    if text:
        return text[:300]
    return f"HTTP {response.status_code}"


def transcribe_audio_bytes(
    *,
    content: bytes,
    filename: str,
    content_type: str | None,
) -> tuple[str, str, str]:
    api_key = _voice_api_key()
    if not api_key:
        raise RuntimeError("Voice API key not configured")
    if not content:
        raise RuntimeError("Audio payload is empty")

    max_size = int(settings.voice_max_audio_bytes or 0)
    if max_size > 0 and len(content) > max_size:
        raise RuntimeError(
            f"Audio payload exceeds limit ({len(content)} > {max_size} bytes)"
        )

    endpoint = f"{_voice_base_v1()}/audio/transcriptions"
    model = str(settings.voice_stt_model or "").strip() or "gpt-4o-mini-transcribe"
    safe_content_type = (content_type or "").strip() or "application/octet-stream"
    safe_filename = (filename or "").strip() or "voice.webm"

    try:
        response = httpx.post(
            endpoint,
            headers={"Authorization": f"Bearer {api_key}"},
            data={"model": model},
            files={"file": (safe_filename, content, safe_content_type)},
            timeout=float(settings.voice_timeout_seconds or 45),
        )
    except httpx.RequestError as exc:
        raise RuntimeError(f"STT request failed: {exc}") from exc

    if response.status_code >= 400:
        raise RuntimeError(
            f"STT request failed ({response.status_code}): {_extract_error_text(response)}"
        )

    try:
        payload: dict[str, Any] = response.json()
    except ValueError as exc:
        raise RuntimeError("STT response was not valid JSON") from exc

    transcript = ""
    if isinstance(payload.get("text"), str):
        transcript = payload["text"].strip()
    elif isinstance(payload.get("transcript"), str):
        transcript = payload["transcript"].strip()

    if not transcript:
        raise RuntimeError("STT did not return transcript text")

    provider = "voice-api"
    model_used = str(payload.get("model") or model).strip() or model
    return transcript, provider, model_used


def synthesize_speech_bytes(
    *,
    text: str,
    voice: str | None = None,
) -> tuple[bytes, str, str, str]:
    api_key = _voice_api_key()
    if not api_key:
        raise RuntimeError("Voice API key not configured")

    normalized_text = str(text or "").strip()
    if not normalized_text:
        raise RuntimeError("TTS input text is empty")

    endpoint = f"{_voice_base_v1()}/audio/speech"
    model = str(settings.voice_tts_model or "").strip() or "gpt-4o-mini-tts"
    voice_name = str(voice or settings.voice_tts_voice or "alloy").strip() or "alloy"

    payload = {
        "model": model,
        "voice": voice_name,
        "input": normalized_text,
        "format": "mp3",
    }

    try:
        response = httpx.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=float(settings.voice_timeout_seconds or 45),
        )
    except httpx.RequestError as exc:
        raise RuntimeError(f"TTS request failed: {exc}") from exc

    if response.status_code >= 400:
        raise RuntimeError(
            f"TTS request failed ({response.status_code}): {_extract_error_text(response)}"
        )

    audio_bytes = response.content
    if not audio_bytes:
        raise RuntimeError("TTS returned empty audio")

    content_type = (
        response.headers.get("content-type", "").strip() or "audio/mpeg"
    )
    provider = "voice-api"
    model_used = model
    return audio_bytes, content_type, provider, model_used
