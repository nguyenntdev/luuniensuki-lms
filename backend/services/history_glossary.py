# -*- coding: utf-8 -*-
"""Service implementation for Bilingual Pedagogical Glossary (V5-T098 / W09-A08).

Provides query, authoring, review, and negative abuse guardrails for
multilingual glossary terms and Hán–Nôm epigraphy.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..domain.multilingual_glossary import (
    CANONICAL_PEDAGOGICAL_GLOSSARY,
    GlossaryCategory,
    GlossaryReviewStatus,
    GlossaryValidationError,
    MismatchedTranslationError,
    TranslationOrigin,
    UNREVIEWED_GLOSSARY_STATUSES,
    UnreviewedTranslationPromotionError,
    VERIFIED_GLOSSARY_STATUSES,
    build_translation_provenance,
    detect_translation_mismatch,
    validate_glossary_term_invariants,
)
from ..errors import AppError
from ..history_models import HistoricalContentAuditLog, HistoricalGlossaryTerm, HistoricalSource
from ..models import User


def seed_canonical_glossary_if_needed(db: Session) -> int:
    """Seed canonical Cửu Đỉnh pedagogical glossary if table is empty or missing terms."""
    count = 0
    for seed in CANONICAL_PEDAGOGICAL_GLOSSARY:
        existing = db.execute(
            select(HistoricalGlossaryTerm).where(HistoricalGlossaryTerm.term_key == seed["term_key"])
        ).scalar_one_or_none()
        if not existing:
            provenance = build_translation_provenance(
                origin=seed.get("origin", TranslationOrigin.human_epigrapher.value),
                translator_or_reviewer=seed.get("epigrapher_signoff"),
                citation_locator=seed.get("citation_locator"),
                is_machine_translated=seed.get("is_machine_translated", False),
                is_uncertain=seed.get("is_uncertain", False),
                uncertainty_label=seed.get("uncertainty_label"),
            )
            term = HistoricalGlossaryTerm(
                term_key=seed["term_key"],
                term_vi=seed["term_vi"],
                term_en=seed["term_en"],
                term_han_nom=seed.get("term_han_nom"),
                reading_quoc_ngu=seed.get("reading_quoc_ngu"),
                category=seed.get("category", GlossaryCategory.general.value),
                definition_vi=seed["definition_vi"],
                definition_en=seed["definition_en"],
                contextual_usage_vi=seed.get("contextual_usage_vi"),
                contextual_usage_en=seed.get("contextual_usage_en"),
                citation_locator=seed.get("citation_locator"),
                bilingual_citation=seed.get("bilingual_citation", {}),
                review_status=seed.get("review_status", GlossaryReviewStatus.verified.value),
                origin=seed.get("origin", TranslationOrigin.human_epigrapher.value),
                is_machine_translated=seed.get("is_machine_translated", False),
                is_uncertain=seed.get("is_uncertain", False),
                uncertainty_label=seed.get("uncertainty_label"),
                epigrapher_signoff=seed.get("epigrapher_signoff"),
                translation_provenance=provenance,
                related_entity_slugs=seed.get("related_entity_slugs", []),
            )
            db.add(term)
            count += 1
    if count > 0:
        db.commit()
    return count


def list_glossary_terms(
    db: Session,
    category: Optional[str] = None,
    search: Optional[str] = None,
    review_status: Optional[str] = None,
    origin: Optional[str] = None,
    include_unreviewed: bool = True,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[HistoricalGlossaryTerm], int]:
    """Retrieve glossary terms with filtering, search, and pagination."""
    # Ensure baseline seeds exist
    seed_canonical_glossary_if_needed(db)

    query = select(HistoricalGlossaryTerm)

    if category:
        query = query.where(HistoricalGlossaryTerm.category == category.strip().lower())

    if review_status:
        query = query.where(HistoricalGlossaryTerm.review_status == review_status.strip().lower())
    elif not include_unreviewed:
        query = query.where(HistoricalGlossaryTerm.review_status.in_(VERIFIED_GLOSSARY_STATUSES))

    if origin:
        query = query.where(HistoricalGlossaryTerm.origin == origin.strip().lower())

    if search:
        s = f"%{search.strip().lower()}%"
        query = query.where(
            or_(
                func.lower(HistoricalGlossaryTerm.term_vi).like(s),
                func.lower(HistoricalGlossaryTerm.term_en).like(s),
                func.lower(HistoricalGlossaryTerm.term_key).like(s),
                func.lower(HistoricalGlossaryTerm.reading_quoc_ngu).like(s),
                func.lower(HistoricalGlossaryTerm.definition_vi).like(s),
                func.lower(HistoricalGlossaryTerm.definition_en).like(s),
            )
        )

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(
        query.order_by(HistoricalGlossaryTerm.category, HistoricalGlossaryTerm.term_key)
        .offset(offset)
        .limit(limit)
    ).all()

    return list(items), total


def get_glossary_term(db: Session, term_key: str) -> HistoricalGlossaryTerm:
    """Retrieve a single glossary term by its unique key."""
    seed_canonical_glossary_if_needed(db)
    term = db.scalars(
        select(HistoricalGlossaryTerm).where(HistoricalGlossaryTerm.term_key == term_key.strip().lower())
    ).first()
    if not term:
        raise AppError("GLOSSARY_TERM_NOT_FOUND", f"Glossary term '{term_key}' does not exist.", 404)
    return term


def create_or_upsert_glossary_term(
    db: Session,
    payload: Any,
    actor: User,
) -> HistoricalGlossaryTerm:
    """Create or update a glossary term with strict negative abuse guardrail validation."""
    term_key = payload.term_key.strip().lower()

    # Validate domain invariants & negative abuse rules
    try:
        norm = validate_glossary_term_invariants(
            term_key=term_key,
            term_vi=payload.term_vi,
            term_en=payload.term_en,
            definition_vi=payload.definition_vi,
            definition_en=payload.definition_en,
            review_status=payload.review_status,
            origin=payload.origin,
            term_han_nom=payload.term_han_nom,
            reading_quoc_ngu=payload.reading_quoc_ngu,
            epigrapher_signoff=payload.epigrapher_signoff,
            source_id=payload.source_id,
            citation_locator=payload.citation_locator,
            is_machine_translated=payload.is_machine_translated,
            is_uncertain=payload.is_uncertain,
            uncertainty_label=payload.uncertainty_label,
        )
    except (MismatchedTranslationError, UnreviewedTranslationPromotionError, GlossaryValidationError) as exc:
        raise AppError("GLOSSARY_VALIDATION_ERROR", str(exc), 422) from exc

    # Check source_id if provided
    if payload.source_id:
        src = db.get(HistoricalSource, payload.source_id)
        if not src:
            raise AppError("SOURCE_NOT_FOUND", f"Referenced source {payload.source_id} not found.", 404)

    existing = db.scalars(
        select(HistoricalGlossaryTerm).where(HistoricalGlossaryTerm.term_key == term_key)
    ).first()

    provenance = build_translation_provenance(
        origin=payload.origin,
        translator_or_reviewer=payload.epigrapher_signoff,
        citation_locator=payload.citation_locator,
        is_machine_translated=norm["is_machine_translated"],
        is_uncertain=norm["is_uncertain"],
        uncertainty_label=norm["uncertainty_label"],
        notes=f"Created/updated by {actor.email} ({actor.role})",
    )

    if existing:
        existing.term_vi = payload.term_vi
        existing.term_en = payload.term_en
        existing.term_han_nom = payload.term_han_nom
        existing.reading_quoc_ngu = payload.reading_quoc_ngu
        existing.category = payload.category
        existing.definition_vi = payload.definition_vi
        existing.definition_en = payload.definition_en
        existing.contextual_usage_vi = payload.contextual_usage_vi
        existing.contextual_usage_en = payload.contextual_usage_en
        existing.source_id = payload.source_id
        existing.citation_locator = payload.citation_locator
        if payload.bilingual_citation is not None:
            existing.bilingual_citation = payload.bilingual_citation
        existing.review_status = norm["review_status"]
        existing.origin = payload.origin
        existing.is_machine_translated = norm["is_machine_translated"]
        existing.is_uncertain = norm["is_uncertain"]
        existing.uncertainty_label = norm["uncertainty_label"]
        existing.epigrapher_signoff = payload.epigrapher_signoff
        existing.translation_provenance = provenance
        if payload.related_entity_slugs is not None:
            existing.related_entity_slugs = payload.related_entity_slugs
        term = existing
        action = "update"
    else:
        term = HistoricalGlossaryTerm(
            term_key=term_key,
            term_vi=payload.term_vi,
            term_en=payload.term_en,
            term_han_nom=payload.term_han_nom,
            reading_quoc_ngu=payload.reading_quoc_ngu,
            category=payload.category,
            definition_vi=payload.definition_vi,
            definition_en=payload.definition_en,
            contextual_usage_vi=payload.contextual_usage_vi,
            contextual_usage_en=payload.contextual_usage_en,
            source_id=payload.source_id,
            citation_locator=payload.citation_locator,
            bilingual_citation=payload.bilingual_citation or {},
            review_status=norm["review_status"],
            origin=payload.origin,
            is_machine_translated=norm["is_machine_translated"],
            is_uncertain=norm["is_uncertain"],
            uncertainty_label=norm["uncertainty_label"],
            epigrapher_signoff=payload.epigrapher_signoff,
            translation_provenance=provenance,
            related_entity_slugs=payload.related_entity_slugs or [],
        )
        db.add(term)
        action = "create"

    audit = HistoricalContentAuditLog(
        resource_type="glossary_term",
        resource_id=term.id,
        action=action,
        actor_id=actor.id,
        after_json={
            "term_key": term_key,
            "review_status": term.review_status,
            "origin": term.origin,
            "is_uncertain": term.is_uncertain,
            "uncertainty_label": term.uncertainty_label,
            "epigrapher_signoff": term.epigrapher_signoff,
        },
    )
    db.add(audit)
    db.commit()
    db.refresh(term)
    return term


def update_glossary_term(
    db: Session,
    term_key: str,
    payload: Any,
    actor: User,
) -> HistoricalGlossaryTerm:
    """Patch update a glossary term with invariant validation."""
    term = get_glossary_term(db, term_key)

    new_term_vi = payload.term_vi if payload.term_vi is not None else term.term_vi
    new_term_en = payload.term_en if payload.term_en is not None else term.term_en
    new_def_vi = payload.definition_vi if payload.definition_vi is not None else term.definition_vi
    new_def_en = payload.definition_en if payload.definition_en is not None else term.definition_en
    new_status = payload.review_status if payload.review_status is not None else term.review_status
    new_origin = payload.origin if payload.origin is not None else term.origin
    new_han_nom = payload.term_han_nom if payload.term_han_nom is not None else term.term_han_nom
    new_reading = payload.reading_quoc_ngu if payload.reading_quoc_ngu is not None else term.reading_quoc_ngu
    new_signoff = payload.epigrapher_signoff if payload.epigrapher_signoff is not None else term.epigrapher_signoff
    new_source_id = payload.source_id if payload.source_id is not None else term.source_id
    new_locator = payload.citation_locator if payload.citation_locator is not None else term.citation_locator
    new_machine = payload.is_machine_translated if payload.is_machine_translated is not None else term.is_machine_translated
    new_uncertain = payload.is_uncertain if payload.is_uncertain is not None else term.is_uncertain
    new_label = payload.uncertainty_label if payload.uncertainty_label is not None else term.uncertainty_label

    try:
        norm = validate_glossary_term_invariants(
            term_key=term_key,
            term_vi=new_term_vi,
            term_en=new_term_en,
            definition_vi=new_def_vi,
            definition_en=new_def_en,
            review_status=new_status,
            origin=new_origin,
            term_han_nom=new_han_nom,
            reading_quoc_ngu=new_reading,
            epigrapher_signoff=new_signoff,
            source_id=new_source_id,
            citation_locator=new_locator,
            is_machine_translated=new_machine,
            is_uncertain=new_uncertain,
            uncertainty_label=new_label,
        )
    except (MismatchedTranslationError, UnreviewedTranslationPromotionError, GlossaryValidationError) as exc:
        raise AppError("GLOSSARY_VALIDATION_ERROR", str(exc), 422) from exc

    term.term_vi = new_term_vi
    term.term_en = new_term_en
    term.definition_vi = new_def_vi
    term.definition_en = new_def_en
    term.review_status = norm["review_status"]
    term.origin = new_origin
    term.term_han_nom = new_han_nom
    term.reading_quoc_ngu = new_reading
    term.epigrapher_signoff = new_signoff
    term.source_id = new_source_id
    term.citation_locator = new_locator
    term.is_machine_translated = norm["is_machine_translated"]
    term.is_uncertain = norm["is_uncertain"]
    term.uncertainty_label = norm["uncertainty_label"]

    if payload.category is not None:
        term.category = payload.category
    if payload.contextual_usage_vi is not None:
        term.contextual_usage_vi = payload.contextual_usage_vi
    if payload.contextual_usage_en is not None:
        term.contextual_usage_en = payload.contextual_usage_en
    if payload.bilingual_citation is not None:
        term.bilingual_citation = payload.bilingual_citation
    if payload.related_entity_slugs is not None:
        term.related_entity_slugs = payload.related_entity_slugs

    term.translation_provenance = build_translation_provenance(
        origin=term.origin,
        translator_or_reviewer=term.epigrapher_signoff,
        citation_locator=term.citation_locator,
        is_machine_translated=term.is_machine_translated,
        is_uncertain=term.is_uncertain,
        uncertainty_label=term.uncertainty_label,
        notes=f"Updated by {actor.email} ({actor.role})",
    )

    audit = HistoricalContentAuditLog(
        resource_type="glossary_term",
        resource_id=term.id,
        action="update",
        actor_id=actor.id,
        after_json={
            "term_key": term_key,
            "review_status": term.review_status,
            "is_uncertain": term.is_uncertain,
            "uncertainty_label": term.uncertainty_label,
        },
    )
    db.add(audit)
    db.commit()
    db.refresh(term)
    return term


def review_glossary_term(
    db: Session,
    term_key: str,
    payload: Any,
    actor: User,
) -> HistoricalGlossaryTerm:
    """Submit expert review sign-off or status transition for a glossary term."""
    term = get_glossary_term(db, term_key)

    new_status = payload.review_status
    new_signoff = payload.epigrapher_signoff or term.epigrapher_signoff
    new_source_id = payload.source_id or term.source_id
    new_locator = payload.citation_locator or term.citation_locator

    try:
        norm = validate_glossary_term_invariants(
            term_key=term.term_key,
            term_vi=term.term_vi,
            term_en=term.term_en,
            definition_vi=term.definition_vi,
            definition_en=term.definition_en,
            review_status=new_status,
            origin=term.origin,
            term_han_nom=term.term_han_nom,
            reading_quoc_ngu=term.reading_quoc_ngu,
            epigrapher_signoff=new_signoff,
            source_id=new_source_id,
            citation_locator=new_locator,
            is_machine_translated=term.is_machine_translated,
            is_uncertain=False if new_status in VERIFIED_GLOSSARY_STATUSES else term.is_uncertain,
            uncertainty_label=None if new_status in VERIFIED_GLOSSARY_STATUSES else term.uncertainty_label,
        )
    except (MismatchedTranslationError, UnreviewedTranslationPromotionError, GlossaryValidationError) as exc:
        raise AppError("GLOSSARY_VALIDATION_ERROR", str(exc), 422) from exc

    term.review_status = norm["review_status"]
    term.epigrapher_signoff = new_signoff
    term.source_id = new_source_id
    term.citation_locator = new_locator
    term.is_uncertain = norm["is_uncertain"]
    term.uncertainty_label = norm["uncertainty_label"]

    term.translation_provenance = build_translation_provenance(
        origin=term.origin,
        translator_or_reviewer=term.epigrapher_signoff,
        citation_locator=term.citation_locator,
        is_machine_translated=term.is_machine_translated,
        is_uncertain=term.is_uncertain,
        uncertainty_label=term.uncertainty_label,
        notes=payload.notes or f"Reviewed by {actor.email} ({actor.role})",
    )

    audit = HistoricalContentAuditLog(
        resource_type="glossary_term",
        resource_id=term.id,
        action=f"review_{new_status}",
        actor_id=actor.id,
        reason=payload.notes,
        after_json={
            "review_status": term.review_status,
            "epigrapher_signoff": term.epigrapher_signoff,
            "notes": payload.notes,
        },
    )
    db.add(audit)
    db.commit()
    db.refresh(term)
    return term
