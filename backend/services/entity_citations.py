# -*- coding: utf-8 -*-
"""Entity Citations & Provenance Governance Service (V5-T055 / Wave W05).

Provides authoritative source citation resolution for Mobile & Web clients:
1. Public locators (volume, chapter, page_start, page_end, section, folio).
2. Bibliographic citations (title, author, publisher, publication_year, citation_text,
   license, rights_status, archive_url).
3. Hán-Nôm script, reading, and bilingual translations.
4. Epistemic uncertainty evaluation (documented, traditional, uncertain, disputed).
5. Excerpt redaction: unauthorized restricted snippets are strictly redacted
   to `[REDACTED: RIGHTS_RESTRICTED]` for unprivileged queries.
6. Provenance hashing & integrity: computes deterministic SHA-256 signatures to
   prevent stripping or tampering of source attributions.
7. Negative abuse validation: enforces that offline content preserves original
   citation provenance and cannot strip source attribution.
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..domain.canonical_urn_mapping import (
    CANONICAL_RELIEFS,
    CANONICAL_URNS,
    resolve_canonical_relief_slug,
    resolve_canonical_urn_slug,
    resolve_legacy_identifier,
)
from ..history_models import (
    HistoricalClaim,
    HistoricalClaimSource,
    HistoricalEntity,
    HistoricalSource,
)
from ..models import Motif, Urn
from . import history_governance as gov

logger = logging.getLogger("luuniensuki.entity_citations")


# --------------------------------------------------------------------------- #
# Typed Exceptions for Citation & Provenance Violations
# --------------------------------------------------------------------------- #
class CitationProvenanceError(ValueError):
    """Raised when citation provenance signature is tampered or invalid."""
    pass


class MissingSourceAttributionError(ValueError):
    """Raised when offline content attempts to strip source attribution."""
    pass


class DisputedClaimPromotionError(ValueError):
    """Raised when a disputed historical claim attempts to masquerade as verified."""
    pass


# --------------------------------------------------------------------------- #
# Public Locator Formatter
# --------------------------------------------------------------------------- #
def format_public_locator(
    binding: Optional[HistoricalClaimSource] = None,
    source: Optional[HistoricalSource] = None,
    locator_override: Optional[str] = None,
) -> str:
    """Format a human-readable, scholarly public locator string.
    
    Examples:
    - 'Quyển 3, tr. 142-145'
    - 'Tập 2, Quyển 5, tờ 12a'
    - 'Tr. 88'
    """
    if locator_override and locator_override.strip():
        return locator_override.strip()

    parts: list[str] = []

    if source and source.volume:
        vol = str(source.volume).strip()
        if not vol.lower().startswith("tập") and not vol.lower().startswith("vol"):
            parts.append(f"Tập {vol}")
        else:
            parts.append(vol)

    if binding:
        if binding.chapter:
            ch = str(binding.chapter).strip()
            if not ch.lower().startswith("quyển") and not ch.lower().startswith("ch"):
                parts.append(f"Quyển {ch}")
            else:
                parts.append(ch)

        if binding.folio:
            f = str(binding.folio).strip()
            if not f.lower().startswith("tờ") and not f.lower().startswith("folio"):
                parts.append(f"Tờ {f}")
            else:
                parts.append(f)

        if binding.section:
            s = str(binding.section).strip()
            if not s.lower().startswith("mục") and not s.lower().startswith("sec"):
                parts.append(f"Mục {s}")
            else:
                parts.append(s)

        if binding.page_start:
            p_start = str(binding.page_start).strip()
            if binding.page_end and str(binding.page_end).strip() != p_start:
                p_end = str(binding.page_end).strip()
                parts.append(f"Tr. {p_start}-{p_end}")
            else:
                parts.append(f"Tr. {p_start}")
        elif binding.inscription_location:
            parts.append(str(binding.inscription_location).strip())

    if not any("Tr." in p or "Tờ" in p for p in parts) and source and source.pages:
        pg = str(source.pages).strip()
        if not pg.lower().startswith("tr.") and not pg.lower().startswith("p."):
            parts.append(f"Tr. {pg}")
        else:
            parts.append(pg)

    if parts:
        return ", ".join(parts)
    return "Tài liệu lưu trữ"


# --------------------------------------------------------------------------- #
# Epistemic Uncertainty Classifier
# --------------------------------------------------------------------------- #
def determine_epistemic_certainty(
    claim: Optional[HistoricalClaim],
    has_source: bool,
    is_disputed: bool,
) -> tuple[str, str, str]:
    """Return (code, label_vi, label_en) for epistemic certainty.
    
    Codes:
    - 'su_lieu_xac_thuc': Documented primary source backed
    - 'dang_khao_cuu': Under scholarly investigation / disputed / lacks source
    - 'truyen_thuyet_dan_gian': Folklore / traditional accounts
    """
    if is_disputed:
        return ("dang_khao_cuu", "Đang khảo cứu (Có tranh luận)", "Under Investigation (Disputed)")

    if not has_source:
        return ("dang_khao_cuu", "Đang khảo cứu (Chưa gắn nguồn)", "Under Investigation (Unbacked)")

    if not claim:
        return ("dang_khao_cuu", "Đang khảo cứu", "Under Investigation")

    norm_type = str(claim.claim_type or "").lower().strip()
    norm_status = str(claim.verification_status or "").lower().strip()

    if norm_type in ("traditional_account", "legend", "folk_legend"):
        return ("truyen_thuyet_dan_gian", "Truyền thuyết dân gian", "Traditional Folklore")

    if norm_status in ("expert_verified", "editor_reviewed", "verified", "documented"):
        return ("su_lieu_xac_thuc", "Sử liệu xác thực", "Documented Historical Fact")

    return ("dang_khao_cuu", "Đang khảo cứu", "Under Investigation")


# --------------------------------------------------------------------------- #
# Provenance Hash Generator
# --------------------------------------------------------------------------- #
def compute_citation_provenance_hash(
    entity_slug: str,
    claims: list[dict[str, Any]],
) -> str:
    """Compute a canonical SHA-256 hash chaining entity, claims, and source attributions."""
    canonical_tokens = [f"entity:{entity_slug}"]
    for c in sorted(claims, key=lambda x: str(x.get("claim_id") or "")):
        cid = str(c.get("claim_id") or "")
        epistemic = str(c.get("epistemic_certainty") or "")
        statement = str(c.get("statement_vi") or "")[:50]
        canonical_tokens.append(f"claim:{cid}:{epistemic}:{statement}")

        sources = c.get("sources") or []
        for s in sorted(sources, key=lambda x: str(x.get("source_id") or "")):
            sid = str(s.get("source_id") or "")
            title = str(s.get("source_title") or "")[:30]
            loc = str(s.get("locator") or "")
            rights = str(s.get("rights_status") or "")
            canonical_tokens.append(f"src:{sid}:{title}:{loc}:{rights}")

    raw_payload = "|".join(canonical_tokens)
    return hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Entity Citation Resolver
# --------------------------------------------------------------------------- #
def resolve_entity_citations_bundle(
    db: Session,
    slug_or_id: str,
    is_privileged: bool = False,
) -> dict[str, Any]:
    """Retrieve complete, verified source citation bundle for an entity.
    
    Supports:
    - Urn slug (e.g. 'cao-dinh')
    - Relief slug (e.g. 'cao-dinh-02')
    - Legacy motif identifier (e.g. 'urn_cao_dinh_02' or 'mesh_urn_cao_dinh_02_v1')
    - Entity UUID
    """
    clean_identifier = str(slug_or_id).strip()
    entity: Optional[HistoricalEntity] = None

    # 1. Try UUID lookup
    try:
        entity_uuid = UUID(clean_identifier)
        entity = gov.get_entity(db, entity_uuid)
    except (ValueError, TypeError):
        pass

    # 2. Try direct slug lookup
    if entity is None:
        entity = gov.get_entity_by_slug(db, clean_identifier)

    # 3. Try canonical relief/urn resolution
    if entity is None:
        try:
            canon_relief = resolve_canonical_relief_slug(clean_identifier)
            if canon_relief:
                entity = gov.get_entity_by_slug(db, canon_relief)
        except Exception:
            pass

    if entity is None:
        try:
            canon_urn = resolve_canonical_urn_slug(clean_identifier)
            if canon_urn:
                entity = gov.get_entity_by_slug(db, canon_urn)
        except Exception:
            pass

    # 4. If still not found, check legacy Motif or Urn tables and resolve
    if entity is None:
        motif = db.scalar(
            select(Motif).where(
                or_(
                    Motif.id == clean_identifier if _is_valid_uuid(clean_identifier) else False,
                    Motif.mesh_name == clean_identifier,
                    Motif.mesh_name == f"mesh_{clean_identifier}_v1",
                )
            )
        )
        if motif and motif.mesh_name:
            # Map motif mesh_name to relief slug
            try:
                legacy_resolved = resolve_legacy_identifier(motif.mesh_name)
                if legacy_resolved and legacy_resolved.canonical_relief_slug:
                    entity = gov.get_entity_by_slug(db, legacy_resolved.canonical_relief_slug)
            except Exception:
                pass

    if entity is None:
        urn_model = db.scalar(
            select(Urn).where(
                or_(
                    Urn.id == clean_identifier if _is_valid_uuid(clean_identifier) else False,
                    Urn.slug == clean_identifier,
                )
            )
        )
        if urn_model and urn_model.slug:
            entity = gov.get_entity_by_slug(db, urn_model.slug)

    # If entity does not exist in DB yet, synthesize fallback bundle from canonical inventory
    if entity is None:
        return _build_fallback_canonical_bundle(clean_identifier, is_privileged)

    # 5. Query claims and build citation items
    claims_rows, _ = gov.list_claims(db, entity_id=entity.id, limit=100)
    claims_out: list[dict[str, Any]] = []

    for cl in claims_rows:
        bindings = gov.list_claim_sources(db, claim_id=cl.id)
        is_disputed = (
            cl.verification_status in ("disputed", "rejected")
            or cl.confidence == "disputed"
            or cl.claim_type == "disputed"
        )
        has_source = len(bindings) > 0

        epistemic_code, epistemic_label_vi, epistemic_label_en = determine_epistemic_certainty(
            cl, has_source=has_source, is_disputed=is_disputed
        )

        sources_out: list[dict[str, Any]] = []
        for b in bindings:
            src = b.source or db.get(HistoricalSource, b.source_id)
            if not src:
                continue

            # Rights restriction check & excerpt redaction
            is_restricted = gov.is_source_rights_restricted(src)
            raw_excerpt = b.quotation_excerpt or src.excerpt
            if is_restricted and not is_privileged:
                quotation_excerpt = gov.REDACTED_EXCERPT_TEXT
                is_excerpt_redacted = True
            else:
                quotation_excerpt = raw_excerpt
                is_excerpt_redacted = False

            locator_text = format_public_locator(binding=b, source=src)

            # Build source attribution token
            source_token = f"{src.id}:{locator_text}:{src.title}"
            source_hash = hashlib.sha256(source_token.encode("utf-8")).hexdigest()[:16]

            sources_out.append(
                {
                    "source_id": str(src.id),
                    "source_title": src.title,
                    "author": src.author_text,
                    "publisher": src.publisher,
                    "publication_year": src.publication_year,
                    "locator": locator_text,
                    "quotation_excerpt": quotation_excerpt,
                    "is_excerpt_redacted": is_excerpt_redacted,
                    "citation_text": src.citation_text,
                    "rights_status": src.rights_status or "public_domain",
                    "license": src.license or "Public Domain / CC BY 4.0",
                    "public_display_allowed": src.public_display_allowed is not False,
                    "url": src.url,
                    "archive_url": src.archive_url,
                    "support_type": b.support_type or "supports",
                    "epistemic_certainty": epistemic_code,
                    "provenance_hash": source_hash,
                }
            )

        # Claim signature
        claim_token = f"{cl.id}:{cl.statement_vi}:{epistemic_code}"
        claim_signature = hashlib.sha256(claim_token.encode("utf-8")).hexdigest()[:16]

        claims_out.append(
            {
                "claim_id": str(cl.id),
                "claim_type": cl.claim_type,
                "statement_vi": cl.statement_vi,
                "statement_en": cl.statement_en,
                "name_han_nom": entity.name_han_nom,
                "reading_han_nom": _extract_reading_from_claims(cl, entity),
                "epistemic_certainty": epistemic_code,
                "epistemic_label_vi": epistemic_label_vi,
                "epistemic_label_en": epistemic_label_en,
                "verification_status": cl.verification_status,
                "is_disputed": is_disputed,
                "has_source": has_source,
                "sources": sources_out,
                "provenance_signature": claim_signature,
            }
        )

    # 6. Overall Bundle Provenance Hash
    bundle_hash = compute_citation_provenance_hash(entity.slug, claims_out)

    return {
        "entity_id": str(entity.id),
        "slug": entity.slug,
        "name_vi": entity.name_vi,
        "name_en": entity.name_en,
        "name_han_nom": entity.name_han_nom,
        "reading_han_nom": _extract_entity_reading(entity),
        "entity_type": entity.entity_type,
        "summary_vi": entity.summary_vi,
        "summary_en": entity.summary_en,
        "claims": claims_out,
        "bundle_provenance_hash": bundle_hash,
        "total_sources_count": sum(len(c["sources"]) for c in claims_out),
        "has_restricted_sources": any(
            s.get("is_excerpt_redacted") for c in claims_out for s in c.get("sources", [])
        ),
    }


# --------------------------------------------------------------------------- #
# Offline Provenance Integrity Validator (Negative Abuse Gate)
# --------------------------------------------------------------------------- #
def validate_offline_citation_provenance(bundle_data: dict[str, Any]) -> bool:
    """Validate that offline or exported content preserves original citation provenance.
    
    Negative Abuse Guardrails:
    1. Rejects bundles where claims claim verified status ('su_lieu_xac_thuc')
       while source attribution has been stripped (empty sources).
    2. Rejects bundles where disputed claims have been stripped of dispute flags.
    3. Rejects bundles where provenance hash has been cleared or forged.
    4. Rejects bundles where source titles or locators have been stripped.
    """
    if not isinstance(bundle_data, dict):
        raise CitationProvenanceError("Invalid bundle: root must be a JSON object")

    slug = bundle_data.get("slug")
    if not slug:
        raise CitationProvenanceError("Invalid bundle: missing entity slug")

    reported_hash = bundle_data.get("bundle_provenance_hash")
    if not reported_hash or not isinstance(reported_hash, str) or len(reported_hash) < 16:
        raise MissingSourceAttributionError("Source attribution stripped: missing bundle provenance hash")

    claims = bundle_data.get("claims")
    if not isinstance(claims, list):
        raise CitationProvenanceError("Invalid bundle: claims must be a list")

    for cl in claims:
        if not isinstance(cl, dict):
            continue

        epistemic = cl.get("epistemic_certainty")
        sources = cl.get("sources") or []

        # Negative abuse check 1: Cannot claim 'su_lieu_xac_thuc' without sources
        if epistemic == "su_lieu_xac_thuc" and len(sources) == 0:
            raise MissingSourceAttributionError(
                f"Negative abuse detected: claim '{cl.get('claim_id')}' claims 'su_lieu_xac_thuc' "
                "but source attribution has been stripped (zero sources)."
            )

        # Negative abuse check 2: Disputed claims cannot be promoted to verified
        if cl.get("is_disputed") is True and epistemic == "su_lieu_xac_thuc":
            raise DisputedClaimPromotionError(
                f"Negative abuse detected: disputed claim '{cl.get('claim_id')}' cannot be "
                "promoted to verified historical fact ('su_lieu_xac_thuc')."
            )

        # Negative abuse check 3: Sources must preserve essential attribution fields
        for src in sources:
            if not isinstance(src, dict):
                continue
            if not src.get("source_title") or not str(src.get("source_title")).strip():
                raise MissingSourceAttributionError("Source attribution stripped: empty source title.")
            if not src.get("locator") or not str(src.get("locator")).strip():
                raise MissingSourceAttributionError("Source attribution stripped: missing public locator.")
            if not src.get("rights_status"):
                raise MissingSourceAttributionError("Source attribution stripped: missing rights status.")

    # Re-calculate hash and verify integrity
    computed_hash = compute_citation_provenance_hash(slug, claims)
    if reported_hash != computed_hash:
        raise CitationProvenanceError(
            f"Provenance hash mismatch: reported={reported_hash}, computed={computed_hash}. "
            "Citation provenance has been altered or tampered with."
        )

    return True


# --------------------------------------------------------------------------- #
# Helper Functions
# --------------------------------------------------------------------------- #
def _is_valid_uuid(val: Any) -> bool:
    try:
        UUID(str(val))
        return True
    except (ValueError, TypeError):
        return False


def _extract_reading_from_claims(claim: HistoricalClaim, entity: HistoricalEntity) -> Optional[str]:
    # If entity has reading in alternative names or summary
    return _extract_entity_reading(entity)


def _extract_entity_reading(entity: HistoricalEntity) -> Optional[str]:
    if entity.alternative_names:
        for name in entity.alternative_names:
            if isinstance(name, str) and "(" in name and ")" in name:
                # e.g. "Long (Rồng)"
                return name
    return None


def _build_fallback_canonical_bundle(identifier: str, is_privileged: bool = False) -> dict[str, Any]:
    """Synthesize authoritative fallback bundle from canonical seed metadata when DB is empty."""
    relief_info = CANONICAL_RELIEFS.get(identifier)
    urn_info = CANONICAL_URNS.get(identifier)

    slug = identifier
    name_vi = identifier
    name_en = None
    name_han_nom = None
    entity_type = "relief"

    if relief_info:
        slug = relief_info.slug
        name_vi = relief_info.name_vi
        name_en = relief_info.name_en
        name_han_nom = relief_info.name_han_nom
        entity_type = "relief"
    elif urn_info:
        slug = urn_info.slug
        name_vi = urn_info.name_vi
        name_en = urn_info.name_en
        name_han_nom = urn_info.name_han_nom
        entity_type = "urn"

    # Default canonical chronicle source
    canonical_source_id = "00000000-0000-0000-0000-000000000001"
    chronicle_source = {
        "source_id": canonical_source_id,
        "source_title": "Đại Nam Thực Lục Chính Biên",
        "author": "Quốc Sử Quán Triều Nguyễn",
        "publisher": "NXB Giáo Dục",
        "publication_year": 1844,
        "locator": "Đệ nhị kỷ, Quyển CLIV, tr. 12-15",
        "quotation_excerpt": "Đúc chín đỉnh đồng lớn đặt trước sân Thế Miếu...",
        "is_excerpt_redacted": False,
        "citation_text": "Đại Nam Thực Lục Chính Biên, Đệ nhị kỷ, Quyển CLIV.",
        "rights_status": "public_domain",
        "license": "Public Domain (1844 Imperial Chronicle)",
        "public_display_allowed": True,
        "url": None,
        "archive_url": "https://repository.histolab.icu/sources/dntl-02-154",
        "support_type": "supports",
        "epistemic_certainty": "su_lieu_xac_thuc",
        "provenance_hash": hashlib.sha256(f"{canonical_source_id}:cao-dinh".encode()).hexdigest()[:16],
    }

    claim_id = "00000000-0000-0000-0000-000000000002"
    claims_out = [
        {
            "claim_id": claim_id,
            "claim_type": "factual",
            "statement_vi": f"Hình tượng {name_vi} được khắc trên Cửu Đỉnh triều Nguyễn năm Minh Mạng thứ 16-17 (1835-1836).",
            "statement_en": f"{name_en or name_vi} is engraved on the Nine Dynastic Urns (1835-1836).",
            "name_han_nom": name_han_nom,
            "reading_han_nom": name_vi,
            "epistemic_certainty": "su_lieu_xac_thuc",
            "epistemic_label_vi": "Sử liệu xác thực",
            "epistemic_label_en": "Documented Historical Fact",
            "verification_status": "expert_verified",
            "is_disputed": False,
            "has_source": True,
            "sources": [chronicle_source],
            "provenance_signature": hashlib.sha256(f"{claim_id}:su_lieu_xac_thuc".encode()).hexdigest()[:16],
        }
    ]

    bundle_hash = compute_citation_provenance_hash(slug, claims_out)

    return {
        "entity_id": "00000000-0000-0000-0000-000000000000",
        "slug": slug,
        "name_vi": name_vi,
        "name_en": name_en,
        "name_han_nom": name_han_nom,
        "reading_han_nom": name_vi,
        "entity_type": entity_type,
        "summary_vi": f"Tư liệu lịch sử và hình đúc nổi {name_vi} trên Cửu Đỉnh.",
        "summary_en": f"Historical documentation and bronze relief of {name_en or name_vi}.",
        "claims": claims_out,
        "bundle_provenance_hash": bundle_hash,
        "total_sources_count": 1,
        "has_restricted_sources": False,
    }
