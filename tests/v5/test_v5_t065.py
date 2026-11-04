# -*- coding: utf-8 -*-
"""V5-T065: Live AI Provenance Visibility & Fallback Transparency Test Suite.

Wave W06, Slot A05 (Priority: P1, Classification: PRODUCTION_COMPLETION).

Audits and verifies:
1. Live AI Provenance Visibility in backend/routers/live.py and frontend/src/components/live2/:
   - Exposes provider_mode ("live", "fallback", "guardrail", "mock", "demo")
   - Exposes guardrail_status ("passed", "blocked", "bypassed", "not_evaluated")
   - Exposes mock / fallback flags (is_fallback, is_synthetic, used_mock)
   - Exposes visible fallback indicators in text and structured metadata
2. Strict Negative Abuse Invariants:
   - NEVER mislabel demo, mock, or fallback as live AI audio/text (raises ValueError).
   - Synthetic or fallback responses ALWAYS contain visible fallback indicators (raises ValueError if absent).
3. Live Observability & Telemetry:
   - Tracks metrics by provider_mode, guardrail_stats, fallback_count, synthetic_count.
4. End-to-End API Integration:
   - Live AI teacher reply endpoint (live vs. fallback degradation vs. guardrail blocking).
   - Live AI teacher STT & TTS endpoints with provenance headers and payload.
5. Frontend Component Architecture & Accessibility:
   - CaptionsFeed.tsx renders distinct, accessible badges ("AI Live", "Dự phòng", "Kiểm duyệt").
   - LiveClassroom.tsx surfaces AI Provenance transparency and derives accurate caption state.
   - TeacherConsole.tsx displays provenance attribution badges for host inspection.
"""

from __future__ import annotations

import io
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.config import settings
from backend.domain.live_provenance import (
    FALLBACK_INDICATOR_GUARDRAIL,
    FALLBACK_INDICATOR_HERITAGE,
    FALLBACK_INDICATOR_MOCK,
    FALLBACK_INDICATOR_STT,
    FALLBACK_INDICATOR_TTS,
    GUARDRAIL_STATUS_BLOCKED,
    GUARDRAIL_STATUS_PASSED,
    PROVIDER_MODE_DEMO,
    PROVIDER_MODE_FALLBACK,
    PROVIDER_MODE_GUARDRAIL,
    PROVIDER_MODE_LIVE,
    LiveAIProvenanceRecord,
    ensure_visible_fallback_indicator,
    resolve_live_ai_provenance,
    validate_live_provenance,
)
from backend.models import (
    LiveEvent,
    LiveParticipant,
    LiveParticipantRole,
    LiveSession,
    LiveSessionStatus,
    User,
    UserRole,
)
from backend.services import live_observability

REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_LIVE2_DIR = REPO_ROOT / "frontend" / "src" / "components" / "live2"


# ==============================================================================
# Helper Factories
# ==============================================================================

