# -*- coding: utf-8 -*-
"""Canonical Heritage Catalog Service (Cửu Đỉnh 9 Urns & 162 Motifs).

Enforces:
1. Strict 9 Urns & 162 Motifs canonical parity between web and mobile platforms.
2. Canonical object IDs (stable IDs: urn_cao_dinh_01..18, slugs: cao-dinh-01..18).
3. Evidence status labels matching web platform: verified, needs_review, disputed, rejected.
   - The 4 known incomplete motifs (urn_nghi_dinh_03, urn_thuan_dinh_13, urn_tuyen_dinh_11,
     urn_huyen_dinh_12) strictly default to 'needs_review'.
   - All other canonical motifs default to 'verified'.
4. Approved revision versioning and ETag cryptographic hash calculation for HTTP conditional caching (304 Not Modified).
5. Anti-drift protection: Server revision updates strictly invalidate old ETags so clients refresh to latest approved data.
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

from ..apischemas.heritage import (
    HeritageCatalogMotifOut,
    HeritageCatalogOut,
    HeritageCatalogUrnOut,
    HeritageEvidenceStatus,
)
from ..domain.canonical_urn_mapping import (
    CANONICAL_RELIEFS,
    CANONICAL_RELIEF_SLUGS,
    CANONICAL_URNS,
    CANONICAL_URN_SLUGS,
    CrossUrnMisassignmentError,
    MOTIFS_PER_URN,
    STABLE_MOTIF_IDS,
    TOTAL_MOTIFS,
    TOTAL_URNS,
    resolve_canonical_motif_id,
    resolve_canonical_relief_slug,
    resolve_canonical_urn_slug,
    resolve_legacy_identifier,
)
from ..domain.han_nom_review import KNOWN_MISSING_HAN_NOM_MOTIF_IDS
from ..errors import AppError

logger = logging.getLogger("luuniensuki.heritage_catalog")

CATALOG_VERSION: str = "v1.0"

# In-memory revision and editorial overlay store
# Key: canonical identifier (urn slug or motif stable_id)
# Value: dict of overridden attributes (e.g. revision, evidence_status, name_vi, notes)
_REVISION_OVERLAYS: Dict[str, Dict[str, Any]] = {}
_GLOBAL_CATALOG_REVISION: int = 1


def reset_catalog_revisions() -> None:
    """Reset all revision overlays back to canonical baseline (for test isolation)."""
    global _REVISION_OVERLAYS, _GLOBAL_CATALOG_REVISION
    _REVISION_OVERLAYS.clear()
    _GLOBAL_CATALOG_REVISION = 1


def get_global_revision() -> int:
    """Return the current global catalog revision sequence."""
    return _GLOBAL_CATALOG_REVISION


def update_catalog_revision(
    identifier: str,
    *,
    revision: Optional[int] = None,
    evidence_status: Optional[str] = None,
    name_vi: Optional[str] = None,
    name_en: Optional[str] = None,
    name_han_nom: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Apply an approved editorial revision update to a canonical urn or motif.

    Bumps the global catalog revision and returns the updated entity payload.
    """
    global _GLOBAL_CATALOG_REVISION

    # Use canonical domain resolver to distinguish urn vs relief
    is_urn = False
    try:
        resolved = resolve_legacy_identifier(identifier)
        if resolved["entity_type"] == "urn":
            target_key = resolved["canonical_slug"]
            is_urn = True
        else:
            target_key = resolved["stable_id"]
    except Exception:
        raise AppError(
            "CANONICAL_ENTITY_NOT_FOUND",
            f"Identifier '{identifier}' could not be resolved to any canonical Urn or Motif.",
            404,
        )

    current_overlay = _REVISION_OVERLAYS.get(target_key, {})
    current_rev = current_overlay.get("revision", 1)
    new_rev = revision if revision is not None else current_rev + 1

    updates: Dict[str, Any] = {
        "revision": new_rev,
    }
    if evidence_status is not None:
        # Validate evidence status against controlled vocabulary
        if evidence_status not in [e.value for e in HeritageEvidenceStatus]:
            raise AppError(
                "INVALID_EVIDENCE_STATUS",
                f"Invalid evidence status '{evidence_status}'. Must be one of: {[e.value for e in HeritageEvidenceStatus]}",
                400,
            )
        updates["evidence_status"] = evidence_status

    if name_vi is not None:
        updates["name_vi"] = name_vi
    if name_en is not None:
        updates["name_en"] = name_en
    if name_han_nom is not None:
        updates["name_han_nom"] = name_han_nom
    if notes is not None:
        updates["reviewer_notes"] = notes

    current_overlay.update(updates)
    _REVISION_OVERLAYS[target_key] = current_overlay

    _GLOBAL_CATALOG_REVISION += 1

    logger.info(
        "Updated catalog revision for %s: revision=%d global_revision=%d",
        target_key,
        new_rev,
        _GLOBAL_CATALOG_REVISION,
    )
    return current_overlay


