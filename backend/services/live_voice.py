"""
Backend voice helpers for live AI teacher (STT/TTS).
"""

from __future__ import annotations

import asyncio
import io
import time
from typing import Any

import httpx

from ..config import settings
from . import live_circuit_breaker
from . import live_observability

try:
    import edge_tts
except Exception:  # pragma: no cover - optional dependency in some environments
    edge_tts = None

try:
    from gtts import gTTS
except Exception:  # pragma: no cover - optional dependency in some environments
    gTTS = None


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
    session_id: str | None = None,
) -> tuple[str, str, str]:
    api_key = _voice_api_key()
    if not api_key:
        raise RuntimeError("Voice API key not configured")
    if not content:
        raise RuntimeError("Audio payload is empty")
    provider = "voice-api"

    max_size = int(settings.voice_max_audio_bytes or 0)
    if max_size > 0 and len(content) > max_size:
        raise RuntimeError(
            f"Audio payload exceeds limit ({len(content)} > {max_size} bytes)"
        )

    endpoint = f"{_voice_base_v1()}/audio/transcriptions"
    model = str(settings.voice_stt_model or "").strip() or "gpt-4o-transcribe"
    safe_content_type = (content_type or "").strip() or "application/octet-stream"
    safe_filename = (filename or "").strip() or "voice.webm"
    started = time.perf_counter()

    # Bias the recognizer toward Vietnamese to improve accuracy and reduce
    # latency (skips language auto-detection). An optional domain prompt nudges
    # the model toward heritage/lich-su vocabulary.
    form_data: dict[str, str] = {"model": model}
    stt_language = str(settings.voice_stt_language or "").strip()
    if stt_language:
        form_data["language"] = stt_language
    stt_prompt = str(settings.voice_stt_prompt or "").strip()
    if stt_prompt:
        form_data["prompt"] = stt_prompt
    # Low temperature keeps transcription verbatim.
    form_data["temperature"] = "0"

    try:
        live_circuit_breaker.assert_provider_available(provider)
    except RuntimeError:
        live_observability.record_point(
            session_id=session_id,
            operation="stt",
            provider=provider,
            latency_ms=0.0,
            ok=False,
            drop=True,
        )
        raise

    try:
        response = httpx.post(
            endpoint,
            headers={"Authorization": f"Bearer {api_key}"},
            data=form_data,
            files={"file": (safe_filename, content, safe_content_type)},
            timeout=float(settings.voice_timeout_seconds or 45),
        )
    except httpx.RequestError as exc:
        live_circuit_breaker.record_failure(provider, str(exc))
        live_observability.record_point(
            session_id=session_id,
            operation="stt",
            provider=provider,
            latency_ms=(time.perf_counter() - started) * 1000.0,
            ok=False,
            drop=False,
        )
        raise RuntimeError(f"STT request failed: {exc}") from exc

    if response.status_code >= 400:
        live_circuit_breaker.record_failure(provider, _extract_error_text(response))
        live_observability.record_point(
            session_id=session_id,
            operation="stt",
            provider=provider,
            latency_ms=(time.perf_counter() - started) * 1000.0,
            ok=False,
            drop=False,
        )
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
        live_circuit_breaker.record_failure(provider, "empty_transcript")
        live_observability.record_point(
            session_id=session_id,
            operation="stt",
            provider=provider,
            latency_ms=(time.perf_counter() - started) * 1000.0,
            ok=False,
            drop=False,
        )
        raise RuntimeError("STT did not return transcript text")

    model_used = str(payload.get("model") or model).strip() or model
    live_circuit_breaker.record_success(provider)
    live_observability.record_point(
        session_id=session_id,
        operation="stt",
        provider=provider,
        latency_ms=(time.perf_counter() - started) * 1000.0,
        ok=True,
        drop=False,
        tokens_in=0,
        tokens_out=max(1, int(len(transcript) / 4)),
    )
    return transcript, provider, model_used


