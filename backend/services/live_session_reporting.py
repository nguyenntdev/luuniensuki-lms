"""Reporting pipeline for live AI classroom sessions."""

from __future__ import annotations

import csv
import io
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, delete, desc, distinct, func, select
from sqlalchemy.orm import Session

from ..config import settings
from ..models import (
    ClassMember,
    Classroom,
    LiveEvent,
    LiveParticipant,
    LiveSession,
    SessionAction,
    SessionSummary,
    SessionTranscript,
)
from . import live_crypto


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_utc(value: datetime | None) -> datetime:
    if value is None:
        return _utcnow()
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _retention_expires(days: int) -> datetime:
    return _utcnow() + timedelta(days=max(1, int(days)))


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _event_text(event_type: str, payload: dict[str, Any]) -> str:
    if event_type == "ai_transcript_chunk" and payload.get("partial") is True:
        return ""

    for key in ("text", "answer", "message", "delta"):
        text = str(payload.get(key) or "").strip()
        if text:
            return text
    return ""


def _event_speaker(event_type: str, payload: dict[str, Any]) -> str:
    if event_type in {"ai_voice_ready", "ai_teacher_reply", "ai_transcript_chunk"}:
        return "ai"
    if event_type in {"voice_user_final", "ai_teacher_user_message", "ai_voice_request"}:
        return "user"
    source = str(payload.get("speaker") or "").strip().lower()
    if source in {"ai", "assistant"}:
        return "ai"
    if source in {"user", "learner"}:
        return "user"
    return "system"


def _extract_citations(text: str) -> list[str]:
    found = re.findall(r"\[S(\d{1,2})\]", text or "")
    normalized = []
    seen = set()
    for item in found:
        token = f"S{item}"
        if token in seen:
            continue
        seen.add(token)
        normalized.append(token)
    return normalized


def cleanup_expired_reporting_data(db: Session, *, live_session_id: uuid.UUID | None = None) -> None:
    now = _utcnow()

    transcript_q = delete(SessionTranscript).where(
        and_(
            SessionTranscript.expires_at.is_not(None),
            SessionTranscript.expires_at < now,
        )
    )
    summary_q = delete(SessionSummary).where(
        and_(
            SessionSummary.expires_at.is_not(None),
            SessionSummary.expires_at < now,
        )
    )
    action_q = delete(SessionAction).where(
        and_(
            SessionAction.expires_at.is_not(None),
            SessionAction.expires_at < now,
        )
    )

    if live_session_id:
        transcript_q = transcript_q.where(SessionTranscript.live_session_id == live_session_id)
        summary_q = summary_q.where(SessionSummary.live_session_id == live_session_id)
        action_q = action_q.where(SessionAction.live_session_id == live_session_id)

    db.execute(transcript_q)
    db.execute(summary_q)
    db.execute(action_q)


def ingest_transcript_from_event(
    db: Session,
    *,
    live_session: LiveSession,
    event: LiveEvent,
) -> SessionTranscript | None:
    payload = _safe_payload(event.payload)
    text = _event_text(str(event.event_type), payload)
    if not text:
        return None

    existing = (
        db.execute(
            select(SessionTranscript).where(
                and_(
                    SessionTranscript.live_session_id == live_session.id,
                    SessionTranscript.source_event_id == event.id,
                )
            )
        )
        .scalars()
        .first()
    )
    if existing is not None:
        return existing

    speaker_type = _event_speaker(str(event.event_type), payload)
    confidence = _safe_float(payload.get("confidence"))
    started_at = _ensure_utc(event.created_at)
    ended_at = _ensure_utc(payload.get("ended_at") if isinstance(payload.get("ended_at"), datetime) else event.created_at)

    transcript = SessionTranscript(
        live_session_id=live_session.id,
        source_event_id=event.id,
        speaker_type=speaker_type,
        speaker_identity=(event.participant_identity or payload.get("participant_identity")),
        speaker_user_id=event.participant_user_id,
        content_encrypted=live_crypto.encrypt_text(text),
        confidence=confidence,
        started_at=started_at,
        ended_at=ended_at,
        transcript_metadata={
            "event_type": event.event_type,
            "mode": payload.get("mode"),
            "provider": payload.get("provider"),
            "model": payload.get("model"),
            "citations": _extract_citations(text),
            "checkpoint_prompt": payload.get("checkpoint_prompt"),
            "references": payload.get("references") if isinstance(payload.get("references"), list) else [],
            "rubric": payload.get("rubric") if isinstance(payload.get("rubric"), dict) else None,
        },
        expires_at=_retention_expires(int(settings.live_transcript_retention_days or 30)),
    )
    db.add(transcript)
    return transcript