def _build_motif_out(stable_id: str) -> HeritageCatalogMotifOut:
    """Construct HeritageCatalogMotifOut from canonical metadata and revision overlays."""
    relief_info = STABLE_MOTIF_IDS.get(stable_id)
    if not relief_info:
        relief_info = CANONICAL_RELIEFS.get(stable_id)
    if not relief_info:
        raise AppError(
            "MOTIF_NOT_FOUND",
            f"Motif stable_id '{stable_id}' not found in canonical dataset",
            404,
        )

    overlay = _REVISION_OVERLAYS.get(stable_id, {})

    # Epistemic default: the 4 known incomplete motifs default to needs_review
    if stable_id in KNOWN_MISSING_HAN_NOM_MOTIF_IDS:
        default_status = HeritageEvidenceStatus.needs_review
    else:
        default_status = HeritageEvidenceStatus.verified

    status_val = overlay.get("evidence_status", default_status.value)
    if isinstance(status_val, HeritageEvidenceStatus):
        evidence_status = status_val
    else:
        evidence_status = HeritageEvidenceStatus(status_val)

    revision = overlay.get("revision", 1)
    name_vi = overlay.get("name_vi", relief_info.name_vi)
    name_en = overlay.get("name_en", relief_info.name_en)
    name_han_nom = overlay.get("name_han_nom", relief_info.name_han_nom)

    # Standard thumbnail URL
    urn_folder = relief_info.urn_slug.upper().replace("-", " ")
    thumbnail_url = f"/assets/ban-duc-noi/{urn_folder}/{relief_info.mesh_name}.jpg"

    return HeritageCatalogMotifOut(
        id=relief_info.stable_id,
        slug=relief_info.slug,
        urn_slug=relief_info.urn_slug,
        order=relief_info.order,
        name_vi=name_vi,
        name_en=name_en,
        name_han_nom=name_han_nom,
        category=relief_info.category,
        rarity=relief_info.rarity,
        mesh_name=relief_info.mesh_name,
        pos_x=relief_info.pos_x,
        pos_y=relief_info.pos_y,
        pos_z=relief_info.pos_z,
        bounding_radius=relief_info.bounding_radius or 0.08,
        evidence_status=evidence_status,
        revision=revision,
        thumbnail_url=thumbnail_url,
    )


