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


class STTNoSpeechError(RuntimeError):
    """Raised when STT produced no usable speech (empty or a hallucination).

    Subclasses RuntimeError so existing ``except RuntimeError`` handlers keep
    working, but callers that want to distinguish "no speech" from a real
    provider failure can catch this type and stay silent instead of surfacing
    an error or feeding filler text to the LLM.
    """


def _normalize_base_url(url: str | None) -> str:
    raw = (url or "").strip().rstrip("/")
    if raw.endswith("/v1"):
        raw = raw[:-3].rstrip("/")
    return raw


def _voice_api_key() -> str | None:
    voice_key = (settings.voice_api_key or "").strip()
    if voice_key:
        return voice_key

    voice_base = (settings.voice_base_url or "").strip()
    deepseek_base = (settings.deepseek_base_url or "").strip()
    deepseek_key = (settings.deepseek_api_key or "").strip()

    # Prevent leaking deepseek_api_key to a third-party voice base URL
    # when voice_api_key is not explicitly configured.
    if voice_base and _normalize_base_url(voice_base) != _normalize_base_url(deepseek_base):
        return None

    return deepseek_key or None


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


# Known STT hallucination outputs on silence / noise / very short clips.
# Whisper-family models frequently emit these stock phrases (often in the wrong
# language) when the audio has little or no real speech. We drop them so they
# never reach the LLM as a "user turn".
_STT_HALLUCINATION_PHRASES = frozenset(
    {
        "you",
        "bye",
        "bye.",
        "bye bye",
        "thank you",
        "thank you.",
        "thanks for watching",
        "thanks for watching!",
        "thank you for watching",
        "ciao",
        "ciao.",
        "tchau",
        "tchau, tchau.",
        "see you",
        "see you.",
        "see you, ciao.",
        "and ciao.",
        "okay",
        "ok",
        "hmm",
        "uh",
        "um",
        "...",
        ".",
        "merci",
        "gracias",
        "obrigado",
        "amara.org",
        "subtitles by the amara.org community",
    }
)


def _looks_like_vietnamese(text: str) -> bool:
    """True if the text contains Vietnamese-specific diacritics or common words."""
    if any(
        ch in text
        for ch in "ăâđêôơưĂÂĐÊÔƠƯàáảãạèéẻẽẹìíỉĩịòóỏõọùúủũụỳýỷỹỵ"
        "ÀÁẢÃẠÈÉẺẼẸÌÍỈĨỊÒÓỎÕỌÙÚỦŨỤỲÝỶỸỴ"
    ):
        return True
    lowered = f" {text.lower()} "
    common = (
        " là ", " gì ", " không ", " của ", " và ", " có ", " cho ", " nào ",
        " xin ", " chào ", " được ", " thế ", " sao ", " ạ ", " nhé ",
    )
    return any(word in lowered for word in common)


