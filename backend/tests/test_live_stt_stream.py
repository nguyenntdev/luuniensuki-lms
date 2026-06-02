"""Tests for the streaming STT adapter (Task 4.3).

Covers the network-free pieces of ``backend/services/live_stt_stream.py``:
``MockStreamingSTT`` interim->final promotion, the factory selecting the mock
provider, the pure ``promote_interim_to_final`` rule, and the shape of the
``voice_user_partial`` / ``voice_user_final`` payload builders.

Everything here uses ``MockStreamingSTT`` only — no network, no voice API.

Validates: Requirements (Task 4.3 — interim->final promotion against the mock
provider).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Mirror the repo's existing test bootstrap (see test_live_turn.py): make the
# repo root importable so ``backend.services`` resolves regardless of cwd.
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from backend.services.live_stt_stream import (  # noqa: E402
    MockStreamingSTT,
    StreamingSTT,
    VoiceApiStreamingSTT,
    build_final_event_payload,
    build_partial_event_payload,
    build_streaming_stt,
    promote_interim_to_final,
)


# --------------------------------------------------------------------------- #
# MockStreamingSTT: interim -> final
# --------------------------------------------------------------------------- #


def test_mock_interim_tracks_running_decode() -> None:
    stt = MockStreamingSTT()
    assert stt.interim() == ""
    stt.feed(b"hello")
    assert stt.interim() == "hello"
    stt.feed(b" world")
    assert stt.interim() == "hello world"


def test_mock_final_returns_full_transcript_and_resets() -> None:
    stt = MockStreamingSTT()
    stt.feed(b"hello")
    stt.feed(b" world")
    assert stt.final() == "hello world"
    # Buffer reset: a fresh interim/final after commit is empty.
    assert stt.interim() == ""
    assert stt.final() == ""


def test_mock_supports_back_to_back_utterances() -> None:
    stt = MockStreamingSTT()
    stt.feed(b"first")
    assert stt.final() == "first"
    stt.feed(b"second")
    assert stt.interim() == "second"
    assert stt.final() == "second"


def test_mock_interim_promotes_to_final_consistently() -> None:
    # The promotion helper should keep the committed final transcript when one
    # exists; here interim and final agree.
    stt = MockStreamingSTT()
    stt.feed(b"the quick brown fox")
    interim = stt.interim()
    final = stt.final()
    assert interim == "the quick brown fox"
    assert final == "the quick brown fox"
    assert promote_interim_to_final(interim, final) == "the quick brown fox"


def test_mock_ignores_empty_chunks() -> None:
    stt = MockStreamingSTT()
    stt.feed(b"")
    assert stt.interim() == ""
    stt.feed(b"data")
    stt.feed(b"")
    assert stt.interim() == "data"


# --------------------------------------------------------------------------- #
# Factory
# --------------------------------------------------------------------------- #


def test_factory_returns_mock_for_mock_provider() -> None:
    stt = build_streaming_stt("mock")
    assert isinstance(stt, MockStreamingSTT)
    assert isinstance(stt, StreamingSTT)


def test_factory_is_case_insensitive_for_mock() -> None:
    assert isinstance(build_streaming_stt("MOCK"), MockStreamingSTT)


def test_factory_defaults_to_voice_api_when_unspecified() -> None:
    # No explicit provider and (in the test env) no LIVE_STT_PROVIDER set ->
    # the default voice-api adapter. This must not crash on missing settings.
    stt = build_streaming_stt(None)
    assert isinstance(stt, VoiceApiStreamingSTT)


def test_factory_unknown_provider_falls_back_to_voice_api() -> None:
    stt = build_streaming_stt("some-unknown-provider")
    assert isinstance(stt, VoiceApiStreamingSTT)


def test_factory_env_var_selects_mock(monkeypatch) -> None:
    monkeypatch.setenv("LIVE_STT_PROVIDER", "mock")
    assert isinstance(build_streaming_stt(None), MockStreamingSTT)


# --------------------------------------------------------------------------- #
# promote_interim_to_final
# --------------------------------------------------------------------------- #


def test_promote_prefers_final_when_present() -> None:
    assert promote_interim_to_final("partial text", "final text") == "final text"


def test_promote_falls_back_to_interim_when_final_empty() -> None:
    assert promote_interim_to_final("partial text", "") == "partial text"


def test_promote_strips_whitespace() -> None:
    assert promote_interim_to_final("  interim  ", "   ") == "interim"
    assert promote_interim_to_final("   ", "  final ") == "final"


def test_promote_returns_empty_when_both_empty() -> None:
    assert promote_interim_to_final("", "") == ""
    assert promote_interim_to_final("   ", "") == ""


# --------------------------------------------------------------------------- #
# Payload builders (pure dict shape)
# --------------------------------------------------------------------------- #


def test_partial_payload_shape() -> None:
    payload = build_partial_event_payload("req-123", "hello")
    assert payload == {
        "request_id": "req-123",
        "text": "hello",
        "partial": True,
    }


def test_final_payload_shape() -> None:
    payload = build_final_event_payload("req-123", "hello world")
    assert payload == {
        "request_id": "req-123",
        "text": "hello world",
        "partial": False,
    }


def test_payload_builders_coerce_none_to_strings() -> None:
    partial = build_partial_event_payload(None, None)  # type: ignore[arg-type]
    final = build_final_event_payload(None, None)  # type: ignore[arg-type]
    assert partial == {"request_id": "", "text": "", "partial": True}
    assert final == {"request_id": "", "text": "", "partial": False}


def test_payload_builders_return_distinct_partial_flag() -> None:
    partial = build_partial_event_payload("r", "t")
    final = build_final_event_payload("r", "t")
    assert partial["partial"] is True
    assert final["partial"] is False
