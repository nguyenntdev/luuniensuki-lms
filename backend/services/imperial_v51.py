# -*- coding: utf-8 -*-
"""Service layer for Imperial City V5.1 modules (STTTNNĐ).

Provides domain services for:
- Learning Media & Media Hotspots (UV coordinates, 360 panoramas, 3D models)
- Art Details, Primary Source Claim Citations, and Detail Questions
- Heritage Detective Clues & Student Attempts
- Gamified Interactive Questions & Answer Submissions (with evidence rationale)
- Teacher Assignment Releases & Tracking
- Admin CRUD with optimistic concurrency control
"""
from __future__ import annotations

from typing import Any, Optional, Union
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from ..apischemas.imperial_v51 import (
    ImperialArtDetailCreate,
    ImperialArtDetailUpdate,
    ImperialAssignmentReleaseCreate,
    ImperialAssignmentReleaseUpdate,
    ImperialClueCreate,
    ImperialClueUpdate,
    ImperialLearningMediaCreate,
    ImperialLearningMediaUpdate,
    ImperialMediaHotspotCreate,
    ImperialMediaHotspotUpdate,
    ImperialQuestionCreate,
    ImperialQuestionUpdate,
)
from ..errors import AppError
from ..imperial_models import CONTENT_SCOPE_IMPERIAL, ImperialSite
from ..imperial_v51_models import (
    ImperialArtDetail,
    ImperialArtDetailClaimSource,
    ImperialArtDetailQuestion,
    ImperialAssignmentRelease,
    ImperialClue,
    ImperialClueAttempt,
    ImperialLearningMedia,
    ImperialMediaHotspot,
    ImperialQuestion,
)


def _resolve_site(db: Session, site_slug_or_id: Union[UUID, str]) -> ImperialSite:
    """Helper to resolve site by slug or UUID within imperial scope."""
    if isinstance(site_slug_or_id, UUID):
        site = db.get(ImperialSite, site_slug_or_id)
    else:
        try:
            val_uuid = UUID(str(site_slug_or_id))
            site = db.get(ImperialSite, val_uuid)
        except ValueError:
            site = db.scalar(
                select(ImperialSite).where(
                    ImperialSite.slug == str(site_slug_or_id),
                    ImperialSite.content_scope == CONTENT_SCOPE_IMPERIAL,
                )
            )
    if not site or site.content_scope != CONTENT_SCOPE_IMPERIAL:
        raise AppError("IMPERIAL_SITE_NOT_FOUND", f"Site '{site_slug_or_id}' not found", 404)
    return site


# --------------------------------------------------------------------------- #
# 1. Learning Media & Hotspots
# --------------------------------------------------------------------------- #
def get_site_learning_media(
    db: Session, site_slug: str, include_drafts: bool = False
) -> list[ImperialLearningMedia]:
    """Retrieve learning media assets for a site with associated hotspots."""
    site = _resolve_site(db, site_slug)

    stmt = (
        select(ImperialLearningMedia)
        .where(
            ImperialLearningMedia.site_id == site.id,
            ImperialLearningMedia.content_scope == CONTENT_SCOPE_IMPERIAL,
        )
        .options(
            selectinload(ImperialLearningMedia.hotspots).selectinload(ImperialMediaHotspot.art_detail)
        )
        .order_by(ImperialLearningMedia.created_at.asc())
    )
    if not include_drafts:
        stmt = stmt.where(ImperialLearningMedia.review_status == "published")

    media_items = list(db.scalars(stmt).all())
    if not include_drafts:
        # Filter hotspots to published only for public viewing
        for m in media_items:
            m.hotspots = [h for h in m.hotspots if h.review_status == "published"]
    return media_items


def get_media_hotspots(
    db: Session, media_id: UUID, include_drafts: bool = False
) -> list[ImperialMediaHotspot]:
    """Retrieve hotspots for a media asset."""
    media = db.get(ImperialLearningMedia, media_id)
    if not media or media.content_scope != CONTENT_SCOPE_IMPERIAL:
        raise AppError("IMPERIAL_MEDIA_NOT_FOUND", f"Media '{media_id}' not found", 404)

    stmt = (
        select(ImperialMediaHotspot)
        .where(
            ImperialMediaHotspot.media_id == media_id,
            ImperialMediaHotspot.content_scope == CONTENT_SCOPE_IMPERIAL,
        )
        .options(selectinload(ImperialMediaHotspot.art_detail))
        .order_by(ImperialMediaHotspot.created_at.asc())
    )
    if not include_drafts:
        stmt = stmt.where(ImperialMediaHotspot.review_status == "published")

    return list(db.scalars(stmt).all())


