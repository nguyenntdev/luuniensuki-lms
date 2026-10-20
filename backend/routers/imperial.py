# -*- coding: utf-8 -*-
"""FastAPI router for STTTNNĐ (Lưu Niên — Đại Nội Huế).

Contains:
- Public endpoints for spatial zones, architectural site dossiers, timeline,
  evidence claims, and published aerial map annotations.
- Admin endpoints protected by RBAC (staff/admin) for aerial map versioning,
  marker curation with optimistic concurrency control, atomic map publication,
  audit history, and JSON export/import verification.
"""
from __future__ import annotations

import io
from typing import Any, Optional, Union
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from ..apischemas.imperial import (
    ImperialActivityOut,
    ImperialAIAskRequest,
    ImperialAIAskResponse,
    ImperialAnnotationAuditOut,
    ImperialAnnotationBase,
    ImperialAnnotationCreate,
    ImperialAnnotationOut,
    ImperialAnnotationUpdate,
    ImperialLearningPathDetail,
    ImperialMapAssetDetail,
    ImperialMapAssetSummary,
    ImperialMapAssetUpload,
    ImperialSiteDetail,
    ImperialSiteEvidence,
    ImperialSiteSummary,
    ImperialSiteTimeline,
    ImperialSubmissionCreate,
    ImperialSubmissionGrade,
    ImperialSubmissionOut,
    ImperialZoneSummary,
)
from ..db import get_db
from ..deps import (
    get_admin_user,
    get_current_user,
    get_current_user_optional,
    get_staff_user,
)
from ..errors import AppError
from ..models import User, UserRole
from ..services import (
    imperial_ai,
    imperial_audio,
    imperial_learning,
    imperial_map,
    imperial_site,
    imperial_sync,
    imperial_v51,
)
from ..apischemas.imperial_audio import (
    ImperialAudioCatalogOut,
    ImperialAudioGuideOut,
)
from ..apischemas.imperial_sync import (
    ImperialBatchSyncRequest,
    ImperialBatchSyncResponse,
)
from ..apischemas.imperial_v51 import (
    ImperialArtDetailCreate,
    ImperialArtDetailDetail,
    ImperialArtDetailSummary,
    ImperialArtDetailUpdate,
    ImperialAssignmentReleaseCreate,
    ImperialAssignmentReleaseOut,
    ImperialAssignmentReleaseUpdate,
    ImperialClueAttemptRequest,
    ImperialClueAttemptResponse,
    ImperialClueCreate,
    ImperialClueOut,
    ImperialClueUpdate,
    ImperialGameSubmitRequest,
    ImperialGameSubmitResponse,
    ImperialLearningMediaCreate,
    ImperialLearningMediaOut,
    ImperialLearningMediaUpdate,
    ImperialMediaHotspotCreate,
    ImperialMediaHotspotOut,
    ImperialMediaHotspotUpdate,
    ImperialQuestionAdminOut,
    ImperialQuestionCreate,
    ImperialQuestionOut,
    ImperialQuestionUpdate,
)

router = APIRouter(prefix="/api/v1/imperial", tags=["imperial"])

# Minimal transparent 1x1 WEBP image bytes for placeholder
_PLACEHOLDER_WEBP = (
    b"RIFF\x1a\x00\x00\x00WEBPVP8L\x0e\x00\x00\x00/\x00\x00\x00\x00\x07\x88\x85%*'\x00\x00"
)


def get_learner_user(current_user: User = Depends(get_current_user)) -> User:
    """Ensure the user has learner role or higher (not guest)."""
    if current_user.role == UserRole.guest:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Learner role or higher required for submitting activities",
        )
    return current_user


class ImperialAnnotationCreateRequest(ImperialAnnotationBase):
    site_id: UUID
    map_asset_id: Optional[UUID] = None


# =========================================================================== #
# Public Endpoints
# =========================================================================== #
@router.get("/zones", response_model=list[ImperialZoneSummary])
def get_zones(db: Session = Depends(get_db)):
    """List 4 spatial zones with site counts."""
    return imperial_site.get_zones(db)


@router.get("/maps/active")
def get_active_map(db: Session = Depends(get_db)):
    """Retrieve the current active published aerial map asset with all published annotations."""
    return imperial_map.get_active_map(db)


