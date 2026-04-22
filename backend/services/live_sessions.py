"""
Live session service for realtime classrooms (LiveKit).
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse

import httpx
from jose import jwt
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from ..config import settings
from ..models import (
    ClassMember,
    Classroom,
    LiveEvent,
    LiveParticipant,
    LiveParticipantRole,
    LiveSession,
    LiveSessionStatus,
    User,
    UserRole,
)

ADMIN_ROLES = {UserRole.admin, UserRole.super_admin}
STAFF_ROLES = {UserRole.teacher, UserRole.admin, UserRole.super_admin}

JOIN_EVENT_TYPES = {
    "participant_joined",
    "participant_connected",
    "participant_join",
}
LEFT_EVENT_TYPES = {
    "participant_left",
    "participant_disconnected",
    "participant_leave",
}
ROOM_END_EVENT_TYPES = {
    "room_finished",
    "room_ended",
    "room_closed",
}
SESSION_METADATA_LOCK_ROOM_KEY = "lock_room"
SESSION_METADATA_AI_ENABLED_KEY = "ai_enabled"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _room_name_for_classroom(classroom_id: uuid.UUID) -> str:
    suffix = uuid.uuid4().hex[:10]
    return f"{settings.livekit_room_prefix}-{str(classroom_id)[:8]}-{suffix}"


def _resolve_livekit_http_base_url() -> str:
    if not settings.livekit_url:
        raise RuntimeError("LiveKit URL is not configured")

    parsed = urlparse(settings.livekit_url)
    scheme = parsed.scheme.lower()
    if scheme == "wss":
        http_scheme = "https"
    elif scheme == "ws":
        http_scheme = "http"
    elif scheme in {"http", "https"}:
        http_scheme = scheme
    else:
        http_scheme = "https"

    host = parsed.netloc or parsed.path
    host = host.strip().rstrip("/")
    if not host:
        raise RuntimeError("Invalid LiveKit URL")
    # Support deployments where LiveKit is reverse-proxied under a path prefix,
    # for example: wss://example.com/livekit
    base_path = (parsed.path or "").strip()
    if parsed.netloc and base_path:
        base_path = "/" + base_path.strip("/")
    else:
        base_path = ""

    return f"{http_scheme}://{host}{base_path}"


def _build_livekit_server_token() -> str:
    if not settings.livekit_api_key or not settings.livekit_api_secret:
        raise RuntimeError("LiveKit API credentials are not configured")

    now = _utcnow()
    expires_at = now + timedelta(minutes=5)
    claims: dict[str, Any] = {
        "iss": settings.livekit_api_key,
        "nbf": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "video": {
            "roomAdmin": True,
            "roomCreate": True,
            "roomList": True,
        },
    }
    return jwt.encode(claims, settings.livekit_api_secret, algorithm="HS256")


def _extract_error_text(response: httpx.Response) -> str:
    text = response.text.strip()
    if not text:
        return f"HTTP {response.status_code}"
    try:
        payload = response.json()
    except ValueError:
        return text

    for key in ("error", "message", "msg"):
        if isinstance(payload, dict) and payload.get(key):
            return str(payload[key])
    return text


def _livekit_room_service_request(
    method: str,
    payload: dict[str, Any],
    *,
    allow_not_found: bool = False,
) -> dict[str, Any]:
    base_url = _resolve_livekit_http_base_url()
    token = _build_livekit_server_token()
    url = f"{base_url}/twirp/livekit.RoomService/{method}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    attempts = max(1, int(settings.livekit_server_api_retry_attempts))
    backoff = max(0.05, float(settings.livekit_server_api_retry_backoff_seconds))
    timeout_seconds = max(1, int(settings.livekit_server_api_timeout_seconds))

    last_error = ""
    for attempt in range(1, attempts + 1):
        try:
            response = httpx.post(
                url,
                headers=headers,
                json=payload,
                timeout=timeout_seconds,
            )
        except httpx.RequestError as exc:
            last_error = str(exc)
            if attempt < attempts:
                time.sleep(backoff * attempt)
                continue
            raise RuntimeError(f"LiveKit {method} request failed: {last_error}") from exc

        if 200 <= response.status_code < 300:
            if not response.text.strip():
                return {}
            try:
                return response.json()
            except ValueError:
                return {}

        error_text = _extract_error_text(response)
        normalized_error = error_text.lower()

        if allow_not_found and "not found" in normalized_error:
            return {}

        retryable = response.status_code in {408, 409, 429} or response.status_code >= 500
        if retryable and attempt < attempts:
            time.sleep(backoff * attempt)
            continue

        raise RuntimeError(
            f"LiveKit {method} failed ({response.status_code}): {error_text}"
        )

    raise RuntimeError(f"LiveKit {method} failed: {last_error or 'unknown error'}")


def _create_livekit_room(room_name: str) -> None:
    try:
        _livekit_room_service_request(
            "CreateRoom",
            {
                "name": room_name,
                "empty_timeout": max(30, int(settings.livekit_room_empty_timeout_seconds)),
            },
        )
    except RuntimeError as exc:
        if "already exists" in str(exc).lower():
            return
        raise


def _close_livekit_room(room_name: str) -> None:
    _livekit_room_service_request(
        "DeleteRoom",
        {
            "room": room_name,
        },
        allow_not_found=True,
    )


def _list_livekit_participants(room_name: str) -> list[dict[str, Any]]:
    payload = _livekit_room_service_request(
        "ListParticipants",
        {
            "room": room_name,
        },
        allow_not_found=True,
    )
    participants = payload.get("participants")
    if isinstance(participants, list):
        return [item for item in participants if isinstance(item, dict)]
    return []


def _mute_livekit_participant_audio(
    room_name: str,
    identity: str,
    audio_track_sids: list[str],
) -> None:
    for track_sid in audio_track_sids:
        _livekit_room_service_request(
            "MutePublishedTrack",
            {
                "room": room_name,
                "identity": identity,
                "track_sid": track_sid,
                "muted": True,
            },
            allow_not_found=True,
        )


def _remove_livekit_participant(room_name: str, identity: str) -> None:
    _livekit_room_service_request(
        "RemoveParticipant",
        {
            "room": room_name,
            "identity": identity,
        },
        allow_not_found=True,
    )


def _parse_uuid(value: Any) -> uuid.UUID | None:
    if value is None:
        return None
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError):
        return None


def _append_live_event(
    db: Session,
    *,
    live_session_id: uuid.UUID,
    event_type: str,
    event_source: str = "app",
    participant_identity: str | None = None,
    participant_user_id: uuid.UUID | None = None,
    payload: dict[str, Any] | None = None,
) -> LiveEvent:
    event = LiveEvent(
        live_session_id=live_session_id,
        event_type=event_type,
        event_source=event_source,
        participant_identity=participant_identity,
        participant_user_id=participant_user_id,
        payload=payload or {},
    )
    db.add(event)
    return event


def _session_metadata_dict(live_session: LiveSession) -> dict[str, Any]:
    if isinstance(live_session.session_metadata, dict):
        return dict(live_session.session_metadata)
    return {}


def is_room_locked(live_session: LiveSession) -> bool:
    metadata = _session_metadata_dict(live_session)
    return bool(metadata.get(SESSION_METADATA_LOCK_ROOM_KEY, False))


def is_ai_enabled(live_session: LiveSession) -> bool:
    metadata = _session_metadata_dict(live_session)
    return bool(metadata.get(SESSION_METADATA_AI_ENABLED_KEY, True))


def record_live_event(
    db: Session,
    *,
    live_session_id: uuid.UUID,
    event_type: str,
    event_source: str = "app",
    participant_identity: str | None = None,
    participant_user_id: uuid.UUID | None = None,
    payload: dict[str, Any] | None = None,
) -> LiveEvent:
    event = _append_live_event(
        db,
        live_session_id=live_session_id,
        event_type=event_type,
        event_source=event_source,
        participant_identity=participant_identity,
        participant_user_id=participant_user_id,
        payload=payload,
    )
    db.commit()
    db.refresh(event)
    return event


def list_live_events(
    db: Session,
    *,
    live_session_id: uuid.UUID,
    limit: int = 50,
    since: datetime | None = None,
) -> list[LiveEvent]:
    query = select(LiveEvent).where(LiveEvent.live_session_id == live_session_id)
    if since is not None:
        query = query.where(LiveEvent.created_at >= since)

    return (
        db.execute(
            query.order_by(LiveEvent.created_at.desc()).limit(max(1, min(limit, 200)))
        )
        .scalars()
        .all()
    )


def find_live_session_by_room_name(db: Session, room_name: str) -> LiveSession | None:
    return (
        db.execute(select(LiveSession).where(LiveSession.room_name == room_name))
        .scalars()
        .first()
    )


def can_manage_classroom(user: User, classroom: Classroom) -> bool:
    if user.role in ADMIN_ROLES:
        return True
    return user.role == UserRole.teacher and classroom.teacher_id == user.id


def can_access_classroom(db: Session, user: User, classroom: Classroom) -> bool:
    if can_manage_classroom(user, classroom):
        return True
    membership = db.execute(
        select(ClassMember.id).where(
            and_(ClassMember.class_id == classroom.id, ClassMember.user_id == user.id)
        )
    ).scalar_one_or_none()
    return membership is not None


def _get_active_participant_for_user(
    db: Session,
    *,
    live_session_id: uuid.UUID,
    user_id: uuid.UUID,
) -> LiveParticipant | None:
    return (
        db.execute(
            select(LiveParticipant).where(
                and_(
                    LiveParticipant.live_session_id == live_session_id,
                    LiveParticipant.user_id == user_id,
                    LiveParticipant.left_at.is_(None),
                )
            )
        )
        .scalars()
        .first()
    )


def can_user_moderate_live_session(
    db: Session,
    *,
    user: User,
    live_session: LiveSession,
    allow_cohost: bool = True,
) -> bool:
    classroom = db.get(Classroom, live_session.classroom_id)
    if classroom is None:
        return False

    if can_manage_classroom(user, classroom):
        return True

    active_participant = _get_active_participant_for_user(
        db,
        live_session_id=live_session.id,
        user_id=user.id,
    )
    if active_participant is None:
        return False

    allowed_roles = {LiveParticipantRole.host.value}
    if allow_cohost:
        allowed_roles.add(LiveParticipantRole.cohost.value)
    return active_participant.role in allowed_roles


def _user_has_role_history(
    db: Session,
    *,
    live_session_id: uuid.UUID,
    user_id: uuid.UUID,
    roles: set[str],
) -> bool:
    if not roles:
        return False
    found = (
        db.execute(
            select(LiveParticipant.id).where(
                and_(
                    LiveParticipant.live_session_id == live_session_id,
                    LiveParticipant.user_id == user_id,
                    LiveParticipant.role.in_(roles),
                )
            )
        )
        .scalars()
        .first()
    )
    return found is not None


def _can_user_bypass_room_lock(
    db: Session,
    *,
    user: User,
    live_session: LiveSession,
) -> bool:
    if can_user_moderate_live_session(
        db,
        user=user,
        live_session=live_session,
        allow_cohost=True,
    ):
        return True
    return _user_has_role_history(
        db,
        live_session_id=live_session.id,
        user_id=user.id,
        roles={LiveParticipantRole.host.value, LiveParticipantRole.cohost.value},
    )


def create_live_session(
    db: Session,
    *,
    classroom: Classroom,
    created_by: User,
    title: str | None = None,
    starts_at: datetime | None = None,
    idempotency_key: str | None = None,
    session_metadata: dict[str, Any] | None = None,
) -> LiveSession:
    normalized_key = (idempotency_key or "").strip() or None
    if normalized_key:
        existing = (
            db.execute(
                select(LiveSession)
                .where(
                    and_(
                        LiveSession.classroom_id == classroom.id,
                        LiveSession.idempotency_key == normalized_key,
                    )
                )
                .order_by(LiveSession.created_at.desc())
            )
            .scalars()
            .first()
        )
        if existing is not None:
            return existing

    now = _utcnow()
    starts = starts_at or now
    status = (
        LiveSessionStatus.scheduled.value
        if starts > now + timedelta(minutes=1)
        else LiveSessionStatus.live.value
    )
    session = LiveSession(
        classroom_id=classroom.id,
        created_by_id=created_by.id,
        room_name=_room_name_for_classroom(classroom.id),
        title=title.strip() if title else None,
        status=status,
        starts_at=starts,
        idempotency_key=normalized_key,
        session_metadata=session_metadata or {},
    )
    db.add(session)
    db.flush()

    if settings.livekit_url and settings.livekit_api_key and settings.livekit_api_secret:
        try:
            _create_livekit_room(session.room_name)
        except RuntimeError:
            db.rollback()
            raise

    _append_live_event(
        db,
        live_session_id=session.id,
        event_type="session_created",
        participant_user_id=created_by.id,
        payload={
            "classroom_id": str(classroom.id),
            "status": status,
            "idempotency_key": normalized_key,
        },
    )
    db.commit()
    db.refresh(session)
    return session


def list_live_sessions_for_classroom(
    db: Session,
    *,
    classroom_id: uuid.UUID,
    limit: int = 20,
) -> list[LiveSession]:
    return (
        db.execute(
            select(LiveSession)
            .where(LiveSession.classroom_id == classroom_id)
            .order_by(LiveSession.created_at.desc())
            .limit(max(1, min(limit, 100)))
        )
        .scalars()
        .all()
    )


def get_live_session(db: Session, live_session_id: uuid.UUID) -> LiveSession | None:
    return db.get(LiveSession, live_session_id)


def list_live_participants(
    db: Session,
    *,
    live_session_id: uuid.UUID,
    include_inactive: bool = False,
) -> list[LiveParticipant]:
    query = select(LiveParticipant).where(LiveParticipant.live_session_id == live_session_id)
    if not include_inactive:
        query = query.where(LiveParticipant.left_at.is_(None))

    return (
        db.execute(query.order_by(LiveParticipant.joined_at.desc()))
        .scalars()
        .all()
    )


def get_live_participant(
    db: Session,
    *,
    live_session_id: uuid.UUID,
    participant_id: uuid.UUID,
) -> LiveParticipant | None:
    return (
        db.execute(
            select(LiveParticipant).where(
                and_(
                    LiveParticipant.id == participant_id,
                    LiveParticipant.live_session_id == live_session_id,
                )
            )
        )
        .scalars()
        .first()
    )


def count_active_participants(db: Session, live_session_id: uuid.UUID) -> int:
    return int(
        db.execute(
            select(func.count(LiveParticipant.id)).where(
                and_(
                    LiveParticipant.live_session_id == live_session_id,
                    LiveParticipant.left_at.is_(None),
                )
            )
        ).scalar_one()
    )


def ensure_user_can_access_live_session(
    db: Session,
    *,
    user: User,
    live_session: LiveSession,
) -> None:
    classroom = db.get(Classroom, live_session.classroom_id)
    if classroom is None:
        raise ValueError("Classroom not found")
    if not can_access_classroom(db, user, classroom):
        raise PermissionError("Not authorized to access this live session")


def ensure_user_can_join_live_session(
    db: Session,
    *,
    user: User,
    live_session: LiveSession,
) -> None:
    ensure_user_can_access_live_session(db, user=user, live_session=live_session)
    if is_room_locked(live_session) and not _can_user_bypass_room_lock(
        db,
        user=user,
        live_session=live_session,
    ):
        raise PermissionError("This live room is currently locked by host")


def ensure_user_can_manage_live_session(
    db: Session,
    *,
    user: User,
    live_session: LiveSession,
) -> None:
    classroom = db.get(Classroom, live_session.classroom_id)
    if classroom is None:
        raise ValueError("Classroom not found")
    if not can_manage_classroom(user, classroom):
        raise PermissionError("Not authorized to manage this live session")


def update_live_session_settings(
    db: Session,
    *,
    live_session: LiveSession,
    lock_room: bool | None,
    ai_enabled: bool | None,
    acted_by: User,
) -> LiveSession:
    metadata = _session_metadata_dict(live_session)
    changed: dict[str, Any] = {}
    if lock_room is not None:
        metadata[SESSION_METADATA_LOCK_ROOM_KEY] = bool(lock_room)
        changed[SESSION_METADATA_LOCK_ROOM_KEY] = bool(lock_room)
    if ai_enabled is not None:
        metadata[SESSION_METADATA_AI_ENABLED_KEY] = bool(ai_enabled)
        changed[SESSION_METADATA_AI_ENABLED_KEY] = bool(ai_enabled)

    if not changed:
        return live_session

    live_session.session_metadata = metadata
    _append_live_event(
        db,
        live_session_id=live_session.id,
        event_type="session_settings_updated",
        participant_user_id=acted_by.id,
        payload=changed,
    )
    db.commit()
    db.refresh(live_session)
    return live_session


def ensure_user_can_moderate_live_session(
    db: Session,
    *,
    user: User,
    live_session: LiveSession,
    allow_cohost: bool = True,
) -> None:
    classroom = db.get(Classroom, live_session.classroom_id)
    if classroom is None:
        raise ValueError("Classroom not found")
    if not can_user_moderate_live_session(
        db,
        user=user,
        live_session=live_session,
        allow_cohost=allow_cohost,
    ):
        raise PermissionError("Not authorized to moderate this live session")


def end_live_session(
    db: Session,
    live_session: LiveSession,
    *,
    ended_by_user_id: uuid.UUID | None = None,
) -> LiveSession:
    if live_session.status == LiveSessionStatus.ended.value:
        return live_session

    live_session.status = LiveSessionStatus.ended.value
    live_session.ended_at = _utcnow()

    _append_live_event(
        db,
        live_session_id=live_session.id,
        event_type="session_ended",
        participant_user_id=ended_by_user_id,
        payload={"room_name": live_session.room_name},
    )

    if settings.livekit_url and settings.livekit_api_key and settings.livekit_api_secret:
        try:
            _close_livekit_room(live_session.room_name)
        except RuntimeError as exc:
            _append_live_event(
                db,
                live_session_id=live_session.id,
                event_type="room_close_failed",
                participant_user_id=ended_by_user_id,
                payload={"error": str(exc)},
            )

    db.commit()
    db.refresh(live_session)
    return live_session


def _participant_role_for_user(user: User, classroom: Classroom) -> str:
    if user.role in ADMIN_ROLES:
        return LiveParticipantRole.host.value
    if user.role == UserRole.teacher and classroom.teacher_id == user.id:
        return LiveParticipantRole.host.value
    return LiveParticipantRole.learner.value


def upsert_participant_join(
    db: Session,
    *,
    live_session: LiveSession,
    user: User,
    identity: str,
    display_name: str | None = None,
) -> LiveParticipant:
    if live_session.status == LiveSessionStatus.ended.value:
        raise ValueError("Live session has ended")

    classroom = db.get(Classroom, live_session.classroom_id)
    if classroom is None:
        raise ValueError("Classroom not found")

    participant = db.execute(
        select(LiveParticipant).where(
            and_(
                LiveParticipant.live_session_id == live_session.id,
                LiveParticipant.user_id == user.id,
            )
        )
    ).scalar_one_or_none()

    joined_at = _utcnow()
    if participant is None:
        participant = LiveParticipant(
            live_session_id=live_session.id,
            user_id=user.id,
            participant_identity=identity,
            display_name=display_name or user.display_name,
            role=_participant_role_for_user(user, classroom),
            is_ai=False,
            joined_at=joined_at,
            left_at=None,
        )
        db.add(participant)
    else:
        participant.participant_identity = identity
        participant.display_name = display_name or user.display_name
        participant.left_at = None
        participant.joined_at = joined_at

    if live_session.status == LiveSessionStatus.scheduled.value:
        live_session.status = LiveSessionStatus.live.value
        if live_session.starts_at is None:
            live_session.starts_at = joined_at

    _append_live_event(
        db,
        live_session_id=live_session.id,
        event_type="participant_joined",
        participant_identity=identity,
        participant_user_id=user.id,
        payload={"display_name": participant.display_name, "role": participant.role},
    )

    db.commit()
    db.refresh(participant)
    return participant


def participant_identity_for_user(user: User) -> str:
    return f"user-{user.id}"


def ai_teacher_identity_for_session(live_session_id: uuid.UUID) -> str:
    """Build deterministic AI teacher identity per session."""
    compact = str(live_session_id).replace("-", "")
    return f"ai-teacher-{compact[:16]}"


def ensure_ai_teacher_participant(
    db: Session,
    *,
    live_session: LiveSession,
    display_name: str = "AI Teacher",
    identity: str | None = None,
    connection_metadata: dict[str, Any] | None = None,
    event_source: str = "ai_agent",
) -> LiveParticipant:
    """
    Ensure AI teacher is present in participant roster for one session.

    This does not require a real user account and is safe to call repeatedly.
    """
    if live_session.status == LiveSessionStatus.ended.value:
        raise ValueError("Live session has ended")

    ai_identity = (identity or ai_teacher_identity_for_session(live_session.id)).strip()
    if not ai_identity:
        raise ValueError("Invalid AI teacher identity")

    participant = (
        db.execute(
            select(LiveParticipant).where(
                and_(
                    LiveParticipant.live_session_id == live_session.id,
                    LiveParticipant.participant_identity == ai_identity,
                )
            )
        )
        .scalars()
        .first()
    )

    now = _utcnow()
    should_emit_join = False
    if participant is None:
        participant = LiveParticipant(
            live_session_id=live_session.id,
            user_id=None,
            participant_identity=ai_identity,
            display_name=display_name,
            role=LiveParticipantRole.ai_teacher.value,
            is_ai=True,
            joined_at=now,
            left_at=None,
            connection_metadata=connection_metadata or {},
        )
        db.add(participant)
        should_emit_join = True
    else:
        participant.is_ai = True
        participant.role = LiveParticipantRole.ai_teacher.value
        participant.display_name = display_name or participant.display_name
        if participant.left_at is not None:
            participant.left_at = None
            participant.joined_at = now
            should_emit_join = True
        if connection_metadata:
            merged = participant.connection_metadata or {}
            merged.update(connection_metadata)
            participant.connection_metadata = merged

    if should_emit_join:
        _append_live_event(
            db,
            live_session_id=live_session.id,
            event_type="participant_joined",
            event_source=event_source,
            participant_identity=ai_identity,
            participant_user_id=None,
            payload={
                "display_name": participant.display_name,
                "role": LiveParticipantRole.ai_teacher.value,
                "is_ai": True,
            },
        )

    db.commit()
    db.refresh(participant)
    return participant


def mark_participant_left(
    db: Session,
    *,
    live_session: LiveSession,
    user: User,
    identity: str | None = None,
) -> LiveParticipant | None:
    query = select(LiveParticipant).where(
        and_(
            LiveParticipant.live_session_id == live_session.id,
            LiveParticipant.left_at.is_(None),
        )
    )
    if identity:
        query = query.where(
            or_(
                LiveParticipant.user_id == user.id,
                LiveParticipant.participant_identity == identity,
            )
        )
    else:
        query = query.where(LiveParticipant.user_id == user.id)

    participant = db.execute(query).scalars().first()
    if participant is None:
        return None

    participant.left_at = _utcnow()
    _append_live_event(
        db,
        live_session_id=live_session.id,
        event_type="participant_left",
        participant_identity=participant.participant_identity,
        participant_user_id=participant.user_id,
        payload={"source": "leave_api"},
    )
    db.commit()
    db.refresh(participant)
    return participant


def issue_livekit_token(
    *,
    live_session: LiveSession,
    identity: str,
    display_name: str,
    metadata: dict[str, Any] | None = None,
) -> tuple[str, datetime]:
    if not settings.livekit_api_key or not settings.livekit_api_secret:
        raise RuntimeError("LiveKit API credentials are not configured")
    if not settings.livekit_url:
        raise RuntimeError("LiveKit URL is not configured")

    _create_livekit_room(live_session.room_name)

    now = _utcnow()
    expires_at = now + timedelta(minutes=max(5, settings.livekit_token_ttl_minutes))

    claims: dict[str, Any] = {
        "iss": settings.livekit_api_key,
        "sub": identity,
        "name": display_name,
        "nbf": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "video": {
            "roomJoin": True,
            "room": live_session.room_name,
            "canPublish": True,
            "canSubscribe": True,
            "canPublishData": True,
        },
    }
    if metadata:
        claims["metadata"] = json.dumps(metadata, ensure_ascii=False)

    token = jwt.encode(
        claims,
        settings.livekit_api_secret,
        algorithm="HS256",
    )
    return token, expires_at


def update_participant_role(
    db: Session,
    *,
    live_session: LiveSession,
    participant: LiveParticipant,
    role: str,
    acted_by: User,
) -> LiveParticipant:
    allowed_roles = {
        LiveParticipantRole.host.value,
        LiveParticipantRole.cohost.value,
        LiveParticipantRole.learner.value,
    }
    if role not in allowed_roles:
        raise ValueError("Invalid role")
    if participant.is_ai:
        raise ValueError("Cannot update AI participant role")

    previous_role = participant.role
    participant.role = role
    _append_live_event(
        db,
        live_session_id=live_session.id,
        event_type="participant_role_updated",
        participant_identity=participant.participant_identity,
        participant_user_id=participant.user_id,
        payload={
            "from": previous_role,
            "to": role,
            "acted_by": str(acted_by.id),
        },
    )
    db.commit()
    db.refresh(participant)
    return participant


def _extract_audio_track_sids(participant_payload: dict[str, Any]) -> list[str]:
    track_entries = participant_payload.get("tracks")
    if not isinstance(track_entries, list):
        return []

    sids: list[str] = []
    for track in track_entries:
        if not isinstance(track, dict):
            continue
        track_sid = str(track.get("sid") or "").strip()
        if not track_sid:
            continue

        track_type_raw = str(track.get("type") or "").upper()
        is_audio = track_type_raw in {"AUDIO", "1"}
        if not is_audio:
            continue

        muted = bool(track.get("muted", False))
        if muted:
            continue
        sids.append(track_sid)
    return sids


def mute_all_participants(
    db: Session,
    *,
    live_session: LiveSession,
    include_cohosts: bool,
    acted_by: User,
) -> tuple[int, int]:
    targets = list_live_participants(
        db,
        live_session_id=live_session.id,
        include_inactive=False,
    )

    filtered_targets: list[LiveParticipant] = []
    for participant in targets:
        if participant.is_ai:
            continue
        if participant.role == LiveParticipantRole.host.value:
            continue
        if (
            participant.role == LiveParticipantRole.cohost.value
            and not include_cohosts
        ):
            continue
        filtered_targets.append(participant)

    sid_map: dict[str, list[str]] = {}
    if settings.livekit_url and settings.livekit_api_key and settings.livekit_api_secret:
        for room_participant in _list_livekit_participants(live_session.room_name):
            identity = str(room_participant.get("identity") or "").strip()
            if not identity:
                continue
            sid_map[identity] = _extract_audio_track_sids(room_participant)

    processed = 0
    failed = 0
    muted_at = _utcnow().isoformat()

    for participant in filtered_targets:
        metadata = participant.connection_metadata or {}
        metadata["muted_by_host_at"] = muted_at
        metadata["muted_by_host_user_id"] = str(acted_by.id)
        participant.connection_metadata = metadata

        if settings.livekit_url and settings.livekit_api_key and settings.livekit_api_secret:
            try:
                _mute_livekit_participant_audio(
                    live_session.room_name,
                    participant.participant_identity,
                    sid_map.get(participant.participant_identity, []),
                )
                processed += 1
            except RuntimeError:
                failed += 1
        else:
            processed += 1

    _append_live_event(
        db,
        live_session_id=live_session.id,
        event_type="mute_all",
        participant_user_id=acted_by.id,
        payload={
            "include_cohosts": include_cohosts,
            "targets": [p.participant_identity for p in filtered_targets],
            "processed": processed,
            "failed": failed,
        },
    )

    db.commit()
    return processed, failed


def remove_participant(
    db: Session,
    *,
    live_session: LiveSession,
    participant: LiveParticipant,
    acted_by: User,
) -> tuple[LiveParticipant, str | None]:
    detail: str | None = None

    if settings.livekit_url and settings.livekit_api_key and settings.livekit_api_secret:
        try:
            _remove_livekit_participant(
                live_session.room_name,
                participant.participant_identity,
            )
        except RuntimeError as exc:
            detail = str(exc)

    participant.left_at = participant.left_at or _utcnow()
    metadata = participant.connection_metadata or {}
    metadata["removed_by"] = str(acted_by.id)
    metadata["removed_at"] = _utcnow().isoformat()
    participant.connection_metadata = metadata

    _append_live_event(
        db,
        live_session_id=live_session.id,
        event_type="participant_removed",
        participant_identity=participant.participant_identity,
        participant_user_id=participant.user_id,
        payload={
            "acted_by": str(acted_by.id),
            "detail": detail,
        },
    )

    db.commit()
    db.refresh(participant)
    return participant, detail


def _upsert_participant_from_webhook(
    db: Session,
    *,
    live_session: LiveSession,
    participant_payload: dict[str, Any],
    event_type: str,
) -> None:
    identity = str(participant_payload.get("identity") or "").strip()
    if not identity:
        return

    display_name = str(participant_payload.get("name") or "").strip() or None
    metadata_raw = participant_payload.get("metadata")
    metadata: dict[str, Any] = {}
    if isinstance(metadata_raw, str) and metadata_raw.strip():
        try:
            parsed = json.loads(metadata_raw)
            if isinstance(parsed, dict):
                metadata = parsed
        except json.JSONDecodeError:
            metadata = {}
    elif isinstance(metadata_raw, dict):
        metadata = metadata_raw

    user_id = _parse_uuid(metadata.get("user_id"))
    if user_id is None and identity.startswith("user-"):
        user_id = _parse_uuid(identity.replace("user-", "", 1))

    participant_lookup_filters = [LiveParticipant.participant_identity == identity]
    if user_id is not None:
        participant_lookup_filters.append(LiveParticipant.user_id == user_id)

    participant = (
        db.execute(
            select(LiveParticipant).where(
                and_(
                    LiveParticipant.live_session_id == live_session.id,
                    or_(*participant_lookup_filters),
                )
            )
        )
        .scalars()
        .first()
    )

    is_ai = bool(metadata.get("is_ai", False)) or identity.startswith("ai-")
    role = (
        LiveParticipantRole.ai_teacher.value
        if is_ai
        else (participant.role if participant else LiveParticipantRole.learner.value)
    )

    if event_type in JOIN_EVENT_TYPES:
        if participant is None:
            participant = LiveParticipant(
                live_session_id=live_session.id,
                user_id=user_id,
                participant_identity=identity,
                display_name=display_name,
                role=role,
                is_ai=is_ai,
                joined_at=_utcnow(),
                left_at=None,
                connection_metadata=metadata or {},
            )
            db.add(participant)
        else:
            participant.user_id = participant.user_id or user_id
            participant.display_name = display_name or participant.display_name
            participant.role = role
            participant.is_ai = is_ai
            participant.joined_at = _utcnow()
            participant.left_at = None
            merged_metadata = participant.connection_metadata or {}
            merged_metadata.update(metadata)
            participant.connection_metadata = merged_metadata

        if live_session.status == LiveSessionStatus.scheduled.value:
            live_session.status = LiveSessionStatus.live.value

        _append_live_event(
            db,
            live_session_id=live_session.id,
            event_type="participant_joined",
            event_source="webhook",
            participant_identity=identity,
            participant_user_id=participant.user_id,
            payload={"display_name": display_name, "role": role},
        )
        return

    if event_type in LEFT_EVENT_TYPES:
        if participant is not None:
            participant.left_at = _utcnow()
        _append_live_event(
            db,
            live_session_id=live_session.id,
            event_type="participant_left",
            event_source="webhook",
            participant_identity=identity,
            participant_user_id=participant.user_id if participant else user_id,
            payload={"display_name": display_name},
        )


def process_livekit_webhook_event(
    db: Session,
    *,
    payload: dict[str, Any],
) -> dict[str, Any]:
    event_type = str(payload.get("event") or payload.get("type") or "").strip().lower()
    if not event_type:
        raise ValueError("Missing webhook event type")

    room_payload = payload.get("room")
    room_name = ""
    if isinstance(room_payload, dict):
        room_name = str(room_payload.get("name") or "").strip()
    elif isinstance(room_payload, str):
        room_name = room_payload.strip()

    if not room_name:
        raise ValueError("Missing room name in webhook payload")

    live_session = find_live_session_by_room_name(db, room_name)
    if live_session is None:
        return {
            "processed": False,
            "reason": "live_session_not_found",
            "event_type": event_type,
            "room_name": room_name,
        }

    participant_payload = payload.get("participant")
    if not isinstance(participant_payload, dict):
        participant_payload = {}

    _append_live_event(
        db,
        live_session_id=live_session.id,
        event_type=f"webhook.{event_type}",
        event_source="webhook",
        participant_identity=str(participant_payload.get("identity") or "") or None,
        participant_user_id=_parse_uuid(
            (participant_payload.get("metadata") or {}).get("user_id")
            if isinstance(participant_payload.get("metadata"), dict)
            else None
        ),
        payload=payload,
    )

    if event_type in JOIN_EVENT_TYPES or event_type in LEFT_EVENT_TYPES:
        _upsert_participant_from_webhook(
            db,
            live_session=live_session,
            participant_payload=participant_payload,
            event_type=event_type,
        )

    if event_type in ROOM_END_EVENT_TYPES:
        if live_session.status != LiveSessionStatus.ended.value:
            live_session.status = LiveSessionStatus.ended.value
            live_session.ended_at = live_session.ended_at or _utcnow()
            _append_live_event(
                db,
                live_session_id=live_session.id,
                event_type="session_ended",
                event_source="webhook",
                payload={"reason": event_type},
            )

    db.commit()
    return {
        "processed": True,
        "event_type": event_type,
        "live_session_id": str(live_session.id),
    }