# --------------------------------------------------------------------------- #
# 2. Art Details & Claims
# --------------------------------------------------------------------------- #
def get_art_detail(
    db: Session, detail_id_or_slug: Union[UUID, str], include_drafts: bool = False
) -> ImperialArtDetail:
    """Retrieve art detail dossier with claims and inquiry questions."""
    stmt = (
        select(ImperialArtDetail)
        .options(
            selectinload(ImperialArtDetail.claim_sources),
            selectinload(ImperialArtDetail.questions),
        )
        .where(ImperialArtDetail.content_scope == CONTENT_SCOPE_IMPERIAL)
    )

    if isinstance(detail_id_or_slug, UUID):
        stmt = stmt.where(ImperialArtDetail.id == detail_id_or_slug)
    else:
        try:
            val_uuid = UUID(str(detail_id_or_slug))
            stmt = stmt.where(ImperialArtDetail.id == val_uuid)
        except ValueError:
            stmt = stmt.where(ImperialArtDetail.slug == str(detail_id_or_slug))

    detail = db.scalar(stmt)
    if not detail:
        raise AppError(
            "IMPERIAL_ART_DETAIL_NOT_FOUND",
            f"Art detail '{detail_id_or_slug}' not found",
            404,
        )
    if not include_drafts and detail.review_status != "published":
        raise AppError(
            "IMPERIAL_ART_DETAIL_NOT_FOUND",
            f"Art detail '{detail_id_or_slug}' not published",
            404,
        )
    return detail


def get_site_art_details(
    db: Session, site_slug: str, include_drafts: bool = False
) -> list[ImperialArtDetail]:
    """Retrieve all art details belonging to a site."""
    site = _resolve_site(db, site_slug)
    stmt = (
        select(ImperialArtDetail)
        .where(
            ImperialArtDetail.site_id == site.id,
            ImperialArtDetail.content_scope == CONTENT_SCOPE_IMPERIAL,
        )
        .order_by(ImperialArtDetail.created_at.asc())
    )
    if not include_drafts:
        stmt = stmt.where(ImperialArtDetail.review_status == "published")
    return list(db.scalars(stmt).all())


# --------------------------------------------------------------------------- #
# 3. Heritage Detective Clues & Attempts
# --------------------------------------------------------------------------- #
def get_clues(
    db: Session, target_type: Optional[str] = None, include_drafts: bool = False
) -> list[ImperialClue]:
    """Retrieve heritage detective clues."""
    stmt = select(ImperialClue).where(ImperialClue.content_scope == CONTENT_SCOPE_IMPERIAL)
    if target_type:
        stmt = stmt.where(ImperialClue.target_type == target_type)
    if not include_drafts:
        stmt = stmt.where(ImperialClue.review_status == "published")
    stmt = stmt.order_by(ImperialClue.created_at.asc())
    return list(db.scalars(stmt).all())


