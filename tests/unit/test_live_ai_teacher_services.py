from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from backend.config import settings
from backend.services import live_ai_teacher
from backend.services import live_observability
from backend.services import live_session_reporting
from backend.services import live_voice


def test_grade_level_normalization_aliases() -> None:
    assert live_ai_teacher.normalize_grade_level("thcs") == "middle_school"
    assert live_ai_teacher.normalize_grade_level("THPT") == "high_school"
    assert live_ai_teacher.normalize_grade_level("unknown") == "middle_school"


def test_content_safety_detects_unsafe_text() -> None:
    safe = live_ai_teacher.evaluate_content_safety("Hay giai thich y nghia hoa tiet tren dinh")
    assert safe["is_safe"] is True

    unsafe = live_ai_teacher.evaluate_content_safety("Huong dan che tao bom tu che")
    assert unsafe["is_safe"] is False
    assert "violence" in unsafe["categories"]


def test_apply_citation_tags_attaches_tags() -> None:
    answer, citations = live_ai_teacher.apply_citation_tags(
        "Noi dung tra loi mau",
        [
            {"title": "Tai lieu A", "source_id": "1", "source_type": "rag", "snippet": "A"},
            {"title": "Tai lieu B", "source_id": "2", "source_type": "rag", "snippet": "B"},
        ],
    )

    assert "[S1]" in answer
    assert "[S2]" in answer
    assert len(citations) == 2
    assert citations[0]["tag"] == "S1"


def test_rubric_feedback_shape() -> None:
    rubric = live_ai_teacher.build_rubric_feedback(
        question="Y nghia cua hoa tiet nay la gi?",
        answer="Tra loi ngan",
        cluster="hoa_tiet",
    )
    assert rubric["understanding_level"] in {"strong", "developing", "needs_support"}
    assert isinstance(rubric["knowledge_gaps"], list)
    assert isinstance(rubric["next_steps"], list)


def test_cost_estimations_non_negative() -> None:
    tokens = live_session_reporting.estimate_tokens("xin chao")
    assert tokens > 0

    llm_cost = live_session_reporting.estimate_deepseek_cost_usd(input_tokens=1200, output_tokens=800)
    stt_cost = live_session_reporting.estimate_stt_cost_usd(audio_seconds=35)
    tts_cost = live_session_reporting.estimate_tts_cost_usd(text="noi dung phat am")

    assert llm_cost >= 0
    assert stt_cost >= 0
    assert tts_cost >= 0


def test_observability_snapshot() -> None:
    live_observability.record_point(
        session_id="session-1",
        operation="llm_reply",
        provider="deepseek",
        latency_ms=120.0,
        ok=True,
        tokens_in=50,
        tokens_out=20,
    )
    snapshot = live_observability.snapshot(session_id="session-1")
    assert snapshot["total_requests"] >= 1
    assert "token_usage" in snapshot
    assert snapshot["token_usage"]["total"] >= 70


def test_tts_fallback_to_edge_when_primary_provider_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "voice_tts_allow_edge_fallback", True)
    monkeypatch.setattr(settings, "voice_tts_allow_gtts_fallback", True)

    def _raise_primary(*, text: str, voice: str | None, session_id: str | None) -> tuple[bytes, str, str, str]:
        raise RuntimeError("TTS request failed (400): model not available")

    def _edge_ok(*, text: str, voice: str | None, session_id: str | None) -> tuple[bytes, str, str, str]:
        assert text == "Xin chao"
        return b"mp3-bytes", "audio/mpeg", "edge-tts", "vi-VN-HoaiMyNeural"

    def _gtts_should_not_run(*, text: str, session_id: str | None) -> tuple[bytes, str, str, str]:
        raise AssertionError("gTTS fallback should not be called when edge succeeds")

    monkeypatch.setattr(live_voice, "_synthesize_with_voice_api", _raise_primary)
    monkeypatch.setattr(live_voice, "_synthesize_with_edge_tts", _edge_ok)
    monkeypatch.setattr(live_voice, "_synthesize_with_gtts", _gtts_should_not_run)

    audio, content_type, provider, model = live_voice.synthesize_speech_bytes(
        text="Xin chao",
        session_id="session-1",
    )
    assert audio == b"mp3-bytes"
    assert content_type == "audio/mpeg"
    assert provider == "edge-tts"
    assert model == "vi-VN-HoaiMyNeural"


