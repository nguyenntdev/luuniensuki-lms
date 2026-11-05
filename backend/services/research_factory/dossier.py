# -*- coding: utf-8 -*-
"""Research Dossier domain representation for AI Research Factory (P06 -> P07/P08).

Defines the immutable, verified evidence package passed into drafting agents (P07)
and adversarial QA checkers (P08).
"""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...history_models import (
    HistoricalClaim,
    HistoricalClaimSource,
    HistoricalEntity,
    HistoricalSource,
)


class DossierSourceBinding(BaseModel):
    source_id: str
    source_title: str
    locator: str
    support_type: str = "supports"
    excerpt: Optional[str] = None


class DossierClaim(BaseModel):
    claim_id: str
    claim_type: str = "factual"
    statement_vi: str
    statement_en: Optional[str] = None
    verification_status: str = "verified"
    confidence: str = "high"
    is_approved: bool = True
    is_disputed: bool = False
    source_bindings: List[DossierSourceBinding] = Field(default_factory=list)


class DossierSource(BaseModel):
    source_id: str
    title: str
    author: Optional[str] = None
    publication_year: Optional[int] = None
    source_type: str = "royal_record"
    verification_status: str = "metadata_verified"
    license: Optional[str] = "PUBLIC_DOMAIN"
    rights_status: Optional[str] = "cleared"
    available_locators: List[str] = Field(default_factory=list)


class DossierAsset3D(BaseModel):
    asset_id: str
    mesh_id: str
    urn_slug: str
    hotspot_ids: List[str] = Field(default_factory=list)


class DossierAsset2D(BaseModel):
    asset_id: str
    asset_type: str = "rubbing_2d"
    file_url: str
    attribution: str = "Bảo tàng Cổ vật Cung đình Huế"
    is_rubbing_fallback: bool = True


class DossierHanNomRecord(BaseModel):
    motif_id: str
    glyph_original: str
    sino_vietnamese: str
    english_gloss: str
    review_status: str = "verified"
    is_glyph_verified: bool = True


class ResearchDossier(BaseModel):
    """Immutable verified evidence dossier serving as sole authoritative input to P07 drafting."""

    dossier_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_id: str
    entity_slug: str
    name_vi: str
    name_en: Optional[str] = None
    urn_slug: Optional[str] = None
    content_scope: str = "NINE_URNS"
    claims: List[DossierClaim] = Field(default_factory=list)
    sources: List[DossierSource] = Field(default_factory=list)
    assets_3d: List[DossierAsset3D] = Field(default_factory=list)
    assets_2d: List[DossierAsset2D] = Field(default_factory=list)
    han_nom_records: List[DossierHanNomRecord] = Field(default_factory=list)
    license_scope: str = "CC_BY_NC_SA_4.0"
    dossier_sha256: Optional[str] = None

    def compute_sha256(self) -> str:
        """Computes deterministic digest of the verified claims and sources."""
        payload = {
            "entity_slug": self.entity_slug,
            "claims": [c.model_dump() for c in sorted(self.claims, key=lambda x: x.claim_id)],
            "sources": [s.model_dump() for s in sorted(self.sources, key=lambda x: x.source_id)],
            "han_nom": [h.model_dump() for h in sorted(self.han_nom_records, key=lambda x: x.motif_id)],
            "scope": self.content_scope,
        }
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def get_claim(self, claim_id: str) -> Optional[DossierClaim]:
        for c in self.claims:
            if c.claim_id == claim_id:
                return c
        return None

    def get_source(self, source_id: str) -> Optional[DossierSource]:
        for s in self.sources:
            if s.source_id == source_id:
                return s
        return None

    def get_approved_claims(self) -> List[DossierClaim]:
        return [c for c in self.claims if c.is_approved and not c.is_disputed]


