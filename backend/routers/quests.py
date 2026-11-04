# -*- coding: utf-8 -*-
"""Quests APIRouter module for Luuniensuki LMS.

W05-A08 / V5-T058: Server-verified quest progression, source task rewards,
and anti-abuse validation against stale client reward claiming.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..deps import get_current_user, get_db
from ..models import (
    Certificate,
    Quest,
    QuestProgress,
    QuestStep,
    User,
)
from ..apischemas.quests import (
    QuestClaimRewardOut,
    QuestDetailOut,
    QuestListItemOut,
    QuestObjectiveOut,
    QuestPrerequisiteOut,
    QuestStepOut,
    QuestSummaryOut,
    QuestCertificateOut,
)
from ..domain.helpers import (
    get_allowed_content_ratings,
    _apply_quest_rewards,
    _build_quest_rewards,
    _compute_quest_progress_data,
    _extract_next_objective,
    _quest_prerequisite_completed,
)

router = APIRouter()


@router.get("/api/v1/quests", response_model=list[QuestListItemOut])
def list_quests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[QuestListItemOut]:
    allowed_ratings = get_allowed_content_ratings(current_user)

    quests = (
        db.execute(
            select(Quest)
            .options(
                selectinload(Quest.steps).selectinload(QuestStep.objectives),
                selectinload(Quest.rewards),
                selectinload(Quest.prerequisite),
            )
            .where(Quest.is_active.is_(True), Quest.content_rating.in_(allowed_ratings))
            .order_by(Quest.display_order.asc(), Quest.created_at.asc())
        )
        .scalars()
        .all()
    )
    if not quests:
        return []

    progress_entries = (
        db.execute(
            select(QuestProgress).where(
                QuestProgress.user_id == current_user.id,
                QuestProgress.quest_id.in_([q.id for q in quests]),
            )
        )
        .scalars()
        .all()
    )
    progress_by_quest = {p.quest_id: p for p in progress_entries}

    items: list[QuestListItemOut] = []
    for quest in quests:
        progress_entry = progress_by_quest.get(quest.id)
        prereq_complete = _quest_prerequisite_completed(
            db,
            user_id=current_user.id,
            quest=quest,
            progress_by_quest=progress_by_quest,
        )
        is_locked = not prereq_complete
        status = "locked" if is_locked else "not_started"
        progress_percent = 0.0

        if not is_locked and progress_entry is not None:
            steps_payload, progress_percent = _compute_quest_progress_data(
                db, user=current_user, quest=quest, progress_entry=progress_entry
            )
            if progress_entry.status != "completed" and progress_percent >= 100.0:
                _apply_quest_rewards(
                    db, user=current_user, quest=quest, progress_entry=progress_entry
                )
                db.commit()
                progress_percent = 100.0
            status = progress_entry.status

        items.append(
            QuestListItemOut(
                id=quest.id,
                slug=quest.slug,
                name=quest.name,
                description=quest.description,
                category=quest.category,
                display_order=int(quest.display_order or 0),
                status=status,
                progress_percent=progress_percent,
                is_locked=is_locked,
                lock_reason=(
                    f"Hoàn thành {quest.prerequisite.name}"
                    if is_locked and quest.prerequisite
                    else None
                ),
                prerequisite=(
                    QuestPrerequisiteOut(
                        id=quest.prerequisite.id,
                        slug=quest.prerequisite.slug,
                        name=quest.prerequisite.name,
                    )
                    if quest.prerequisite
                    else None
                ),
                rewards=_build_quest_rewards(quest),
            )
        )

    return items


@router.get("/api/v1/quests/{quest_slug}", response_model=QuestDetailOut)
def get_quest_detail(
    quest_slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuestDetailOut:
    quest = db.execute(
        select(Quest)
        .options(
            selectinload(Quest.steps).selectinload(QuestStep.objectives),
            selectinload(Quest.rewards),
            selectinload(Quest.prerequisite),
        )
        .where(Quest.slug == quest_slug, Quest.is_active.is_(True))
    ).scalar_one_or_none()
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")

    allowed_ratings = get_allowed_content_ratings(current_user)
    if quest.content_rating not in allowed_ratings:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this content. Please verify your age.",
        )

    progress_entry = db.execute(
        select(QuestProgress).where(
            QuestProgress.user_id == current_user.id, QuestProgress.quest_id == quest.id
        )
    ).scalar_one_or_none()

    progress_by_quest = {quest.id: progress_entry} if progress_entry else {}
    prereq_complete = _quest_prerequisite_completed(
        db, user_id=current_user.id, quest=quest, progress_by_quest=progress_by_quest
    )
    is_locked = not prereq_complete
    status = "locked" if is_locked else "not_started"

    steps_payload, progress_percent = _compute_quest_progress_data(
        db, user=current_user, quest=quest, progress_entry=progress_entry
    )
    if progress_entry is not None:
        status = progress_entry.status
        if progress_entry.status != "completed" and progress_percent >= 100.0:
            _apply_quest_rewards(
                db, user=current_user, quest=quest, progress_entry=progress_entry
            )
            db.commit()
            progress_percent = 100.0
            status = "completed"

    certificate = db.execute(
        select(Certificate).where(
            Certificate.user_id == current_user.id,
            Certificate.reason_type == "quest",
            Certificate.reason_id == quest.id,
        )
    ).scalar_one_or_none()

    return QuestDetailOut(
        id=quest.id,
        slug=quest.slug,
        name=quest.name,
        description=quest.description,
        category=quest.category,
        display_order=int(quest.display_order or 0),
        status=status,
        progress_percent=progress_percent,
        is_locked=is_locked,
        lock_reason=(
            f"Hoàn thành {quest.prerequisite.name}"
            if is_locked and quest.prerequisite
            else None
        ),
        prerequisite=(
            QuestPrerequisiteOut(
                id=quest.prerequisite.id,
                slug=quest.prerequisite.slug,
                name=quest.prerequisite.name,
            )
            if quest.prerequisite
            else None
        ),
        rewards=_build_quest_rewards(quest),
        steps=[
            QuestStepOut(
                id=step["id"],
                title=step["title"],
                description=step["description"],
                display_order=step["display_order"],
                completion_percent=step["completion_percent"],
                objectives=[
                    QuestObjectiveOut(
                        id=obj["id"],
                        objective_type=obj["objective_type"],
                        target_value=obj["target_value"],
                        current_value=obj["current_value"],
                        is_complete=obj["is_complete"],
                        params=obj["params"],
                    )
                    for obj in step["objectives"]
                ],
            )
            for step in steps_payload
        ],
        certificate=(
            QuestCertificateOut(
                code=certificate.code,
                issued_at=certificate.issued_at,
                issuer_name=certificate.issuer_name,
            )
            if certificate is not None
            else None
        ),
    )


@router.post("/api/v1/quests/{quest_slug}/start", response_model=QuestDetailOut)
def start_quest(
    quest_slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuestDetailOut:
    quest = db.execute(
        select(Quest)
        .options(
            selectinload(Quest.steps).selectinload(QuestStep.objectives),
            selectinload(Quest.rewards),
            selectinload(Quest.prerequisite),
        )
        .where(Quest.slug == quest_slug, Quest.is_active.is_(True))
    ).scalar_one_or_none()
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")

    progress_entry = db.execute(
        select(QuestProgress).where(
            QuestProgress.user_id == current_user.id, QuestProgress.quest_id == quest.id
        )
    ).scalar_one_or_none()
    if progress_entry is None:
        prereq_complete = True
        if quest.prerequisite_id:
            prereq_complete = (
                db.execute(
                    select(QuestProgress).where(
                        QuestProgress.user_id == current_user.id,
                        QuestProgress.quest_id == quest.prerequisite_id,
                        QuestProgress.status == "completed",
                    )
                ).scalar_one_or_none()
                is not None
            )
        if not prereq_complete:
            raise HTTPException(status_code=403, detail="Quest is locked")

        progress_entry = QuestProgress(user_id=current_user.id, quest_id=quest.id)
        db.add(progress_entry)
        db.commit()
        db.refresh(progress_entry)

    return get_quest_detail(quest_slug, current_user=current_user, db=db)


@router.post("/api/v1/quests/{quest_slug}/claim", response_model=QuestClaimRewardOut)
def claim_quest_reward(
    quest_slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuestClaimRewardOut:
    """Explicitly claim rewards for a completed quest with server-side verification.

    Negative abuse defense: Stale clients or unverified claims are strictly rejected.
    """
    quest = db.execute(
        select(Quest)
        .options(
            selectinload(Quest.steps).selectinload(QuestStep.objectives),
            selectinload(Quest.rewards),
            selectinload(Quest.prerequisite),
        )
        .where(Quest.slug == quest_slug, Quest.is_active.is_(True))
    ).scalar_one_or_none()
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")

    # Content rating access check
    allowed_ratings = get_allowed_content_ratings(current_user)
    if quest.content_rating not in allowed_ratings:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this content. Please verify your age.",
        )

    progress_entry = db.execute(
        select(QuestProgress).where(
            QuestProgress.user_id == current_user.id, QuestProgress.quest_id == quest.id
        )
    ).scalar_one_or_none()

    if progress_entry is None:
        raise HTTPException(
            status_code=400,
            detail="Quest has not been started yet",
        )

    # Prerequisite check
    if quest.prerequisite_id:
        prereq_complete = (
            db.execute(
                select(QuestProgress).where(
                    QuestProgress.user_id == current_user.id,
                    QuestProgress.quest_id == quest.prerequisite_id,
                    QuestProgress.status == "completed",
                )
            ).scalar_one_or_none()
            is not None
        )
        if not prereq_complete:
            raise HTTPException(
                status_code=403,
                detail="Quest is locked: prerequisite not completed",
            )

    # If already marked completed and certificate exists
    existing_cert = db.execute(
        select(Certificate).where(
            Certificate.user_id == current_user.id,
            Certificate.reason_type == "quest",
            Certificate.reason_id == quest.id,
        )
    ).scalar_one_or_none()

    if progress_entry.status == "completed" and existing_cert is not None:
        raise HTTPException(
            status_code=400,
            detail="Quest rewards have already been claimed",
        )

    # Server-verified objective completion calculation
    steps_payload, progress_percent = _compute_quest_progress_data(
        db, user=current_user, quest=quest, progress_entry=progress_entry
    )

    if progress_percent < 100.0:
        raise HTTPException(
            status_code=400,
            detail="Cannot claim rewards without server-verified quest completion",
        )

    # Server confirmed 100% completion! Award rewards atomically
    xp_awarded, badges_awarded, certificate = _apply_quest_rewards(
        db, user=current_user, quest=quest, progress_entry=progress_entry
    )
    db.commit()
    db.refresh(current_user)

    streak_freezes_awarded = sum(
        int(r.amount or 1)
        for r in quest.rewards
        if str(r.reward_type or "").strip().lower() == "streak_freeze"
    )

    cert_out = (
        QuestCertificateOut(
            code=certificate.code,
            issued_at=certificate.issued_at,
            issuer_name=certificate.issuer_name,
        )
        if certificate is not None
        else (
            QuestCertificateOut(
                code=existing_cert.code,
                issued_at=existing_cert.issued_at,
                issuer_name=existing_cert.issuer_name,
            )
            if existing_cert is not None
            else None
        )
    )

    return QuestClaimRewardOut(
        quest_id=quest.id,
        quest_slug=quest.slug,
        quest_name=quest.name,
        status="completed",
        xp_awarded=xp_awarded,
        badges_awarded=badges_awarded,
        streak_freezes_awarded=streak_freezes_awarded,
        certificate=cert_out,
        message="Quest rewards successfully claimed!",
    )


@router.get("/api/v1/users/me/quest-summary", response_model=Optional[QuestSummaryOut])
def get_quest_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Optional[QuestSummaryOut]:
    active_progress = db.execute(
        select(QuestProgress)
        .join(Quest, QuestProgress.quest_id == Quest.id)
        .where(
            QuestProgress.user_id == current_user.id,
            QuestProgress.status != "completed",
            Quest.is_active.is_(True),
        )
        .order_by(QuestProgress.started_at.desc())
        .limit(1)
    ).scalars().first()

    quest = None
    progress_entry = None
    if active_progress is not None:
        quest = db.execute(
            select(Quest)
            .options(
                selectinload(Quest.steps).selectinload(QuestStep.objectives),
                selectinload(Quest.rewards),
                selectinload(Quest.prerequisite),
            )
            .where(Quest.id == active_progress.quest_id)
        ).scalar_one_or_none()
        progress_entry = active_progress
    else:
        quests = (
            db.execute(
                select(Quest)
                .options(
                    selectinload(Quest.steps).selectinload(QuestStep.objectives),
                    selectinload(Quest.rewards),
                    selectinload(Quest.prerequisite),
                )
                .where(Quest.is_active.is_(True))
                .order_by(Quest.display_order.asc(), Quest.created_at.asc())
            )
            .scalars()
            .all()
        )
        if quests:
            progress_entries = (
                db.execute(
                    select(QuestProgress).where(
                        QuestProgress.user_id == current_user.id,
                        QuestProgress.quest_id.in_([q.id for q in quests]),
                    )
                )
                .scalars()
                .all()
            )
            progress_by_quest = {p.quest_id: p for p in progress_entries}
            for candidate in quests:
                if _quest_prerequisite_completed(
                    db,
                    user_id=current_user.id,
                    quest=candidate,
                    progress_by_quest=progress_by_quest,
                ):
                    quest = candidate
                    break

    if quest is None:
        return None

    steps_payload, progress_percent = _compute_quest_progress_data(
        db, user=current_user, quest=quest, progress_entry=progress_entry
    )
    status = progress_entry.status if progress_entry else "not_started"
    if (
        progress_entry is not None
        and status != "completed"
        and progress_percent >= 100.0
    ):
        _apply_quest_rewards(
            db, user=current_user, quest=quest, progress_entry=progress_entry
        )
        db.commit()
        progress_percent = 100.0
        status = "completed"

    next_step_title, next_objective = _extract_next_objective(steps_payload)

    return QuestSummaryOut(
        quest_id=quest.id,
        quest_slug=quest.slug,
        quest_name=quest.name,
        status=status,
        progress_percent=progress_percent,
        next_step_title=next_step_title,
        next_objective=next_objective,
    )
