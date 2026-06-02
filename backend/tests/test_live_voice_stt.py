"""Tests for STT hallucination filtering and no_speech_prob segment rejection.

Plain pytest; no real network. We monkeypatch httpx.post inside live_voice to
return canned transcription payloads (whisper verbose_json shapes and the
plain {"text": ...} shape) and assert that:

- known stock-phrase hallucinations are dropped (STTNoSpeechError),
- whisper segments with high no_speech_prob are rejected,
- genuine Vietnamese speech passes through unchanged.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from backend.services import live_voice  # noqa: E402
from backend.services import live_circuit_breaker  # noqa: E402


class _FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.headers = {"content-type": "application/json"}
        self.text = str(payload)

    def json(self):
        return self._payload


@pytest.fixture(autouse=True)
def _reset_breaker(monkeypatch):
    # Provide a fake voice key/base so the request path runs, and ensure the
    # circuit breaker is closed before each test.
    monkeypatch.setattr(live_voice.settings, "voice_api_key", "sk-test", raising=False)
    monkeypatch.setattr(live_voice.settings, "voice_base_url", "https://example.test/v1", raising=False)
    monkeypatch.setattr(live_voice.settings, "voice_stt_model", "whisper-1", raising=False)
    monkeypatch.setattr(live_voice.settings, "voice_stt_language", "vi", raising=False)
    monkeypatch.setattr(live_voice.settings, "voice_stt_prompt", "", raising=False)
    live_circuit_breaker.record_success("voice-api")
    yield
    live_circuit_breaker.record_success("voice-api")


def _patch_post(monkeypatch, payload):
    def fake_post(*args, **kwargs):
        return _FakeResponse(payload)

    monkeypatch.setattr(live_voice.httpx, "post", fake_post)


def _transcribe():
    return live_voice.transcribe_audio_bytes(
        content=b"\x00" * 4000,
        filename="utterance.webm",
        content_type="audio/webm",
        session_id="test-session",
    )


def test_plain_vietnamese_passes(monkeypatch):
    _patch_post(monkeypatch, {"text": "Đỉnh nào lớn nhất trong Cửu Đỉnh?"})
    transcript, provider, _model = _transcribe()
    assert transcript == "Đỉnh nào lớn nhất trong Cửu Đỉnh?"
    assert provider == "voice-api"


@pytest.mark.parametrize(
    "phrase",
    [
        "you",
        "Bye.",
        "Tchau, tchau.",
        "See you, ciao.",
        "Thank you for watching!",
        "Hãy subscribe cho kênh Ghiền Mì Gõ Để không bỏ lỡ những video hấp dẫn",
    ],
)
def test_stock_hallucinations_dropped(monkeypatch, phrase):
    _patch_post(monkeypatch, {"text": phrase})
    with pytest.raises(live_voice.STTNoSpeechError):
        _transcribe()


def test_high_no_speech_segment_dropped(monkeypatch):
    # whisper verbose_json shape: a silence hallucination with high no_speech_prob.
    payload = {
        "text": "Hãy subscribe cho kênh Ghiền Mì Gõ",
        "segments": [
            {
                "text": " Hãy subscribe cho kênh Ghiền Mì Gõ",
                "no_speech_prob": 0.974,
                "avg_logprob": -0.42,
                "compression_ratio": 0.89,
            }
        ],
    }
    _patch_post(monkeypatch, payload)
    with pytest.raises(live_voice.STTNoSpeechError):
        _transcribe()


def test_speechful_segment_passes(monkeypatch):
    payload = {
        "text": "Định nào lớn nhất trong cửu đỉnh?",
        "segments": [
            {
                "text": " Định nào lớn nhất trong cửu đỉnh?",
                "no_speech_prob": 0.04,
                "avg_logprob": -0.18,
                "compression_ratio": 1.1,
            }
        ],
    }
    _patch_post(monkeypatch, payload)
    transcript, _provider, _model = _transcribe()
    assert "lớn nhất" in transcript


def test_mixed_segments_keep_only_speech(monkeypatch):
    payload = {
        "text": "ignored top-level",
        "segments": [
            {
                "text": " Thank you for watching",
                "no_speech_prob": 0.92,
                "avg_logprob": -0.5,
            },
            {
                "text": " Cửu Đỉnh là gì?",
                "no_speech_prob": 0.05,
                "avg_logprob": -0.2,
            },
        ],
    }
    _patch_post(monkeypatch, payload)
    transcript, _provider, _model = _transcribe()
    assert transcript.strip() == "Cửu Đỉnh là gì?"