def synthesize_speech_bytes(
    *,
    text: str,
    voice: str | None = None,
    session_id: str | None = None,
) -> tuple[bytes, str, str, str]:
    normalized_text = str(text or "").strip()
    if not normalized_text:
        raise RuntimeError("TTS input text is empty")

    errors: list[str] = []
    try:
        return _synthesize_with_voice_api(
            text=normalized_text,
            voice=voice,
            session_id=session_id,
        )
    except RuntimeError as exc:
        errors.append(str(exc))

    if bool(settings.voice_tts_allow_edge_fallback):
        try:
            return _synthesize_with_edge_tts(
                text=normalized_text,
                voice=voice,
                session_id=session_id,
            )
        except RuntimeError as fallback_exc:
            errors.append(f"Edge TTS fallback failed: {fallback_exc}")

    if bool(settings.voice_tts_allow_gtts_fallback):
        try:
            return _synthesize_with_gtts(
                text=normalized_text,
                session_id=session_id,
            )
        except RuntimeError as fallback_exc:
            errors.append(f"gTTS fallback failed: {fallback_exc}")

    if errors:
        raise RuntimeError(" | ".join(errors))
    raise RuntimeError("No TTS provider is enabled")


def _synthesize_with_voice_api(
    *,
    text: str,
    voice: str | None,
    session_id: str | None,
) -> tuple[bytes, str, str, str]:
    api_key = _voice_api_key()
    if not api_key:
        raise RuntimeError("Voice API key not configured")

    endpoint = f"{_voice_base_v1()}/audio/speech"
    model = str(settings.voice_tts_model or "").strip() or "gpt-4o-mini-tts"
    voice_name = str(voice or settings.voice_tts_voice or "alloy").strip() or "alloy"
    provider = "voice-api"
    started = time.perf_counter()

    try:
        live_circuit_breaker.assert_provider_available(provider)
    except RuntimeError:
        live_observability.record_point(
            session_id=session_id,
            operation="tts",
            provider=provider,
            latency_ms=0.0,
            ok=False,
            drop=True,
        )
        raise

    payload = {
        "model": model,
        "voice": voice_name,
        "input": text,
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
        live_circuit_breaker.record_failure(provider, str(exc))
        live_observability.record_point(
            session_id=session_id,
            operation="tts",
            provider=provider,
            latency_ms=(time.perf_counter() - started) * 1000.0,
            ok=False,
            drop=False,
        )
        raise RuntimeError(f"TTS request failed: {exc}") from exc

    if response.status_code >= 400:
        live_circuit_breaker.record_failure(provider, _extract_error_text(response))
        live_observability.record_point(
            session_id=session_id,
            operation="tts",
            provider=provider,
            latency_ms=(time.perf_counter() - started) * 1000.0,
            ok=False,
            drop=False,
        )
        raise RuntimeError(
            f"TTS request failed ({response.status_code}): {_extract_error_text(response)}"
        )

    audio_bytes = response.content
    if not audio_bytes:
        live_circuit_breaker.record_failure(provider, "empty_tts_audio")
        live_observability.record_point(
            session_id=session_id,
            operation="tts",
            provider=provider,
            latency_ms=(time.perf_counter() - started) * 1000.0,
            ok=False,
            drop=False,
        )
        raise RuntimeError("TTS returned empty audio")

    content_type = (
        response.headers.get("content-type", "").strip() or "audio/mpeg"
    )
    model_used = model
    live_circuit_breaker.record_success(provider)
    live_observability.record_point(
        session_id=session_id,
        operation="tts",
        provider=provider,
        latency_ms=(time.perf_counter() - started) * 1000.0,
        ok=True,
        drop=False,
        tokens_in=max(1, int(len(text) / 4)),
        tokens_out=0,
    )
    return audio_bytes, content_type, provider, model_used


def _run_async(coro: Any) -> Any:
    try:
        return asyncio.run(coro)
    except RuntimeError as exc:
        if "asyncio.run() cannot be called from a running event loop" not in str(exc):
            raise
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


def _resolve_edge_voice(voice: str | None) -> str:
    requested = str(voice or "").strip()
    fallback_default = (
        str(settings.voice_edge_tts_voice or "").strip() or "vi-VN-HoaiMyNeural"
    )
    if not requested:
        return fallback_default

    normalized = requested.lower()
    if normalized in {"alloy", "echo", "fable", "onyx", "nova", "shimmer"}:
        return fallback_default
    return requested


async def _edge_tts_render(
    *,
    text: str,
    voice: str,
    rate: str,
    pitch: str,
    volume: str,
) -> bytes:
    communicator = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        pitch=pitch,
        volume=volume,
    )
    chunks = bytearray()
    async for event in communicator.stream():
        if event.get("type") != "audio":
            continue
        chunk = event.get("data")
        if isinstance(chunk, (bytes, bytearray)):
            chunks.extend(chunk)
    return bytes(chunks)