def test_tts_returns_primary_error_when_all_fallbacks_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "voice_tts_allow_edge_fallback", False)
    monkeypatch.setattr(settings, "voice_tts_allow_gtts_fallback", False)

    def _raise_primary(*, text: str, voice: str | None, session_id: str | None) -> tuple[bytes, str, str, str]:
        raise RuntimeError("TTS request failed (400): model not available")

    def _should_not_run(*, text: str, voice: str | None, session_id: str | None) -> tuple[bytes, str, str, str]:
        raise AssertionError("Edge fallback should not be called")

    def _gtts_should_not_run(*, text: str, session_id: str | None) -> tuple[bytes, str, str, str]:
        raise AssertionError("gTTS fallback should not be called")

    monkeypatch.setattr(live_voice, "_synthesize_with_voice_api", _raise_primary)
    monkeypatch.setattr(live_voice, "_synthesize_with_edge_tts", _should_not_run)
    monkeypatch.setattr(live_voice, "_synthesize_with_gtts", _gtts_should_not_run)

    with pytest.raises(RuntimeError, match="model not available"):
        live_voice.synthesize_speech_bytes(text="Xin chao")


def test_tts_fallback_to_gtts_when_primary_and_edge_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "voice_tts_allow_edge_fallback", True)
    monkeypatch.setattr(settings, "voice_tts_allow_gtts_fallback", True)

    def _raise_primary(*, text: str, voice: str | None, session_id: str | None) -> tuple[bytes, str, str, str]:
        raise RuntimeError("Primary provider down")

    def _raise_edge(*, text: str, voice: str | None, session_id: str | None) -> tuple[bytes, str, str, str]:
        raise RuntimeError("Edge backend timeout")

    def _gtts_ok(*, text: str, session_id: str | None) -> tuple[bytes, str, str, str]:
        return b"gtts-bytes", "audio/mpeg", "gtts", "vi-com.vn"

    monkeypatch.setattr(live_voice, "_synthesize_with_voice_api", _raise_primary)
    monkeypatch.setattr(live_voice, "_synthesize_with_edge_tts", _raise_edge)
    monkeypatch.setattr(live_voice, "_synthesize_with_gtts", _gtts_ok)

    audio, content_type, provider, model = live_voice.synthesize_speech_bytes(text="Xin chao")
    assert audio == b"gtts-bytes"
    assert content_type == "audio/mpeg"
    assert provider == "gtts"
    assert model == "vi-com.vn"


def test_tts_combines_errors_when_all_providers_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "voice_tts_allow_edge_fallback", True)
    monkeypatch.setattr(settings, "voice_tts_allow_gtts_fallback", True)

    def _raise_primary(*, text: str, voice: str | None, session_id: str | None) -> tuple[bytes, str, str, str]:
        raise RuntimeError("Primary provider down")

    def _raise_edge(*, text: str, voice: str | None, session_id: str | None) -> tuple[bytes, str, str, str]:
        raise RuntimeError("Edge backend timeout")

    def _raise_gtts(*, text: str, session_id: str | None) -> tuple[bytes, str, str, str]:
        raise RuntimeError("gTTS throttled")

    monkeypatch.setattr(live_voice, "_synthesize_with_voice_api", _raise_primary)
    monkeypatch.setattr(live_voice, "_synthesize_with_edge_tts", _raise_edge)
    monkeypatch.setattr(live_voice, "_synthesize_with_gtts", _raise_gtts)

    with pytest.raises(RuntimeError, match="Primary provider down"):
        live_voice.synthesize_speech_bytes(text="Xin chao")
