#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Idempotent database seeder for STTT Imperial City extended historical sources & claims.

Follow-on historical corpus expansion:
- Seeds primary dynastic chronicles and archival repositories into `historical_sources`.
- Seeds monument entities into `historical_entities` with `content_scope = 'STTT_IMPERIAL_CITY'`.
- Seeds verified evidence-backed claims into `historical_claims` with `content_scope = 'STTT_IMPERIAL_CITY'`.
- Binds claims to sources in `historical_claim_sources` with exact locators.
- Fully idempotent: safe to execute repeatedly without duplicating records or breaking constraints.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, NAMESPACE_DNS, uuid5

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.history_models import (
    HistoricalClaim,
    HistoricalClaimSource,
    HistoricalEntity,
    HistoricalSource,
)
from backend.models import User, UserRole

logger = logging.getLogger("seed_extended_sources")
CONTENT_SCOPE_IMPERIAL = "STTT_IMPERIAL_CITY"
DEFAULT_DB_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/luuniensuki"


def get_or_create_curator_user(session: Session) -> User | None:
    """Find an administrative user or create deterministic curator user for provenance."""
    try:
        admin = session.execute(
            select(User).where(User.role.in_([UserRole.admin, UserRole.super_admin]))
        ).scalars().first()
        if admin:
            return admin

        admin = session.execute(select(User)).scalars().first()
        if admin:
            return admin

        curator = User(
            id=UUID("00000000-0000-0000-0000-000000000001"),
            username="system_curator",
            display_name="System Curator",
            email="curator@luuniensuki.vn",
            password_hash="$2b$12$eX.SampleHashForSystemAdminUserOnly123456789012345678",
            role=UserRole.admin,
        )
        session.add(curator)
        session.flush()
        return curator
    except Exception:
        # Table users might not exist or be accessible in lightweight/sqlite test sessions
        session.rollback()
        return None


def ensure_content_scope_columns(engine) -> None:
    """Ensure content_scope columns exist on historical tables if running against Postgres."""
    if engine.dialect.name != "postgresql":
        return

    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE historical_sources ADD COLUMN IF NOT EXISTS content_scope TEXT DEFAULT 'STTT_IMPERIAL_CITY';"
            )
        )
        conn.execute(
            text(
                "ALTER TABLE historical_claims ADD COLUMN IF NOT EXISTS content_scope TEXT DEFAULT 'STTT_IMPERIAL_CITY';"
            )
        )
        conn.execute(
            text(
                "ALTER TABLE historical_entities ADD COLUMN IF NOT EXISTS content_scope TEXT DEFAULT 'STTT_IMPERIAL_CITY';"
            )
        )