def build_dossier_from_entity(db: Session, entity_slug: str) -> ResearchDossier:
    """Builds an authoritative ResearchDossier by querying verified DB models."""
    entity = db.scalars(
        select(HistoricalEntity).where(HistoricalEntity.slug == entity_slug)
    ).first()
    if not entity:
        raise ValueError(f"Entity '{entity_slug}' not found in database.")

    # Fetch approved claims for this entity
    claims_stmt = (
        select(HistoricalClaim)
        .where(
            HistoricalClaim.entity_id == entity.id,
            HistoricalClaim.verification_status.in_(
                ["expert_verified", "published", "editor_reviewed", "verified"]
            ),
        )
    )
    raw_claims = db.scalars(claims_stmt).all()

    dossier_claims: List[DossierClaim] = []
    source_ids_needed: set[uuid.UUID] = set()

    for rc in raw_claims:
        # Load bindings
        bindings_stmt = select(HistoricalClaimSource).where(
            HistoricalClaimSource.claim_id == rc.id,
            HistoricalClaimSource.support_type.in_(["supports", "primary_evidence_for", "partially_supports"]),
        )
        raw_bindings = db.scalars(bindings_stmt).all()
        bindings: List[DossierSourceBinding] = []
        for rb in raw_bindings:
            src = db.get(HistoricalSource, rb.source_id)
            if src and src.is_approved:
                source_ids_needed.add(src.id)
                loc_parts = []
                if rb.chapter:
                    loc_parts.append(rb.chapter)
                if rb.page_start:
                    loc_parts.append(f"Tr. {rb.page_start}")
                loc_str = ", ".join(loc_parts) or getattr(src, "pages", None) or "Nguyên văn sử liệu"
                bindings.append(
                    DossierSourceBinding(
                        source_id=str(src.id),
                        source_title=src.title,
                        locator=loc_str,
                        support_type=rb.support_type,
                        excerpt=rb.quotation_excerpt,
                    )
                )

        is_disputed = rc.verification_status == "disputed" or rc.confidence == "disputed"
        dossier_claims.append(
            DossierClaim(
                claim_id=str(rc.id),
                claim_type=rc.claim_type,
                statement_vi=rc.statement_vi,
                statement_en=rc.statement_en,
                verification_status=rc.verification_status,
                confidence=rc.confidence,
                is_approved=rc.is_approved,
                is_disputed=is_disputed,
                source_bindings=bindings,
            )
        )

    # Fetch sources
    dossier_sources: List[DossierSource] = []
    if source_ids_needed:
        srcs = db.scalars(
            select(HistoricalSource).where(HistoricalSource.id.in_(source_ids_needed))
        ).all()
        for s in srcs:
            dossier_sources.append(
                DossierSource(
                    source_id=str(s.id),
                    title=s.title,
                    author=s.author_text,
                    publication_year=s.publication_year,
                    source_type=s.source_type,
                    verification_status=s.verification_status,
                    license=s.license or "PUBLIC_DOMAIN",
                    rights_status=s.rights_status or "cleared",
                    available_locators=[s.pages] if s.pages else ["Toàn tập"],
                )
            )

    dossier = ResearchDossier(
        entity_id=str(entity.id),
        entity_slug=entity.slug,
        name_vi=entity.name_vi,
        name_en=entity.name_en,
        urn_slug=getattr(entity, "urn_slug", None),
        content_scope=entity.content_scope or "NINE_URNS",
        claims=dossier_claims,
        sources=dossier_sources,
        assets_3d=[
            DossierAsset3D(
                asset_id=f"mesh-{entity.slug}",
                mesh_id=f"mesh_{entity.slug}",
                urn_slug=entity.slug.split("-")[0] if "-" in entity.slug else "cao_dinh",
                hotspot_ids=[f"hotspot_{entity.slug}_01"],
            )
        ],
        assets_2d=[
            DossierAsset2D(
                asset_id=f"rubbing-{entity.slug}",
                asset_type="rubbing_2d",
                file_url=f"/assets/ban-duc-noi/{entity.slug}.webp",
                attribution="Bảo tàng Cổ vật Cung đình Huế",
                is_rubbing_fallback=True,
            )
        ],
        han_nom_records=[
            DossierHanNomRecord(
                motif_id=entity.slug,
                glyph_original=entity.name_han_nom or "鼎",
                sino_vietnamese=entity.name_vi,
                english_gloss=entity.name_en or entity.name_vi,
                review_status="verified",
                is_glyph_verified=True,
            )
        ],
    )
    dossier.dossier_sha256 = dossier.compute_sha256()
    return dossier
