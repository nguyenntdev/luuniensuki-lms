"""
Provision a stable demo teacher + classroom + live session for direct testing.

This script is idempotent:
- Reuses existing teacher account by email.
- Reuses an active (not ended) live session when available.
- Creates missing resources when needed.

Run inside API container:
  python -m backend.provision_live_demo
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from .config import settings
from .models import Classroom, LiveSession, LiveSessionStatus, User, UserRole
from .security import hash_password
from .services import classroom as classroom_service
from .services import live_sessions as live_session_service


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _session_factory():
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


def _ensure_teacher(
    db: Session,
    *,
    email: str,
    password: str,
    display_name: str,
) -> tuple[User, bool]:
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    created = False

    if user is None:
        user = User(
            email=email,
            password_hash=hash_password(password),
            display_name=display_name,
            role=UserRole.teacher,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user, True

    user.display_name = display_name
    user.password_hash = hash_password(password)
    if user.role != UserRole.admin:
        user.role = UserRole.teacher
    db.commit()
    db.refresh(user)
    return user, created


def _ensure_classroom(
    db: Session,
    *,
    teacher: User,
    class_name: str,
    max_students: int,
) -> tuple[Classroom, bool]:
    classroom = (
        db.execute(
            select(Classroom)
            .where(
                Classroom.teacher_id == teacher.id,
                Classroom.name == class_name,
            )
            .order_by(Classroom.created_at.desc())
        )
        .scalars()
        .first()
    )
    if classroom is not None:
        if classroom.is_archived:
            classroom.is_archived = False
            db.commit()
            db.refresh(classroom)
        return classroom, False

    classroom = classroom_service.create_classroom(
        db=db,
        teacher=teacher,
        name=class_name,
        description="Demo lớp học live AI Teacher (auto provision).",
        max_students=max_students,
        settings={},
    )
    return classroom, True


def _find_active_session(db: Session, *, classroom_id) -> LiveSession | None:
    sessions = (
        db.execute(
            select(LiveSession)
            .where(LiveSession.classroom_id == classroom_id)
            .order_by(LiveSession.created_at.desc())
            .limit(10)
        )
        .scalars()
        .all()
    )
    for session in sessions:
        if session.status == LiveSessionStatus.ended.value:
            continue
        if session.ended_at is not None:
            continue
        return session
    return None


def _ensure_live_session(
    db: Session,
    *,
    classroom: Classroom,
    teacher: User,
    session_title: str,
) -> tuple[LiveSession, bool]:
    existing = _find_active_session(db, classroom_id=classroom.id)
    if existing is not None:
        metadata = dict(existing.session_metadata or {})
        changed = False
        if metadata.get("ai_enabled") is not True:
            metadata["ai_enabled"] = True
            changed = True
        if metadata.get("lock_room") is not False:
            metadata["lock_room"] = False
            changed = True
        if changed:
            existing.session_metadata = metadata
            db.commit()
            db.refresh(existing)
        return existing, False

    live_session = live_session_service.create_live_session(
        db=db,
        classroom=classroom,
        created_by=teacher,
        title=session_title,
        starts_at=_utcnow(),
        session_metadata={
            "ai_enabled": True,
            "lock_room": False,
        },
    )
    return live_session, True


def run_provision(
    *,
    email: str,
    password: str,
    display_name: str,
    class_name: str,
    session_title: str,
    max_students: int,
    base_url: str,
) -> dict[str, Any]:
    session_factory = _session_factory()
    db = session_factory()
    try:
        teacher, teacher_created = _ensure_teacher(
            db,
            email=email,
            password=password,
            display_name=display_name,
        )
        classroom, classroom_created = _ensure_classroom(
            db,
            teacher=teacher,
            class_name=class_name,
            max_students=max_students,
        )
        live_session, session_created = _ensure_live_session(
            db,
            classroom=classroom,
            teacher=teacher,
            session_title=session_title,
        )
    finally:
        db.close()

    base = base_url.rstrip("/")
    demo_key = str(os.getenv("DEMO_LIVE_ENTRY_KEY", "")).strip()
    entry_url = f"{base}/api/v1/live/demo-enter"
    if demo_key:
        entry_url = f"{entry_url}?key={demo_key}"
    return {
        "teacher_created": teacher_created,
        "classroom_created": classroom_created,
        "live_session_created": session_created,
        "teacher": {
            "email": email,
            "password": password,
            "display_name": display_name,
            "role": "teacher",
        },
        "classroom": {
            "id": str(classroom.id),
            "name": classroom.name,
            "class_code": classroom.class_code,
            "max_students": classroom.max_students,
        },
        "live_session": {
            "id": str(live_session.id),
            "title": live_session.title,
            "status": live_session.status,
            "room_name": live_session.room_name,
            "url": f"{base}/live/{live_session.id}",
        },
        "login_url": f"{base}/login",
        "entry_url": entry_url,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Provision stable demo teacher + live classroom session."
    )
    parser.add_argument(
        "--email",
        default=os.getenv("DEMO_LIVE_TEACHER_EMAIL", "live.teacher@histolab.icu"),
    )
    parser.add_argument(
        "--password",
        default=os.getenv("DEMO_LIVE_TEACHER_PASSWORD", "LiveTeacher@2026"),
    )
    parser.add_argument(
        "--display-name",
        default=os.getenv("DEMO_LIVE_TEACHER_NAME", "Live Demo Teacher"),
    )
    parser.add_argument(
        "--class-name",
        default=os.getenv("DEMO_LIVE_CLASS_NAME", "AI Teacher Demo Class"),
    )
    parser.add_argument(
        "--session-title",
        default=os.getenv("DEMO_LIVE_SESSION_TITLE", "AI Teacher Live Demo Session"),
    )
    parser.add_argument(
        "--max-students",
        type=int,
        default=int(os.getenv("DEMO_LIVE_MAX_STUDENTS", "60")),
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("DEMO_LIVE_BASE_URL", "https://lms.histolab.icu"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_provision(
        email=args.email.strip().lower(),
        password=args.password,
        display_name=args.display_name.strip() or "Live Demo Teacher",
        class_name=args.class_name.strip() or "AI Teacher Demo Class",
        session_title=args.session_title.strip() or "AI Teacher Live Demo Session",
        max_students=max(10, args.max_students),
        base_url=args.base_url.strip() or "https://lms.histolab.icu",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