def attempt_clue(
    db: Session,
    clue_id: UUID,
    selected_target_id: UUID,
    attempt_number: int = 1,
    user_id: Optional[UUID] = None,
) -> dict[str, Any]:
    """Evaluate clue guess, reveal progressive hints if incorrect, and log attempt."""
    clue = db.get(ImperialClue, clue_id)
    if not clue or clue.content_scope != CONTENT_SCOPE_IMPERIAL:
        raise AppError("IMPERIAL_CLUE_NOT_FOUND", f"Clue '{clue_id}' not found", 404)

    is_correct = clue.target_id == selected_target_id

    attempt = ImperialClueAttempt(
        content_scope=CONTENT_SCOPE_IMPERIAL,
        clue_id=clue.id,
        user_id=user_id,
        selected_target_id=selected_target_id,
        is_correct=is_correct,
        attempt_number=attempt_number,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    hint_steps = clue.hint_steps if isinstance(clue.hint_steps, list) else []
    # Progressively reveal hints: reveal up to attempt_number hints on wrong answer
    revealed_hints = hint_steps[:attempt_number] if not is_correct else hint_steps

    if is_correct:
        message = "Chính xác! Bạn đã tìm ra di tích / chi tiết kiến trúc phù hợp với manh mối."
    else:
        message = f"Chưa chính xác. Đã mở gợi ý cấp độ {min(attempt_number, len(hint_steps))}."

    return {
        "id": attempt.id,
        "clue_id": clue.id,
        "is_correct": is_correct,
        "attempt_number": attempt_number,
        "hint_steps": revealed_hints,
        "message": message,
    }


# --------------------------------------------------------------------------- #
# 4. Interactive Questions & Gamified Submissions
# --------------------------------------------------------------------------- #
def get_game_questions(
    db: Session,
    site_slug: Optional[str] = None,
    question_type: Optional[str] = None,
    include_drafts: bool = False,
) -> list[ImperialQuestion]:
    """Retrieve quiz/game questions (public responses must omit answer_key)."""
    stmt = select(ImperialQuestion).where(ImperialQuestion.content_scope == CONTENT_SCOPE_IMPERIAL)
    if site_slug:
        site = _resolve_site(db, site_slug)
        stmt = stmt.where(ImperialQuestion.site_id == site.id)
    if question_type:
        stmt = stmt.where(ImperialQuestion.question_type == question_type)
    if not include_drafts:
        stmt = stmt.where(ImperialQuestion.review_status == "published")
    stmt = stmt.order_by(ImperialQuestion.created_at.asc())
    return list(db.scalars(stmt).all())


def submit_game_answer(
    db: Session,
    question_id: UUID,
    user_answer: str,
) -> dict[str, Any]:
    """Evaluate submitted quiz answer and return correct key with explanation."""
    question = db.get(ImperialQuestion, question_id)
    if not question or question.content_scope != CONTENT_SCOPE_IMPERIAL:
        raise AppError("IMPERIAL_QUESTION_NOT_FOUND", f"Question '{question_id}' not found", 404)

    is_correct = user_answer.strip().lower() == question.answer_key.strip().lower()

    return {
        "question_id": question.id,
        "is_correct": is_correct,
        "user_answer": user_answer,
        "correct_answer": question.answer_key,
        "explanation_why": question.explanation_why,
        "source_citation": question.source_citation,
    }


# --------------------------------------------------------------------------- #
# 5. Teacher Assignment Releases
# --------------------------------------------------------------------------- #
def create_assignment_release(
    db: Session, teacher_id: UUID, payload: ImperialAssignmentReleaseCreate
) -> ImperialAssignmentRelease:
    """Create teacher assignment release for a classroom journey."""
    release = ImperialAssignmentRelease(
        content_scope=CONTENT_SCOPE_IMPERIAL,
        teacher_id=teacher_id,
        class_name=payload.class_name,
        journey_slug=payload.journey_slug,
        title=payload.title,
        due_date=payload.due_date,
        rubric_weights=payload.rubric_weights or {},
        is_active=payload.is_active,
        row_version=1,
    )
    db.add(release)
    db.commit()
    db.refresh(release)
    return release


def get_assignment_releases(
    db: Session,
    teacher_id: Optional[UUID] = None,
    class_name: Optional[str] = None,
) -> list[ImperialAssignmentRelease]:
    """Retrieve teacher assignment releases."""
    stmt = select(ImperialAssignmentRelease).where(
        ImperialAssignmentRelease.content_scope == CONTENT_SCOPE_IMPERIAL
    )
    if teacher_id:
        stmt = stmt.where(ImperialAssignmentRelease.teacher_id == teacher_id)
    if class_name:
        stmt = stmt.where(ImperialAssignmentRelease.class_name == class_name)
    stmt = stmt.order_by(ImperialAssignmentRelease.created_at.desc())
    return list(db.scalars(stmt).all())


def update_assignment_release(
    db: Session,
    assignment_id: UUID,
    payload: ImperialAssignmentReleaseUpdate,
    teacher_id: Optional[UUID] = None,
) -> ImperialAssignmentRelease:
    """Update assignment release with optimistic locking."""
    release = db.get(ImperialAssignmentRelease, assignment_id)
    if not release or release.content_scope != CONTENT_SCOPE_IMPERIAL:
        raise AppError("IMPERIAL_ASSIGNMENT_NOT_FOUND", f"Assignment '{assignment_id}' not found", 404)

    if teacher_id and release.teacher_id != teacher_id:
        raise AppError("FORBIDDEN", "You can only update assignments created by yourself", 403)

    if payload.row_version is not None and payload.row_version != release.row_version:
        raise AppError(
            "IMPERIAL_CONCURRENCY_CONFLICT",
            "Assignment was modified by another request. Please reload.",
            409,
            {"current_row_version": release.row_version, "submitted_row_version": payload.row_version},
        )

    for field, val in payload.model_dump(exclude_unset=True, exclude={"row_version"}).items():
        if val is not None:
            setattr(release, field, val)

    release.row_version += 1
    db.commit()
    db.refresh(release)
    return release


# --------------------------------------------------------------------------- #
# 6. Admin CRUD Helpers for V5.1 Entities
# --------------------------------------------------------------------------- #
def create_learning_media(
    db: Session, payload: ImperialLearningMediaCreate
) -> ImperialLearningMedia:
    """Create learning media entry."""
    site = db.get(ImperialSite, payload.site_id)
    if not site or site.content_scope != CONTENT_SCOPE_IMPERIAL:
        raise AppError("IMPERIAL_SITE_NOT_FOUND", f"Site '{payload.site_id}' not found", 404)

    media = ImperialLearningMedia(
        content_scope=CONTENT_SCOPE_IMPERIAL,
        site_id=payload.site_id,
        kind=payload.kind,
        media_url=payload.media_url,
        thumbnail_url=payload.thumbnail_url,
        asset_revision=payload.asset_revision,
        width_px=payload.width_px,
        height_px=payload.height_px,
        license_status=payload.license_status,
        review_status=payload.review_status,
        alt_text=payload.alt_text,
        credit_text=payload.credit_text,
        asset_context=payload.asset_context,
        row_version=1,
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


def update_learning_media(
    db: Session, media_id: UUID, payload: ImperialLearningMediaUpdate
) -> ImperialLearningMedia:
    """Update learning media with optimistic locking."""
    media = db.get(ImperialLearningMedia, media_id)
    if not media or media.content_scope != CONTENT_SCOPE_IMPERIAL:
        raise AppError("IMPERIAL_MEDIA_NOT_FOUND", f"Media '{media_id}' not found", 404)

    if payload.row_version is not None and payload.row_version != media.row_version:
        raise AppError(
            "IMPERIAL_CONCURRENCY_CONFLICT",
            "Media was modified by another editor. Please reload.",
            409,
            {"current_row_version": media.row_version, "submitted_row_version": payload.row_version},
        )

    for field, val in payload.model_dump(exclude_unset=True, exclude={"row_version"}).items():
        if val is not None:
            setattr(media, field, val)

    media.row_version += 1
    db.commit()
    db.refresh(media)
    return media


def delete_learning_media(db: Session, media_id: UUID) -> None:
    """Delete learning media asset."""
    media = db.get(ImperialLearningMedia, media_id)
    if not media or media.content_scope != CONTENT_SCOPE_IMPERIAL:
        raise AppError("IMPERIAL_MEDIA_NOT_FOUND", f"Media '{media_id}' not found", 404)
    db.delete(media)
    db.commit()


def create_media_hotspot(
    db: Session, media_id: UUID, payload: ImperialMediaHotspotCreate
) -> ImperialMediaHotspot:
    """Create normalized UV hotspot marker on media."""
    media = db.get(ImperialLearningMedia, media_id)
    if not media or media.content_scope != CONTENT_SCOPE_IMPERIAL:
        raise AppError("IMPERIAL_MEDIA_NOT_FOUND", f"Media '{media_id}' not found", 404)

    if not (0.0 <= payload.u <= 1.0 and 0.0 <= payload.v <= 1.0):
        raise AppError("IMPERIAL_UV_OUT_OF_BOUNDS", "UV coordinates must be between 0.0 and 1.0", 422)

    hotspot = ImperialMediaHotspot(
        content_scope=CONTENT_SCOPE_IMPERIAL,
        media_id=media_id,
        point_kind=payload.point_kind,
        u=payload.u,
        v=payload.v,
        position_payload=payload.position_payload,
        title=payload.title,
        description=payload.description,
        detail_id=payload.detail_id,
        review_status=payload.review_status,
        row_version=1,
    )
    db.add(hotspot)
    db.commit()
    db.refresh(hotspot)
    return hotspot


def update_media_hotspot(
    db: Session, hotspot_id: UUID, payload: ImperialMediaHotspotUpdate
) -> ImperialMediaHotspot:
    """Update media hotspot with UV validation and optimistic locking."""
    hotspot = db.get(ImperialMediaHotspot, hotspot_id)
    if not hotspot or hotspot.content_scope != CONTENT_SCOPE_IMPERIAL:
        raise AppError("IMPERIAL_HOTSPOT_NOT_FOUND", f"Hotspot '{hotspot_id}' not found", 404)

    if payload.row_version is not None and payload.row_version != hotspot.row_version:
        raise AppError(
            "IMPERIAL_CONCURRENCY_CONFLICT",
            "Hotspot was modified by another editor. Please reload.",
            409,
            {"current_row_version": hotspot.row_version, "submitted_row_version": payload.row_version},
        )

    new_u = payload.u if payload.u is not None else float(hotspot.u)
    new_v = payload.v if payload.v is not None else float(hotspot.v)
    if not (0.0 <= new_u <= 1.0 and 0.0 <= new_v <= 1.0):
        raise AppError("IMPERIAL_UV_OUT_OF_BOUNDS", "UV coordinates must be between 0.0 and 1.0", 422)

    for field, val in payload.model_dump(exclude_unset=True, exclude={"row_version"}).items():
        if val is not None:
            setattr(hotspot, field, val)

    hotspot.row_version += 1
    db.commit()
    db.refresh(hotspot)
    return hotspot


def delete_media_hotspot(db: Session, hotspot_id: UUID) -> None:
    """Delete media hotspot."""
    hotspot = db.get(ImperialMediaHotspot, hotspot_id)
    if not hotspot or hotspot.content_scope != CONTENT_SCOPE_IMPERIAL:
        raise AppError("IMPERIAL_HOTSPOT_NOT_FOUND", f"Hotspot '{hotspot_id}' not found", 404)
    db.delete(hotspot)
    db.commit()


def create_art_detail(
    db: Session, payload: ImperialArtDetailCreate
) -> ImperialArtDetail:
    """Create art detail with claims and questions."""
    site = db.get(ImperialSite, payload.site_id)
    if not site or site.content_scope != CONTENT_SCOPE_IMPERIAL:
        raise AppError("IMPERIAL_SITE_NOT_FOUND", f"Site '{payload.site_id}' not found", 404)

    existing = db.scalar(
        select(ImperialArtDetail).where(
            ImperialArtDetail.slug == payload.slug,
            ImperialArtDetail.content_scope == CONTENT_SCOPE_IMPERIAL,
        )
    )
    if existing:
        raise AppError("IMPERIAL_SLUG_EXISTS", f"Art detail with slug '{payload.slug}' already exists", 409)

    detail = ImperialArtDetail(
        content_scope=CONTENT_SCOPE_IMPERIAL,
        site_id=payload.site_id,
        title=payload.title,
        slug=payload.slug,
        kind=payload.kind,
        motif=payload.motif,
        material=payload.material,
        technique=payload.technique,
        description_observation=payload.description_observation,
        story_body=payload.story_body,
        story_type=payload.story_type,
        meaning_body=payload.meaning_body,
        historical_value_body=payload.historical_value_body,
        cultural_value_body=payload.cultural_value_body,
        art_value_body=payload.art_value_body,
        review_status=payload.review_status,
        content_revision=payload.content_revision,
        row_version=1,
    )
    db.add(detail)
    db.flush()

    for cs in payload.claim_sources:
        claim = ImperialArtDetailClaimSource(
            content_scope=CONTENT_SCOPE_IMPERIAL,
            detail_id=detail.id,
            section=cs.section,
            claim_text=cs.claim_text,
            source_title=cs.source_title,
            source_locator=cs.source_locator,
            evidence_strength=cs.evidence_strength,
        )
        db.add(claim)

    for q in payload.questions:
        q_item = ImperialArtDetailQuestion(
            content_scope=CONTENT_SCOPE_IMPERIAL,
            detail_id=detail.id,
            question_type=q.question_type,
            prompt=q.prompt,
            options=q.options,
            answer_key=q.answer_key,
            explanation=q.explanation,
            display_order=q.display_order,
        )
        db.add(q_item)

    db.commit()
    db.refresh(detail)
    return detail


def update_art_detail(
    db: Session, detail_id: UUID, payload: ImperialArtDetailUpdate
) -> ImperialArtDetail:
    """Update art detail with optimistic locking."""
    detail = db.get(ImperialArtDetail, detail_id)
    if not detail or detail.content_scope != CONTENT_SCOPE_IMPERIAL:
        raise AppError("IMPERIAL_ART_DETAIL_NOT_FOUND", f"Art detail '{detail_id}' not found", 404)

    if payload.row_version is not None and payload.row_version != detail.row_version:
        raise AppError(
            "IMPERIAL_CONCURRENCY_CONFLICT",
            "Art detail was modified by another editor. Please reload.",
            409,
            {"current_row_version": detail.row_version, "submitted_row_version": payload.row_version},
        )

    for field, val in payload.model_dump(exclude_unset=True, exclude={"row_version"}).items():
        if val is not None:
            setattr(detail, field, val)

    detail.row_version += 1
    db.commit()
    db.refresh(detail)
    return detail


def delete_art_detail(db: Session, detail_id: UUID) -> None:
    """Delete art detail."""
    detail = db.get(ImperialArtDetail, detail_id)
    if not detail or detail.content_scope != CONTENT_SCOPE_IMPERIAL:
        raise AppError("IMPERIAL_ART_DETAIL_NOT_FOUND", f"Art detail '{detail_id}' not found", 404)
    db.delete(detail)
    db.commit()


def create_clue(db: Session, payload: ImperialClueCreate) -> ImperialClue:
    """Create detective clue."""
    clue = ImperialClue(
        content_scope=CONTENT_SCOPE_IMPERIAL,
        title=payload.title,
        clue_text=payload.clue_text,
        target_type=payload.target_type,
        target_id=payload.target_id,
        hint_steps=payload.hint_steps,
        grade_level=payload.grade_level,
        difficulty=payload.difficulty,
        review_status=payload.review_status,
        row_version=1,
    )
    db.add(clue)
    db.commit()
    db.refresh(clue)
    return clue


def update_clue(db: Session, clue_id: UUID, payload: ImperialClueUpdate) -> ImperialClue:
    """Update clue with optimistic locking."""
    clue = db.get(ImperialClue, clue_id)
    if not clue or clue.content_scope != CONTENT_SCOPE_IMPERIAL:
        raise AppError("IMPERIAL_CLUE_NOT_FOUND", f"Clue '{clue_id}' not found", 404)

    if payload.row_version is not None and payload.row_version != clue.row_version:
        raise AppError(
            "IMPERIAL_CONCURRENCY_CONFLICT",
            "Clue was modified by another editor. Please reload.",
            409,
            {"current_row_version": clue.row_version, "submitted_row_version": payload.row_version},
        )

    for field, val in payload.model_dump(exclude_unset=True, exclude={"row_version"}).items():
        if val is not None:
            setattr(clue, field, val)

    clue.row_version += 1
    db.commit()
    db.refresh(clue)
    return clue


def delete_clue(db: Session, clue_id: UUID) -> None:
    """Delete clue."""
    clue = db.get(ImperialClue, clue_id)
    if not clue or clue.content_scope != CONTENT_SCOPE_IMPERIAL:
        raise AppError("IMPERIAL_CLUE_NOT_FOUND", f"Clue '{clue_id}' not found", 404)
    db.delete(clue)
    db.commit()


def create_question(db: Session, payload: ImperialQuestionCreate) -> ImperialQuestion:
    """Create gamified inquiry question."""
    question = ImperialQuestion(
        content_scope=CONTENT_SCOPE_IMPERIAL,
        site_id=payload.site_id,
        detail_id=payload.detail_id,
        question_type=payload.question_type,
        prompt=payload.prompt,
        options=payload.options,
        answer_key=payload.answer_key,
        explanation_why=payload.explanation_why,
        source_citation=payload.source_citation,
        review_status=payload.review_status,
        row_version=1,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def update_question(
    db: Session, question_id: UUID, payload: ImperialQuestionUpdate
) -> ImperialQuestion:
    """Update gamified question with optimistic locking."""
    question = db.get(ImperialQuestion, question_id)
    if not question or question.content_scope != CONTENT_SCOPE_IMPERIAL:
        raise AppError("IMPERIAL_QUESTION_NOT_FOUND", f"Question '{question_id}' not found", 404)

    if payload.row_version is not None and payload.row_version != question.row_version:
        raise AppError(
            "IMPERIAL_CONCURRENCY_CONFLICT",
            "Question was modified by another editor. Please reload.",
            409,
            {"current_row_version": question.row_version, "submitted_row_version": payload.row_version},
        )

    for field, val in payload.model_dump(exclude_unset=True, exclude={"row_version"}).items():
        if val is not None:
            setattr(question, field, val)

    question.row_version += 1
    db.commit()
    db.refresh(question)
    return question


def delete_question(db: Session, question_id: UUID) -> None:
    """Delete gamified question."""
    question = db.get(ImperialQuestion, question_id)
    if not question or question.content_scope != CONTENT_SCOPE_IMPERIAL:
        raise AppError("IMPERIAL_QUESTION_NOT_FOUND", f"Question '{question_id}' not found", 404)
    db.delete(question)
    db.commit()
