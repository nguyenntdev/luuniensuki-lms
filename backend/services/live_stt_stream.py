"""
Streaming STT adapter for the real-time conversational AI teacher (Path B).

Wraps the existing, synchronous :func:`backend.services.live_voice.transcribe_audio_bytes`
in a chunked/streaming-shaped interface so the realtime audio loop can feed
rolling audio buffers and pull interim/final transcripts without caring which
provider is behind it. No new dependencies; provider-pluggable; mockable.

Design notes
------------
* ``StreamingSTT`` is the small contract every backend implements:
    - ``feed(chunk)``  accumulate an audio chunk
    - ``interim()``    best-effort current transcript (may be "")
    - ``final()``      commit the buffered audio, return the final transcript,
                       and reset the buffer for the next utterance.

* ``VoiceApiStreamingSTT`` buffers chunks and, on ``final()``, sends the joined
  buffer to the existing voice API (``live_voice.transcribe_audio_bytes``).
  IMPORTANT: the voice API is *not* truly streaming — it transcribes a complete
  audio blob. So ``interim()`` here is a best-effort placeholder that returns the
  last committed final transcript (or ""). True low-latency partials require a
  genuinely streaming provider; this adapter keeps the call sites stable until
  such a provider is wired in.

* ``MockStreamingSTT`` is network-free and deterministic for tests: it treats fed
  chunks as UTF-8 text, so ``interim()`` returns the running decode and
  ``final()`` returns the joined decode (then resets).

* ``build_streaming_stt`` is the factory. Provider selection order:
    1. explicit ``provider`` arg, else
    2. ``settings.live_stt_provider`` (optional; never required), else
    3. ``LIVE_STT_PROVIDER`` env var, else
    4. ``"voice-api"`` default.
  Missing settings must NOT crash — every lookup is defensive.

This module performs NO database writes. The pure ``build_*_event_payload``
helpers only shape dicts for the ``voice_user_partial`` / ``voice_user_final``
live_events that the worker already consumes for history.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Optional

# Provider constants ---------------------------------------------------------
PROVIDER_VOICE_API = "voice-api"
PROVIDER_MOCK = "mock"
DEFAULT_PROVIDER = PROVIDER_VOICE_API

# Defaults used when calling the existing voice API. WebM/Opus is what the
# browser captures and what the legacy turn path already sends.
_DEFAULT_FILENAME = "voice.webm"
_DEFAULT_CONTENT_TYPE = "audio/webm"


class StreamingSTT(ABC):
    """Contract for a chunked/streaming speech-to-text backend.

    Implementations accumulate audio via :meth:`feed`, expose a best-effort
    :meth:`interim` transcript, and commit a :meth:`final` transcript that also
    resets the internal buffer for the next utterance.
    """

    @abstractmethod
    def feed(self, audio_chunk: bytes) -> None:
        """Accumulate an audio chunk into the current utterance buffer."""

    @abstractmethod
    def interim(self) -> str:
        """Return a best-effort current transcript. May be "" if unavailable."""

    @abstractmethod
    def final(self) -> str:
        """Commit the buffered audio, return the final transcript, reset buffer."""


class VoiceApiStreamingSTT(StreamingSTT):
    """Streaming-shaped adapter over the existing (non-streaming) voice API.

    Buffers fed chunks; on :meth:`final` it joins the buffer and hands it to
    :func:`live_voice.transcribe_audio_bytes`. Because that API is not truly
    streaming, :meth:`interim` is a best-effort placeholder that returns the last
    committed final transcript (or "") rather than a live partial.
    """

    def __init__(
        self,
        *,
        session_id: Optional[str] = None,
        filename: str = _DEFAULT_FILENAME,
        content_type: Optional[str] = _DEFAULT_CONTENT_TYPE,
    ) -> None:
        self._session_id = session_id
        self._filename = filename or _DEFAULT_FILENAME
        self._content_type = content_type or _DEFAULT_CONTENT_TYPE
        self._buffer: bytearray = bytearray()
        self._last_final: str = ""

    def feed(self, audio_chunk: bytes) -> None:
        if not audio_chunk:
            return
        self._buffer.extend(audio_chunk)

    def interim(self) -> str:
        # The voice API isn't truly streaming, so there's no real partial to
        # surface mid-utterance. Best-effort: echo the last committed final
        # transcript (empty until the first final()). Callers that want true
        # partials must use a streaming-capable provider.
        return self._last_final

    def final(self) -> str:
        # Import lazily so importing this module never forces network/config
        # side effects of live_voice (and to avoid import cycles).
        from . import live_voice

        content = bytes(self._buffer)
        # Reset the buffer up front so a failed transcription doesn't leave a
        # stale partial utterance bleeding into the next turn.
        self._buffer = bytearray()
        if not content:
            return ""

        transcript, _provider, _model = live_voice.transcribe_audio_bytes(
            content=content,
            filename=self._filename,
            content_type=self._content_type,
            session_id=self._session_id,
        )
        self._last_final = transcript or ""
        return self._last_final


class MockStreamingSTT(StreamingSTT):
    """Deterministic, network-free STT for tests.

    Treats fed chunks as UTF-8 text. ``interim()`` returns the running decode of
    everything fed so far; ``final()`` returns the same decode and resets the
    buffer. Invalid UTF-8 is decoded leniently (``errors="replace"``).
    """

    def __init__(self, *, session_id: Optional[str] = None) -> None:
        self._session_id = session_id
        self._buffer: bytearray = bytearray()

    def feed(self, audio_chunk: bytes) -> None:
        if not audio_chunk:
            return
        self._buffer.extend(audio_chunk)

    def _decode(self) -> str:
        return bytes(self._buffer).decode("utf-8", errors="replace")

    def interim(self) -> str:
        return self._decode()

    def final(self) -> str:
        text = self._decode()
        self._buffer = bytearray()
        return text


def _resolve_provider(provider: Optional[str]) -> str:
    """Resolve the provider name defensively (never crashes on missing config).

    Order: explicit arg -> settings.live_stt_provider -> $LIVE_STT_PROVIDER ->
    default ("voice-api").
    """
    candidate = (provider or "").strip()
    if not candidate:
        try:
            from ..config import settings

            candidate = (getattr(settings, "live_stt_provider", None) or "").strip()
        except Exception:  # pragma: no cover - config import must never break factory
            candidate = ""
    if not candidate:
        candidate = (os.environ.get("LIVE_STT_PROVIDER") or "").strip()
    return candidate.lower() or DEFAULT_PROVIDER


def build_streaming_stt(
    provider: Optional[str] = None,
    *,
    session_id: Optional[str] = None,
) -> StreamingSTT:
    """Build a :class:`StreamingSTT` for ``provider``.

    ``"mock"`` -> :class:`MockStreamingSTT`; anything else (including the default
    ``"voice-api"``) -> :class:`VoiceApiStreamingSTT`. Missing/blank settings are
    tolerated and fall back to the default provider.
    """
    resolved = _resolve_provider(provider)
    if resolved == PROVIDER_MOCK:
        return MockStreamingSTT(session_id=session_id)
    return VoiceApiStreamingSTT(session_id=session_id)


def promote_interim_to_final(interim: str, final: str) -> str:
    """Deterministic promotion: prefer ``final`` when non-empty, else ``interim``.

    Lets callers commit a turn without re-deriving which transcript to keep when
    the final transcription came back empty (e.g. a provider hiccup) but a usable
    interim exists.
    """
    final_text = (final or "").strip()
    if final_text:
        return final_text
    return (interim or "").strip()


def build_partial_event_payload(request_id: str, text: str) -> dict:
    """Pure payload for a ``voice_user_partial`` live_event (no I/O).

    Shaped like the existing user-voice events: ``request_id`` + ``text`` (the
    fields the worker/frontend read), plus ``partial=True`` so consumers can tell
    interim captions from committed ones.
    """
    return {
        "request_id": str(request_id or ""),
        "text": str(text or ""),
        "partial": True,
    }


def build_final_event_payload(request_id: str, text: str) -> dict:
    """Pure payload for a ``voice_user_final`` live_event (no I/O).

    Matches what the worker already consumes for history (``request_id`` +
    ``text``); ``partial=False`` marks it as the committed transcript.
    """
    return {
        "request_id": str(request_id or ""),
        "text": str(text or ""),
        "partial": False,
    }