def _synthesize_with_edge_tts(
    *,
    text: str,
    voice: str | None,
    session_id: str | None,
) -> tuple[bytes, str, str, str]:
    if edge_tts is None:
        raise RuntimeError("edge-tts package is not installed")

    provider = "edge-tts"
    started = time.perf_counter()
    resolved_voice = _resolve_edge_voice(voice)
    rate = str(settings.voice_edge_tts_rate or "+0%").strip() or "+0%"
    pitch = str(settings.voice_edge_tts_pitch or "+0Hz").strip() or "+0Hz"
    volume = str(settings.voice_edge_tts_volume or "+0%").strip() or "+0%"

    try:
        live_circuit_breaker.assert_provider_available(provider)
    except RuntimeError:
        live_observability.record_point(
            session_id=session_id,
            operation="tts",
            provider=provider,
            latency_ms=0.0,
            ok=False,
            drop=True,
        )
        raise

    try:
        audio_bytes = _run_async(
            _edge_tts_render(
                text=text,
                voice=resolved_voice,
                rate=rate,
                pitch=pitch,
                volume=volume,
            )
        )
    except Exception as exc:
        live_circuit_breaker.record_failure(provider, str(exc))
        live_observability.record_point(
            session_id=session_id,
            operation="tts",
            provider=provider,
            latency_ms=(time.perf_counter() - started) * 1000.0,
            ok=False,
            drop=False,
        )
        raise RuntimeError(f"Edge TTS request failed: {exc}") from exc

    if not audio_bytes:
        live_circuit_breaker.record_failure(provider, "empty_tts_audio")
        live_observability.record_point(
            session_id=session_id,
            operation="tts",
            provider=provider,
            latency_ms=(time.perf_counter() - started) * 1000.0,
            ok=False,
            drop=False,
        )
        raise RuntimeError("Edge TTS returned empty audio")

    live_circuit_breaker.record_success(provider)
    live_observability.record_point(
        session_id=session_id,
        operation="tts",
        provider=provider,
        latency_ms=(time.perf_counter() - started) * 1000.0,
        ok=True,
        drop=False,
        tokens_in=max(1, int(len(text) / 4)),
        tokens_out=0,
    )
    return audio_bytes, "audio/mpeg", provider, resolved_voice


def _synthesize_with_gtts(
    *,
    text: str,
    session_id: str | None,
) -> tuple[bytes, str, str, str]:
    if gTTS is None:
        raise RuntimeError("gTTS package is not installed")

    provider = "gtts"
    started = time.perf_counter()
    lang = str(settings.voice_gtts_lang or "vi").strip() or "vi"
    tld = str(settings.voice_gtts_tld or "com.vn").strip() or "com.vn"
    slow = bool(settings.voice_gtts_slow)

    try:
        live_circuit_breaker.assert_provider_available(provider)
    except RuntimeError:
        live_observability.record_point(
            session_id=session_id,
            operation="tts",
            provider=provider,
            latency_ms=0.0,
            ok=False,
            drop=True,
        )
        raise

    try:
        output = io.BytesIO()
        speaker = gTTS(text=text, lang=lang, tld=tld, slow=slow)
        speaker.write_to_fp(output)
        audio_bytes = output.getvalue()
    except Exception as exc:
        live_circuit_breaker.record_failure(provider, str(exc))
        live_observability.record_point(
            session_id=session_id,
            operation="tts",
            provider=provider,
            latency_ms=(time.perf_counter() - started) * 1000.0,
            ok=False,
            drop=False,
        )
        raise RuntimeError(f"gTTS request failed: {exc}") from exc

    if not audio_bytes:
        live_circuit_breaker.record_failure(provider, "empty_tts_audio")
        live_observability.record_point(
            session_id=session_id,
            operation="tts",
            provider=provider,
            latency_ms=(time.perf_counter() - started) * 1000.0,
            ok=False,
            drop=False,
        )
        raise RuntimeError("gTTS returned empty audio")

    live_circuit_breaker.record_success(provider)
    live_observability.record_point(
        session_id=session_id,
        operation="tts",
        provider=provider,
        latency_ms=(time.perf_counter() - started) * 1000.0,
        ok=True,
        drop=False,
        tokens_in=max(1, int(len(text) / 4)),
        tokens_out=0,
    )
    return audio_bytes, "audio/mpeg", provider, f"{lang}-{tld}"