@router.get("/maps/{map_id}/annotations", response_model=list[ImperialAnnotationOut])
def get_map_annotations(
    map_id: UUID,
    zone: Optional[str] = Query(default=None, description="Filter by zone slug or UUID"),
    lens: Optional[UUID] = Query(default=None, description="Filter by lens UUID"),
    db: Session = Depends(get_db),
):
    """List published annotations for a published map asset."""
    return imperial_map.get_map_annotations(
        db, map_id=map_id, zone_id=zone, lens_id=lens, include_drafts=False
    )


@router.get("/sites", response_model=list[ImperialSiteSummary])
def get_sites(
    zone: Optional[str] = Query(default=None, description="Filter by zone slug or UUID"),
    condition: Optional[str] = Query(default=None, description="Filter by condition (extant, ruined, lost, reconstructed)"),
    search: Optional[str] = Query(default=None, description="Full-text search by monument name or slug"),
    db: Session = Depends(get_db),
):
    """List architectural sites in Đại Nội Huế with pedagogical filters."""
    return imperial_site.get_sites(
        db, zone_id=zone, condition=condition, search=search, is_published=True
    )


@router.get("/sites/{slug}", response_model=ImperialSiteDetail)
def get_site_by_slug(slug: str, db: Session = Depends(get_db)):
    """Retrieve detailed site dossier with condition, learning level, and architecture."""
    site = imperial_site.get_site_by_slug(db, slug)
    if not site:
        raise AppError("IMPERIAL_SITE_NOT_FOUND", f"Imperial site '{slug}' not found", 404)
    return site


@router.get("/sites/{slug}/evidence", response_model=ImperialSiteEvidence)
def get_site_evidence(slug: str, db: Session = Depends(get_db)):
    """Retrieve historical claims and primary source references for a site."""
    return imperial_site.get_site_evidence(db, slug)


@router.get("/sites/{slug}/timeline", response_model=ImperialSiteTimeline)
def get_site_timeline(slug: str, db: Session = Depends(get_db)):
    """Retrieve chronological events (construction, alterations, conservation) for a site."""
    return imperial_site.get_site_timeline(db, slug)


@router.get("/audio-guides", response_model=ImperialAudioCatalogOut)
def list_all_audio_guides():
    """Retrieve all available audio guide tracks for Đại Nội monuments with aggregate duration."""
    return imperial_audio.list_all_audio_guides()


@router.get("/sites/{slug}/audio", response_model=ImperialAudioGuideOut)
def get_audio_guide_by_slug(slug: str):
    """Retrieve audio guide track narration, duration, and timed transcript for a specific monument."""
    guide = imperial_audio.get_audio_guide_by_slug(slug)
    if not guide:
        raise AppError("AUDIO_GUIDE_NOT_FOUND", f"Audio guide for monument '{slug}' not found", 404)
    return guide


@router.get("/assets/{asset_id}/image")
def get_map_asset_image(asset_id: UUID, db: Session = Depends(get_db)):
    """Serve map asset image with caching headers."""
    from ..imperial_models import ImperialMapAsset

    map_asset = db.get(ImperialMapAsset, asset_id)
    if not map_asset:
        raise AppError("IMPERIAL_MAP_NOT_FOUND", f"Map asset '{asset_id}' not found", 404)

    headers = {
        "Cache-Control": "public, max-age=86400, immutable",
        "ETag": f'"{map_asset.image_sha256}"',
        "Content-Type": map_asset.mime_type or "image/webp",
    }
    return Response(content=_PLACEHOLDER_WEBP, status_code=200, headers=headers)


# =========================================================================== #
# Admin Endpoints (RBAC Protected)
# =========================================================================== #
@router.get("/admin/maps", response_model=list[ImperialMapAssetSummary])
def list_maps(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
):
    """List all aerial map asset versions for admin curation."""
    return imperial_map.list_maps(db)


@router.post("/admin/maps", response_model=ImperialMapAssetDetail, status_code=status.HTTP_201_CREATED)
def create_map(
    payload: ImperialMapAssetUpload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
):
    """Create metadata for an aerial map asset."""
    return imperial_map.create_map_asset(db, payload, actor_id=current_user.id)