def _build_urn_out(urn_slug: str, include_motifs: bool = True) -> HeritageCatalogUrnOut:
    """Construct HeritageCatalogUrnOut from canonical metadata and revision overlays."""
    if urn_slug not in CANONICAL_URNS:
        raise AppError("URN_NOT_FOUND", f"Urn slug '{urn_slug}' not found in canonical dataset", 404)

    urn_info = CANONICAL_URNS[urn_slug]
    overlay = _REVISION_OVERLAYS.get(urn_slug, {})

    revision = overlay.get("revision", 1)
    name_vi = overlay.get("name_vi", urn_info.name_vi)
    name_en = overlay.get("name_en", urn_info.name_en)
    name_han_nom = overlay.get("name_han_nom", urn_info.name_han_nom)

    status_val = overlay.get("evidence_status", HeritageEvidenceStatus.verified.value)
    evidence_status = (
        status_val if isinstance(status_val, HeritageEvidenceStatus) else HeritageEvidenceStatus(status_val)
    )

    motifs: List[HeritageCatalogMotifOut] = []
    if include_motifs:
        # Find all 18 canonical motifs for this urn sorted by order
        for relief in STABLE_MOTIF_IDS.values():
            if relief.urn_slug == urn_slug:
                motifs.append(_build_motif_out(relief.stable_id))
        motifs.sort(key=lambda m: m.order)

    thumbnail_url = f"/assets/ban-duc-noi/{urn_slug.upper().replace('-', ' ')}/{urn_slug}.jpg"
    model_3d = f"/models/{urn_info.model_3d}"

    return HeritageCatalogUrnOut(
        id=urn_info.slug,
        slug=urn_info.slug,
        order=urn_info.order,
        name_vi=name_vi,
        name_en=name_en,
        name_han_nom=name_han_nom,
        reign_title=urn_info.reign_title,
        temple_name=urn_info.temple_name,
        motif_count=MOTIFS_PER_URN,
        model_3d=model_3d,
        evidence_status=evidence_status,
        revision=revision,
        thumbnail_url=thumbnail_url,
        motifs=motifs,
    )


def get_canonical_motif(identifier: str) -> HeritageCatalogMotifOut:
    """Retrieve a single canonical motif by slug, stable ID, or alias."""
    stable_id = resolve_canonical_motif_id(identifier)
    if not stable_id:
        raise AppError("MOTIF_NOT_FOUND", f"Motif identifier '{identifier}' not found in canonical dataset", 404)

    return _build_motif_out(stable_id)


def get_canonical_urn(urn_slug: str, include_motifs: bool = True) -> HeritageCatalogUrnOut:
    """Retrieve a single canonical urn with its 18 motifs."""
    canonical_slug = resolve_canonical_urn_slug(urn_slug)
    if not canonical_slug or canonical_slug not in CANONICAL_URNS:
        raise AppError("URN_NOT_FOUND", f"Urn slug '{urn_slug}' not found in canonical dataset", 404)

    return _build_urn_out(canonical_slug, include_motifs=include_motifs)


def compute_catalog_etag(urns: List[HeritageCatalogUrnOut], global_rev: int) -> str:
    """Compute a deterministic strong ETag from the serialized canonical catalog state."""
    hasher = hashlib.sha256()
    hasher.update(CATALOG_VERSION.encode("utf-8"))
    hasher.update(str(global_rev).encode("utf-8"))

    for u in urns:
        u_token = f"{u.slug}:{u.revision}:{u.evidence_status}:{u.name_vi}"
        hasher.update(u_token.encode("utf-8"))
        for m in u.motifs:
            m_token = f"{m.id}:{m.revision}:{m.evidence_status}:{m.name_vi}:{m.pos_x}:{m.pos_y}:{m.pos_z}"
            hasher.update(m_token.encode("utf-8"))

    digest = hasher.hexdigest()[:32]
    return f'"{digest}"'


def get_canonical_catalog(
    *,
    urn_slug: Optional[str] = None,
    include_motifs: bool = True,
) -> HeritageCatalogOut:
    """Build the complete canonical catalog payload for 9 Urns and 162 Motifs."""
    if urn_slug is not None:
        canonical_slug = resolve_canonical_urn_slug(urn_slug)
        if not canonical_slug or canonical_slug not in CANONICAL_URNS:
            raise AppError("URN_NOT_FOUND", f"Urn slug '{urn_slug}' not found in canonical dataset", 404)
        urn_slugs = [canonical_slug]
    else:
        urn_slugs = list(CANONICAL_URN_SLUGS)

    urns_out: List[HeritageCatalogUrnOut] = []
    for slug in urn_slugs:
        urns_out.append(_build_urn_out(slug, include_motifs=include_motifs))

    urns_out.sort(key=lambda u: u.order)

    global_rev = get_global_revision()
    etag = compute_catalog_etag(urns_out, global_rev)

    return HeritageCatalogOut(
        catalog_version=CATALOG_VERSION,
        total_urns=len(urns_out),
        total_motifs=sum(len(u.motifs) for u in urns_out) if include_motifs else TOTAL_MOTIFS,
        global_revision=global_rev,
        etag=etag,
        urns=urns_out,
    )