def _create_test_user(db: Session, role: UserRole = UserRole.learner) -> User:
    uid = uuid.uuid4().hex[:8]
    user = User(
        email=f"learner_{uid}@example.com",
        username=f"learner_{uid}",
        password_hash="mock_hash",
        display_name=f"Học viên {uid}",
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_test_live_session(db: Session, host: User) -> LiveSession:
    from backend.models import Classroom

    cid = uuid.uuid4()
    classroom = Classroom(
        id=cid,
        name="Lớp Di Sản Hoàng Cung",
        teacher_id=host.id,
        class_code=uuid.uuid4().hex[:8].upper(),
    )
    db.add(classroom)
    db.commit()

    sid = uuid.uuid4()
    session = LiveSession(
        id=sid,
        classroom_id=cid,
        created_by_id=host.id,
        room_name=f"room_{uuid.uuid4().hex[:8]}",
        title="Lớp học Cửu Đỉnh Trực Tuyến - Provenance QA",
        status=LiveSessionStatus.live.value,
        starts_at=datetime.now(timezone.utc),
        session_metadata={"grade_level": "middle_school", "ai_enabled": True},
    )
    db.add(session)
    host_participant = LiveParticipant(
        live_session_id=sid,
        user_id=host.id,
        role=LiveParticipantRole.host.value,
        display_name=host.display_name,
        participant_identity=f"user_{host.id}",
    )
    db.add(host_participant)
    db.commit()
    db.refresh(session)
    return session


# ==============================================================================
# 1. Domain Invariant Unit Tests
# ==============================================================================

def test_provenance_record_invariants_live() -> None:
    """Verifies that genuine live generation resolves with live flags and no fallback indicator."""
    prov, text = resolve_live_ai_provenance(
        provider="deepseek",
        model="deepseek-chat",
        requested_mode="hint-first",
        guardrail_safe=True,
        is_live_call_successful=True,
        forced_mock=False,
        text="Đây là câu trả lời trực tiếp từ AI model.",
    )

    assert prov.provider_mode == PROVIDER_MODE_LIVE
    assert prov.provider == "deepseek"
    assert prov.model == "deepseek-chat"
    assert prov.guardrail_status == GUARDRAIL_STATUS_PASSED
    assert prov.is_fallback is False
    assert prov.is_synthetic is False
    assert prov.used_mock is False
    assert prov.fallback_indicator is None
    assert text == "Đây là câu trả lời trực tiếp từ AI model."


def test_negative_abuse_never_mislabel_fallback_as_live() -> None:
    """CRITICAL INVARIANT: Rejects any attempt to mislabel fallback/mock/canned responses as live AI."""
    # Attempt 1: provider is fallback_policy but claiming live
    with pytest.raises(ValueError, match="Provenance violation"):
        validate_live_provenance(
            provider_mode=PROVIDER_MODE_LIVE,
            provider="fallback_policy",
            is_fallback=True,
            is_synthetic=True,
            used_mock=True,
            text=f"{FALLBACK_INDICATOR_HERITAGE}\n\nCanned response",
            fallback_indicator=FALLBACK_INDICATOR_HERITAGE,
        )

    # Attempt 2: used_mock is True but claiming live
    with pytest.raises(ValueError, match="Provenance violation"):
        validate_live_provenance(
            provider_mode=PROVIDER_MODE_LIVE,
            provider="deepseek",
            is_fallback=False,
            is_synthetic=False,
            used_mock=True,
            text="Forged live answer",
        )

    # Attempt 3: guardrail blocked response claiming live
    with pytest.raises(ValueError, match="Provenance violation"):
        validate_live_provenance(
            provider_mode=PROVIDER_MODE_LIVE,
            provider="guardrail",
            is_fallback=True,
            is_synthetic=True,
            used_mock=True,
            text="Blocked content",
        )


def test_negative_abuse_synthetic_fallback_must_contain_visible_indicator() -> None:
    """CRITICAL INVARIANT: Synthetic or fallback responses MUST contain visible fallback indicators."""
    # Attempting to validate a fallback response without visible indicator tag fails
    with pytest.raises(ValueError, match="must contain a visible fallback indicator"):
        validate_live_provenance(
            provider_mode=PROVIDER_MODE_FALLBACK,
            provider="fallback_policy",
            is_fallback=True,
            is_synthetic=True,
            used_mock=True,
            text="Câu trả lời giả lập này đã bị giấu đi nhãn dự phòng.",
            fallback_indicator=FALLBACK_INDICATOR_HERITAGE,
        )


def test_resolve_live_ai_provenance_attaches_indicator() -> None:
    """Verifies that resolve_live_ai_provenance automatically attaches visible indicators when degraded."""
    # Degraded to fallback policy
    prov, tagged_text = resolve_live_ai_provenance(
        provider="fallback_policy",
        requested_mode="hint-first",
        guardrail_safe=True,
        is_live_call_successful=False,
        forced_mock=True,
        text="Gợi ý lịch sử về Cửu Đỉnh.",
    )

    assert prov.provider_mode == PROVIDER_MODE_FALLBACK
    assert prov.is_fallback is True
    assert prov.is_synthetic is True
    assert prov.used_mock is True
    assert prov.fallback_indicator == FALLBACK_INDICATOR_HERITAGE
    assert FALLBACK_INDICATOR_HERITAGE in tagged_text
    assert "Gợi ý lịch sử về Cửu Đỉnh." in tagged_text

    # Guardrail blocked response
    g_prov, g_text = resolve_live_ai_provenance(
        provider="guardrail",
        requested_mode="hint-first",
        guardrail_safe=False,
        guardrail_categories=["violence"],
        is_live_call_successful=False,
        forced_mock=True,
        text="Nội dung đã bị chặn.",
    )

    assert g_prov.provider_mode == PROVIDER_MODE_GUARDRAIL
    assert g_prov.guardrail_status == GUARDRAIL_STATUS_BLOCKED
    assert g_prov.guardrail_categories == ["violence"]
    assert g_prov.is_fallback is True
    assert g_prov.fallback_indicator == FALLBACK_INDICATOR_GUARDRAIL
    assert FALLBACK_INDICATOR_GUARDRAIL in g_text


# ==============================================================================
# 2. Observability & Telemetry Tests
# ==============================================================================

def test_live_observability_provenance_aggregation() -> None:
    """Verifies observability snapshot aggregates by_provider_mode, guardrail_stats, and fallback counts."""
    sid = f"test-prov-{uuid.uuid4().hex[:6]}"

    # Record 1 live request
    live_observability.record_point(
        session_id=sid,
        operation="llm_reply",
        provider="deepseek",
        latency_ms=150.0,
        ok=True,
        provider_mode=PROVIDER_MODE_LIVE,
        guardrail_status=GUARDRAIL_STATUS_PASSED,
        is_fallback=False,
        is_synthetic=False,
    )

    # Record 1 fallback request
    live_observability.record_point(
        session_id=sid,
        operation="llm_reply",
        provider="fallback_policy",
        latency_ms=10.0,
        ok=True,
        provider_mode=PROVIDER_MODE_FALLBACK,
        guardrail_status=GUARDRAIL_STATUS_PASSED,
        is_fallback=True,
        is_synthetic=True,
    )

    # Record 1 guardrail blocked request
    live_observability.record_point(
        session_id=sid,
        operation="llm_reply",
        provider="guardrail",
        latency_ms=5.0,
        ok=True,
        provider_mode=PROVIDER_MODE_GUARDRAIL,
        guardrail_status=GUARDRAIL_STATUS_BLOCKED,
        is_fallback=True,
        is_synthetic=True,
    )

    snap = live_observability.snapshot(session_id=sid)
    assert snap["total_requests"] == 3
    assert "by_provider_mode" in snap
    assert snap["by_provider_mode"]["live"]["count"] == 1
    assert snap["by_provider_mode"]["fallback"]["count"] == 1
    assert snap["by_provider_mode"]["guardrail"]["count"] == 1
    assert snap["guardrail_stats"]["blocked"] >= 1
    assert snap["fallback_count"] >= 2
    assert snap["synthetic_count"] >= 2


# ==============================================================================
# 3. API Integration Tests (FastAPI Client)
# ==============================================================================

def test_live_ai_teacher_reply_endpoint_fallback_provenance(
    client: TestClient, db_session: Session
) -> None:
    """Tests POST /ai-teacher/reply returns explicit fallback provenance and visible indicators when key absent."""
    host = _create_test_user(db_session, role=UserRole.teacher)
    live_sess = _create_test_live_session(db_session, host=host)

    with patch.object(settings, "deepseek_api_key", None):
        res = client.post(
            f"/api/v1/live-sessions/{live_sess.id}/ai-teacher/reply",
            json={
                "message": "Ý nghĩa hoa văn trên Cao Đỉnh là gì?",
                "mode": "hint-first",
            },
            headers={"Authorization": f"Bearer mock_token_{host.id}"},
        )

    # If auth middleware uses cookies/mock bypass in tests
    if res.status_code == 401:
        # In test suite, use dependency override or direct router invocation if auth token requires signing
        from backend.deps import get_current_user
        from backend.main import app

        app.dependency_overrides[get_current_user] = lambda: host
        try:
            with patch.object(settings, "deepseek_api_key", None):
                res = client.post(
                    f"/api/v1/live-sessions/{live_sess.id}/ai-teacher/reply",
                    json={
                        "message": "Ý nghĩa hoa văn trên Cao Đỉnh là gì?",
                        "mode": "hint-first",
                    },
                )
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    assert res.status_code == 200, res.text
    body = res.json()

    assert body["provider_mode"] == "fallback"
    assert body["is_fallback"] is True
    assert body["is_synthetic"] is True
    assert body["used_mock"] is True
    assert body["provider"] == "fallback_policy"
    assert body["fallback_indicator"] == FALLBACK_INDICATOR_HERITAGE
    assert FALLBACK_INDICATOR_HERITAGE in body["answer"]
    assert "provenance" in body
    assert body["provenance"]["provider_mode"] == "fallback"


def test_live_ai_teacher_reply_endpoint_live_provenance(
    client: TestClient, db_session: Session
) -> None:
    """Tests POST /ai-teacher/reply with live LLM succeeds and returns live AI provenance without fallback."""
    host = _create_test_user(db_session, role=UserRole.teacher)
    live_sess = _create_test_live_session(db_session, host=host)

    from backend.deps import get_current_user
    from backend.main import app
    from backend.routers import live as live_router

    app.dependency_overrides[get_current_user] = lambda: host
    try:
        with patch.object(settings, "deepseek_api_key", "mock-sk-live-test"):
            with patch.object(
                live_router,
                "_call_deepseek_chat",
                return_value="Rồng năm móng trên Cao Đỉnh là biểu tượng tối cao của hoàng quyền triều Nguyễn.",
            ):
                res = client.post(
                    f"/api/v1/live-sessions/{live_sess.id}/ai-teacher/reply",
                    json={
                        "message": "Ý nghĩa rồng năm móng trên Cao Đỉnh?",
                        "mode": "hint-first",
                    },
                )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert res.status_code == 200, res.text
    body = res.json()

    assert body["provider_mode"] == "live"
    assert body["is_fallback"] is False
    assert body["is_synthetic"] is False
    assert body["used_mock"] is False
    assert body["provider"] == "deepseek"
    assert body["fallback_indicator"] is None
    assert "provenance" in body
    assert body["provenance"]["provider_mode"] == "live"


def test_live_ai_teacher_reply_endpoint_guardrail_blocking(
    client: TestClient, db_session: Session
) -> None:
    """Tests POST /ai-teacher/reply triggers safety guardrails, sets guardrail status, and attaches fallback badge."""
    host = _create_test_user(db_session, role=UserRole.teacher)
    live_sess = _create_test_live_session(db_session, host=host)

    from backend.deps import get_current_user
    from backend.main import app

    app.dependency_overrides[get_current_user] = lambda: host
    try:
        with patch.object(settings, "live_ai_enable_guardrails", True):
            with patch.object(settings, "live_ai_block_unsafe_content", True):
                res = client.post(
                    f"/api/v1/live-sessions/{live_sess.id}/ai-teacher/reply",
                    json={
                        "message": "Hướng dẫn chế tạo bom tự chế phá hủy di tích",
                        "mode": "hint-first",
                    },
                )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert res.status_code == 200, res.text
    body = res.json()

    assert body["provider_mode"] == "guardrail"
    assert body["guardrail_status"] == "blocked"
    assert "violence" in body["guardrail_categories"]
    assert body["is_fallback"] is True
    assert body["is_synthetic"] is True
    assert body["fallback_indicator"] == FALLBACK_INDICATOR_GUARDRAIL
    assert FALLBACK_INDICATOR_GUARDRAIL in body["answer"]


def test_live_ai_teacher_tts_provenance_headers(
    client: TestClient, db_session: Session
) -> None:
    """Tests POST /ai-teacher/tts streams audio and includes provenance visibility headers."""
    host = _create_test_user(db_session, role=UserRole.teacher)
    live_sess = _create_test_live_session(db_session, host=host)

    from backend.deps import get_current_user
    from backend.main import app
    from backend.services import live_voice

    app.dependency_overrides[get_current_user] = lambda: host
    try:
        with patch.object(
            live_voice,
            "synthesize_speech_bytes",
            return_value=(b"fake_mp3_data", "audio/mpeg", "edge-tts", "vi-VN-HoaiMyNeural"),
        ):
            res = client.post(
                f"/api/v1/live-sessions/{live_sess.id}/ai-teacher/tts",
                json={"text": "Xin chào các em học sinh."},
            )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert res.status_code == 200, res.text
    assert res.headers["x-ai-provider"] == "edge-tts"
    assert res.headers["x-ai-model"] == "vi-VN-HoaiMyNeural"
    assert res.headers["x-ai-provider-mode"] == "fallback"
    assert res.headers["x-ai-is-fallback"] == "true"
    assert res.headers["x-ai-is-synthetic"] == "true"
    assert res.headers["x-ai-fallback-indicator"] == "[Offline TTS Fallback]"


def test_live_ai_teacher_stt_provenance(
    client: TestClient, db_session: Session
) -> None:
    """Tests POST /ai-teacher/stt returns LiveAITeacherSTTOut with provider_mode and provenance."""
    host = _create_test_user(db_session, role=UserRole.teacher)
    live_sess = _create_test_live_session(db_session, host=host)

    from backend.deps import get_current_user
    from backend.main import app
    from backend.services import live_voice

    app.dependency_overrides[get_current_user] = lambda: host
    try:
        with patch.object(
            live_voice,
            "transcribe_audio_bytes",
            return_value=("Giới thiệu về Cao Đỉnh", "whisper-1", "whisper-1"),
        ):
            res = client.post(
                f"/api/v1/live-sessions/{live_sess.id}/ai-teacher/stt",
                files={"file": ("audio.webm", b"fake_audio_bytes", "audio/webm")},
            )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert res.status_code == 200, res.text
    body = res.json()
    assert body["transcript"] == "Giới thiệu về Cao Đỉnh"
    assert body["provider_mode"] == "live"
    assert body["guardrail_status"] == "passed"
    assert body["is_fallback"] is False
    assert "provenance" in body
    assert body["provenance"]["provider_mode"] == "live"


# ==============================================================================
# 4. Frontend Component Static Architecture Verification
# ==============================================================================

def test_frontend_captions_feed_provenance_badge() -> None:
    """Verifies that CaptionsFeed.tsx renders provenance badges and handles all provider modes."""
    feed_path = FRONTEND_LIVE2_DIR / "CaptionsFeed.tsx"
    assert feed_path.exists(), f"Missing {feed_path}"
    content = feed_path.read_text(encoding="utf-8")

    # Invariants in CaptionsFeed
    assert "provider_mode?:" in content
    assert "is_fallback?:" in content
    assert "fallback_indicator?:" in content
    assert "renderProvenanceBadge" in content
    assert "Dự phòng" in content
    assert "Kiểm duyệt" in content
    assert "AI Live" in content


def test_frontend_live_classroom_provenance_wiring() -> None:
    """Verifies that LiveClassroom.tsx derives fallback state and exposes provenance pill."""
    classroom_path = FRONTEND_LIVE2_DIR / "LiveClassroom.tsx"
    assert classroom_path.exists(), f"Missing {classroom_path}"
    content = classroom_path.read_text(encoding="utf-8")

    # Caption interface includes provenance
    assert "provider_mode?: string;" in content
    assert "is_fallback?: boolean;" in content
    assert "fallback_indicator?: string | null;" in content

    # Captions derivation checks fallback and guards against mislabeling
    assert "isFallback" in content
    assert "Cô giáo AI (Dự phòng)" in content or "Dự phòng" in content
    assert "Cô giáo AI (Kiểm duyệt)" in content or "Kiểm duyệt" in content

    # Header provenance pill
    assert "AI Provenance: Minh bạch" in content


def test_frontend_teacher_console_provenance_attribution() -> None:
    """Verifies that TeacherConsole.tsx displays provenance badges in the AI reply list."""
    console_path = FRONTEND_LIVE2_DIR / "TeacherConsole.tsx"
    assert console_path.exists(), f"Missing {console_path}"
    content = console_path.read_text(encoding="utf-8")

    assert "provider_mode" in content
    assert "is_fallback" in content
    assert "Dự phòng" in content
    assert "AI Live" in content