@router.get("/admin/maps/{map_id}/annotations", response_model=list[ImperialAnnotationOut])
def get_admin_map_annotations(
    map_id: UUID,
    zone: Optional[str] = Query(default=None),
    lens: Optional[UUID] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
):
    """List annotations including drafts for curatorial editor."""
    return imperial_map.get_map_annotations(
        db, map_id=map_id, zone_id=zone, lens_id=lens, include_drafts=True
    )


@router.post("/admin/maps/{map_id}/annotations", response_model=ImperialAnnotationOut, status_code=status.HTTP_201_CREATED)
def create_annotation(
    map_id: UUID,
    payload: ImperialAnnotationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
):
    """Create a draft annotation marker with UV bounds validation and audit entry."""
    create_dto = ImperialAnnotationCreate(
        map_asset_id=map_id,
        site_id=payload.site_id,
        shape_type=payload.shape_type,
        u=payload.u,
        v=payload.v,
        polygon_uv=payload.polygon_uv,
        label=payload.label,
        marker_style=payload.marker_style,
        z_index=payload.z_index,
        is_visible=payload.is_visible,
        position_confidence=payload.position_confidence,
        position_source_ref=payload.position_source_ref,
        editorial_notes=payload.editorial_notes,
    )
    return imperial_map.create_annotation(db, map_id=map_id, payload=create_dto, actor_id=current_user.id)


@router.patch("/admin/annotations/{id}", response_model=ImperialAnnotationOut)
def update_annotation(
    id: UUID,
    payload: ImperialAnnotationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
):
    """Update annotation coordinates or metadata with optimistic locking check."""
    return imperial_map.update_annotation(db, annotation_id=id, payload=payload, actor_id=current_user.id)


@router.delete("/admin/annotations/{id}")
def delete_annotation(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
):
    """Soft-delete / archive annotation with audit log."""
    imperial_map.delete_annotation(db, annotation_id=id, actor_id=current_user.id)
    return {"ok": True, "message": "Annotation archived"}


