# -*- coding: utf-8 -*-
"""History-First governance services (Phase 1).

Business logic for the historical domain: entity/claim/source/relation CRUD,
the verification-state machine, the claim-source verification invariant, and
the append-only governance audit log.

Rules enforced here (docs/specs/HISTORY_FIRST_MASTER_SPEC.md Part III):

- Engineering completion never implies historical verification.
- A factual/chronology/geographic/identification claim MUST NOT reach
  ``expert_verified`` unless it has at least one eligible source binding
  (``supports`` / ``primary_evidence_for``) and has passed editor review.
- State transitions are audited to ``historical_content_audit_log``.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import re
import unicodedata
import uuid
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from ..domain.atomic_claims import (
    claim_has_contradicting_source,
    reject_compound_claim_with_disputed_facts,
    validate_atomic_claim,
)
from ..errors import AppError
from ..history_models import (
    HistoricalAsset,
    HistoricalClaim,
    HistoricalClaimSource,
    HistoricalClaimType,
    HistoricalContentAuditLog,
    HistoricalEntity,
    HistoricalEntityRelation,
    HistoricalGeography,
    HistoricalSource,
    HistoricalSupportType,
)
from ..models import (
    User,
    UserRole,
)
from ..rbac import STAFF_ROLES


# --------------------------------------------------------------------------- #
# Audit
# --------------------------------------------------------------------------- #
def audit_action(
    db: Session,
    *,
    actor_id: Optional[UUID],
    action: str,
    resource_type: str,
    resource_id: Optional[UUID] = None,
    before_json: Optional[dict[str, Any]] = None,
    after_json: Optional[dict[str, Any]] = None,
    reason: Optional[str] = None,
    request_id: Optional[str] = None,
) -> None:
    """Append an immutable governance audit entry."""
    db.add(
        HistoricalContentAuditLog(
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            before_json=before_json,
            after_json=after_json,
            reason=reason,
            request_id=request_id,
        )
    )


# --------------------------------------------------------------------------- #
# Editorial Roles & Governance Permissions
# --------------------------------------------------------------------------- #
EDITORIAL_ROLES = {UserRole.admin, UserRole.super_admin, UserRole.teacher}
EDITORIAL_ROLE_STRINGS = {"admin", "super_admin", "staff", "teacher"}


def is_editorial_user(user: User) -> bool:
    """Return True if user has editorial authority (admin, super_admin, teacher/editor)."""
    if getattr(user, "role", None) in EDITORIAL_ROLES:
        return True
    if str(getattr(user, "role", "")).lower() in EDITORIAL_ROLE_STRINGS:
        return True
    return False


def is_ai_agent_user(user: Optional[User]) -> bool:
    """Return True if user represents an automated AI agent or worker bot."""
    if not user:
        return False
    if getattr(user, "is_ai_agent", False):
        return True
    email = str(getattr(user, "email", "") or "").lower()
    if any(k in email for k in ("ai-agent", "ai_agent", "bot@", "automated", "ai-teacher")):
        return True
    username = str(getattr(user, "username", "") or "").lower()
    if any(k in username for k in ("ai_agent", "bot_", "automated_")):
        return True
    role_str = str(getattr(user, "role", "") or "").lower()
    if role_str in ("ai", "bot", "automated_agent"):
        return True
    return False


# --------------------------------------------------------------------------- #
# Entities
# --------------------------------------------------------------------------- #
def list_entities(
    db: Session,
    *,
    entity_type: Optional[str] = None,
    publication_status: Optional[str] = None,
    search: Optional[str] = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[HistoricalEntity], int]:
    q = select(HistoricalEntity)
    if entity_type:
        q = q.where(HistoricalEntity.entity_type == entity_type)
    if publication_status:
        q = q.where(HistoricalEntity.publication_status == publication_status)
    if search:
        like = f"%{search}%"
        q = q.where(
            or_(
                HistoricalEntity.name_vi.ilike(like),
                HistoricalEntity.name_en.ilike(like),
                HistoricalEntity.slug.ilike(like),
            )
        )
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = list(
        db.scalars(
            q.order_by(HistoricalEntity.name_vi).offset(offset).limit(limit)
        )
    )
    return items, total


def get_entity(db: Session, entity_id: UUID) -> Optional[HistoricalEntity]:
    return db.get(HistoricalEntity, entity_id)


def get_entity_by_slug(db: Session, slug: str) -> Optional[HistoricalEntity]:
    return db.scalar(
        select(HistoricalEntity).where(
            func.lower(HistoricalEntity.slug) == slug.lower()
        )
    )


def create_entity(
    db: Session,
    *,
    data: dict[str, Any],
    actor_id: Optional[UUID] = None,
    flush: bool = True,
) -> HistoricalEntity:
    entity_data = {**data}
    entity_data.setdefault("id", uuid.uuid4())
    entity = HistoricalEntity(**entity_data)
    if actor_id:
        entity.created_by = actor_id
        entity.updated_by = actor_id
    db.add(entity)
    if flush:
        db.flush()
    audit_action(
        db,
        actor_id=actor_id,
        action="create",
        resource_type="entity",
        resource_id=entity.id,
        after_json={"slug": entity.slug, "entity_type": entity.entity_type},
    )
    return entity


EDITORIAL_ENTITY_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"internal_review", "disputed", "archived"},
    "internal_review": {"verified", "draft", "disputed", "archived", "rejected"},
    "verified": {"published", "internal_review", "draft", "disputed", "archived"},
    "published": {"disputed", "archived", "internal_review", "draft"},
    "disputed": {"draft", "internal_review", "archived"},
    "archived": {"draft"},
    "rejected": {"draft", "internal_review", "archived"},
}

ENTITY_ACTION_MAP: dict[str, str] = {
    "draft": "draft",
    "internal_review": "submit_for_review",
    "verified": "verify",
    "published": "publish",
    "rejected": "reject",
    "disputed": "dispute",
    "archived": "archive",
}


def transition_entity_status(
    db: Session,
    *,
    entity: HistoricalEntity,
    target: str,
    actor_id: Optional[UUID],
    reason: Optional[str] = None,
    action: Optional[str] = None,
    require_four_eyes: bool = False,
) -> HistoricalEntity:
    """Move an entity through the publication state machine, enforcing role checks, 4-eyes review, and audit logging."""
    before = entity.publication_status
    if target == before:
        return entity

    # 1. Role-based governance and anti-AI self-approval checks
    if actor_id:
        actor = db.get(User, actor_id)
        if not actor:
            raise ValueError(f"Reviewer actor '{actor_id}' not found.")
        if is_ai_agent_user(actor):
            raise PermissionError(
                f"Automated AI agent cannot self-approve or sign off on entity '{target}'; "
                f"human editorial review is required."
            )
        if not is_editorial_user(actor):
            raise PermissionError(
                f"User '{actor.email}' with role '{actor.role}' is not authorized to advance entity "
                f"to '{target}'. Editorial role (admin, staff, teacher) required."
            )
        # Author / Reviewer separation (Four-Eyes Principle)
        if require_four_eyes and target in ("verified", "published"):
            if entity.created_by and str(actor_id) == str(entity.created_by):
                raise PermissionError(
                    "Author cannot review, verify, or publish their own entity draft (four-eyes human review required)."
                )

    # 2. State machine transition validity check
    if before in EDITORIAL_ENTITY_TRANSITIONS:
        allowed = EDITORIAL_ENTITY_TRANSITIONS[before]
        if target not in allowed:
            raise ValueError(
                f"Invalid editorial transition for entity from '{before}' to '{target}'. "
                f"Allowed transitions from '{before}' are: {sorted(allowed)}."
            )

    if target in ("verified", "published"):
        if not actor_id:
            raise ValueError(
                f"Advancing entity to '{target}' requires authenticated human reviewer attribution."
            )
        if not reason or not str(reason).strip():
            raise ValueError(f"Advancing entity to '{target}' requires a review note.")

    if target == "published":
        claims = list(db.scalars(select(HistoricalClaim).where(HistoricalClaim.entity_id == entity.id)))
        for c in claims:
            if c.confidence in ("disputed", "contested") or c.verification_status == "disputed":
                raise ValueError(
                    f"Cannot publish entity '{entity.slug}': contains disputed claim '{c.id}'."
                )
            if claim_has_contradicting_source(db, c):
                raise ValueError(
                    f"Cannot publish entity '{entity.slug}': contains contradicted claim '{c.id}'."
                )

    before_version = entity.content_version
    entity.publication_status = target
    entity.content_version += 1
    if actor_id:
        entity.updated_by = actor_id
    db.flush()

    resolved_action = action or ENTITY_ACTION_MAP.get(target, "update")
    audit_action(
        db,
        actor_id=actor_id,
        action=resolved_action,
        resource_type="entity",
        resource_id=entity.id,
        before_json={"publication_status": before, "content_version": before_version},
        after_json={"publication_status": target, "content_version": entity.content_version},
        reason=reason,
    )
    return entity


def update_entity(
    db: Session,
    *,
    entity: HistoricalEntity,
    data: dict[str, Any],
    actor_id: Optional[UUID] = None,
) -> HistoricalEntity:
    if "summary_vi" in data and data["summary_vi"]:
        claims = list(db.scalars(select(HistoricalClaim).where(HistoricalClaim.entity_id == entity.id)))
        is_valid, err = reject_compound_claim_with_disputed_facts(data["summary_vi"], claims)
        if not is_valid:
            raise ValueError(f"Negative abuse: {err}")
    if "summary_en" in data and data["summary_en"]:
        claims = list(db.scalars(select(HistoricalClaim).where(HistoricalClaim.entity_id == entity.id)))
        is_valid, err = reject_compound_claim_with_disputed_facts(data["summary_en"], claims)
        if not is_valid:
            raise ValueError(f"Negative abuse: {err}")

    new_status = data.pop("publication_status", None)
    if new_status and new_status != entity.publication_status:
        reason = data.pop("reason", None) or "Entity publication status update"
        transition_entity_status(
            db,
            entity=entity,
            target=new_status,
            actor_id=actor_id,
            reason=reason,
        )

    if not data:
        return entity

    before = {
        "slug": entity.slug,
        "name_vi": entity.name_vi,
        "publication_status": entity.publication_status,
    }
    for key, value in data.items():
        setattr(entity, key, value)
    entity.content_version += 1
    if actor_id:
        entity.updated_by = actor_id
    db.flush()
    audit_action(
        db,
        actor_id=actor_id,
        action="update",
        resource_type="entity",
        resource_id=entity.id,
        before_json=before,
        after_json={
            "slug": entity.slug,
            "name_vi": entity.name_vi,
            "publication_status": entity.publication_status,
            "content_version": entity.content_version,
        },
    )
    return entity


# --------------------------------------------------------------------------- #
# Sources & Bibliographic Registry
# --------------------------------------------------------------------------- #
REDACTED_EXCERPT_TEXT = "[REDACTED: RIGHTS_RESTRICTED]"

RESTRICTED_RIGHTS_STATUSES = {
    "unlicensed",
    "copyrighted",
    "all_rights_reserved",
    "in_copyright",
    "proprietary",
    "rights_restricted",
    "restricted",
}


def is_source_rights_restricted(source: Optional[HistoricalSource]) -> bool:
    """Returns True if the source indicates copyrighted, unlicensed, or restricted excerpts."""
    if source is None:
        return False
    if source.public_display_allowed is False:
        return True
    if source.verification_status == "rights_restricted":
        return True
    if source.rights_status:
        norm = source.rights_status.strip().lower().replace("-", "_").replace(" ", "_")
        if norm in RESTRICTED_RIGHTS_STATUSES:
            return True
        if any(term in norm for term in ("copyright", "unlicensed", "restricted", "all_rights_reserved")):
            return True
    if source.license:
        norm_lic = source.license.strip().lower()
        if any(term in norm_lic for term in ("all rights reserved", "proprietary", "unlicensed", "restricted")):
            return True
    return False


def redact_excerpt_for_public(text: Optional[str]) -> Optional[str]:
    """Redacts raw excerpt text for public consumption while preserving metadata."""
    if not text:
        return text
    return REDACTED_EXCERPT_TEXT


def normalize_isbn(isbn: Optional[str]) -> Optional[str]:
    """Normalize ISBN-10 or ISBN-13 by stripping hyphens and whitespace."""
    if not isbn:
        return None
    cleaned = re.sub(r"[\s\-]", "", str(isbn)).upper()
    return cleaned if cleaned else None


def normalize_doi(doi: Optional[str]) -> Optional[str]:
    """Normalize DOI by stripping leading URL resolvers, prefixes, and lowercasing."""
    if not doi:
        return None
    cleaned = str(doi).strip()
    cleaned = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip().lower()
    return cleaned if cleaned else None


def normalize_bibliographic_text(text: Optional[str]) -> Optional[str]:
    """Normalize title/author by stripping accents, extra whitespace, and lowercasing."""
    if not text:
        return None
    raw = str(text).replace("đ", "d").replace("Đ", "d")
    normalized = unicodedata.normalize("NFKD", raw)
    unaccented = "".join(c for c in normalized if not unicodedata.combining(c))
    collapsed = re.sub(r"\s+", " ", unaccented).strip().lower()
    return collapsed if collapsed else None


def compute_source_checksum(data: dict[str, Any]) -> str:
    """Compute deterministic SHA-256 checksum over canonical bibliographic fields."""
    canonical_parts = [
        str(data.get("source_type") or "").strip().lower(),
        normalize_bibliographic_text(data.get("title")) or "",
        normalize_bibliographic_text(data.get("author_text")) or "",
        str(data.get("publication_year") or "").strip(),
        str(data.get("edition") or "").strip().lower(),
        normalize_isbn(data.get("isbn")) or "",
        normalize_doi(data.get("doi")) or "",
    ]
    raw = "|".join(canonical_parts).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def find_duplicate_source(
    db: Session,
    *,
    isbn: Optional[str] = None,
    doi: Optional[str] = None,
    title: Optional[str] = None,
    author_text: Optional[str] = None,
    publication_year: Optional[int] = None,
    checksum: Optional[str] = None,
    exclude_id: Optional[UUID] = None,
) -> tuple[Optional[HistoricalSource], Optional[str]]:
    """Find existing HistoricalSource matching by ISBN, DOI, normalized Title+Author, or Checksum.
    
    Returns (duplicate_source, matched_by) or (None, None).
    """
    norm_isbn = normalize_isbn(isbn)
    norm_doi = normalize_doi(doi)

    # 1. Match by normalized ISBN
    if norm_isbn:
        sources = list(
            db.scalars(select(HistoricalSource).where(HistoricalSource.isbn.is_not(None)))
        )
        for s in sources:
            if exclude_id and s.id == exclude_id:
                continue
            if normalize_isbn(s.isbn) == norm_isbn:
                return s, "isbn"

    # 2. Match by normalized DOI
    if norm_doi:
        sources = list(
            db.scalars(select(HistoricalSource).where(HistoricalSource.doi.is_not(None)))
        )
        for s in sources:
            if exclude_id and s.id == exclude_id:
                continue
            if normalize_doi(s.doi) == norm_doi:
                return s, "doi"

    # 3. Match by normalized Title + Author
    norm_title = normalize_bibliographic_text(title)
    norm_author = normalize_bibliographic_text(author_text)
    if norm_title and norm_author:
        sources = list(
            db.scalars(
                select(HistoricalSource).where(
                    HistoricalSource.title.is_not(None),
                    HistoricalSource.author_text.is_not(None),
                )
            )
        )
        for s in sources:
            if exclude_id and s.id == exclude_id:
                continue
            if (
                normalize_bibliographic_text(s.title) == norm_title
                and normalize_bibliographic_text(s.author_text) == norm_author
            ):
                return s, "title_author"

    # 4. Match by explicit Checksum
    if checksum:
        norm_checksum = checksum.strip().lower()
        sources = list(
            db.scalars(select(HistoricalSource).where(HistoricalSource.checksum.is_not(None)))
        )
        for s in sources:
            if exclude_id and s.id == exclude_id:
                continue
            if s.checksum and s.checksum.strip().lower() == norm_checksum:
                return s, "checksum"

    return None, None


def list_sources(
    db: Session,
    *,
    source_type: Optional[str] = None,
    search: Optional[str] = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[HistoricalSource], int]:
    q = select(HistoricalSource)
    if source_type:
        q = q.where(HistoricalSource.source_type == source_type)
    if search:
        like = f"%{search}%"
        q = q.where(
            or_(
                HistoricalSource.title.ilike(like),
                HistoricalSource.author_text.ilike(like),
            )
        )
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = list(
        db.scalars(
            q.order_by(HistoricalSource.title).offset(offset).limit(limit)
        )
    )
    return items, total


def get_source(db: Session, source_id: UUID) -> Optional[HistoricalSource]:
    return db.get(HistoricalSource, source_id)


def create_source(
    db: Session,
    *,
    data: dict[str, Any],
    actor_id: Optional[UUID] = None,
    flush: bool = True,
    check_duplicate: bool = False,
) -> HistoricalSource:
    source_data = {**data}
    if check_duplicate:
        dup, matched_by = find_duplicate_source(
            db,
            isbn=source_data.get("isbn"),
            doi=source_data.get("doi"),
            title=source_data.get("title"),
            author_text=source_data.get("author_text"),
            publication_year=source_data.get("publication_year"),
            checksum=source_data.get("checksum"),
        )
        if dup:
            raise AppError(
                "HISTORICAL_SOURCE_DUPLICATE",
                f"A bibliographic source already exists matching this identifier via {matched_by} (ID: {dup.id}, Title: '{dup.title}')",
                status_code=409,
                details={
                    "duplicate_id": str(dup.id),
                    "duplicate_title": dup.title,
                    "matched_by": matched_by,
                },
            )

    # Normalize identifiers if provided
    if source_data.get("isbn"):
        source_data["isbn"] = normalize_isbn(source_data["isbn"])
    if source_data.get("doi"):
        source_data["doi"] = normalize_doi(source_data["doi"])

    # If no checksum provided, compute canonical metadata checksum
    if not source_data.get("checksum"):
        source_data["checksum"] = compute_source_checksum(source_data)

    source_data.setdefault("id", uuid.uuid4())
    source = HistoricalSource(**source_data)
    if actor_id:
        source.created_by = actor_id
    db.add(source)
    if flush:
        db.flush()
    audit_action(
        db,
        actor_id=actor_id,
        action="create",
        resource_type="source",
        resource_id=source.id,
        after_json={"title": source.title, "source_type": source.source_type},
    )
    return source


def update_source(
    db: Session,
    *,
    source: HistoricalSource,
    data: dict[str, Any],
    actor_id: Optional[UUID] = None,
    check_duplicate: bool = False,
) -> HistoricalSource:
    if check_duplicate:
        new_isbn = data.get("isbn", source.isbn)
        new_doi = data.get("doi", source.doi)
        new_title = data.get("title", source.title)
        new_author = data.get("author_text", source.author_text)
        new_year = data.get("publication_year", source.publication_year)
        new_checksum = data.get("checksum", source.checksum)
        dup, matched_by = find_duplicate_source(
            db,
            isbn=new_isbn,
            doi=new_doi,
            title=new_title,
            author_text=new_author,
            publication_year=new_year,
            checksum=new_checksum,
            exclude_id=source.id,
        )
        if dup:
            raise AppError(
                "HISTORICAL_SOURCE_DUPLICATE",
                f"Cannot update source: matching source already exists via {matched_by} (ID: {dup.id}, Title: '{dup.title}')",
                status_code=409,
                details={
                    "duplicate_id": str(dup.id),
                    "duplicate_title": dup.title,
                    "matched_by": matched_by,
                },
            )

    before = {"title": source.title, "verification_status": source.verification_status}
    for key, value in data.items():
        if key == "isbn" and value:
            value = normalize_isbn(value)
        elif key == "doi" and value:
            value = normalize_doi(value)
        setattr(source, key, value)
    db.flush()
    audit_action(
        db,
        actor_id=actor_id,
        action="update",
        resource_type="source",
        resource_id=source.id,
        before_json=before,
        after_json={"title": source.title, "verification_status": source.verification_status},
    )
    return source


# --------------------------------------------------------------------------- #
# Claims & Editorial Governance (V5-T025)
# --------------------------------------------------------------------------- #
ELIGIBLE_SUPPORT_TYPES = {"supports", "primary_evidence_for"}
REVIEWABLE_CLAIM_TYPES = {
    "factual",
    "chronology",
    "geographic",
    "identification",
}

EDITORIAL_CLAIM_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"internal_review", "disputed", "archived"},
    "internal_review": {"verified", "draft", "disputed", "archived", "rejected"},
    "verified": {"published", "internal_review", "draft", "disputed", "archived"},
    "published": {"disputed", "archived", "internal_review", "draft"},
    "disputed": {"draft", "internal_review", "archived"},
    "archived": {"draft"},
    "rejected": {"draft", "internal_review", "archived"},
}

LEGACY_CLAIM_TRANSITIONS: dict[str, set[str]] = {
    "unreviewed": {
        "needs_source", "source_attached", "editor_reviewed", "internal_review",
        "draft", "disputed", "archived", "rejected"
    },
    "needs_source": {
        "source_attached", "unreviewed", "draft", "internal_review",
        "disputed", "archived", "rejected"
    },
    "source_attached": {
        "editor_reviewed", "expert_verified", "verified", "internal_review",
        "needs_source", "disputed", "archived", "rejected"
    },
    "editor_reviewed": {
        "expert_verified", "verified", "published", "needs_source",
        "rejected", "disputed", "archived", "internal_review", "draft"
    },
    "expert_verified": {
        "published", "disputed", "archived", "superseded", "internal_review",
        "draft", "editor_reviewed"
    },
    "rejected": {"draft", "internal_review", "archived"},
    "superseded": {"archived"},
}

CLAIM_ACTION_MAP: dict[str, str] = {
    "draft": "draft",
    "internal_review": "submit_for_review",
    "editor_reviewed": "editor_approve",
    "expert_verified": "expert_verify",
    "verified": "verify",
    "published": "publish",
    "rejected": "reject",
    "disputed": "dispute",
    "needs_source": "request_source",
    "superseded": "supersede",
    "archived": "archive",
}


def claim_has_eligible_source(db: Session, claim: HistoricalClaim) -> bool:
    """True if the claim has at least one binding whose support type is eligible
    for verification (``supports`` or ``primary_evidence_for``)."""
    if not claim.id:
        return False
    count = db.scalar(
        select(func.count())
        .select_from(HistoricalClaimSource)
        .where(
            HistoricalClaimSource.claim_id == claim.id,
            HistoricalClaimSource.support_type.in_(ELIGIBLE_SUPPORT_TYPES),
        )
    )
    return bool(count and count > 0)


def _can_be_editor_reviewed(db: Session, claim: HistoricalClaim) -> bool:
    """A reviewable factual claim requires an eligible source binding before it
    may pass editorial review (Spec 9.2: source-attached is a precondition of
    the review workflow). Contradicted or disputed claims cannot pass review."""
    if claim.confidence in ("disputed", "contested") or claim.claim_type == "disputed":
        return False
    if claim_has_contradicting_source(db, claim):
        return False
    if claim.claim_type in REVIEWABLE_CLAIM_TYPES:
        return claim_has_eligible_source(db, claim)
    return True


def _can_be_expert_verified(db: Session, claim: HistoricalClaim) -> bool:
    """A reviewable factual claim requires an eligible source binding AND prior
    editor review before it may be expert-verified (Spec section 9.2).
    Contradicted or disputed claims cannot be expert-verified."""
    if (
        claim.confidence in ("disputed", "contested", "insufficient_sources")
        or claim.claim_type == "disputed"
        or claim.verification_status == "disputed"
    ):
        return False
    if claim_has_contradicting_source(db, claim):
        return False
    if claim.claim_type in REVIEWABLE_CLAIM_TYPES:
        return (
            claim.verification_status == "editor_reviewed"
            and claim_has_eligible_source(db, claim)
        )
    return claim.verification_status == "editor_reviewed"


def _can_be_verified(db: Session, claim: HistoricalClaim) -> bool:
    """A claim requires an eligible source binding and internal review before verification."""
    if (
        claim.confidence in ("disputed", "contested", "insufficient_sources")
        or claim.claim_type == "disputed"
        or claim.verification_status == "disputed"
    ):
        return False
    if claim_has_contradicting_source(db, claim):
        return False
    if claim.claim_type in REVIEWABLE_CLAIM_TYPES:
        return (
            claim.verification_status in ("internal_review", "editor_reviewed")
            and claim_has_eligible_source(db, claim)
        )
    return claim.verification_status in ("internal_review", "editor_reviewed")


def list_claims(
    db: Session,
    *,
    entity_id: Optional[UUID] = None,
    verification_status: Optional[str] = None,
    claim_type: Optional[str] = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[HistoricalClaim], int]:
    q = select(HistoricalClaim)
    if entity_id:
        q = q.where(HistoricalClaim.entity_id == entity_id)
    if verification_status:
        q = q.where(HistoricalClaim.verification_status == verification_status)
    if claim_type:
        q = q.where(HistoricalClaim.claim_type == claim_type)
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = list(
        db.scalars(
            q.order_by(HistoricalClaim.created_at).offset(offset).limit(limit)
        )
    )
    return items, total


def get_claim(db: Session, claim_id: UUID) -> Optional[HistoricalClaim]:
    return db.get(HistoricalClaim, claim_id)


def create_claim(
    db: Session,
    *,
    data: dict[str, Any],
    actor_id: Optional[UUID] = None,
    flush: bool = True,
    validate_atomic: bool = True,
) -> HistoricalClaim:
    statement = data.get("statement_vi", "")
    if validate_atomic:
        is_atomic, err_msg = validate_atomic_claim(statement)
        if not is_atomic:
            raise ValueError(err_msg)
    claim_data = {**data}
    claim_data.setdefault("id", uuid.uuid4())
    claim = HistoricalClaim(**claim_data)
    if actor_id:
        claim.created_by = actor_id
    db.add(claim)
    if flush:
        db.flush()
    audit_action(
        db,
        actor_id=actor_id,
        action="create",
        resource_type="claim",
        resource_id=claim.id,
        after_json={
            "statement_vi": claim.statement_vi,
            "claim_type": claim.claim_type,
            "verification_status": claim.verification_status,
            "origin": claim.origin,
        },
    )
    return claim


def transition_claim_status(
    db: Session,
    *,
    claim: HistoricalClaim,
    target: str,
    actor_id: Optional[UUID],
    reason: Optional[str] = None,
    action: Optional[str] = None,
    require_four_eyes: bool = False,
) -> HistoricalClaim:
    """Move a claim through the verification and publication state machine,
    enforcing human editorial governance, role checks, 4-eyes review, and source-binding invariants."""
    before = claim.verification_status
    if target == before:
        return claim

    # 1. Role-based governance and anti-AI self-approval checks
    if actor_id:
        actor = db.get(User, actor_id)
        if not actor:
            raise ValueError(f"Reviewer actor '{actor_id}' not found.")
        if is_ai_agent_user(actor):
            raise PermissionError(
                f"Automated AI agent cannot self-approve or sign off on '{target}'; "
                f"human editorial review is required."
            )
        if not is_editorial_user(actor):
            raise PermissionError(
                f"User '{actor.email}' with role '{actor.role}' is not authorized to advance claims "
                f"to '{target}'. Editorial role (admin, staff, teacher) required."
            )
        # Author / Reviewer separation (Four-Eyes Principle)
        if require_four_eyes and target in ("verified", "published", "expert_verified", "editor_reviewed"):
            if claim.created_by and str(actor_id) == str(claim.created_by):
                raise PermissionError(
                    "Author cannot review, verify, or publish their own claim (four-eyes human review principle required)."
                )

    # 2. State machine transition validity check
    if before in EDITORIAL_CLAIM_TRANSITIONS:
        allowed = EDITORIAL_CLAIM_TRANSITIONS[before]
        if target not in allowed:
            raise ValueError(
                f"Invalid editorial transition from '{before}' to '{target}'. "
                f"Allowed transitions from '{before}' are: {sorted(allowed)}."
            )
    elif before in LEGACY_CLAIM_TRANSITIONS:
        allowed = LEGACY_CLAIM_TRANSITIONS[before]
        if target not in allowed:
            raise ValueError(
                f"Invalid transition from '{before}' to '{target}'. "
                f"Allowed transitions from '{before}' are: {sorted(allowed)}."
            )

    if target in ("verified", "published"):
        if not actor_id:
            raise ValueError(
                f"Advancing claim to '{target}' requires authenticated human reviewer attribution."
            )
        if not reason or not str(reason).strip():
            raise ValueError(f"Advancing claim to '{target}' requires a review note.")

    # 3. Target-specific verification & safety checks
    if target == "editor_reviewed":
        if claim_has_contradicting_source(db, claim):
            raise ValueError("Contradicted claim cannot be approved as editor_reviewed.")
        if claim.confidence in ("disputed", "contested"):
            raise ValueError("Disputed claim cannot be approved as editor_reviewed.")
        if not _can_be_editor_reviewed(db, claim):
            raise ValueError(
                "Editor review of a factual claim requires an eligible source."
            )

    if target in ("verified", "expert_verified"):
        if claim_has_contradicting_source(db, claim):
            raise ValueError(f"Contradicted claim cannot be marked as {target}.")
        if claim.confidence in ("disputed", "contested"):
            raise ValueError(f"Disputed claim cannot be marked as {target}.")
        if claim.claim_type in ("translation", "etymology"):
            if claim.origin in ("ai_generated", "ai_ocr_candidate", "unspecified_seed"):
                raise ValueError(
                    f"AI-guessed or machine-generated translation/Hán-Nôm claim cannot be promoted to "
                    f"{target} without human epigrapher review."
                )
            if claim.confidence in ("disputed", "uncertain", "provisional"):
                raise ValueError(f"Uncertain or provisional reading cannot be promoted to {target}.")

        if target == "verified":
            if not _can_be_verified(db, claim):
                raise ValueError(
                    "Verified factual claims require an eligible source (supports or primary_evidence_for) "
                    "and prior review."
                )
        elif target == "expert_verified":
            if not _can_be_expert_verified(db, claim):
                raise ValueError(
                    "Verified factual claims require an eligible source and prior "
                    "editor review."
                )

    if target == "published":
        if before not in ("verified", "expert_verified"):
            raise ValueError(
                f"Cannot publish claim from status '{before}'; claim must be 'verified' before publishing."
            )
        if claim_has_contradicting_source(db, claim):
            raise ValueError("Contradicted claim cannot be published.")
        if claim.confidence in ("disputed", "contested") or claim.claim_type == "disputed":
            raise ValueError("Disputed claim cannot be published.")
        if claim.claim_type in REVIEWABLE_CLAIM_TYPES and not claim_has_eligible_source(db, claim):
            raise ValueError("Published factual claims require an eligible source.")
        # Rights clearance gate: cannot publish if bound sources have restricted/revoked rights
        for binding in claim.source_bindings:
            src = binding.source or db.get(HistoricalSource, binding.source_id)
            if src and getattr(src, "rights_status", None) in ("revoked", "withdrawn", "restricted", "blocked", "all_rights_reserved"):
                raise ValueError(
                    f"Cannot publish claim: bound source '{src.title}' has restricted/revoked rights status ('{src.rights_status}')."
                )

    if target == "needs_source" and claim_has_eligible_source(db, claim):
        raise ValueError(
            "Cannot mark a claim as needs_source while an eligible source is bound."
        )

    # 4. State updates
    claim.verification_status = target
    if reason:
        claim.review_notes = reason

    if target in ("editor_reviewed", "internal_review"):
        claim.reviewed_by = actor_id
        claim.reviewed_at = func.now()
    elif target in ("expert_verified", "verified"):
        claim.verified_by = actor_id
        claim.verified_at = func.now()
        if claim.confidence in ("unknown", "unreviewed"):
            claim.confidence = "high"
    elif target == "published":
        if not claim.verified_by and actor_id:
            claim.verified_by = actor_id
            claim.verified_at = func.now()
        if claim.confidence in ("unknown", "unreviewed"):
            claim.confidence = "high"
    elif target == "disputed":
        claim.confidence = "disputed"
    elif target == "archived":
        claim.is_current = False
    elif target == "draft":
        if before == "archived":
            claim.is_current = True
        if before == "disputed" and claim.confidence in ("disputed", "contested"):
            claim.confidence = "unknown"

    db.flush()

    # 5. Append-only governance audit logging
    resolved_action = action or CLAIM_ACTION_MAP.get(target, "update")
    audit_action(
        db,
        actor_id=actor_id,
        action=resolved_action,
        resource_type="claim",
        resource_id=claim.id,
        before_json={"verification_status": before},
        after_json={"verification_status": target},
        reason=reason,
    )
    return claim


def update_claim(
    db: Session,
    *,
    claim: HistoricalClaim,
    data: dict[str, Any],
    actor_id: Optional[UUID] = None,
) -> HistoricalClaim:
    if "statement_vi" in data and data["statement_vi"] is not None:
        is_atomic, err_msg = validate_atomic_claim(data["statement_vi"])
        if not is_atomic:
            raise ValueError(err_msg)

    new_status = data.pop("verification_status", None)
    if new_status and new_status != claim.verification_status:
        reason = data.pop("review_notes", None) or data.pop("reason", None)
        transition_claim_status(
            db,
            claim=claim,
            target=new_status,
            actor_id=actor_id,
            reason=reason,
        )

    if not data:
        return claim

    before = {
        "statement_vi": claim.statement_vi,
        "verification_status": claim.verification_status,
        "confidence": claim.confidence,
    }
    for key, value in data.items():
        setattr(claim, key, value)
    if actor_id:
        claim.updated_by = actor_id  # type: ignore[attr-defined]
    db.flush()
    audit_action(
        db,
        actor_id=actor_id,
        action="update",
        resource_type="claim",
        resource_id=claim.id,
        before_json=before,
        after_json={
            "statement_vi": claim.statement_vi,
            "verification_status": claim.verification_status,
            "confidence": claim.confidence,
        },
    )
    return claim


def attach_source_to_claim(
    db: Session,
    *,
    claim: HistoricalClaim,
    source: HistoricalSource,
    data: dict[str, Any],
    actor_id: Optional[UUID] = None,
) -> HistoricalClaimSource:
    binding = HistoricalClaimSource(
        claim_id=claim.id,
        source_id=source.id,
        support_type=data.get("support_type", "supports"),
        locator_type=data.get("locator_type"),
        page_start=data.get("page_start"),
        page_end=data.get("page_end"),
        chapter=data.get("chapter"),
        section=data.get("section"),
        figure=data.get("figure"),
        folio=data.get("folio"),
        inscription_location=data.get("inscription_location"),
        quotation_excerpt=data.get("quotation_excerpt"),
        quotation_language=data.get("quotation_language"),
        editor_note=data.get("editor_note"),
        created_by=actor_id,
    )
    db.add(binding)
    db.flush()
    # A claim with an eligible source may now move toward review, but is not
    # automatically verified.
    if claim.verification_status == "unreviewed" and binding.support_type in ELIGIBLE_SUPPORT_TYPES:
        claim.verification_status = "source_attached"
        db.flush()
    elif binding.support_type == "contradicts":
        # A contradicting source invalidates prior verification
        if claim.verification_status in ("verified", "published", "expert_verified", "editor_reviewed"):
            old_status = claim.verification_status
            claim.verification_status = "disputed"
            claim.confidence = "disputed"
            db.flush()
            audit_action(
                db,
                actor_id=actor_id,
                action="contradict_demote",
                resource_type="claim",
                resource_id=claim.id,
                before_json={"verification_status": old_status},
                after_json={"verification_status": "disputed", "confidence": "disputed"},
                reason=f"Demoted to disputed because source {source.id} contradicts this claim.",
            )
        elif claim.verification_status in ("unreviewed", "source_attached", "needs_source", "draft", "internal_review"):
            claim.confidence = "disputed"
            db.flush()
    audit_action(
        db,
        actor_id=actor_id,
        action="attach_source",
        resource_type="claim",
        resource_id=claim.id,
        after_json={"source_id": str(source.id), "support_type": binding.support_type},
    )
    return binding


def list_claim_sources(
    db: Session, *, claim_id: UUID
) -> list[HistoricalClaimSource]:
    return list(
        db.scalars(
            select(HistoricalClaimSource)
            .where(HistoricalClaimSource.claim_id == claim_id)
            .options(selectinload(HistoricalClaimSource.source))
        )
    )


# --------------------------------------------------------------------------- #
# Relations
# --------------------------------------------------------------------------- #
def list_relations(
    db: Session,
    *,
    entity_id: Optional[UUID] = None,
    offset: int = 0,
    limit: int = 100,
) -> tuple[list[HistoricalEntityRelation], int]:
    q = select(HistoricalEntityRelation)
    if entity_id:
        q = q.where(
            or_(
                HistoricalEntityRelation.subject_entity_id == entity_id,
                HistoricalEntityRelation.object_entity_id == entity_id,
            )
        )
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = list(db.scalars(q.offset(offset).limit(limit)))
    return items, total


def create_relation(
    db: Session,
    *,
    data: dict[str, Any],
    actor_id: Optional[UUID] = None,
    flush: bool = True,
) -> HistoricalEntityRelation:
    rel_data = {**data}
    rel_data.setdefault("id", uuid.uuid4())
    relation = HistoricalEntityRelation(**rel_data)
    if actor_id:
        relation.created_by = actor_id
    db.add(relation)
    if flush:
        db.flush()
    audit_action(
        db,
        actor_id=actor_id,
        action="create",
        resource_type="relation",
        resource_id=relation.id,
        after_json={
            "subject_entity_id": str(relation.subject_entity_id),
            "predicate": relation.predicate,
            "object_entity_id": str(relation.object_entity_id),
        },
    )
    return relation


def delete_relation(db: Session, *, relation_id: UUID) -> bool:
    relation = db.get(HistoricalEntityRelation, relation_id)
    if not relation:
        return False
    db.delete(relation)
    db.flush()
    audit_action(
        db,
        actor_id=None,
        action="delete",
        resource_type="relation",
        resource_id=relation_id,
        before_json={"subject_entity_id": str(relation.subject_entity_id)},
    )
    return True


# --------------------------------------------------------------------------- #
# Geography
# --------------------------------------------------------------------------- #
def get_geography(db: Session, entity_id: UUID) -> Optional[HistoricalGeography]:
    return db.get(HistoricalGeography, entity_id)


def upsert_geography(
    db: Session,
    *,
    entity_id: UUID,
    data: dict[str, Any],
) -> HistoricalGeography:
    geo = db.get(HistoricalGeography, entity_id)
    if geo is None:
        geo = HistoricalGeography(entity_id=entity_id, **data)
        db.add(geo)
    else:
        for key, value in data.items():
            setattr(geo, key, value)
    db.flush()
    return geo


# --------------------------------------------------------------------------- #
# Human Editorial Review Queue, Disputes & Rights Sign-off (V5-T078 / W07-A08)
# --------------------------------------------------------------------------- #
def get_editorial_queue(
    db: Session,
    *,
    item_type: Optional[str] = None,
    status: Optional[str] = None,
    origin: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int, dict[str, int]]:
    """Retrieve items in the human editorial review queue with metadata and summary metrics."""
    items: list[dict[str, Any]] = []

    # Summary metrics calculation
    claims_q = select(HistoricalClaim)
    all_claims = list(db.scalars(claims_q))

    pending_review_count = sum(1 for c in all_claims if c.verification_status in ("draft", "unreviewed", "internal_review"))
    internal_review_count = sum(1 for c in all_claims if c.verification_status == "internal_review")
    disputed_count = sum(1 for c in all_claims if c.verification_status == "disputed" or c.confidence in ("disputed", "contested"))
    needs_source_count = sum(1 for c in all_claims if c.verification_status == "needs_source")
    ai_draft_count = sum(1 for c in all_claims if c.origin in ("ai_generated", "ai_ocr_candidate", "ai_draft"))
    verified_count = sum(1 for c in all_claims if c.verification_status in ("verified", "expert_verified"))

    sources_q = select(HistoricalSource)
    all_sources = list(db.scalars(sources_q))
    needs_rights_count = sum(1 for s in all_sources if getattr(s, "rights_status", None) in (None, "needs_review", "needs_rights_review", "unreviewed"))

    # Populate items based on item_type
    if not item_type or item_type in ("claim", "all"):
        q = select(HistoricalClaim)
        if status and status != "all":
            if status == "pending_review":
                q = q.where(HistoricalClaim.verification_status.in_(["draft", "internal_review", "unreviewed"]))
            else:
                q = q.where(HistoricalClaim.verification_status == status)
        if origin and origin != "all":
            q = q.where(HistoricalClaim.origin == origin)
        if search:
            like = f"%{search}%"
            q = q.where(HistoricalClaim.statement_vi.ilike(like))

        claims = list(db.scalars(q.order_by(HistoricalClaim.created_at.desc()).limit(limit)))
        for c in claims:
            entity = c.entity or (db.get(HistoricalEntity, c.entity_id) if c.entity_id else None)
            author = db.get(User, c.created_by) if c.created_by else None
            is_ai = bool(
                c.origin in ("ai_generated", "ai_ocr_candidate", "ai_draft")
                or (author and is_ai_agent_user(author))
            )
            has_elig = claim_has_eligible_source(db, c)
            src_count = len(c.source_bindings) if hasattr(c, "source_bindings") else 0
            is_disp = bool(
                c.verification_status in ("disputed", "rejected")
                or c.confidence in ("disputed", "contested")
                or c.claim_type == "disputed"
            )
            items.append({
                "id": c.id,
                "item_type": "claim",
                "title": c.statement_vi,
                "statement_en": c.statement_en,
                "entity_id": c.entity_id,
                "entity_slug": entity.slug if entity else None,
                "entity_name": entity.name_vi if entity else None,
                "status": c.verification_status,
                "confidence": c.confidence,
                "origin": c.origin,
                "is_ai_draft": is_ai,
                "author_id": c.created_by,
                "author_email": author.email if author else None,
                "author_name": author.display_name if author else None,
                "reviewer_id": c.reviewed_by or c.verified_by,
                "has_eligible_source": has_elig,
                "source_count": src_count,
                "rights_status": getattr(c, "rights_status", "cleared" if has_elig else "unreviewed"),
                "rights_cleared": has_elig and not is_disp,
                "is_disputed": is_disp,
                "review_notes": c.review_notes,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
            })

    if item_type in ("entity", "all"):
        eq = select(HistoricalEntity)
        if status and status != "all":
            eq = eq.where(HistoricalEntity.publication_status == status)
        entities = list(db.scalars(eq.order_by(HistoricalEntity.created_at.desc()).limit(limit)))
        for e in entities:
            author = db.get(User, e.created_by) if e.created_by else None
            items.append({
                "id": e.id,
                "item_type": "entity",
                "title": e.name_vi,
                "statement_en": e.name_en,
                "entity_id": e.id,
                "entity_slug": e.slug,
                "entity_name": e.name_vi,
                "status": e.publication_status,
                "confidence": "high",
                "origin": "editorial",
                "is_ai_draft": False,
                "author_id": e.created_by,
                "author_email": author.email if author else None,
                "author_name": author.display_name if author else None,
                "reviewer_id": e.updated_by,
                "has_eligible_source": True,
                "source_count": 0,
                "rights_status": "cleared",
                "rights_cleared": True,
                "is_disputed": False,
                "review_notes": None,
                "created_at": e.created_at,
                "updated_at": e.updated_at,
            })

    total = len(items)
    summary = {
        "pending_review_count": pending_review_count,
        "internal_review_count": internal_review_count,
        "disputed_count": disputed_count,
        "needs_source_count": needs_source_count,
        "needs_rights_count": needs_rights_count,
        "ai_draft_count": ai_draft_count,
        "verified_count": verified_count,
    }
    return items[offset : offset + limit], total, summary


def perform_editorial_review(
    db: Session,
    *,
    item_type: str,
    item_id: UUID,
    action: str,
    actor_id: UUID,
    notes: Optional[str] = None,
    require_four_eyes: bool = True,
) -> dict[str, Any]:
    """Execute a structured review action with strict author/reviewer separation."""
    actor = db.get(User, actor_id)
    if not actor:
        raise ValueError(f"Reviewer actor '{actor_id}' not found.")
    if is_ai_agent_user(actor):
        raise PermissionError(
            "Automated AI agent cannot approve, verify, or publish drafts through API; human editorial review is required."
        )
    if not is_editorial_user(actor):
        raise PermissionError(
            f"User '{actor.email}' does not have editorial permissions (admin, staff, teacher required)."
        )

    action_to_target = {
        "submit_for_review": "internal_review",
        "verify": "verified",
        "publish": "published",
        "reject": "rejected",
        "flag_dispute": "disputed",
        "request_changes": "draft",
    }
    target = action_to_target.get(action)
    if not target:
        raise ValueError(f"Unknown review action '{action}'.")

    if item_type == "claim":
        claim = db.get(HistoricalClaim, item_id)
        if not claim:
            raise AppError("HISTORY_CLAIM_NOT_FOUND", "Claim not found.", 404)
        prev_status = claim.verification_status

        # Four-eyes check
        if require_four_eyes and action in ("verify", "publish"):
            if claim.created_by and str(claim.created_by) == str(actor_id):
                raise PermissionError(
                    "Author cannot approve or verify their own claim (four-eyes human review required)."
                )

        transition_claim_status(
            db,
            claim=claim,
            target=target,
            actor_id=actor_id,
            reason=notes or f"Editorial action: {action}",
            action="dispute" if action == "flag_dispute" else action,
            require_four_eyes=require_four_eyes,
        )
        return {
            "success": True,
            "item_id": claim.id,
            "item_type": "claim",
            "previous_status": prev_status,
            "new_status": claim.verification_status,
            "action": action,
            "reviewer_id": actor_id,
            "notes": notes,
            "message": f"Claim status transitioned from '{prev_status}' to '{claim.verification_status}' via {action}.",
        }

    elif item_type == "entity":
        entity = db.get(HistoricalEntity, item_id)
        if not entity:
            raise AppError("HISTORY_ENTITY_NOT_FOUND", "Entity not found.", 404)
        prev_status = entity.publication_status

        # Four-eyes check
        if require_four_eyes and action in ("verify", "publish"):
            if entity.created_by and str(entity.created_by) == str(actor_id):
                raise PermissionError(
                    "Author cannot approve or verify their own entity draft (four-eyes human review required)."
                )

        transition_entity_status(
            db,
            entity=entity,
            target=target,
            actor_id=actor_id,
            reason=notes or f"Editorial action: {action}",
            action=action,
            require_four_eyes=require_four_eyes,
        )
        return {
            "success": True,
            "item_id": entity.id,
            "item_type": "entity",
            "previous_status": prev_status,
            "new_status": entity.publication_status,
            "action": action,
            "reviewer_id": actor_id,
            "notes": notes,
            "message": f"Entity status transitioned from '{prev_status}' to '{entity.publication_status}' via {action}.",
        }

    elif item_type == "source":
        source = db.get(HistoricalSource, item_id)
        if not source:
            raise AppError("HISTORY_SOURCE_NOT_FOUND", "Source not found.", 404)
        prev_status = source.verification_status
        if require_four_eyes and action in ("verify", "publish"):
            if source.created_by and str(source.created_by) == str(actor_id):
                raise PermissionError(
                    "Author cannot approve or verify their own source (four-eyes human review required)."
                )
        source.verification_status = "verified" if action in ("verify", "publish") else target
        db.flush()
        audit_action(
            db,
            actor_id=actor_id,
            action=action,
            resource_type="source",
            resource_id=source.id,
            before_json={"verification_status": prev_status},
            after_json={"verification_status": source.verification_status},
            reason=notes,
        )
        return {
            "success": True,
            "item_id": source.id,
            "item_type": "source",
            "previous_status": prev_status,
            "new_status": source.verification_status,
            "action": action,
            "reviewer_id": actor_id,
            "notes": notes,
            "message": f"Source status transitioned from '{prev_status}' to '{source.verification_status}' via {action}.",
        }
    else:
        raise ValueError(f"Unsupported item type '{item_type}'.")


def resolve_editorial_dispute(
    db: Session,
    *,
    item_type: str,
    item_id: UUID,
    resolution: str,
    resolution_notes: str,
    actor_id: UUID,
    cited_source_id: Optional[UUID] = None,
) -> dict[str, Any]:
    """Adjudicate and resolve a dispute in the dispute resolution ledger."""
    actor = db.get(User, actor_id)
    if not actor:
        raise ValueError(f"Reviewer actor '{actor_id}' not found.")
    if is_ai_agent_user(actor):
        raise PermissionError(
            "Automated AI agent cannot adjudicate or resolve disputes; human review is required."
        )
    if not is_editorial_user(actor):
        raise PermissionError("Editorial authority required to resolve disputes.")
    if resolution not in ("resolved", "upheld"):
        raise ValueError("Resolution must be 'resolved' or 'upheld'.")
    if not resolution_notes or not str(resolution_notes).strip():
        raise ValueError("Substantive resolution notes are required to resolve a dispute.")

    now = datetime.now(timezone.utc)
    if item_type == "claim":
        claim = db.get(HistoricalClaim, item_id)
        if not claim:
            raise AppError("HISTORY_CLAIM_NOT_FOUND", "Claim not found.", 404)
        prev_status = claim.verification_status
        prev_conf = claim.confidence

        if resolution == "resolved":
            claim.verification_status = "draft"
            if claim.confidence in ("disputed", "contested"):
                claim.confidence = "medium"
            if cited_source_id:
                source = db.get(HistoricalSource, cited_source_id)
                if source:
                    existing_binding = db.get(
                        HistoricalClaimSource,
                        {"claim_id": claim.id, "source_id": source.id, "support_type": "supports"},
                    )
                    if not existing_binding:
                        attach_source_to_claim(
                            db, claim=claim, source=source, data={"support_type": "supports"}, actor_id=actor_id
                        )
        else:  # upheld
            claim.verification_status = "disputed"
            claim.confidence = "disputed"

        claim.review_notes = resolution_notes
        db.flush()
        audit_action(
            db,
            actor_id=actor_id,
            action=f"dispute_{resolution}",
            resource_type="claim",
            resource_id=claim.id,
            before_json={"verification_status": prev_status, "confidence": prev_conf},
            after_json={"verification_status": claim.verification_status, "confidence": claim.confidence},
            reason=resolution_notes,
        )
        return {
            "item_id": claim.id,
            "item_type": "claim",
            "resolution": resolution,
            "status": claim.verification_status,
            "adjudicator_id": actor_id,
            "notes": resolution_notes,
            "resolved_at": now,
        }
    elif item_type == "entity":
        entity = db.get(HistoricalEntity, item_id)
        if not entity:
            raise AppError("HISTORY_ENTITY_NOT_FOUND", "Entity not found.", 404)
        prev_status = entity.publication_status
        if resolution == "resolved":
            entity.publication_status = "draft"
        else:
            entity.publication_status = "disputed"
        db.flush()
        audit_action(
            db,
            actor_id=actor_id,
            action=f"dispute_{resolution}",
            resource_type="entity",
            resource_id=entity.id,
            before_json={"publication_status": prev_status},
            after_json={"publication_status": entity.publication_status},
            reason=resolution_notes,
        )
        return {
            "item_id": entity.id,
            "item_type": "entity",
            "resolution": resolution,
            "status": entity.publication_status,
            "adjudicator_id": actor_id,
            "notes": resolution_notes,
            "resolved_at": now,
        }
    else:
        raise ValueError(f"Unsupported item type '{item_type}'.")


def list_editorial_disputes(
    db: Session,
    *,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int, int, int]:
    """Query dispute events and current disputed claims from the audit ledger."""
    q = (
        select(HistoricalContentAuditLog)
        .where(
            HistoricalContentAuditLog.action.in_([
                "dispute", "flag_dispute", "dispute_resolved", "dispute_upheld"
            ])
        )
        .order_by(HistoricalContentAuditLog.created_at.desc(), HistoricalContentAuditLog.id.desc())
    )
    all_logs = list(db.scalars(q))

    items = []
    active_count = 0
    resolved_count = 0

    for log in all_logs:
        res_title = f"{log.resource_type}:{log.resource_id}"
        if log.resource_type == "claim" and log.resource_id:
            c = db.get(HistoricalClaim, log.resource_id)
            if c:
                res_title = c.statement_vi
        elif log.resource_type == "entity" and log.resource_id:
            e = db.get(HistoricalEntity, log.resource_id)
            if e:
                res_title = e.name_vi

        is_res = log.action == "dispute_resolved"
        is_uph = log.action == "dispute_upheld"
        disp_status = "resolved" if is_res else ("upheld" if is_uph else "active")

        if disp_status == "active":
            active_count += 1
        else:
            resolved_count += 1

        if status and status != "all" and disp_status != status:
            continue

        actor = db.get(User, log.actor_id) if log.actor_id else None

        items.append({
            "dispute_id": log.id,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "resource_title": res_title,
            "dispute_reason": log.reason,
            "disputed_by_id": log.actor_id,
            "disputed_by_email": actor.email if actor else None,
            "status": disp_status,
            "resolution_notes": log.reason if is_res or is_uph else None,
            "resolved_by_id": log.actor_id if is_res or is_uph else None,
            "created_at": log.created_at,
        })

    total = len(items)
    return items[offset : offset + limit], total, active_count, resolved_count


def signoff_rights(
    db: Session,
    *,
    resource_type: str,
    resource_id: UUID,
    rights_status: str,
    rights_owner: str,
    license: str,
    actor_id: UUID,
    legal_basis: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict[str, Any]:
    """Sign off on intellectual property and reuse rights for a historical resource."""
    actor = db.get(User, actor_id)
    if not actor:
        raise ValueError(f"Reviewer actor '{actor_id}' not found.")
    if is_ai_agent_user(actor):
        raise PermissionError(
            "Automated AI agent cannot sign off on rights clearance; human editorial review is required."
        )
    if not is_editorial_user(actor):
        raise PermissionError("Editorial authority required for rights sign-off.")

    now = datetime.now(timezone.utc)
    before_status = None

    if resource_type == "source":
        source = db.get(HistoricalSource, resource_id)
        if not source:
            raise AppError("HISTORY_SOURCE_NOT_FOUND", "Source not found.", 404)
        before_status = getattr(source, "rights_status", "unreviewed")
        source.rights_status = rights_status
        if hasattr(source, "license"):
            source.license = license
        db.flush()
    elif resource_type == "asset":
        asset = db.get(HistoricalAsset, resource_id)
        if not asset:
            raise AppError("HISTORY_ASSET_NOT_FOUND", "Asset not found.", 404)
        before_status = getattr(asset, "rights_status", "unreviewed")
        asset.rights_status = rights_status
        if hasattr(asset, "rights_owner"):
            asset.rights_owner = rights_owner
        if hasattr(asset, "license"):
            asset.license = license
        db.flush()
    elif resource_type in ("claim", "entity"):
        before_status = "unreviewed"
    else:
        raise ValueError(f"Unsupported resource type for rights sign-off: '{resource_type}'.")

    audit_action(
        db,
        actor_id=actor_id,
        action="rights_signoff",
        resource_type=resource_type,
        resource_id=resource_id,
        before_json={"rights_status": before_status},
        after_json={
            "rights_status": rights_status,
            "rights_owner": rights_owner,
            "license": license,
            "legal_basis": legal_basis,
        },
        reason=notes or f"Rights sign-off by {actor.email}",
    )

    return {
        "success": True,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "rights_status": rights_status,
        "rights_owner": rights_owner,
        "license": license,
        "signed_off_by": actor_id,
        "signed_off_at": now,
        "message": f"Rights clearance '{rights_status}' successfully signed off by human reviewer.",
    }