def seed_extended_sources(
    session: Session,
    sources_data: dict[str, Any],
    claims_data: dict[str, Any],
    dry_run: bool = False,
) -> dict[str, int]:
    """Seed sources and claims inside an active SQLAlchemy session."""
    stats = {
        "sources_seeded": 0,
        "entities_seeded": 0,
        "claims_seeded": 0,
        "claim_sources_seeded": 0,
    }

    curator = get_or_create_curator_user(session)
    curator_id = curator.id if curator else None
    source_uuid_map: dict[str, UUID] = {}

    # ----------------------------------------------------------------------- #
    # 1. Historical Sources
    # ----------------------------------------------------------------------- #
    for src in sources_data.get("bibliography", []):
        src_id_str = src.get("uuid")
        source_id = (
            UUID(src_id_str)
            if src_id_str
            else uuid5(NAMESPACE_DNS, f"imperial_source:{src['id']}")
        )
        source_uuid_map[src["id"]] = source_id

        existing_source = session.get(HistoricalSource, source_id)
        if not existing_source:
            existing_source = session.execute(
                select(HistoricalSource).where(
                    HistoricalSource.title == src["title"],
                    HistoricalSource.volume == src.get("volume"),
                )
            ).scalar_one_or_none()

        if existing_source:
            existing_source.source_type = src.get("source_type", "royal_record")
            existing_source.title = src["title"]
            existing_source.subtitle = src.get("subtitle")
            existing_source.author_text = src.get("author_text")
            existing_source.publisher = src.get("publisher")
            existing_source.publication_year = src.get("publication_year")
            existing_source.edition = src.get("edition")
            existing_source.volume = src.get("volume")
            existing_source.pages = src.get("pages")
            existing_source.language = src.get("language", "vi")
            existing_source.citation_text = src.get("citation_text")
            existing_source.rights_status = src.get("rights_status", "public_domain")
            existing_source.public_display_allowed = src.get("public_display_allowed", True)
            existing_source.derivative_allowed = src.get("derivative_allowed", True)
            existing_source.verification_status = src.get("verification_status", "verified")
            existing_source.repository_identifier = src.get("repository_identifier")
            existing_source.content_scope = CONTENT_SCOPE_IMPERIAL
        else:
            new_source = HistoricalSource(
                id=source_id,
                source_type=src.get("source_type", "royal_record"),
                title=src["title"],
                subtitle=src.get("subtitle"),
                author_text=src.get("author_text"),
                publisher=src.get("publisher"),
                publication_year=src.get("publication_year"),
                edition=src.get("edition"),
                volume=src.get("volume"),
                pages=src.get("pages"),
                language=src.get("language", "vi"),
                citation_text=src.get("citation_text"),
                rights_status=src.get("rights_status", "public_domain"),
                public_display_allowed=src.get("public_display_allowed", True),
                derivative_allowed=src.get("derivative_allowed", True),
                verification_status=src.get("verification_status", "verified"),
                repository_identifier=src.get("repository_identifier"),
                content_scope=CONTENT_SCOPE_IMPERIAL,
                created_by=curator_id,
            )
            session.add(new_source)

        stats["sources_seeded"] += 1

    session.flush()

    # ----------------------------------------------------------------------- #
    # 2. Historical Entities for the 16 Monuments
    # ----------------------------------------------------------------------- #
    monument_slugs = {c["monument_slug"] for c in claims_data.get("claims", [])}
    entity_id_map: dict[str, UUID] = {}

    for slug in monument_slugs:
        entity_id = uuid5(NAMESPACE_DNS, f"imperial_entity:{slug}")
        entity = session.get(HistoricalEntity, entity_id)
        if not entity:
            entity = session.execute(
                select(HistoricalEntity).where(HistoricalEntity.slug == slug)
            ).scalar_one_or_none()

        # Find monument human name from claims
        matching_claim = next(
            (c for c in claims_data.get("claims", []) if c["monument_slug"] == slug), None
        )
        name_vi = matching_claim["monument_name_vi"] if matching_claim else slug

        if entity:
            entity.name_vi = name_vi
            entity.entity_type = "monument"
            entity.publication_status = "published"
            entity.content_scope = CONTENT_SCOPE_IMPERIAL
            entity_id_map[slug] = entity.id
        else:
            entity = HistoricalEntity(
                id=entity_id,
                slug=slug,
                name_vi=name_vi,
                entity_type="monument",
                publication_status="published",
                content_scope=CONTENT_SCOPE_IMPERIAL,
                content_version=1,
                created_by=curator_id,
            )
            session.add(entity)
            session.flush()
            entity_id_map[slug] = entity.id

        stats["entities_seeded"] += 1

    session.flush()

    # ----------------------------------------------------------------------- #
    # 3. Historical Claims & Claim-Source Bindings
    # ----------------------------------------------------------------------- #
    for c in claims_data.get("claims", []):
        claim_id_str = c["claim_id"]
        claim_id = uuid5(NAMESPACE_DNS, f"imperial_claim:{claim_id_str}")
        monument_slug = c["monument_slug"]
        entity_id = entity_id_map.get(monument_slug)
        if not entity_id:
            continue

        existing_claim = session.get(HistoricalClaim, claim_id)
        if not existing_claim:
            existing_claim = session.execute(
                select(HistoricalClaim).where(
                    HistoricalClaim.entity_id == entity_id,
                    HistoricalClaim.claim_key == claim_id_str,
                )
            ).scalar_one_or_none()

        if existing_claim:
            existing_claim.claim_type = c.get("claim_type", "historical_evidence")
            existing_claim.statement_vi = c["statement_vi"]
            existing_claim.statement_en = c.get("statement_en")
            existing_claim.confidence = c.get("confidence", "verified")
            existing_claim.verification_status = "verified"
            existing_claim.origin = c.get("evidence_type", "chính sử")
            existing_claim.risk_level = "normal"
            existing_claim.review_notes = c.get("uncertainty_notes")
            existing_claim.content_scope = CONTENT_SCOPE_IMPERIAL
            existing_claim.is_current = True
            claim_rec_id = existing_claim.id
        else:
            new_claim = HistoricalClaim(
                id=claim_id,
                entity_id=entity_id,
                claim_key=claim_id_str,
                claim_type=c.get("claim_type", "historical_evidence"),
                statement_vi=c["statement_vi"],
                statement_en=c.get("statement_en"),
                confidence=c.get("confidence", "verified"),
                verification_status="verified",
                origin=c.get("evidence_type", "chính sử"),
                risk_level="normal",
                review_notes=c.get("uncertainty_notes"),
                content_scope=CONTENT_SCOPE_IMPERIAL,
                is_current=True,
                created_by=curator_id,
            )
            session.add(new_claim)
            session.flush()
            claim_rec_id = new_claim.id

        stats["claims_seeded"] += 1

        # ------------------------------------------------------------------- #
        # 4. Bind Claim to Source in historical_claim_sources
        # ------------------------------------------------------------------- #
        raw_source_id = c.get("source_id")
        resolved_source_uuid = source_uuid_map.get(raw_source_id)
        if resolved_source_uuid:
            support_type = "primary_evidence"
            existing_binding = session.get(
                HistoricalClaimSource,
                {"claim_id": claim_rec_id, "source_id": resolved_source_uuid, "support_type": support_type},
            )
            if not existing_binding:
                existing_binding = session.execute(
                    select(HistoricalClaimSource).where(
                        HistoricalClaimSource.claim_id == claim_rec_id,
                        HistoricalClaimSource.source_id == resolved_source_uuid,
                        HistoricalClaimSource.support_type == support_type,
                    )
                ).scalar_one_or_none()

            if existing_binding:
                existing_binding.locator_type = "page"
                existing_binding.section = c.get("volume")
                existing_binding.page_start = c.get("page_locator")
                existing_binding.editor_note = c.get("uncertainty_notes")
            else:
                new_binding = HistoricalClaimSource(
                    claim_id=claim_rec_id,
                    source_id=resolved_source_uuid,
                    support_type=support_type,
                    locator_type="page",
                    section=c.get("volume"),
                    page_start=c.get("page_locator"),
                    editor_note=c.get("uncertainty_notes"),
                    created_by=curator_id,
                )
                session.add(new_binding)
            stats["claim_sources_seeded"] += 1

    if dry_run:
        session.rollback()
    else:
        session.commit()

    return stats