def list_session_transcripts(
    db: Session,
    *,
    live_session_id: uuid.UUID,
    limit: int = 500,
    since: datetime | None = None,
) -> list[dict[str, Any]]:
    cleanup_expired_reporting_data(db, live_session_id=live_session_id)

    query = select(SessionTranscript).where(SessionTranscript.live_session_id == live_session_id)
    if since is not None:
        query = query.where(SessionTranscript.created_at >= since)

    rows = (
        db.execute(query.order_by(SessionTranscript.created_at.asc()).limit(max(1, min(limit, 2000))))
        .scalars()
        .all()
    )

    result: list[dict[str, Any]] = []
    for row in rows:
        metadata = row.transcript_metadata or {}
        result.append(
            {
                "id": str(row.id),
                "speaker_type": row.speaker_type,
                "speaker_identity": row.speaker_identity,
                "speaker_user_id": str(row.speaker_user_id) if row.speaker_user_id else None,
                "text": live_crypto.decrypt_text(row.content_encrypted),
                "confidence": row.confidence,
                "started_at": row.started_at.isoformat() if row.started_at else None,
                "ended_at": row.ended_at.isoformat() if row.ended_at else None,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "event_type": metadata.get("event_type"),
                "provider": metadata.get("provider"),
                "model": metadata.get("model"),
                "citations": metadata.get("citations") if isinstance(metadata.get("citations"), list) else [],
                "rubric": metadata.get("rubric") if isinstance(metadata.get("rubric"), dict) else None,
            }
        )
    return result


def create_session_action(
    db: Session,
    *,
    live_session_id: uuid.UUID,
    action_type: str,
    status: str = "open",
    actor_identity: str | None = None,
    actor_user_id: uuid.UUID | None = None,
    payload: dict[str, Any] | None = None,
    cost_usd: float | None = None,
) -> SessionAction:
    action = SessionAction(
        live_session_id=live_session_id,
        action_type=str(action_type).strip()[:40],
        status=str(status).strip()[:20] or "open",
        actor_identity=(str(actor_identity).strip()[:191] if actor_identity else None),
        actor_user_id=actor_user_id,
        payload=payload or {},
        cost_usd=cost_usd,
        expires_at=_retention_expires(int(settings.live_summary_retention_days or 90)),
    )
    db.add(action)
    return action


def estimate_tokens(text: str) -> int:
    cleaned = str(text or "").strip()
    if not cleaned:
        return 0
    return max(1, int(round(len(cleaned) / 4.0)))


def estimate_deepseek_cost_usd(*, input_tokens: int, output_tokens: int) -> float:
    in_cost = (max(0, input_tokens) / 1_000_000.0) * float(settings.live_ai_input_cost_per_1m_tokens or 0.14)
    out_cost = (max(0, output_tokens) / 1_000_000.0) * float(settings.live_ai_output_cost_per_1m_tokens or 0.28)
    return round(in_cost + out_cost, 6)


def estimate_stt_cost_usd(*, audio_seconds: float) -> float:
    minutes = max(0.0, float(audio_seconds or 0.0) / 60.0)
    return round(minutes * float(settings.live_ai_stt_cost_per_minute_usd or 0.006), 6)


def estimate_tts_cost_usd(*, text: str) -> float:
    chars = len(str(text or ""))
    units = max(0.0, chars / 1000.0)
    return round(units * float(settings.live_ai_tts_cost_per_1k_chars_usd or 0.015), 6)


def record_ai_cost(
    db: Session,
    *,
    live_session: LiveSession,
    component: str,
    cost_usd: float,
    token_in: int = 0,
    token_out: int = 0,
    metadata: dict[str, Any] | None = None,
) -> SessionAction:
    payload = {
        "component": component,
        "token_in": int(token_in or 0),
        "token_out": int(token_out or 0),
        "metadata": metadata or {},
    }
    return create_session_action(
        db,
        live_session_id=live_session.id,
        action_type="cost_usage",
        status="recorded",
        payload=payload,
        cost_usd=max(0.0, float(cost_usd or 0.0)),
    )


def session_ai_cost_total(db: Session, *, live_session_id: uuid.UUID) -> float:
    value = db.execute(
        select(func.coalesce(func.sum(SessionAction.cost_usd), 0.0)).where(
            and_(
                SessionAction.live_session_id == live_session_id,
                SessionAction.action_type == "cost_usage",
            )
        )
    ).scalar_one()
    return float(value or 0.0)