def _is_probable_hallucination(transcript: str) -> bool:
    """Detect STT filler/hallucinations that should be dropped, not answered."""
    normalized = transcript.strip().lower()
    if not normalized:
        return True
    # Exact match against the known stock-phrase set.
    if normalized in _STT_HALLUCINATION_PHRASES:
        return True
    # Substring match for well-known Whisper silence hallucinations. These are
    # YouTube outros baked into the training data and surface on silent/noisy
    # Vietnamese clips ("Hãy subscribe cho kênh Ghiền Mì Gõ...").
    for needle in (
        "subscribe",
        "ghiền mì gõ",
        "ghien mi go",
        "đăng ký kênh",
        "dang ky kenh",
        "thank you for watching",
        "thanks for watching",
        "hẹn gặp lại",
        "amara.org",
        "phụ đề",
    ):
        if needle in normalized:
            return True
    # Strip surrounding punctuation/whitespace and retry.
    stripped = normalized.strip(" .,!?\"'…-")
    if stripped in _STT_HALLUCINATION_PHRASES:
        return True
    # Short, non-Vietnamese single-token output (e.g. "you", "ciao") is almost
    # always a hallucination for a Vietnamese-only classroom.
    if len(stripped) <= 12 and not _looks_like_vietnamese(transcript):
        # Allow short Vietnamese-looking inputs; reject short Latin filler.
        if all(ord(ch) < 128 for ch in stripped.replace(" ", "")):
            return True
    return False


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
    # The whisper-1 endpoint on some gateways rejects the `temperature`
    # parameter, while the gpt-4o-* transcribe models accept it. Only send a
    # (verbatim) low temperature for the gpt-4o family.
    is_whisper = "whisper" in model.lower()
    if not is_whisper:
        form_data["temperature"] = "0"
    else:
        # whisper-1 supports verbose_json, which returns per-segment
        # `no_speech_prob` / `avg_logprob`. These are the most reliable signal
        # for rejecting silence hallucinations (e.g. "Hãy subscribe...",
        # "Thank you for watching") before they reach the LLM.
        form_data["response_format"] = "verbose_json"

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

    # Some gateways/models reject specific optional fields (e.g. whisper-1 may
    # 400 on `temperature`). Try the full request first, then progressively
    # strip optional params on a 400 before giving up — this keeps STT working
    # across model/gateway differences without manual reconfiguration.
    optional_keys = ["temperature", "prompt", "language"]
    attempts: list[dict[str, str]] = [dict(form_data)]
    reduced = dict(form_data)
    for key in optional_keys:
        if key in reduced:
            reduced = {k: v for k, v in reduced.items() if k != key}
            attempts.append(dict(reduced))

    response = None
    for attempt_index, attempt_data in enumerate(attempts):
        try:
            response = httpx.post(
                endpoint,
                headers={"Authorization": f"Bearer {api_key}"},
                data=attempt_data,
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

        # Retry with fewer optional params only on a 400 (bad request).
        if response.status_code == 400 and attempt_index < len(attempts) - 1:
            continue
        break

    if response is None:  # pragma: no cover - defensive
        raise RuntimeError("STT request produced no response")

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

    # whisper verbose_json: reject clips that are almost certainly silence/noise
    # using the per-segment no_speech_prob (high) + avg_logprob (very low). This
    # catches the stock "subscribe / thank you for watching" hallucinations even
    # when their exact wording is not in the phrase blocklist.
    segments = payload.get("segments")
    if isinstance(segments, list) and segments:
        speechful = []
        for seg in segments:
            if not isinstance(seg, dict):
                continue
            no_speech = seg.get("no_speech_prob")
            avg_logprob = seg.get("avg_logprob")
            try:
                no_speech_val = float(no_speech) if no_speech is not None else 0.0
            except (TypeError, ValueError):
                no_speech_val = 0.0
            try:
                avg_logprob_val = float(avg_logprob) if avg_logprob is not None else 0.0
            except (TypeError, ValueError):
                avg_logprob_val = 0.0
            # Drop a segment that is very likely silence: high no-speech
            # probability paired with low average token confidence.
            if no_speech_val >= 0.6 and avg_logprob_val <= -0.4:
                continue
            if no_speech_val >= 0.85:
                continue
            speechful.append(str(seg.get("text") or ""))
        filtered = "".join(speechful).strip()
        # If filtering removed everything, treat as no speech.
        if not filtered:
            live_circuit_breaker.record_success(provider)
            live_observability.record_point(
                session_id=session_id,
                operation="stt",
                provider=provider,
                latency_ms=(time.perf_counter() - started) * 1000.0,
                ok=True,
                drop=True,
                tokens_in=0,
                tokens_out=0,
            )
            raise STTNoSpeechError("Dropped STT segments with high no_speech_prob")
        transcript = filtered

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

    # Drop common hallucinations (stock phrases / wrong-language filler that
    # Whisper-family models emit on silence or noise) so they never become a
    # user turn. This is a successful call from the provider's perspective, so
    # we record success on the breaker but raise a sentinel the callers treat
    # as "no speech detected".
    if _is_probable_hallucination(transcript):
        live_circuit_breaker.record_success(provider)
        live_observability.record_point(
            session_id=session_id,
            operation="stt",
            provider=provider,
            latency_ms=(time.perf_counter() - started) * 1000.0,
            ok=True,
            drop=True,
            tokens_in=0,
            tokens_out=0,
        )
        raise STTNoSpeechError(
            f"Dropped probable STT hallucination: {transcript!r}"
        )

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
    # Expressive voice: gpt-4o(-mini)-tts accepts a style "instructions" field
    # for a warm, natural teacher delivery. Older models (tts-1) ignore/​reject
    # it, so only attach when the model supports it.
    if "gpt-4o" in model.lower():
        instructions = str(settings.voice_tts_instructions or "").strip()
        if instructions:
            payload["instructions"] = instructions

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
