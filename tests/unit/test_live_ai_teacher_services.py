from __future__ import annotations

import io
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from backend.config import settings
from backend.models import LiveEvent, LiveSession, User
from backend.routers import live
from backend.services import live_ai_teacher
from backend.services import live_observability
from backend.services import live_session_reporting
from backend.services import live_voice
from services.ai_teacher_agent import realtime_worker


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


def test_voice_api_key_does_not_leak_deepseek_key_to_third_party(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "deepseek_api_key", "sk-deepseek-secret")
    monkeypatch.setattr(settings, "deepseek_base_url", "https://api.yescale.vip/v1")
    monkeypatch.setattr(settings, "voice_api_key", None)
    monkeypatch.setattr(settings, "voice_base_url", "https://api.openai.com/v1")

    # Should NOT return the deepseek key because voice_base_url is a third-party host
    assert live_voice._voice_api_key() is None


def test_voice_api_key_returns_explicit_voice_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "deepseek_api_key", "sk-deepseek-secret")
    monkeypatch.setattr(settings, "voice_api_key", "sk-voice-secret")
    monkeypatch.setattr(settings, "voice_base_url", "https://api.openai.com/v1")

    assert live_voice._voice_api_key() == "sk-voice-secret"


def test_voice_api_key_allows_deepseek_key_for_same_base_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "deepseek_api_key", "sk-deepseek-secret")
    monkeypatch.setattr(settings, "deepseek_base_url", "https://api.yescale.vip/v1")
    monkeypatch.setattr(settings, "voice_api_key", None)
    monkeypatch.setattr(settings, "voice_base_url", None)

    assert live_voice._voice_api_key() == "sk-deepseek-secret"

    monkeypatch.setattr(settings, "voice_base_url", "https://api.yescale.vip")
    assert live_voice._voice_api_key() == "sk-deepseek-secret"


@pytest.mark.asyncio
async def test_livekit_webhook_fails_closed_when_secret_unconfigured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "livekit_webhook_secret", None)
    req = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await live.livekit_webhook_receiver(
            request=req,
            x_livekit_webhook_secret="any-secret",
            db=MagicMock(),
        )
    assert exc_info.value.status_code == 401
    assert "not configured" in exc_info.value.detail


@pytest.mark.asyncio
async def test_livekit_webhook_rejects_invalid_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "livekit_webhook_secret", "secret-webhook-key")
    req = AsyncMock()

    # Wrong secret
    with pytest.raises(HTTPException) as exc_info:
        await live.livekit_webhook_receiver(
            request=req,
            x_livekit_webhook_secret="wrong-secret",
            db=MagicMock(),
        )
    assert exc_info.value.status_code == 401
    assert "Invalid webhook secret" in exc_info.value.detail

    # Missing secret header
    with pytest.raises(HTTPException) as exc_info:
        await live.livekit_webhook_receiver(
            request=req,
            x_livekit_webhook_secret=None,
            db=MagicMock(),
        )
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_livekit_webhook_accepts_valid_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "livekit_webhook_secret", "secret-webhook-key")
    req = AsyncMock()
    req.json = AsyncMock(
        return_value={
            "event": "participant_joined",
            "room": {"name": "test-room"},
            "participant": {"identity": "p1"},
        }
    )
    mock_db = MagicMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    res = await live.livekit_webhook_receiver(
        request=req,
        x_livekit_webhook_secret="secret-webhook-key",
        db=mock_db,
    )
    assert res.get("ok") is True


@pytest.mark.asyncio
async def test_live_ai_teacher_stt_chunked_streaming_bounds_rejects_oversized_audio(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "voice_max_audio_bytes", 100)
    mock_db = MagicMock()
    mock_session = LiveSession(
        id=uuid.uuid4(),
        title="Test Session",
        room_name="room-1",
        status="live",
        session_metadata={"ai_enabled": True},
    )
    mock_user = User(id=uuid.uuid4(), email="student@test.com")
    mock_db.get.return_value = mock_session
    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    # Oversized payload
    large_data = b"a" * 200
    upload_file = UploadFile(file=io.BytesIO(large_data), filename="audio.webm")

    with patch("backend.services.live_sessions.ensure_user_can_access_live_session", return_value=None), \
         patch("backend.services.live_sessions.is_ai_enabled", return_value=True):
        with pytest.raises(HTTPException) as exc_info:
            await live.live_ai_teacher_stt(
                live_session_id=mock_session.id,
                file=upload_file,
                current_user=mock_user,
                db=mock_db,
            )
        assert exc_info.value.status_code == 413
        assert "too large" in exc_info.value.detail


def test_realtime_worker_claim_voice_request_atomicity_and_protection() -> None:
    event_id = uuid.uuid4()
    event = LiveEvent(id=event_id, payload={"text": "Hello AI Teacher"})

    class MockClaimDB:
        def __init__(self, target_event: LiveEvent):
            self.target_event = target_event
            self.locked_by_other = False
            self.committed = 0

        def execute(self, stmt):
            class Result:
                def __init__(self, item):
                    self.item = item
                def scalar_one_or_none(self):
                    return self.item
            if self.locked_by_other:
                return Result(None)
            return Result(self.target_event)

        def get(self, model, eid):
            return self.target_event if self.target_event.id == eid else None

        def commit(self):
            self.committed += 1

        def rollback(self):
            pass

    db = MockClaimDB(event)

    # First worker claims the event
    first_claim = realtime_worker._claim_voice_request(db, event_id)
    assert first_claim is True
    assert event.payload.get("_ai_worker_claimed") is True
    assert event.payload.get("_ai_worker_status") == "processing"
    assert "_ai_worker_claimed_at" in event.payload

    # Second worker attempts to claim the same event while in-progress
    second_claim = realtime_worker._claim_voice_request(db, event_id)
    assert second_claim is False

    # Once marked done, claim cannot be taken
    realtime_worker._mark_event_done(db, event_id=event_id, status="ok")
    assert event.payload.get("_ai_worker_done") is True
    assert realtime_worker._claim_voice_request(db, event_id) is False


def test_realtime_worker_claim_voice_request_stale_claim_recovery() -> None:
    event_id = uuid.uuid4()
    stale_time = (datetime.now(timezone.utc) - timedelta(seconds=400)).strftime("%Y-%m-%dT%H:%M:%SZ")
    event = LiveEvent(
        id=event_id,
        payload={
            "text": "Stale question",
            "_ai_worker_claimed": True,
            "_ai_worker_status": "processing",
            "_ai_worker_claimed_at": stale_time,
        },
    )

    class MockClaimDB:
        def __init__(self, target_event: LiveEvent):
            self.target_event = target_event

        def execute(self, stmt):
            class Result:
                def __init__(self, item):
                    self.item = item
                def scalar_one_or_none(self):
                    return self.item
            return Result(self.target_event)

        def get(self, model, eid):
            return self.target_event if self.target_event.id == eid else None

        def commit(self):
            pass

        def rollback(self):
            pass

    db = MockClaimDB(event)

    # Stale claim (> 300s) should be reclaimable
    assert realtime_worker._claim_voice_request(db, event_id) is True
    assert event.payload.get("_ai_worker_claimed") is True