def resolve_session_cost_ceiling(db: Session, *, live_session: LiveSession) -> float:
    default_ceiling = float(settings.live_ai_cost_ceiling_usd or 3.0)
    metadata = live_session.session_metadata if isinstance(live_session.session_metadata, dict) else {}
    if "ai_cost_ceiling_usd" in metadata:
        try:
            return max(0.1, float(metadata.get("ai_cost_ceiling_usd")))
        except (TypeError, ValueError):
            pass

    classroom = db.get(Classroom, live_session.classroom_id)
    if classroom and isinstance(classroom.settings, dict):
        try:
            value = classroom.settings.get("ai_cost_ceiling_usd")
            if value is not None:
                return max(0.1, float(value))
        except (TypeError, ValueError):
            pass

    return max(0.1, default_ceiling)


def ensure_within_cost_ceiling(
    db: Session,
    *,
    live_session: LiveSession,
    projected_additional_cost: float = 0.0,
) -> None:
    current_total = session_ai_cost_total(db, live_session_id=live_session.id)
    ceiling = resolve_session_cost_ceiling(db, live_session=live_session)
    projected = current_total + max(0.0, float(projected_additional_cost or 0.0))
    if projected <= ceiling:
        return

    create_session_action(
        db,
        live_session_id=live_session.id,
        action_type="cost_ceiling_block",
        status="blocked",
        payload={
            "current_total_usd": round(current_total, 6),
            "projected_total_usd": round(projected, 6),
            "ceiling_usd": round(ceiling, 6),
        },
    )
    raise RuntimeError(
        f"AI cost ceiling reached for this session ({current_total:.3f}/{ceiling:.3f} USD)"
    )


def compute_attendance_engagement(
    db: Session,
    *,
    live_session: LiveSession,
) -> dict[str, Any]:
    cleanup_expired_reporting_data(db, live_session_id=live_session.id)

    classroom_size = int(
        db.execute(
            select(func.count(ClassMember.id)).where(ClassMember.class_id == live_session.classroom_id)
        ).scalar_one()
        or 0
    )

    joined_participants = int(
        db.execute(
            select(func.count(distinct(LiveParticipant.participant_identity))).where(
                LiveParticipant.live_session_id == live_session.id
            )
        ).scalar_one()
        or 0
    )

    active_participants = int(
        db.execute(
            select(func.count(LiveParticipant.id)).where(
                and_(
                    LiveParticipant.live_session_id == live_session.id,
                    LiveParticipant.left_at.is_(None),
                )
            )
        ).scalar_one()
        or 0
    )

    user_turns = int(
        db.execute(
            select(func.count(SessionTranscript.id)).where(
                and_(
                    SessionTranscript.live_session_id == live_session.id,
                    SessionTranscript.speaker_type == "user",
                )
            )
        ).scalar_one()
        or 0
    )
    ai_turns = int(
        db.execute(
            select(func.count(SessionTranscript.id)).where(
                and_(
                    SessionTranscript.live_session_id == live_session.id,
                    SessionTranscript.speaker_type == "ai",
                )
            )
        ).scalar_one()
        or 0
    )

    hand_raises = int(
        db.execute(
            select(func.count(LiveEvent.id)).where(
                and_(
                    LiveEvent.live_session_id == live_session.id,
                    LiveEvent.event_type == "raise_hand",
                )
            )
        ).scalar_one()
        or 0
    )

    low_interaction = user_turns < max(3, int(max(1, joined_participants) / 2))
    attendance_rate = 1.0
    if classroom_size > 0:
        attendance_rate = min(1.0, joined_participants / classroom_size)

    return {
        "attendance": {
            "classroom_size": classroom_size,
            "joined_participants": joined_participants,
            "active_participants": active_participants,
            "attendance_rate": round(attendance_rate, 4),
        },
        "engagement": {
            "user_turns": user_turns,
            "ai_turns": ai_turns,
            "hand_raises": hand_raises,
            "low_interaction": low_interaction,
            "interaction_score": round((user_turns + hand_raises) / max(1, joined_participants), 2),
        },
    }