def seed_extended_sources_from_files(
    db_url: str | None = None,
    dry_run: bool = False,
) -> dict[str, int]:
    """Read JSON source and claims files and execute idempotent seeding."""
    sources_path = REPO_ROOT / "data" / "imperial" / "historical_sources_extended.json"
    claims_path = REPO_ROOT / "data" / "imperial" / "monument_claims_matrix.json"

    if not sources_path.exists():
        raise FileNotFoundError(f"Missing {sources_path}")
    if not claims_path.exists():
        raise FileNotFoundError(f"Missing {claims_path}")

    sources_data = json.loads(sources_path.read_text(encoding="utf-8"))
    claims_data = json.loads(claims_path.read_text(encoding="utf-8"))

    url = db_url or os.environ.get("DATABASE_URL") or DEFAULT_DB_URL
    engine = create_engine(url, pool_pre_ping=True)
    ensure_content_scope_columns(engine)

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with SessionLocal() as session:
        return seed_extended_sources(session, sources_data, claims_data, dry_run=dry_run)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed STTT Imperial City extended historical sources & claims."
    )
    parser.add_argument("--db-url", help="Database connection URL")
    parser.add_argument("--dry-run", action="store_true", help="Validate without committing")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    try:
        stats = seed_extended_sources_from_files(db_url=args.db_url, dry_run=args.dry_run)
        print(f"[SUCCESS] Seeding complete: {stats}")
    except Exception as exc:
        print(f"[ERROR] Seeding failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