@router.post("/admin/maps/{map_id}/publish", response_model=ImperialMapAssetDetail)
def publish_map(
    map_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Atomically publish approved aerial map and its annotations."""
    return imperial_map.publish_map(db, map_id=map_id, actor_id=current_user.id)


@router.get("/admin/maps/{map_id}/export")
def export_annotations(
    map_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
):
    """Export canonical annotations dataset with schema_version and SHA-256 hash."""
    return imperial_map.export_annotations(db, map_id=map_id)


@router.post("/admin/maps/{map_id}/import")
def import_annotations(
    map_id: UUID,
    payload: dict[str, Any],
    dry_run: bool = Query(default=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
):
    """Import annotations dataset with schema validation, site check, UV bounds, and atomic commit."""
    return imperial_map.import_annotations(
        db, map_id=map_id, payload=payload, actor_id=current_user.id, dry_run=dry_run
    )


@router.get("/admin/annotations/{id}/audit", response_model=list[ImperialAnnotationAuditOut])
def get_annotation_audit(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
):
    """Get full append-only audit trail for an annotation."""
    return imperial_map.get_annotation_audit(db, annotation_id=id)


# =========================================================================== #
# Learning Paths & Pedagogical Activities
# =========================================================================== #
@router.get("/paths", response_model=list[ImperialLearningPathDetail])
def get_learning_paths(db: Session = Depends(get_db)):
    """List curated trails with steps and associated monument sites."""
    return imperial_learning.get_learning_paths(db)


@router.get("/learning-paths", response_model=list[ImperialLearningPathDetail], include_in_schema=False)
def get_learning_paths_alias(db: Session = Depends(get_db)):
    """Alias for /paths: List curated trails with steps and associated monument sites."""
    return imperial_learning.get_learning_paths(db)


@router.get("/paths/{slug}", response_model=ImperialLearningPathDetail)
def get_learning_path_by_slug(slug: str, db: Session = Depends(get_db)):
    """Retrieve detailed learning path trail with step sequence and site metadata."""
    return imperial_learning.get_learning_path_by_slug(db, slug)


@router.get("/learning-paths/{slug}", response_model=ImperialLearningPathDetail, include_in_schema=False)
def get_learning_path_by_slug_alias(slug: str, db: Session = Depends(get_db)):
    """Alias for /paths/{slug}: Retrieve detailed learning path trail with step sequence and site metadata."""
    return imperial_learning.get_learning_path_by_slug(db, slug)


@router.get("/sites/{slug}/activities", response_model=list[ImperialActivityOut])
def get_site_activities(slug: str, db: Session = Depends(get_db)):
    """List pedagogical inquiry activities and reflection tasks for an architectural site."""
    return imperial_learning.get_site_activities(db, slug)


@router.post(
    "/activities/{activity_id}/submissions",
    response_model=ImperialSubmissionOut,
    status_code=status.HTTP_201_CREATED,
)
def submit_activity(
    activity_id: UUID,
    payload: ImperialSubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_learner_user),
):
    """Save student answer, evidence references, and timestamp for an inquiry task (requires learner role)."""
    return imperial_learning.submit_activity(
        db, activity_id=activity_id, student_id=current_user.id, payload=payload
    )


@router.post(
    "/submissions/batch-sync",
    response_model=ImperialBatchSyncResponse,
    status_code=status.HTTP_200_OK,
)
def batch_sync_submissions(
    payload: ImperialBatchSyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_learner_user),
):
    """Batch synchronize offline queued student activity submissions (requires learner role or higher)."""
    return imperial_sync.sync_offline_submissions(
        db=db,
        student_id=current_user.id,
        items=payload.items,
    )


@router.get("/teacher/submissions", response_model=list[ImperialSubmissionOut])
def get_submissions_for_teacher(
    activity_id: Optional[UUID] = Query(default=None, description="Filter by activity UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
):
    """List student submissions for teacher evaluation with optional activity filtering (requires staff/teacher role)."""
    return imperial_learning.get_submissions_for_teacher(
        db, teacher_id=current_user.id, activity_id=activity_id
    )


@router.post("/teacher/submissions/{submission_id}/grade", response_model=ImperialSubmissionOut)
def grade_submission(
    submission_id: UUID,
    payload: ImperialSubmissionGrade,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
):
    """Record rubric scores S1-S4 (0-3 scale each), total score, and teacher feedback (requires staff/teacher role)."""
    return imperial_learning.grade_submission(
        db, submission_id=submission_id, teacher_id=current_user.id, payload=payload
    )


# =========================================================================== #
# Scope-Locked AI Tutor
# =========================================================================== #
@router.post("/ai/ask", response_model=ImperialAIAskResponse)
def ask_imperial_tutor(
    payload: ImperialAIAskRequest,
    db: Session = Depends(get_db),
):
    """Query scope-locked AI tutor for Đại Nội Huế with 3-part evidence-grounded response."""
    return imperial_ai.ask_imperial_tutor(
        db, query=payload.query, site_slug=payload.site_slug, context=payload.context
    )


@router.post("/ai/chat", response_model=ImperialAIAskResponse, include_in_schema=False)
def chat_imperial_tutor(
    payload: ImperialAIAskRequest,
    db: Session = Depends(get_db),
):
    """Query scope-locked AI tutor for Đại Nội Huế (alias for /ai/ask)."""
    return imperial_ai.ask_imperial_tutor(
        db, query=payload.query, site_slug=payload.site_slug, context=payload.context
    )


# =========================================================================== #
# V5.1 Modules: Learning Media, Art Details, Clues, Quizzes, Teacher Releases
# =========================================================================== #
@router.get("/sites/{slug}/learning-media", response_model=list[ImperialLearningMediaOut])
def get_site_learning_media(slug: str, db: Session = Depends(get_db)):
    """Retrieve learning media assets (photos, 360s, 3D models) with published hotspots."""
    return imperial_v51.get_site_learning_media(db, site_slug=slug, include_drafts=False)


@router.get("/media/{media_id}/hotspots", response_model=list[ImperialMediaHotspotOut])
def get_media_hotspots(media_id: UUID, db: Session = Depends(get_db)):
    """Retrieve published interactive hotspots placed on a learning media asset."""
    return imperial_v51.get_media_hotspots(db, media_id=media_id, include_drafts=False)


@router.get("/sites/{slug}/art-details", response_model=list[ImperialArtDetailSummary])
def get_site_art_details(slug: str, db: Session = Depends(get_db)):
    """Retrieve list of art details (carvings, patterns, reliefs) belonging to a site."""
    return imperial_v51.get_site_art_details(db, site_slug=slug, include_drafts=False)


@router.get("/art-details/{detail_id_or_slug}", response_model=ImperialArtDetailDetail)
def get_art_detail(detail_id_or_slug: str, db: Session = Depends(get_db)):
    """Retrieve detailed art detail dossier with story, values, primary claim sources, and inquiry questions."""
    return imperial_v51.get_art_detail(db, detail_id_or_slug=detail_id_or_slug, include_drafts=False)


@router.get("/clues", response_model=list[ImperialClueOut])
def get_clues(
    target_type: Optional[str] = Query(default=None, description="Filter by target type: site or art_detail"),
    db: Session = Depends(get_db),
):
    """List published heritage detective clues and riddles."""
    return imperial_v51.get_clues(db, target_type=target_type, include_drafts=False)


@router.post("/clues/{clue_id}/attempt", response_model=ImperialClueAttemptResponse)
def attempt_clue(
    clue_id: UUID,
    payload: ImperialClueAttemptRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Submit a guess for a heritage detective clue and receive progressive hints."""
    user_id = current_user.id if current_user else None
    return imperial_v51.attempt_clue(
        db,
        clue_id=clue_id,
        selected_target_id=payload.selected_target_id,
        attempt_number=payload.attempt_number,
        user_id=user_id,
    )


@router.get("/games/questions", response_model=list[ImperialQuestionOut])
def get_game_questions(
    site: Optional[str] = Query(default=None, description="Filter by site slug"),
    question_type: Optional[str] = Query(default=None, description="Filter by question type"),
    db: Session = Depends(get_db),
):
    """List published gamified questions (answer_key is hidden)."""
    return imperial_v51.get_game_questions(
        db, site_slug=site, question_type=question_type, include_drafts=False
    )


@router.post("/games/submit", response_model=ImperialGameSubmitResponse)
def submit_game_answer(
    payload: ImperialGameSubmitRequest,
    db: Session = Depends(get_db),
):
    """Submit an answer to an interactive quiz question and receive the explanation and citation."""
    return imperial_v51.submit_game_answer(
        db, question_id=payload.question_id, user_answer=payload.user_answer
    )


@router.get("/teacher/assignments", response_model=list[ImperialAssignmentReleaseOut])
def get_teacher_assignments(
    class_name: Optional[str] = Query(default=None, description="Filter by class name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
):
    """Retrieve teacher's assigned classroom journeys."""
    return imperial_v51.get_assignment_releases(
        db, teacher_id=current_user.id, class_name=class_name
    )


@router.post(
    "/teacher/assignments",
    response_model=ImperialAssignmentReleaseOut,
    status_code=status.HTTP_201_CREATED,
)
def create_teacher_assignment(
    payload: ImperialAssignmentReleaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
):
    """Create a new classroom assignment release for a journey."""
    return imperial_v51.create_assignment_release(
        db, teacher_id=current_user.id, payload=payload
    )


@router.patch("/teacher/assignments/{assignment_id}", response_model=ImperialAssignmentReleaseOut)
def update_teacher_assignment(
    assignment_id: UUID,
    payload: ImperialAssignmentReleaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
):
    """Update teacher assignment release with optimistic locking."""
    return imperial_v51.update_assignment_release(
        db, assignment_id=assignment_id, payload=payload, teacher_id=current_user.id
    )


# =========================================================================== #
# V5.1 Admin Endpoints for Learning Media, Hotspots, Art Details, Clues, Questions
# =========================================================================== #
@router.post(
    "/admin/media",
    response_model=ImperialLearningMediaOut,
    status_code=status.HTTP_201_CREATED,
)
def admin_create_media(
    payload: ImperialLearningMediaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
):
    """Admin create learning media asset."""
    return imperial_v51.create_learning_media(db, payload)


@router.patch("/admin/media/{media_id}", response_model=ImperialLearningMediaOut)
def admin_update_media(
    media_id: UUID,
    payload: ImperialLearningMediaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
):
    """Admin update learning media asset with optimistic locking."""
    return imperial_v51.update_learning_media(db, media_id=media_id, payload=payload)


@router.delete("/admin/media/{media_id}")
def admin_delete_media(
    media_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
):
    """Admin delete learning media asset."""
    imperial_v51.delete_learning_media(db, media_id=media_id)
    return {"ok": True, "message": "Media deleted"}


@router.post(
    "/admin/media/{media_id}/hotspots",
    response_model=ImperialMediaHotspotOut,
    status_code=status.HTTP_201_CREATED,
)
def admin_create_media_hotspot(
    media_id: UUID,
    payload: ImperialMediaHotspotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
):
    """Admin create media hotspot marker."""
    return imperial_v51.create_media_hotspot(db, media_id=media_id, payload=payload)


@router.patch("/admin/hotspots/{hotspot_id}", response_model=ImperialMediaHotspotOut)
def admin_update_media_hotspot(
    hotspot_id: UUID,
    payload: ImperialMediaHotspotUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
):
    """Admin update media hotspot marker with optimistic locking."""
    return imperial_v51.update_media_hotspot(db, hotspot_id=hotspot_id, payload=payload)


@router.delete("/admin/hotspots/{hotspot_id}")
def admin_delete_media_hotspot(
    hotspot_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
):
    """Admin delete media hotspot marker."""
    imperial_v51.delete_media_hotspot(db, hotspot_id=hotspot_id)
    return {"ok": True, "message": "Hotspot deleted"}


@router.post(
    "/admin/art-details",
    response_model=ImperialArtDetailDetail,
    status_code=status.HTTP_201_CREATED,
)
def admin_create_art_detail(
    payload: ImperialArtDetailCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
):
    """Admin create art detail entry."""
    return imperial_v51.create_art_detail(db, payload)


@router.patch("/admin/art-details/{detail_id}", response_model=ImperialArtDetailDetail)
def admin_update_art_detail(
    detail_id: UUID,
    payload: ImperialArtDetailUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
):
    """Admin update art detail entry with optimistic locking."""
    return imperial_v51.update_art_detail(db, detail_id=detail_id, payload=payload)


@router.delete("/admin/art-details/{detail_id}")
def admin_delete_art_detail(
    detail_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
):
    """Admin delete art detail entry."""
    imperial_v51.delete_art_detail(db, detail_id=detail_id)
    return {"ok": True, "message": "Art detail deleted"}


@router.post(
    "/admin/clues",
    response_model=ImperialClueOut,
    status_code=status.HTTP_201_CREATED,
)
def admin_create_clue(
    payload: ImperialClueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
):
    """Admin create heritage detective clue."""
    return imperial_v51.create_clue(db, payload)


@router.patch("/admin/clues/{clue_id}", response_model=ImperialClueOut)
def admin_update_clue(
    clue_id: UUID,
    payload: ImperialClueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
):
    """Admin update heritage detective clue with optimistic locking."""
    return imperial_v51.update_clue(db, clue_id=clue_id, payload=payload)


@router.delete("/admin/clues/{clue_id}")
def admin_delete_clue(
    clue_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
):
    """Admin delete heritage detective clue."""
    imperial_v51.delete_clue(db, clue_id=clue_id)
    return {"ok": True, "message": "Clue deleted"}


@router.post(
    "/admin/questions",
    response_model=ImperialQuestionAdminOut,
    status_code=status.HTTP_201_CREATED,
)
def admin_create_question(
    payload: ImperialQuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
):
    """Admin create gamified quiz question."""
    return imperial_v51.create_question(db, payload)


@router.patch("/admin/questions/{question_id}", response_model=ImperialQuestionAdminOut)
def admin_update_question(
    question_id: UUID,
    payload: ImperialQuestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
):
    """Admin update gamified quiz question with optimistic locking."""
    return imperial_v51.update_question(db, question_id=question_id, payload=payload)


@router.delete("/admin/questions/{question_id}")
def admin_delete_question(
    question_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_user),
):
    """Admin delete gamified quiz question."""
    imperial_v51.delete_question(db, question_id=question_id)
    return {"ok": True, "message": "Question deleted"}