def ensure_low_interaction_warning(
    db: Session,
    *,
    live_session: LiveSession,
    metrics: dict[str, Any],
) -> None:
    if not bool(metrics.get("engagement", {}).get("low_interaction")):
        return

    existing = (
        db.execute(
            select(SessionAction.id)
            .where(
                and_(
                    SessionAction.live_session_id == live_session.id,
                    SessionAction.action_type == "low_interaction_warning",
                )
            )
            .order_by(desc(SessionAction.created_at))
            .limit(1)
        )
        .scalars()
        .first()
    )
    if existing:
        return

    create_session_action(
        db,
        live_session_id=live_session.id,
        action_type="low_interaction_warning",
        status="open",
        payload={
            "message": "Canh bao: hoc vien tuong tac thap, de xuat host goi ten hoc vien hoac chen checkpoint.",
            "engagement": metrics.get("engagement", {}),
        },
    )


def _latest_summary(db: Session, *, live_session_id: uuid.UUID) -> SessionSummary | None:
    return (
        db.execute(
            select(SessionSummary)
            .where(SessionSummary.live_session_id == live_session_id)
            .order_by(SessionSummary.created_at.desc())
            .limit(1)
        )
        .scalars()
        .first()
    )


def _rubric_overview(transcripts: list[dict[str, Any]]) -> dict[str, Any]:
    levels = {"strong": 0, "developing": 0, "needs_support": 0}
    gaps: list[str] = []
    for item in transcripts:
        rubric = item.get("rubric") if isinstance(item.get("rubric"), dict) else None
        if not rubric:
            continue
        level = str(rubric.get("understanding_level") or "").strip().lower()
        if level in levels:
            levels[level] += 1
        for gap in rubric.get("knowledge_gaps") or []:
            text = str(gap).strip()
            if text and text not in gaps:
                gaps.append(text)
    return {
        "distribution": levels,
        "knowledge_gaps": gaps[:8],
    }


def _build_summary_text(
    *,
    live_session: LiveSession,
    metrics: dict[str, Any],
    transcripts: list[dict[str, Any]],
) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
    user_lines = [item for item in transcripts if item.get("speaker_type") == "user"]
    ai_lines = [item for item in transcripts if item.get("speaker_type") == "ai"]

    key_questions = [item.get("text") for item in user_lines[-5:] if item.get("text")]
    ai_replies = [item.get("text") for item in ai_lines[-5:] if item.get("text")]
    first_reply = ai_replies[0] if ai_replies else ""

    citations: list[dict[str, Any]] = []
    seen = set()
    for item in ai_lines:
        for token in item.get("citations") or []:
            if token in seen:
                continue
            seen.add(token)
            citations.append({"tag": token, "title": f"Nguon {token}"})
    citations = citations[:8]

    highlights = {
        "key_questions": key_questions,
        "ai_focus": first_reply[:220] if first_reply else "",
        "recommended_homework": [
            "Tom tat lai 3 y chinh ve chu de vua hoc.",
            "Chon 1 hoa tiet/dinh va giai thich y nghia bieu tuong bang ngoi cua em.",
        ],
        "low_interaction": bool(metrics.get("engagement", {}).get("low_interaction")),
    }

    title = (live_session.title or "Buoi hoc live").strip()
    summary_text = (
        f"Tom tat buoi hoc '{title}':\n"
        f"- So luot trao doi: user={metrics.get('engagement', {}).get('user_turns', 0)}, "
        f"ai={metrics.get('engagement', {}).get('ai_turns', 0)}.\n"
        f"- Ty le tham du: {round(float(metrics.get('attendance', {}).get('attendance_rate', 0.0)) * 100, 1)}%.\n"
        f"- Cau hoi noi bat: {('; '.join(key_questions[:3])) if key_questions else 'Khong co du lieu cau hoi.'}\n"
        f"- Goi y bai tap: {highlights['recommended_homework'][0]}"
    )
    if citations:
        citation_tags = " ".join(f"[{item['tag']}]" for item in citations[:5])
        summary_text = (
            f"{summary_text}\n"
            f"- Citation tags: {citation_tags}"
        )

    return summary_text, highlights, citations


def generate_session_summary(
    db: Session,
    *,
    live_session: LiveSession,
    force: bool = False,
) -> SessionSummary:
    cleanup_expired_reporting_data(db, live_session_id=live_session.id)

    if not force:
        existing = _latest_summary(db, live_session_id=live_session.id)
        if existing is not None:
            return existing

    transcripts = list_session_transcripts(
        db,
        live_session_id=live_session.id,
        limit=max(30, min(2000, int(settings.live_summary_max_turns or 120) * 5)),
    )
    metrics = compute_attendance_engagement(db, live_session=live_session)
    ensure_low_interaction_warning(db, live_session=live_session, metrics=metrics)

    summary_text, highlights, citations = _build_summary_text(
        live_session=live_session,
        metrics=metrics,
        transcripts=transcripts,
    )
    rubric = _rubric_overview(transcripts)

    summary = SessionSummary(
        live_session_id=live_session.id,
        summary_encrypted=live_crypto.encrypt_text(summary_text),
        highlights=highlights,
        citations={"items": citations},
        rubric_overview=rubric,
        summary_metadata={
            "attendance": metrics.get("attendance", {}),
            "engagement": metrics.get("engagement", {}),
        },
        created_by="ai_teacher_pipeline",
        expires_at=_retention_expires(int(settings.live_summary_retention_days or 90)),
    )
    db.add(summary)
    # Ensure generated UUID/default timestamps are materialized before serialization.
    db.flush()

    create_session_action(
        db,
        live_session_id=live_session.id,
        action_type="summary_generated",
        status="done",
        payload={
            "citations": citations,
            "attendance": metrics.get("attendance", {}),
            "engagement": metrics.get("engagement", {}),
            "rubric_overview": rubric,
        },
    )

    return summary


def get_or_generate_summary(db: Session, *, live_session: LiveSession) -> SessionSummary:
    existing = _latest_summary(db, live_session_id=live_session.id)
    if existing is not None:
        return existing
    return generate_session_summary(db, live_session=live_session, force=True)


def build_dashboard_payload(db: Session, *, live_session: LiveSession) -> dict[str, Any]:
    summary = get_or_generate_summary(db, live_session=live_session)
    transcripts = list_session_transcripts(db, live_session_id=live_session.id, limit=500)
    metrics = compute_attendance_engagement(db, live_session=live_session)
    ensure_low_interaction_warning(db, live_session=live_session, metrics=metrics)

    actions = (
        db.execute(
            select(SessionAction)
            .where(SessionAction.live_session_id == live_session.id)
            .order_by(SessionAction.created_at.desc())
            .limit(100)
        )
        .scalars()
        .all()
    )

    timeline = [
        {
            "id": str(item.id),
            "type": item.action_type,
            "status": item.status,
            "cost_usd": float(item.cost_usd) if item.cost_usd is not None else None,
            "payload": item.payload if isinstance(item.payload, dict) else {},
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in actions
    ]

    return {
        "session": {
            "id": str(live_session.id),
            "title": live_session.title,
            "status": live_session.status,
            "starts_at": live_session.starts_at.isoformat() if live_session.starts_at else None,
            "ended_at": live_session.ended_at.isoformat() if live_session.ended_at else None,
        },
        "summary": {
            "id": str(summary.id),
            "text": live_crypto.decrypt_text(summary.summary_encrypted),
            "highlights": summary.highlights if isinstance(summary.highlights, dict) else {},
            "citations": summary.citations.get("items", []) if isinstance(summary.citations, dict) else [],
            "rubric_overview": summary.rubric_overview if isinstance(summary.rubric_overview, dict) else {},
            "metadata": summary.summary_metadata if isinstance(summary.summary_metadata, dict) else {},
            "created_at": summary.created_at.isoformat() if summary.created_at else None,
        },
        "metrics": metrics,
        "transcripts": transcripts,
        "actions": timeline,
        "ai_cost": {
            "total_usd": round(session_ai_cost_total(db, live_session_id=live_session.id), 6),
            "ceiling_usd": round(resolve_session_cost_ceiling(db, live_session=live_session), 6),
        },
    }


def export_transcripts_json(db: Session, *, live_session_id: uuid.UUID) -> dict[str, Any]:
    transcripts = list_session_transcripts(db, live_session_id=live_session_id, limit=2000)
    return {
        "live_session_id": str(live_session_id),
        "count": len(transcripts),
        "items": transcripts,
        "generated_at": _utcnow().isoformat(),
    }


def export_transcripts_csv(db: Session, *, live_session_id: uuid.UUID) -> str:
    transcripts = list_session_transcripts(db, live_session_id=live_session_id, limit=2000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "id",
            "speaker_type",
            "speaker_identity",
            "speaker_user_id",
            "text",
            "confidence",
            "started_at",
            "ended_at",
            "created_at",
            "event_type",
            "provider",
            "model",
            "citations",
        ]
    )
    for item in transcripts:
        writer.writerow(
            [
                item.get("id"),
                item.get("speaker_type"),
                item.get("speaker_identity"),
                item.get("speaker_user_id"),
                item.get("text"),
                item.get("confidence"),
                item.get("started_at"),
                item.get("ended_at"),
                item.get("created_at"),
                item.get("event_type"),
                item.get("provider"),
                item.get("model"),
                ";".join(item.get("citations") or []),
            ]
        )
    return output.getvalue()
