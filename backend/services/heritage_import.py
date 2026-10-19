# -*- coding: utf-8 -*-
"""Heritage Knowledge Catalogue Ingestion & Synchronization Service (LƯU NIÊN — RBPC 2026).

Imports and synchronizes:
1. data/heritage-hue/inventory.unesco-14.yaml
   - 14 official UNESCO World Heritage components (Property 678: 678-001..678-014)
   - 6 priority child monuments (enclosed inside Kinh thành Huế)
   - 3 traditional craft communities (living artisanal heritage)
2. data/heritage-hue/sketchfab-curated.yaml
   - 23 curated Sketchfab 3D models with licensing governance, NoAI tagging,
     and negative-case guardrail enforcement (SF-020 rejected accuracy).

Core Guarantees:
- Dry-run validation: slug uniqueness, parent existence, coordinate bounds, NoAI & license tags.
- Epistemic guardrail checks: SF-020 rejected accuracy, SF-010 blocked NC, SF-017 blocked NoAI.
- Commit mode: safe upserts without overwriting existing manual editorial reviews.
- Strict Content Scope Isolation: default content_scope = 'RBPC_HUE'.
"""
from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import yaml
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import User  # Ensures user table is registered in Base.metadata
from ..models_rbpc import (
    HeritageAccuracyGrade,
    HeritageCommercialUseStatus,
    HeritageEmbedPermissionStatus,
    HeritageEntityType,
    HeritageHeritageRelation,
    HeritageMediaAsset,
    HeritageMediaType,
    HeritagePlace,
    HeritageRecordStatus,
    RbpcAvailabilityMode,
    RbpcClaimEvidence,
    RbpcConsentStatus,
    RbpcContentAudit,
    RbpcCreator,
    RbpcExperience,
    RbpcInquiry,
    RbpcStory,
    RbpcStoryStatus,
    RbpcSupportType,
)
from .rbpc_audit import (
    record_creator_consent_change,
    record_experience_update,
    verify_all_audit_chains,
)

logger = logging.getLogger("luuniensuki.heritage_import")

# --------------------------------------------------------------------------- #
# Paths & Default Constants
# --------------------------------------------------------------------------- #
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INVENTORY_PATH = REPO_ROOT / "data" / "heritage-hue" / "inventory.unesco-14.yaml"
DEFAULT_SKETCHFAB_PATH = REPO_ROOT / "data" / "heritage-hue" / "sketchfab-curated.yaml"
DEFAULT_RELATIONS_PATH = REPO_ROOT / "data" / "heritage-hue" / "relations.yaml"
DEFAULT_CREATORS_PATH = REPO_ROOT / "data" / "heritage-hue" / "creators.yaml"
DEFAULT_EXPERIENCES_PATH = REPO_ROOT / "data" / "heritage-hue" / "experiences.yaml"
DEFAULT_STORIES_PATH = REPO_ROOT / "data" / "heritage-hue" / "stories.yaml"

CONTENT_SCOPE_DEFAULT = "RBPC_HUE"

# Statuses indicating manual editorial review has occurred; must NOT be downgraded to candidate/draft
EDITORIAL_PRESERVED_STATUSES = {
    "in_review",
    "approved",
    "published",
    "withdrawn",
}

# Mapping from heritage_relation in sketchfab-curated.yaml to place slugs
HERITAGE_RELATION_SLUG_MAP: dict[str, str] = {
    "Ngọ Môn": "ngo-mon",
    "Kinh thành Huế": "kinh-thanh-hue",
    "Đại Nội — Thái Bình Lâu": "kinh-thanh-hue",
    "Đại Nội — Thế Miếu": "the-mieu",
    "Điện Thái Hòa": "dien-thai-hoa",
    "Lăng Tự Đức": "lang-tu-duc",
    "Lăng Minh Mạng": "lang-minh-mang",
    "Hổ Quyền": "ho-quyen-voi-re",
    "Kinh thành Huế — Cửa Chánh Tây": "kinh-thanh-hue",
    "Cung An Định": "cung-an-dinh",
    "Chùa Thiên Mụ": "chua-thien-mu",
    "Đại Nội": "kinh-thanh-hue",
    "Lăng Khải Định": "lang-khai-dinh",
    "Hải Vân Quan": "hai-van-quan",
}

# Controlled vocabulary normalizers for HeritageMediaAsset
COMMERCIAL_USE_MAP: dict[str, str] = {
    "permitted": HeritageCommercialUseStatus.permitted.value,
    "conditional_attribution_required": HeritageCommercialUseStatus.permitted.value,
    "blocked_nc": HeritageCommercialUseStatus.blocked_nc.value,
    "prohibited": HeritageCommercialUseStatus.blocked_nc.value,
    "prohibited_without_grant": HeritageCommercialUseStatus.requires_custom_grant.value,
    "requires_custom_grant": HeritageCommercialUseStatus.requires_custom_grant.value,
    "unreviewed": HeritageCommercialUseStatus.unreviewed.value,
    "held_pending_identification": HeritageCommercialUseStatus.unreviewed.value,
}

EMBED_PERMISSION_MAP: dict[str, str] = {
    "permitted": HeritageEmbedPermissionStatus.permitted.value,
    "candidate_embed_attribution_required": HeritageEmbedPermissionStatus.permitted.value,
    "candidate_embed_artistic_only": HeritageEmbedPermissionStatus.permitted.value,
    "request_authorisation_required": HeritageEmbedPermissionStatus.needs_rights_review.value,
    "needs_rights_review": HeritageEmbedPermissionStatus.needs_rights_review.value,
    "held_id_unverified": HeritageEmbedPermissionStatus.needs_rights_review.value,
    "author_contacted": HeritageEmbedPermissionStatus.author_contacted.value,
    "blocked": HeritageEmbedPermissionStatus.blocked.value,
    "blocked_nc": HeritageEmbedPermissionStatus.blocked.value,
    "blocked_noai": HeritageEmbedPermissionStatus.blocked.value,
    "rejected": HeritageEmbedPermissionStatus.blocked.value,
}

ACCURACY_GRADE_MAP: dict[str, str] = {
    "survey_grade": HeritageAccuracyGrade.survey_grade.value,
    "expert_survey": HeritageAccuracyGrade.survey_grade.value,
    "reference_checked_lidar": HeritageAccuracyGrade.survey_grade.value,
    "measured_photogrammetry": HeritageAccuracyGrade.measured_photogrammetry.value,
    "reference_checked_photogrammetry": HeritageAccuracyGrade.measured_photogrammetry.value,
    "reference_checked_partial": HeritageAccuracyGrade.measured_photogrammetry.value,
    "historian_reviewed": HeritageAccuracyGrade.historian_reviewed.value,
    "illustrative_only": HeritageAccuracyGrade.illustrative_only.value,
    "partial_object": HeritageAccuracyGrade.illustrative_only.value,
    "partial_model": HeritageAccuracyGrade.illustrative_only.value,
    "illustrative_student_project": HeritageAccuracyGrade.illustrative_only.value,
    "illustrative_reconstruction": HeritageAccuracyGrade.illustrative_only.value,
    "unreviewed": HeritageAccuracyGrade.unreviewed.value,
    "unreviewed_institution_scan": HeritageAccuracyGrade.unreviewed.value,
    "unreviewed_macro_survey": HeritageAccuracyGrade.unreviewed.value,
    "unreviewed_site_scan": HeritageAccuracyGrade.unreviewed.value,
    "unreviewed_monument_scan": HeritageAccuracyGrade.unreviewed.value,
    "unreviewed_embed_endpoint": HeritageAccuracyGrade.unreviewed.value,
    "unreviewed_macro_scan": HeritageAccuracyGrade.unreviewed.value,
    "unreviewed_artifact_scan": HeritageAccuracyGrade.unreviewed.value,
    "rejected_accuracy": HeritageAccuracyGrade.rejected_accuracy.value,
    "rejected_inaccurate": HeritageAccuracyGrade.rejected_accuracy.value,
}


# --------------------------------------------------------------------------- #
# Data Classes
# --------------------------------------------------------------------------- #
@dataclass
class ValidationReport:
    """Report summarizing the outcome of dry-run validation."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    unesco_components_count: int = 0
    child_monuments_count: int = 0
    craft_communities_count: int = 0
    total_places_count: int = 0
    total_relations_count: int = 0
    models_count: int = 0
    creators_count: int = 0
    experiences_count: int = 0
    stories_count: int = 0
    claims_count: int = 0
    guardrails_passed: bool = True
    guardrail_details: dict[str, Any] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "unesco_components_count": self.unesco_components_count,
            "child_monuments_count": self.child_monuments_count,
            "craft_communities_count": self.craft_communities_count,
            "total_places_count": self.total_places_count,
            "total_relations_count": self.total_relations_count,
            "models_count": self.models_count,
            "creators_count": self.creators_count,
            "experiences_count": self.experiences_count,
            "stories_count": self.stories_count,
            "claims_count": self.claims_count,
            "guardrails_passed": self.guardrails_passed,
            "guardrail_details": self.guardrail_details,
            "details": self.details,
        }


@dataclass
class ImportStats:
    """Statistics tracking records inserted, updated, and preserved."""

    dry_run: bool = True
    places_inserted: int = 0
    places_updated: int = 0
    places_preserved_editorial: int = 0
    relations_inserted: int = 0
    relations_updated: int = 0
    relations_preserved_verified: int = 0
    media_inserted: int = 0
    media_updated: int = 0
    media_preserved_editorial: int = 0
    creators_inserted: int = 0
    creators_updated: int = 0
    creators_preserved_consent: int = 0
    inquiries_preserved: int = 0
    audit_logs_preserved: int = 0
    experiences_inserted: int = 0
    experiences_updated: int = 0
    stories_inserted: int = 0
    stories_updated: int = 0
    stories_preserved_editorial: int = 0
    claims_inserted: int = 0
    claims_updated: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dry_run": self.dry_run,
            "places_inserted": self.places_inserted,
            "places_updated": self.places_updated,
            "places_preserved_editorial": self.places_preserved_editorial,
            "relations_inserted": self.relations_inserted,
            "relations_updated": self.relations_updated,
            "relations_preserved_verified": self.relations_preserved_verified,
            "media_inserted": self.media_inserted,
            "media_updated": self.media_updated,
            "media_preserved_editorial": self.media_preserved_editorial,
            "creators_inserted": self.creators_inserted,
            "creators_updated": self.creators_updated,
            "creators_preserved_consent": self.creators_preserved_consent,
            "inquiries_preserved": self.inquiries_preserved,
            "audit_logs_preserved": self.audit_logs_preserved,
            "experiences_inserted": self.experiences_inserted,
            "experiences_updated": self.experiences_updated,
            "stories_inserted": self.stories_inserted,
            "stories_updated": self.stories_updated,
            "stories_preserved_editorial": self.stories_preserved_editorial,
            "claims_inserted": self.claims_inserted,
            "claims_updated": self.claims_updated,
            "errors": self.errors,
            "warnings": self.warnings,
        }


# --------------------------------------------------------------------------- #
# Helper Functions
# --------------------------------------------------------------------------- #
def load_yaml_file(path: Path | str) -> dict[str, Any]:
    """Safely load and parse a YAML file."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"YAML file not found: {p.resolve()}")
    with open(p, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"YAML file root must be a mapping, got {type(data).__name__}")
    return data


def parse_price(pricing_display: Optional[str]) -> Optional[float]:
    """Parse indicative price amount from display string (e.g. 'Từ 650.000 VNĐ / khách' -> 650000.0)."""
    if not pricing_display:
        return None
    nums = re.findall(r"\d+", pricing_display)
    if nums:
        try:
            return float("".join(nums))
        except ValueError:
            return None
    return None


def parse_entity_uuid(raw_id: Any, namespace: str = "rbpc") -> uuid.UUID:
    """Parse or deterministically normalize an entity identifier to standard UUID format."""
    if not raw_id:
        return uuid.uuid4()
    if isinstance(raw_id, uuid.UUID):
        return raw_id
    raw_str = str(raw_id).strip()
    try:
        return uuid.UUID(raw_str)
    except ValueError:
        # Handle structured IDs with non-hex character prefixes (e.g. 's1010001...')
        cleaned = re.sub(r"[^0-9a-fA-F-]", "a", raw_str)
        try:
            return uuid.UUID(cleaned)
        except ValueError:
            return uuid.uuid5(uuid.NAMESPACE_DNS, f"{namespace}:{raw_str}")


def generate_attribution_text(model: dict[str, Any]) -> str:
    """Format mandatory legal attribution credit according to content governance."""
    title = model.get("model_title", "3D Model")
    creator = model.get("creator_name", "Author")
    url = model.get("exact_model_url", "")
    license_label = model.get("displayed_license", "NOT STATED")

    if license_label == "CC BY":
        return f'Mô hình 3D "{title}" bởi {creator} ({url}), cấp phép theo CC BY 4.0.'
    if "NC" in license_label:
        return f'Tài liệu tham chiếu nghiên cứu: "{title}" bởi {creator} ({url}), {license_label}.'
    return f'Mô hình 3D "{title}" bởi {creator} ({url}).'


# --------------------------------------------------------------------------- #
# Dry-Run Validation Functions
# --------------------------------------------------------------------------- #
def validate_inventory_data(
    inventory_data: dict[str, Any],
    existing_slugs: Optional[set[str]] = None,
) -> ValidationReport:
    """Validate UNESCO-14 inventory data for schema, uniqueness, parentage, and bounds."""
    errors: list[str] = []
    warnings: list[str] = []

    unesco_components = inventory_data.get("unesco_components") or []
    child_monuments = inventory_data.get("child_monuments") or []
    craft_communities = inventory_data.get("craft_communities") or []

    if not isinstance(unesco_components, list):
        errors.append("inventory_data 'unesco_components' must be a list")
        unesco_components = []
    if not isinstance(child_monuments, list):
        errors.append("inventory_data 'child_monuments' must be a list")
        child_monuments = []
    if not isinstance(craft_communities, list):
        errors.append("inventory_data 'craft_communities' must be a list")
        craft_communities = []

    all_places = unesco_components + child_monuments + craft_communities
    seen_slugs: set[str] = set()
    all_dataset_slugs: set[str] = set()
    total_relations = 0

    valid_entity_types = {e.value for e in HeritageEntityType}
    valid_record_statuses = {s.value for s in HeritageRecordStatus}

    # 1. First pass: collect all slugs and check slug uniqueness & format
    for idx, place in enumerate(all_places):
        if not isinstance(place, dict):
            errors.append(f"Place at index {idx} must be a dictionary")
            continue

        slug = place.get("slug")
        if not slug or not isinstance(slug, str):
            errors.append(f"Place at index {idx} ({place.get('name_vi')}) is missing a valid 'slug'")
            continue

        slug = slug.strip()
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", slug):
            errors.append(f"Slug '{slug}' does not match standard slug pattern (lowercase alphanumeric and hyphens)")

        if slug in seen_slugs:
            errors.append(f"Duplicate slug detected in inventory: '{slug}'")
        else:
            seen_slugs.add(slug)
            all_dataset_slugs.add(slug)

    # Combined slugs include both dataset slugs and pre-existing DB slugs
    combined_slugs = all_dataset_slugs | (existing_slugs or set())

    # 2. Second pass: validate fields, parents, coordinates, enums, relationships
    for place in all_places:
        if not isinstance(place, dict):
            continue
        slug = place.get("slug", "<unknown>")

        # Name checks
        name_vi = place.get("name_vi")
        if not name_vi or not isinstance(name_vi, str):
            errors.append(f"Place '{slug}' is missing required 'name_vi'")

        # Entity type check
        entity_type = place.get("entity_type")
        if entity_type not in valid_entity_types:
            errors.append(
                f"Place '{slug}' has invalid entity_type '{entity_type}'. Allowed: {sorted(valid_entity_types)}"
            )

        # Heritage category check
        category = place.get("heritage_category")
        if not category or not isinstance(category, str):
            errors.append(f"Place '{slug}' is missing required 'heritage_category'")

        # Editorial status check
        status = place.get("editorial_status", "candidate")
        if status not in valid_record_statuses:
            errors.append(
                f"Place '{slug}' has invalid editorial_status '{status}'. Allowed: {sorted(valid_record_statuses)}"
            )

        # Parent existence check
        parent_slug = place.get("parent_slug")
        if parent_slug:
            if parent_slug == slug:
                errors.append(f"Place '{slug}' cannot be its own parent")
            elif parent_slug not in combined_slugs:
                errors.append(f"Place '{slug}' references non-existent parent_slug '{parent_slug}'")

        # Coordinate bounds check
        coords = place.get("approximate_coordinates")
        if coords:
            if not isinstance(coords, dict):
                errors.append(f"Place '{slug}' 'approximate_coordinates' must be a dictionary")
            else:
                lat = coords.get("latitude")
                lon = coords.get("longitude")
                if lat is not None:
                    try:
                        lat_f = float(lat)
                        if not (-90.0 <= lat_f <= 90.0):
                            errors.append(f"Place '{slug}' latitude {lat_f} is out of bounds [-90, 90]")
                        elif not (15.0 <= lat_f <= 17.5):
                            warnings.append(f"Place '{slug}' latitude {lat_f} is outside expected Huế region [15.0, 17.5]")
                    except (ValueError, TypeError):
                        errors.append(f"Place '{slug}' has invalid latitude: {lat}")
                if lon is not None:
                    try:
                        lon_f = float(lon)
                        if not (-180.0 <= lon_f <= 180.0):
                            errors.append(f"Place '{slug}' longitude {lon_f} is out of bounds [-180, 180]")
                        elif not (106.5 <= lon_f <= 108.5):
                            warnings.append(f"Place '{slug}' longitude {lon_f} is outside expected Huế region [106.5, 108.5]")
                    except (ValueError, TypeError):
                        errors.append(f"Place '{slug}' has invalid longitude: {lon}")

        # Relationships check
        rels = place.get("relationships") or []
        if isinstance(rels, list):
            total_relations += len(rels)
            for rel_idx, rel in enumerate(rels):
                if not isinstance(rel, dict):
                    errors.append(f"Place '{slug}' relationship #{rel_idx} is not a dictionary")
                    continue
                target_slug = rel.get("target_slug")
                rel_type = rel.get("relationship_type")
                if not target_slug or not isinstance(target_slug, str):
                    errors.append(f"Place '{slug}' relationship #{rel_idx} missing 'target_slug'")
                elif target_slug not in combined_slugs:
                    warnings.append(f"Place '{slug}' relationship targets slug '{target_slug}' not yet present in catalogue")
                if not rel_type or not isinstance(rel_type, str):
                    errors.append(f"Place '{slug}' relationship #{rel_idx} missing 'relationship_type'")

    return ValidationReport(
        is_valid=(len(errors) == 0),
        errors=errors,
        warnings=warnings,
        unesco_components_count=len(unesco_components),
        child_monuments_count=len(child_monuments),
        craft_communities_count=len(craft_communities),
        total_places_count=len(all_places),
        total_relations_count=total_relations,
        models_count=0,
        guardrails_passed=True,
    )


def validate_sketchfab_data(
    sketchfab_data: dict[str, Any],
    valid_place_slugs: Optional[set[str]] = None,
) -> ValidationReport:
    """Validate Sketchfab 3D curated registry, model UIDs, NoAI tags, and epistemic guardrails."""
    errors: list[str] = []
    warnings: list[str] = []

    models = sketchfab_data.get("models") or []
    if not isinstance(models, list):
        return ValidationReport(
            is_valid=False,
            errors=["sketchfab_data 'models' must be a list"],
            warnings=[],
        )

    guardrail_details: dict[str, Any] = {
        "sf020_rejected_accuracy": False,
        "sf010_blocked_nc": False,
        "sf017_blocked_noai": False,
        "candidate_cc_by_models": [],
    }

    seen_uids: set[str] = set()

    for idx, model in enumerate(models):
        if not isinstance(model, dict):
            errors.append(f"Model at index {idx} must be a dictionary")
            continue

        model_id = model.get("id", f"INDEX-{idx}")
        model_uid = model.get("model_uid")
        url = model.get("exact_model_url")
        license_label = model.get("displayed_license")
        noai = model.get("noai")
        comm_status = model.get("commercial_use_status")
        embed_status = model.get("embed_permission_status")
        acc_grade = model.get("accuracy_grade")
        content_status = model.get("content_status")

        # 1. UID validation (32 hex characters)
        if not model_uid or not isinstance(model_uid, str):
            errors.append(f"Model '{model_id}' is missing required 'model_uid'")
        else:
            norm_uid = model_uid.strip().lower()
            if not re.fullmatch(r"^[a-f0-9]{32}$", norm_uid):
                errors.append(f"Model '{model_id}' UID '{model_uid}' is not a valid 32-character hexadecimal string")
            elif norm_uid in seen_uids:
                warnings.append(f"Duplicate model_uid '{norm_uid}' in sketchfab registry (model '{model_id}')")
            else:
                seen_uids.add(norm_uid)

        # 2. URL validation
        if not url or not isinstance(url, str) or not url.startswith("https://sketchfab.com/"):
            errors.append(f"Model '{model_id}' URL '{url}' is not a valid Sketchfab URL")

        # 3. License tag validation
        if not license_label or not isinstance(license_label, str):
            errors.append(f"Model '{model_id}' is missing required 'displayed_license'")

        # 4. NoAI tag validation
        if not isinstance(noai, bool):
            errors.append(f"Model '{model_id}' 'noai' must be a boolean (True/False)")

        # 5. Guardrail check: SF-020 (permanently rejected fantasy geometry)
        if model_id == "SF-020" or model_uid == "84a8ab573293497ab0d4f97b4650bb55":
            is_rejected_acc = acc_grade in ("rejected_inaccurate", "rejected_accuracy")
            is_rejected_status = content_status == "rejected_accuracy"
            is_blocked_embed = embed_status in ("rejected", "blocked")
            if is_rejected_acc and is_rejected_status and is_blocked_embed:
                guardrail_details["sf020_rejected_accuracy"] = True
            else:
                errors.append(
                    f"GUARDRAIL VIOLATION: Model SF-020 must be marked rejected_accuracy and blocked from view. "
                    f"Got acc_grade='{acc_grade}', content_status='{content_status}', embed_status='{embed_status}'"
                )

        # 6. Guardrail check: SF-010 (CC BY-NC-SA blocked from commercial use)
        if model_id == "SF-010":
            if comm_status == "blocked_nc" and embed_status == "blocked_nc":
                guardrail_details["sf010_blocked_nc"] = True
            else:
                errors.append(
                    f"GUARDRAIL VIOLATION: Model SF-010 must be blocked from commercial use (blocked_nc). "
                    f"Got comm_status='{comm_status}', embed_status='{embed_status}'"
                )

        # 7. Guardrail check: SF-017 (CC BY-NC-SA, NoAI blocked from AI and commercial use)
        if model_id == "SF-017":
            if noai is True and comm_status == "blocked_nc" and embed_status in ("blocked_noai", "blocked"):
                guardrail_details["sf017_blocked_noai"] = True
            else:
                errors.append(
                    f"GUARDRAIL VIOLATION: Model SF-017 must have noai=True, blocked_nc, and blocked_noai. "
                    f"Got noai={noai}, comm_status='{comm_status}', embed_status='{embed_status}'"
                )

        # 8. Candidate CC BY embeds (SF-009, SF-011, SF-016)
        if model_id in ("SF-009", "SF-011", "SF-016"):
            if license_label == "CC BY":
                guardrail_details["candidate_cc_by_models"].append(model_id)
            else:
                warnings.append(f"Candidate model '{model_id}' was expected to have 'CC BY' license, got '{license_label}'")

        # 9. Heritage relation check
        rel = model.get("heritage_relation")
        if not rel or not isinstance(rel, str):
            warnings.append(f"Model '{model_id}' missing 'heritage_relation' annotation")

    guardrails_passed = (
        guardrail_details.get("sf020_rejected_accuracy") is True
        and guardrail_details.get("sf010_blocked_nc") is True
        and guardrail_details.get("sf017_blocked_noai") is True
    )

    return ValidationReport(
        is_valid=(len(errors) == 0 and guardrails_passed),
        errors=errors,
        warnings=warnings,
        models_count=len(models),
        guardrails_passed=guardrails_passed,
        guardrail_details=guardrail_details,
    )


def validate_creators_data(
    creators_data: dict[str, Any],
    valid_place_slugs: Optional[set[str]] = None,
) -> ValidationReport:
    """Validate consented creators and living artisans dataset."""
    errors: list[str] = []
    warnings: list[str] = []

    creators = creators_data.get("creators") or []
    if not isinstance(creators, list):
        return ValidationReport(
            is_valid=False,
            errors=["creators_data 'creators' must be a list"],
            warnings=[],
        )

    seen_slugs: set[str] = set()
    valid_consent_statuses = {s.value for s in RbpcConsentStatus}

    for idx, creator in enumerate(creators):
        if not isinstance(creator, dict):
            errors.append(f"Creator at index {idx} must be a dictionary")
            continue

        c_id = creator.get("id")
        slug = creator.get("slug")
        public_name = creator.get("public_name")
        craft_tradition = creator.get("craft_tradition")
        approved_bio_vi = creator.get("approved_bio_vi")
        consent_status = creator.get("consent_status", "consented")
        display_consent_ref = creator.get("display_consent_ref")
        is_verified = creator.get("is_verified")

        # 1. UUID validation
        if not c_id:
            errors.append(f"Creator at index {idx} missing 'id'")
        else:
            try:
                parse_entity_uuid(c_id, namespace="rbpc-creator")
            except Exception:
                errors.append(f"Creator at index {idx} has invalid UUID: '{c_id}'")

        # 2. Slug validation
        if not slug or not isinstance(slug, str):
            errors.append(f"Creator at index {idx} ({public_name}) missing valid 'slug'")
        else:
            slug = slug.strip()
            if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", slug):
                errors.append(f"Creator slug '{slug}' does not match standard slug pattern")
            if slug in seen_slugs:
                errors.append(f"Duplicate creator slug: '{slug}'")
            else:
                seen_slugs.add(slug)

        # 3. Required string fields
        if not public_name or not isinstance(public_name, str):
            errors.append(f"Creator '{slug or idx}' missing required 'public_name'")
        if not craft_tradition or not isinstance(craft_tradition, str):
            errors.append(f"Creator '{slug or idx}' missing required 'craft_tradition'")
        if not approved_bio_vi or not isinstance(approved_bio_vi, str):
            errors.append(f"Creator '{slug or idx}' missing required 'approved_bio_vi'")

        # 4. Consent validation
        if consent_status not in valid_consent_statuses:
            errors.append(
                f"Creator '{slug or idx}' invalid consent_status '{consent_status}'. Allowed: {sorted(valid_consent_statuses)}"
            )
        elif consent_status in ("consented", "verified_written_consent"):
            if not display_consent_ref:
                warnings.append(f"Creator '{slug or idx}' is marked consented but missing display_consent_ref")

        # 5. Verification flag
        if not isinstance(is_verified, bool):
            warnings.append(f"Creator '{slug or idx}' 'is_verified' should be a boolean")

        # 6. Associated places check
        assoc_places = creator.get("associated_places") or []
        if isinstance(assoc_places, list) and valid_place_slugs:
            for p_slug in assoc_places:
                if p_slug not in valid_place_slugs:
                    warnings.append(f"Creator '{slug or idx}' associated place '{p_slug}' not recognized in heritage catalogue")

    return ValidationReport(
        is_valid=(len(errors) == 0),
        errors=errors,
        warnings=warnings,
        creators_count=len(creators),
    )


def validate_experiences_data(
    experiences_data: dict[str, Any],
    valid_creator_slugs: Optional[set[str]] = None,
) -> ValidationReport:
    """Validate workshop experiences catalogue and commercial honesty rules."""
    errors: list[str] = []
    warnings: list[str] = []

    experiences = experiences_data.get("experiences") or []
    if not isinstance(experiences, list):
        return ValidationReport(
            is_valid=False,
            errors=["experiences_data 'experiences' must be a list"],
            warnings=[],
        )

    seen_slugs: set[str] = set()
    valid_avail_modes = {m.value for m in RbpcAvailabilityMode}

    for idx, exp in enumerate(experiences):
        if not isinstance(exp, dict):
            errors.append(f"Experience at index {idx} must be a dictionary")
            continue

        exp_id = exp.get("id")
        slug = exp.get("slug")
        creator_slug = exp.get("creator_slug")
        provider_name = exp.get("provider_name")
        title_vi = exp.get("title_vi")
        description_vi = exp.get("description_vi")
        avail_mode = exp.get("availability_mode")

        # 1. UUID validation
        if not exp_id:
            errors.append(f"Experience at index {idx} missing 'id'")
        else:
            try:
                parse_entity_uuid(exp_id, namespace="rbpc-exp")
            except Exception:
                errors.append(f"Experience at index {idx} has invalid UUID: '{exp_id}'")

        # 2. Slug validation
        if not slug or not isinstance(slug, str):
            errors.append(f"Experience at index {idx} missing valid 'slug'")
        else:
            slug = slug.strip()
            if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", slug):
                errors.append(f"Experience slug '{slug}' does not match standard slug pattern")
            if slug in seen_slugs:
                errors.append(f"Duplicate experience slug: '{slug}'")
            else:
                seen_slugs.add(slug)

        # 3. Creator reference check
        if not creator_slug or not isinstance(creator_slug, str):
            errors.append(f"Experience '{slug or idx}' missing required 'creator_slug'")
        elif valid_creator_slugs and creator_slug not in valid_creator_slugs:
            errors.append(f"Experience '{slug or idx}' references unknown creator_slug '{creator_slug}'")

        # 4. Required fields
        if not provider_name or not isinstance(provider_name, str):
            errors.append(f"Experience '{slug or idx}' missing required 'provider_name'")
        if not title_vi or not isinstance(title_vi, str):
            errors.append(f"Experience '{slug or idx}' missing required 'title_vi'")
        if not description_vi or not isinstance(description_vi, str):
            errors.append(f"Experience '{slug or idx}' missing required 'description_vi'")

        # 5. Commercial Honesty Guardrail: availability_mode strictly inquiry_only or disabled
        if not avail_mode:
            errors.append(f"Experience '{slug or idx}' missing required 'availability_mode'")
        elif avail_mode not in valid_avail_modes:
            errors.append(
                f"COMMERCIAL HONESTY VIOLATION: Experience '{slug or idx}' availability_mode '{avail_mode}' is prohibited. "
                f"Must be one of {sorted(valid_avail_modes)} (NEVER instant payment/instant booking)."
            )
        elif avail_mode != "inquiry_only" and avail_mode != "disabled":
            errors.append(f"Experience '{slug or idx}' invalid availability_mode '{avail_mode}'")

        # 6. Languages
        langs = exp.get("languages_supported")
        if langs is not None:
            if not isinstance(langs, list) or "vi" not in langs:
                warnings.append(f"Experience '{slug or idx}' languages_supported should be a list containing at least 'vi'")

        # 7. Max party size
        party_size = exp.get("max_party_size")
        if party_size is not None:
            try:
                ps = int(party_size)
                if not (1 <= ps <= 50):
                    errors.append(f"Experience '{slug or idx}' max_party_size {ps} outside allowed range [1, 50]")
            except (ValueError, TypeError):
                errors.append(f"Experience '{slug or idx}' invalid max_party_size '{party_size}'")

    return ValidationReport(
        is_valid=(len(errors) == 0),
        errors=errors,
        warnings=warnings,
        experiences_count=len(experiences),
    )


def validate_stories_data(
    stories_data: dict[str, Any],
    valid_place_slugs: Optional[set[str]] = None,
    valid_creator_slugs: Optional[set[str]] = None,
    valid_experience_slugs: Optional[set[str]] = None,
) -> ValidationReport:
    """Validate curated cultural stories and evidence claim citations."""
    errors: list[str] = []
    warnings: list[str] = []

    stories = stories_data.get("stories") or []
    if not isinstance(stories, list):
        return ValidationReport(
            is_valid=False,
            errors=["stories_data 'stories' must be a list"],
            warnings=[],
        )

    seen_slugs: set[str] = set()
    valid_statuses = {s.value for s in RbpcStoryStatus}
    valid_support_types = {t.value for t in RbpcSupportType}
    total_claims = 0

    for idx, story in enumerate(stories):
        if not isinstance(story, dict):
            errors.append(f"Story at index {idx} must be a dictionary")
            continue

        s_id = story.get("id")
        slug = story.get("slug")
        title_vi = story.get("title_vi")
        intro_vi = story.get("intro_vi")
        status = story.get("status", "draft")
        place_slug = story.get("place_slug")
        creator_slug = story.get("creator_slug")
        exp_slug = story.get("experience_slug")
        claims = story.get("claims") or []

        # 1. UUID validation
        if not s_id:
            errors.append(f"Story at index {idx} missing 'id'")
        else:
            try:
                parse_entity_uuid(s_id, namespace="rbpc-story")
            except Exception:
                errors.append(f"Story at index {idx} has invalid UUID: '{s_id}'")

        # 2. Slug validation
        if not slug or not isinstance(slug, str):
            errors.append(f"Story at index {idx} missing valid 'slug'")
        else:
            slug = slug.strip()
            if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", slug):
                errors.append(f"Story slug '{slug}' does not match standard slug pattern")
            if slug in seen_slugs:
                errors.append(f"Duplicate story slug: '{slug}'")
            else:
                seen_slugs.add(slug)

        # 3. Required string fields
        if not title_vi or not isinstance(title_vi, str):
            errors.append(f"Story '{slug or idx}' missing required 'title_vi'")
        if not intro_vi or not isinstance(intro_vi, str):
            errors.append(f"Story '{slug or idx}' missing required 'intro_vi'")

        # 4. Status validation
        if status not in valid_statuses:
            errors.append(
                f"Story '{slug or idx}' invalid status '{status}'. Allowed: {sorted(valid_statuses)}"
            )

        # 5. Foreign key references
        if place_slug and valid_place_slugs and place_slug not in valid_place_slugs:
            errors.append(f"Story '{slug or idx}' references unknown place_slug '{place_slug}'")
        if creator_slug and valid_creator_slugs and creator_slug not in valid_creator_slugs:
            errors.append(f"Story '{slug or idx}' references unknown creator_slug '{creator_slug}'")
        if exp_slug and valid_experience_slugs and exp_slug not in valid_experience_slugs:
            errors.append(f"Story '{slug or idx}' references unknown experience_slug '{exp_slug}'")

        # 6. Claims validation
        if not isinstance(claims, list):
            errors.append(f"Story '{slug or idx}' 'claims' must be a list")
        else:
            total_claims += len(claims)
            if len(claims) == 0 and status == "published":
                warnings.append(f"Published story '{slug or idx}' has zero backing claim citations")

            for c_idx, claim in enumerate(claims):
                if not isinstance(claim, dict):
                    errors.append(f"Story '{slug or idx}' claim #{c_idx} must be a dictionary")
                    continue
                stmt = claim.get("statement_vi") or claim.get("statement")
                src_title = claim.get("source_title")
                sup_type = claim.get("support_type", "direct")

                if not stmt or not isinstance(stmt, str):
                    errors.append(f"Story '{slug or idx}' claim #{c_idx} missing statement (statement_vi)")
                if not src_title or not isinstance(src_title, str):
                    errors.append(f"Story '{slug or idx}' claim #{c_idx} missing 'source_title'")
                if sup_type not in valid_support_types:
                    errors.append(
                        f"Story '{slug or idx}' claim #{c_idx} invalid support_type '{sup_type}'. Allowed: {sorted(valid_support_types)}"
                    )

    return ValidationReport(
        is_valid=(len(errors) == 0),
        errors=errors,
        warnings=warnings,
        stories_count=len(stories),
        claims_count=total_claims,
    )


def validate_relations_data(
    relations_data: dict[str, Any] | Path | str,
    known_place_slugs: Optional[set[str]] = None,
) -> ValidationReport:
    """Validate relations.yaml graph relationships against schema, taxonomy, and known places."""
    if isinstance(relations_data, (str, Path)):
        relations_data = load_yaml_file(relations_data)

    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(relations_data, dict):
        return ValidationReport(
            is_valid=False,
            errors=["relations_data root must be a YAML dictionary"],
            total_relations_count=0,
        )

    metadata = relations_data.get("metadata") or {}
    declared_total = metadata.get("total_relations")
    taxonomy = set(metadata.get("taxonomy") or [])

    relations = relations_data.get("relations")
    if not isinstance(relations, list):
        errors.append("relations_data 'relations' must be a list")
        relations = []

    if declared_total is not None and declared_total != len(relations):
        errors.append(
            f"Metadata total_relations ({declared_total}) does not match actual count ({len(relations)})"
        )

    seen_ids: set[str] = set()
    for idx, r in enumerate(relations):
        if not isinstance(r, dict):
            errors.append(f"Relation #{idx} is not a dictionary")
            continue

        rid = r.get("id")
        if not rid or not isinstance(rid, str):
            errors.append(f"Relation #{idx} missing 'id'")
        elif rid in seen_ids:
            errors.append(f"Duplicate relation id '{rid}'")
        else:
            seen_ids.add(rid)

        from_slug = r.get("from_slug")
        to_slug = r.get("to_slug")
        rel_type = r.get("relationship_type")
        review_state = r.get("review_state")
        source_key = r.get("source_key")

        if not from_slug:
            errors.append(f"Relation '{rid or idx}' missing 'from_slug'")
        elif known_place_slugs and from_slug not in known_place_slugs:
            errors.append(f"Relation '{rid or idx}' from_slug '{from_slug}' not found in known places")

        if not to_slug:
            errors.append(f"Relation '{rid or idx}' missing 'to_slug'")
        elif known_place_slugs and to_slug not in known_place_slugs:
            errors.append(f"Relation '{rid or idx}' to_slug '{to_slug}' not found in known places")

        if not rel_type:
            errors.append(f"Relation '{rid or idx}' missing 'relationship_type'")
        elif taxonomy and rel_type not in taxonomy:
            errors.append(f"Relation '{rid or idx}' relationship_type '{rel_type}' not in taxonomy")

        if review_state != "verified":
            warnings.append(f"Relation '{rid or idx}' review_state is '{review_state}' (expected 'verified')")

        if not source_key:
            errors.append(f"Relation '{rid or idx}' missing 'source_key'")

    return ValidationReport(
        is_valid=(len(errors) == 0),
        errors=errors,
        warnings=warnings,
        total_relations_count=len(relations),
    )


def validate_heritage_import(
    inventory_data: dict[str, Any],
    sketchfab_data: dict[str, Any],
    stories_data: Optional[dict[str, Any]] = None,
    creators_data: Optional[dict[str, Any]] = None,
    experiences_data: Optional[dict[str, Any]] = None,
    existing_slugs: Optional[set[str]] = None,
    existing_creator_slugs: Optional[set[str]] = None,
    existing_experience_slugs: Optional[set[str]] = None,
) -> ValidationReport:
    """Perform comprehensive dry-run validation combining inventory, Sketchfab, and commercial datasets."""
    rep_inv = validate_inventory_data(inventory_data, existing_slugs=existing_slugs)
    rep_sf = validate_sketchfab_data(sketchfab_data)

    all_errors = list(rep_inv.errors) + list(rep_sf.errors)
    all_warnings = list(rep_inv.warnings) + list(rep_sf.warnings)
    guardrails_passed = rep_sf.guardrails_passed

    # Collect known place slugs
    inv_places = (
        (inventory_data.get("unesco_components") or [])
        + (inventory_data.get("child_monuments") or [])
        + (inventory_data.get("craft_communities") or [])
    )
    all_place_slugs = {p["slug"] for p in inv_places if isinstance(p, dict) and "slug" in p}
    if existing_slugs:
        all_place_slugs.update(existing_slugs)

    creators_count = 0
    experiences_count = 0
    stories_count = 0
    claims_count = 0

    # Creators validation
    dataset_creator_slugs: set[str] = set()
    if creators_data is not None:
        rep_cr = validate_creators_data(creators_data, valid_place_slugs=all_place_slugs)
        all_errors.extend(rep_cr.errors)
        all_warnings.extend(rep_cr.warnings)
        creators_count = rep_cr.creators_count
        for c in creators_data.get("creators") or []:
            if isinstance(c, dict) and "slug" in c:
                dataset_creator_slugs.add(c["slug"])

    all_creator_slugs = dataset_creator_slugs | (existing_creator_slugs or set())

    # Experiences validation
    dataset_exp_slugs: set[str] = set()
    if experiences_data is not None:
        rep_exp = validate_experiences_data(experiences_data, valid_creator_slugs=all_creator_slugs)
        all_errors.extend(rep_exp.errors)
        all_warnings.extend(rep_exp.warnings)
        experiences_count = rep_exp.experiences_count
        for e in experiences_data.get("experiences") or []:
            if isinstance(e, dict) and "slug" in e:
                dataset_exp_slugs.add(e["slug"])

    all_exp_slugs = dataset_exp_slugs | (existing_experience_slugs or set())

    # Stories validation
    if stories_data is not None:
        rep_st = validate_stories_data(
            stories_data,
            valid_place_slugs=all_place_slugs,
            valid_creator_slugs=all_creator_slugs,
            valid_experience_slugs=all_exp_slugs,
        )
        all_errors.extend(rep_st.errors)
        all_warnings.extend(rep_st.warnings)
        stories_count = rep_st.stories_count
        claims_count = rep_st.claims_count

    return ValidationReport(
        is_valid=(rep_inv.is_valid and rep_sf.is_valid and len(all_errors) == 0 and guardrails_passed),
        errors=all_errors,
        warnings=all_warnings,
        unesco_components_count=rep_inv.unesco_components_count,
        child_monuments_count=rep_inv.child_monuments_count,
        craft_communities_count=rep_inv.craft_communities_count,
        total_places_count=rep_inv.total_places_count,
        total_relations_count=rep_inv.total_relations_count,
        models_count=rep_sf.models_count,
        creators_count=creators_count,
        experiences_count=experiences_count,
        stories_count=stories_count,
        claims_count=claims_count,
        guardrails_passed=guardrails_passed,
        guardrail_details=rep_sf.guardrail_details,
    )


# --------------------------------------------------------------------------- #
# Commit / Upsert Ingestion Service
# --------------------------------------------------------------------------- #
def import_heritage_data(
    db: Session,
    inventory_path: Optional[Path | str] = None,
    sketchfab_path: Optional[Path | str] = None,
    stories_path: Optional[Path | str] = None,
    creators_path: Optional[Path | str] = None,
    experiences_path: Optional[Path | str] = None,
    dry_run: bool = True,
) -> tuple[ValidationReport, ImportStats]:
    """Execute ingestion and synchronization of Huế heritage & commercial data into PostgreSQL.

    Args:
        db: SQLAlchemy database session.
        inventory_path: Path to inventory.unesco-14.yaml.
        sketchfab_path: Path to sketchfab-curated.yaml.
        stories_path: Path to stories.yaml.
        creators_path: Path to creators.yaml.
        experiences_path: Path to experiences.yaml.
        dry_run: If True, validates without committing changes to DB.

    Returns:
        tuple[ValidationReport, ImportStats]: Detailed report and ingestion metrics.
    """
    inv_p = Path(inventory_path) if inventory_path else DEFAULT_INVENTORY_PATH
    sf_p = Path(sketchfab_path) if sketchfab_path else DEFAULT_SKETCHFAB_PATH
    cr_p = Path(creators_path) if creators_path else DEFAULT_CREATORS_PATH
    exp_p = Path(experiences_path) if experiences_path else DEFAULT_EXPERIENCES_PATH
    st_p = Path(stories_path) if stories_path else DEFAULT_STORIES_PATH

    inventory_data = load_yaml_file(inv_p)
    sketchfab_data = load_yaml_file(sf_p)
    creators_data = load_yaml_file(cr_p) if cr_p.is_file() else None
    experiences_data = load_yaml_file(exp_p) if exp_p.is_file() else None
    stories_data = load_yaml_file(st_p) if st_p.is_file() else None

    # Fetch existing entities for validation and upsert logic
    existing_by_slug: dict[str, HeritagePlace] = {}
    existing_creator_slugs: set[str] = set()
    existing_experience_slugs: set[str] = set()
    if db is not None:
        try:
            existing_places_query = db.execute(select(HeritagePlace)).scalars().all()
            existing_by_slug = {p.slug: p for p in existing_places_query}
            existing_creator_slugs = set(db.execute(select(RbpcCreator.slug)).scalars().all())
            existing_experience_slugs = set(db.execute(select(RbpcExperience.slug)).scalars().all())
        except Exception as e:
            logger.debug("Could not query existing DB entities: %s", e)
            try:
                db.rollback()
            except Exception:
                pass

    # Run dry-run validation
    report = validate_heritage_import(
        inventory_data,
        sketchfab_data,
        stories_data=stories_data,
        creators_data=creators_data,
        experiences_data=experiences_data,
        existing_slugs=set(existing_by_slug.keys()),
        existing_creator_slugs=existing_creator_slugs,
        existing_experience_slugs=existing_experience_slugs,
    )

    stats = ImportStats(dry_run=dry_run, warnings=list(report.warnings))

    if not report.is_valid:
        stats.errors = list(report.errors)
        logger.error("Heritage data validation failed with %d errors.", len(report.errors))
        return report, stats

    if dry_run:
        logger.info("Heritage dry-run validation passed successfully. No database writes performed.")
        return report, stats

    # =========================================================================
    # COMMIT MODE EXECUTION
    # =========================================================================
    logger.info("Starting safe upsert of Huế heritage catalogue into database...")

    unesco = inventory_data.get("unesco_components") or []
    children = inventory_data.get("child_monuments") or []
    crafts = inventory_data.get("craft_communities") or []
    all_place_dicts: list[dict[str, Any]] = unesco + children + crafts

    # 1. Upsert Heritage Places (Pass 1 - Place attributes without parent_id)
    parent_links: dict[str, str] = {}

    for p_dict in all_place_dicts:
        slug = p_dict["slug"]
        parent_slug = p_dict.get("parent_slug")
        if parent_slug:
            parent_links[slug] = parent_slug

        coords = p_dict.get("approximate_coordinates") or {}
        lat = coords.get("latitude")
        lon = coords.get("longitude")
        geo_precision = coords.get("geo_precision", "approximate")

        place_kwargs = {
            "name_vi": p_dict["name_vi"],
            "name_en": p_dict.get("name_en"),
            "entity_type": p_dict["entity_type"],
            "heritage_category": p_dict["heritage_category"],
            "official_designation": p_dict.get("official_designation"),
            "official_reference_id": p_dict.get("official_reference_id") or p_dict.get("unesco_id") or p_dict.get("id"),
            "period_label": p_dict.get("historical_period") or p_dict.get("period_label"),
            "historical_state": p_dict.get("survival_state") or p_dict.get("historical_state"),
            "location_lat": float(lat) if lat is not None else None,
            "location_lon": float(lon) if lon is not None else None,
            "geo_precision": geo_precision,
            "current_access_status": p_dict.get("current_access_status", "unknown"),
            "access_notes": p_dict.get("access_notes"),
            "visitor_summary_vi": p_dict.get("visitor_summary_vi"),
            "visitor_summary_en": p_dict.get("visitor_summary_en"),
            "historical_summary_vi": p_dict.get("historical_summary_vi"),
            "historical_summary_en": p_dict.get("historical_summary_en"),
            "content_scope": CONTENT_SCOPE_DEFAULT,
        }

        existing_place = existing_by_slug.get(slug)
        seed_status = p_dict.get("editorial_status", "draft")

        if existing_place:
            # Check if this place has undergone manual editorial review
            if existing_place.editorial_status in EDITORIAL_PRESERVED_STATUSES or existing_place.published_at is not None:
                stats.places_preserved_editorial += 1
                # Update non-editorial physical attributes while preserving editorial status & published_at
                for k, v in place_kwargs.items():
                    if k in ("name_vi", "name_en", "entity_type", "heritage_category", "official_designation", "official_reference_id", "location_lat", "location_lon", "geo_precision"):
                        if v is not None:
                            setattr(existing_place, k, v)
                logger.debug("Preserved manual editorial review for place '%s' (status: %s)", slug, existing_place.editorial_status)
            else:
                # Place is still draft/candidate; safe to update completely
                for k, v in place_kwargs.items():
                    setattr(existing_place, k, v)
                existing_place.editorial_status = seed_status
                stats.places_updated += 1
        else:
            # New place insertion
            new_place = HeritagePlace(
                id=uuid.uuid4(),
                slug=slug,
                editorial_status=seed_status,
                **place_kwargs,
            )
            db.add(new_place)
            existing_by_slug[slug] = new_place
            stats.places_inserted += 1

    # Flush so all place IDs are generated and available in session
    db.flush()

    # 2. Update parent_id hierarchy (Pass 2)
    for child_slug, p_slug in parent_links.items():
        child = existing_by_slug.get(child_slug)
        parent = existing_by_slug.get(p_slug)
        if child and parent and child.parent_id != parent.id:
            child.parent_id = parent.id

    db.flush()

    # 3. Upsert Heritage Relationships
    existing_relations_query = db.execute(select(HeritageHeritageRelation)).scalars().all()
    existing_rel_map: dict[tuple[uuid.UUID, uuid.UUID, str], HeritageHeritageRelation] = {
        (r.from_place_id, r.to_place_id, r.relationship_type): r
        for r in existing_relations_query
    }

    for p_dict in all_place_dicts:
        from_slug = p_dict["slug"]
        from_place = existing_by_slug.get(from_slug)
        if not from_place:
            continue

        for rel in p_dict.get("relationships") or []:
            to_slug = rel.get("target_slug")
            to_place = existing_by_slug.get(to_slug)
            rel_type = rel.get("relationship_type")
            seed_review_state = rel.get("review_state", "draft")

            if not to_place or not rel_type:
                continue

            rel_key = (from_place.id, to_place.id, rel_type)
            existing_rel = existing_rel_map.get(rel_key)

            if existing_rel:
                # Do NOT downgrade a verified relationship to draft
                if existing_rel.review_state == "verified" and seed_review_state == "draft":
                    stats.relations_preserved_verified += 1
                else:
                    existing_rel.review_state = seed_review_state
                    stats.relations_updated += 1
            else:
                new_rel = HeritageHeritageRelation(
                    id=uuid.uuid4(),
                    from_place_id=from_place.id,
                    to_place_id=to_place.id,
                    relationship_type=rel_type,
                    review_state=seed_review_state,
                )
                db.add(new_rel)
                existing_rel_map[rel_key] = new_rel
                stats.relations_inserted += 1

    db.flush()

    # 4. Upsert Sketchfab 3D Models
    existing_media_query = db.execute(select(HeritageMediaAsset)).scalars().all()
    existing_media_by_uid: dict[str, HeritageMediaAsset] = {
        m.model_uid.lower(): m for m in existing_media_query if m.model_uid
    }
    existing_media_by_url: dict[str, HeritageMediaAsset] = {
        m.original_url: m for m in existing_media_query if m.original_url
    }

    for model in sketchfab_data.get("models") or []:
        raw_uid = model.get("model_uid")
        norm_uid = raw_uid.strip().lower() if raw_uid else None
        url = model.get("exact_model_url", "")
        title = model.get("model_title")
        creator_name = model.get("creator_name")
        license_label = model.get("displayed_license")
        noai = bool(model.get("noai", False))
        provenance = model.get("provenance_notes")
        content_status = model.get("content_status", "candidate")

        # Map enum statuses safely
        comm_use_mapped = COMMERCIAL_USE_MAP.get(
            model.get("commercial_use_status"), HeritageCommercialUseStatus.unreviewed.value
        )
        embed_perm_mapped = EMBED_PERMISSION_MAP.get(
            model.get("embed_permission_status"), HeritageEmbedPermissionStatus.needs_rights_review.value
        )
        accuracy_mapped = ACCURACY_GRADE_MAP.get(
            model.get("accuracy_grade"), HeritageAccuracyGrade.unreviewed.value
        )

        # Enforce SF-020 rejected accuracy guardrail
        if model.get("id") == "SF-020" or norm_uid == "84a8ab573293497ab0d4f97b4650bb55":
            comm_use_mapped = HeritageCommercialUseStatus.blocked_nc.value
            embed_perm_mapped = HeritageEmbedPermissionStatus.blocked.value
            accuracy_mapped = HeritageAccuracyGrade.rejected_accuracy.value
            content_status = "rejected_accuracy"

        # Resolve linked place_id
        relation_name = model.get("heritage_relation")
        target_slug = HERITAGE_RELATION_SLUG_MAP.get(relation_name) if relation_name else None
        linked_place = existing_by_slug.get(target_slug) if target_slug else None
        place_id = linked_place.id if linked_place else None

        # Build attribution and embed endpoint
        attr_text = generate_attribution_text(model)
        embed_url = (
            f"https://sketchfab.com/models/{norm_uid}/embed"
            if embed_perm_mapped == HeritageEmbedPermissionStatus.permitted.value
            and accuracy_mapped != HeritageAccuracyGrade.rejected_accuracy.value
            and norm_uid
            else None
        )

        existing_asset = None
        if norm_uid and norm_uid in existing_media_by_uid:
            existing_asset = existing_media_by_uid[norm_uid]
        elif url in existing_media_by_url:
            existing_asset = existing_media_by_url[url]

        if existing_asset:
            # Check if asset has manual editorial review recorded
            if existing_asset.rights_reviewed_by is not None or existing_asset.rights_reviewed_at is not None:
                stats.media_preserved_editorial += 1
                # Preserve manual review fields, update non-destructive provenance/title if missing
                if place_id and not existing_asset.place_id:
                    existing_asset.place_id = place_id
                if not existing_asset.provenance_notes:
                    existing_asset.provenance_notes = provenance
                logger.debug("Preserved manual rights review for media asset UID '%s'", norm_uid)
            else:
                # Safe to update from curated registry
                existing_asset.place_id = place_id
                existing_asset.title = title
                existing_asset.creator_name = creator_name
                existing_asset.license_label = license_label
                existing_asset.noai = noai
                existing_asset.commercial_use_status = comm_use_mapped
                existing_asset.embed_permission_status = embed_perm_mapped
                existing_asset.accuracy_grade = accuracy_mapped
                existing_asset.provenance_notes = provenance
                existing_asset.attribution_text = attr_text
                existing_asset.content_status = content_status
                existing_asset.embed_url = embed_url
                existing_asset.checked_at = datetime.now(timezone.utc)
                stats.media_updated += 1
        else:
            new_asset = HeritageMediaAsset(
                id=uuid.uuid4(),
                place_id=place_id,
                media_type=HeritageMediaType.sketchfab_embed.value,
                source_platform="sketchfab",
                original_url=url,
                title=title,
                creator_name=creator_name,
                model_uid=norm_uid,
                license_label=license_label,
                noai=noai,
                commercial_use_status=comm_use_mapped,
                embed_permission_status=embed_perm_mapped,
                accuracy_grade=accuracy_mapped,
                provenance_notes=provenance,
                attribution_text=attr_text,
                content_status=content_status,
                embed_url=embed_url,
                content_scope=CONTENT_SCOPE_DEFAULT,
                checked_at=datetime.now(timezone.utc),
            )
            db.add(new_asset)
            if norm_uid:
                existing_media_by_uid[norm_uid] = new_asset
            existing_media_by_url[url] = new_asset
            stats.media_inserted += 1

    db.flush()

    # 5. Upsert Consented Creators (rbpc_creators)
    existing_creators_query = db.execute(select(RbpcCreator)).scalars().all()
    existing_creators_by_slug: dict[str, RbpcCreator] = {
        c.slug: c for c in existing_creators_query
    }

    for c_dict in (creators_data.get("creators") if creators_data else []):
        slug = c_dict["slug"]
        c_id = parse_entity_uuid(c_dict["id"], namespace="rbpc-creator") if "id" in c_dict else uuid.uuid4()
        public_name = c_dict["public_name"]
        craft_tradition = c_dict["craft_tradition"]
        craft_tradition_en = c_dict.get("craft_tradition_en")
        approved_bio_vi = c_dict["approved_bio_vi"]
        approved_bio_en = c_dict.get("approved_bio_en")
        approved_portrait_url = c_dict.get("portrait_asset_url") or c_dict.get("approved_portrait_url")
        public_region = c_dict.get("public_region", "Huế")
        display_consent_ref = c_dict.get("display_consent_ref")
        consent_status = c_dict.get("consent_status", RbpcConsentStatus.consented.value)
        is_verified = bool(c_dict.get("is_verified", False))
        years_of_practice = c_dict.get("years_of_practice")
        generation_lineage = c_dict.get("generation_lineage")

        # Resolve associated heritage place
        assoc_places = c_dict.get("associated_places") or []
        primary_place_slug = c_dict.get("heritage_place_slug") or (assoc_places[0] if assoc_places else None)
        linked_place = existing_by_slug.get(primary_place_slug) if primary_place_slug else None
        heritage_place_id = linked_place.id if linked_place else None

        existing_creator = existing_creators_by_slug.get(slug)
        if existing_creator:
            # Preservation guardrail: manual consent revocation must never be silently overturned by re-seeding
            # Also preserve verified_written_consent and pending_review against incoming default seed statuses
            should_preserve_consent = (
                (
                    existing_creator.consent_status == RbpcConsentStatus.revoked.value
                    and consent_status != RbpcConsentStatus.revoked.value
                )
                or (
                    existing_creator.consent_status == RbpcConsentStatus.verified_written_consent.value
                    and consent_status in (RbpcConsentStatus.consented.value, RbpcConsentStatus.pending_review.value)
                )
                or (
                    existing_creator.consent_status == RbpcConsentStatus.pending_review.value
                    and consent_status == RbpcConsentStatus.consented.value
                )
            )
            if should_preserve_consent:
                stats.creators_preserved_consent += 1
                logger.debug(
                    "Preserved existing consent status '%s' for creator '%s'",
                    existing_creator.consent_status,
                    slug,
                )
                # Update other profile information without overwriting consent
                existing_creator.public_name = public_name
                existing_creator.craft_tradition = craft_tradition
                existing_creator.craft_tradition_en = craft_tradition_en
                existing_creator.approved_bio_vi = approved_bio_vi
                existing_creator.approved_bio_en = approved_bio_en
                existing_creator.approved_portrait_url = approved_portrait_url
                existing_creator.public_region = public_region
                if display_consent_ref and not existing_creator.display_consent_ref:
                    existing_creator.display_consent_ref = display_consent_ref
                existing_creator.is_verified = is_verified or existing_creator.is_verified
                existing_creator.years_of_practice = years_of_practice
                existing_creator.generation_lineage = generation_lineage
                if heritage_place_id:
                    existing_creator.heritage_place_id = heritage_place_id
                stats.creators_updated += 1
            else:
                existing_creator.public_name = public_name
                existing_creator.craft_tradition = craft_tradition
                existing_creator.craft_tradition_en = craft_tradition_en
                existing_creator.approved_bio_vi = approved_bio_vi
                existing_creator.approved_bio_en = approved_bio_en
                existing_creator.approved_portrait_url = approved_portrait_url
                existing_creator.public_region = public_region
                existing_creator.display_consent_ref = display_consent_ref
                existing_creator.consent_status = consent_status
                existing_creator.is_verified = is_verified
                existing_creator.years_of_practice = years_of_practice
                existing_creator.generation_lineage = generation_lineage
                if heritage_place_id:
                    existing_creator.heritage_place_id = heritage_place_id
                stats.creators_updated += 1
        else:
            new_creator = RbpcCreator(
                id=c_id,
                slug=slug,
                public_name=public_name,
                craft_tradition=craft_tradition,
                craft_tradition_en=craft_tradition_en,
                approved_bio_vi=approved_bio_vi,
                approved_bio_en=approved_bio_en,
                approved_portrait_url=approved_portrait_url,
                public_region=public_region,
                display_consent_ref=display_consent_ref,
                consent_status=consent_status,
                is_verified=is_verified,
                years_of_practice=years_of_practice,
                generation_lineage=generation_lineage,
                heritage_place_id=heritage_place_id,
            )
            db.add(new_creator)
            existing_creators_by_slug[slug] = new_creator
            stats.creators_inserted += 1

    db.flush()

    # 6. Upsert Experiences (rbpc_experiences)
    existing_exp_query = db.execute(select(RbpcExperience)).scalars().all()
    existing_experiences_by_slug: dict[str, RbpcExperience] = {
        e.slug: e for e in existing_exp_query
    }

    for exp_dict in (experiences_data.get("experiences") if experiences_data else []):
        slug = exp_dict["slug"]
        creator_slug = exp_dict.get("creator_slug")
        creator_obj = existing_creators_by_slug.get(creator_slug)
        if not creator_obj:
            logger.warning("Experience '%s' references missing creator '%s', skipping", slug, creator_slug)
            continue

        exp_id = parse_entity_uuid(exp_dict["id"], namespace="rbpc-exp") if "id" in exp_dict else uuid.uuid4()
        pricing_display = exp_dict.get("pricing_display")
        price_amount = exp_dict.get("indicative_price_amount") or parse_price(pricing_display)
        avail_mode = exp_dict.get("availability_mode", RbpcAvailabilityMode.inquiry_only.value)

        existing_exp = existing_experiences_by_slug.get(slug)
        if existing_exp:
            existing_exp.creator_id = creator_obj.id
            existing_exp.provider_name = exp_dict["provider_name"]
            existing_exp.title_vi = exp_dict["title_vi"]
            existing_exp.title_en = exp_dict.get("title_en")
            existing_exp.description_vi = exp_dict["description_vi"]
            existing_exp.description_en = exp_dict.get("description_en")
            existing_exp.area_public = exp_dict.get("area_public", "Huế")
            existing_exp.duration_minutes = exp_dict.get("duration_minutes")
            existing_exp.pricing_display = pricing_display
            existing_exp.indicative_price_amount = price_amount
            existing_exp.currency = exp_dict.get("currency", "VND")
            existing_exp.availability_mode = avail_mode
            existing_exp.publication_state = exp_dict.get("publication_state", "published")
            existing_exp.cancellation_policy_text_vi = exp_dict.get("cancellation_policy_text_vi")
            existing_exp.cancellation_policy_text_en = exp_dict.get("cancellation_policy_text_en")
            existing_exp.max_party_size = exp_dict.get("max_party_size", 10)
            existing_exp.languages_supported = exp_dict.get("languages_supported") or ["vi"]
            existing_exp.notice = exp_dict.get("notice")
            stats.experiences_updated += 1
        else:
            new_exp = RbpcExperience(
                id=exp_id,
                slug=slug,
                creator_id=creator_obj.id,
                provider_name=exp_dict["provider_name"],
                title_vi=exp_dict["title_vi"],
                title_en=exp_dict.get("title_en"),
                description_vi=exp_dict["description_vi"],
                description_en=exp_dict.get("description_en"),
                area_public=exp_dict.get("area_public", "Huế"),
                duration_minutes=exp_dict.get("duration_minutes"),
                pricing_display=pricing_display,
                indicative_price_amount=price_amount,
                currency=exp_dict.get("currency", "VND"),
                availability_mode=avail_mode,
                publication_state=exp_dict.get("publication_state", "published"),
                cancellation_policy_text_vi=exp_dict.get("cancellation_policy_text_vi"),
                cancellation_policy_text_en=exp_dict.get("cancellation_policy_text_en"),
                max_party_size=exp_dict.get("max_party_size", 10),
                languages_supported=exp_dict.get("languages_supported") or ["vi"],
                notice=exp_dict.get("notice"),
            )
            db.add(new_exp)
            existing_experiences_by_slug[slug] = new_exp
            stats.experiences_inserted += 1

    db.flush()

    # 7. Upsert Curated Stories (rbpc_stories) & Evidence Claims (rbpc_claim_evidence)
    existing_stories_query = db.execute(select(RbpcStory)).scalars().all()
    existing_stories_by_slug: dict[str, RbpcStory] = {
        s.slug: s for s in existing_stories_query
    }

    for story_dict in (stories_data.get("stories") if stories_data else []):
        slug = story_dict["slug"]
        story_id = parse_entity_uuid(story_dict["id"], namespace="rbpc-story") if "id" in story_dict else uuid.uuid4()

        place_obj = existing_by_slug.get(story_dict.get("place_slug"))
        creator_obj = existing_creators_by_slug.get(story_dict.get("creator_slug"))
        exp_obj = existing_experiences_by_slug.get(story_dict.get("experience_slug"))

        place_id = place_obj.id if place_obj else None
        creator_id = creator_obj.id if creator_obj else None
        experience_id = exp_obj.id if exp_obj else None

        title_vi = story_dict["title_vi"]
        title_en = story_dict.get("title_en")
        intro_vi = story_dict["intro_vi"]
        intro_en = story_dict.get("intro_en")
        approved_summary_vi = story_dict.get("approved_summary_vi") or intro_vi
        approved_summary_en = story_dict.get("approved_summary_en") or intro_en
        primary_asset_url = story_dict.get("primary_asset_url")
        category = story_dict.get("category")
        reading_time = story_dict.get("estimated_reading_minutes") or story_dict.get("reading_time_minutes", 3)
        status = story_dict.get("status", "published")
        historical_context = {"chapters": story_dict.get("chapters", [])} if "chapters" in story_dict else None

        existing_story = existing_stories_by_slug.get(slug)
        if existing_story:
            # Preservation guardrail: stories that have undergone manual editorial review retain status and reviewed_by
            is_editorial_reviewed = (
                (existing_story.status in EDITORIAL_PRESERVED_STATUSES and (existing_story.reviewed_by is not None or existing_story.reviewed_at is not None))
                or existing_story.status in ("review", "in_review", "approved", "withdrawn")
            )
            if is_editorial_reviewed:
                stats.stories_preserved_editorial += 1
                existing_story.title_vi = title_vi
                existing_story.title_en = title_en
                existing_story.place_id = place_id
                existing_story.creator_id = creator_id
                existing_story.experience_id = experience_id
                existing_story.primary_asset_url = primary_asset_url
                existing_story.category = category
                existing_story.reading_time_minutes = reading_time
                if historical_context:
                    existing_story.historical_context_json = historical_context
                logger.debug("Preserved manual review for story '%s'", slug)
            else:
                existing_story.title_vi = title_vi
                existing_story.title_en = title_en
                existing_story.intro_vi = intro_vi
                existing_story.intro_en = intro_en
                existing_story.approved_summary_vi = approved_summary_vi
                existing_story.approved_summary_en = approved_summary_en
                existing_story.place_id = place_id
                existing_story.creator_id = creator_id
                existing_story.experience_id = experience_id
                existing_story.primary_asset_url = primary_asset_url
                existing_story.category = category
                existing_story.reading_time_minutes = reading_time
                existing_story.status = status
                if status == "published" and not existing_story.published_at:
                    existing_story.published_at = datetime.now(timezone.utc)
                if historical_context:
                    existing_story.historical_context_json = historical_context
                stats.stories_updated += 1
            target_story = existing_story
        else:
            new_story = RbpcStory(
                id=story_id,
                slug=slug,
                title_vi=title_vi,
                title_en=title_en,
                intro_vi=intro_vi,
                intro_en=intro_en,
                approved_summary_vi=approved_summary_vi,
                approved_summary_en=approved_summary_en,
                place_id=place_id,
                creator_id=creator_id,
                experience_id=experience_id,
                primary_asset_url=primary_asset_url,
                category=category,
                reading_time_minutes=reading_time,
                status=status,
                published_at=datetime.now(timezone.utc) if status == "published" else None,
                historical_context_json=historical_context,
                content_scope=CONTENT_SCOPE_DEFAULT,
            )
            db.add(new_story)
            existing_stories_by_slug[slug] = new_story
            target_story = new_story
            stats.stories_inserted += 1

        db.flush()

        # Evidence claims for this story
        existing_claims = list(db.scalars(select(RbpcClaimEvidence).where(RbpcClaimEvidence.story_id == target_story.id)))
        existing_claims_by_stmt = {c.statement: c for c in existing_claims}

        for claim_dict in story_dict.get("claims", []):
            statement = claim_dict.get("statement_vi") or claim_dict.get("statement", "")
            citation = claim_dict.get("source_locator") or claim_dict.get("citation_label")
            source_title = claim_dict.get("source_title", "")
            source_url = claim_dict.get("source_url")
            support_type = claim_dict.get("support_type", RbpcSupportType.direct.value)
            claim_category = claim_dict.get("claim_category", "historical_fact")
            excerpt_en = claim_dict.get("statement_en")

            existing_claim = existing_claims_by_stmt.get(statement)
            if existing_claim:
                existing_claim.source_title = source_title
                existing_claim.source_url = source_url
                existing_claim.support_type = support_type
                existing_claim.citation_label = citation
                existing_claim.claim_category = claim_category
                if excerpt_en:
                    existing_claim.evidence_excerpt_private = excerpt_en
                stats.claims_updated += 1
            else:
                new_claim = RbpcClaimEvidence(
                    id=uuid.uuid4(),
                    story_id=target_story.id,
                    statement=statement,
                    locale="vi",
                    claim_category=claim_category,
                    source_title=source_title,
                    source_url=source_url,
                    support_type=support_type,
                    citation_label=citation,
                    evidence_excerpt_private=excerpt_en,
                    review_status="verified",
                )
                db.add(new_claim)
                existing_claims_by_stmt[statement] = new_claim
                stats.claims_inserted += 1

    # 8. Preservation Check: rbpc_inquiries and rbpc_content_audit
    # Verify that re-importing content never touches or degrades existing visitor inquiries or audit logs
    existing_inquiries_count = db.scalar(select(func.count(RbpcInquiry.id))) or 0
    existing_audit_count = db.scalar(select(func.count(RbpcContentAudit.id))) or 0
    stats.inquiries_preserved = existing_inquiries_count
    stats.audit_logs_preserved = existing_audit_count

    # Verify audit hash chains are intact before final commit
    chains_intact, chain_summary = verify_all_audit_chains(db)
    if not chains_intact:
        logger.error("Audit hash chain verification failed during re-import: %s", chain_summary)
        raise RuntimeError(f"Audit hash chains corrupted during import: {chain_summary}")

    # Final commit
    db.commit()
    logger.info(
        "Huế heritage data sync complete: %d places inserted, %d updated, %d preserved; "
        "%d relations inserted; %d media inserted, %d updated; "
        "%d creators inserted, %d updated, %d preserved; "
        "%d inquiries preserved, %d audit logs preserved; "
        "%d experiences inserted, %d updated; "
        "%d stories inserted, %d updated, %d preserved; "
        "%d claims inserted, %d updated.",
        stats.places_inserted,
        stats.places_updated,
        stats.places_preserved_editorial,
        stats.relations_inserted,
        stats.media_inserted,
        stats.media_updated,
        stats.creators_inserted,
        stats.creators_updated,
        stats.creators_preserved_consent,
        stats.inquiries_preserved,
        stats.audit_logs_preserved,
        stats.experiences_inserted,
        stats.experiences_updated,
        stats.stories_inserted,
        stats.stories_updated,
        stats.stories_preserved_editorial,
        stats.claims_inserted,
        stats.claims_updated,
    )
    return report, stats


# --------------------------------------------------------------------------- #
# Service Class Interface
# --------------------------------------------------------------------------- #
class HeritageImportService:
    """Service wrapper for validating and importing Huế heritage catalogue data."""

    def __init__(
        self,
        db: Optional[Session] = None,
        inventory_path: Optional[Path | str] = None,
        sketchfab_path: Optional[Path | str] = None,
        stories_path: Optional[Path | str] = None,
        creators_path: Optional[Path | str] = None,
        experiences_path: Optional[Path | str] = None,
    ) -> None:
        self.db = db
        self.inventory_path = Path(inventory_path) if inventory_path else DEFAULT_INVENTORY_PATH
        self.sketchfab_path = Path(sketchfab_path) if sketchfab_path else DEFAULT_SKETCHFAB_PATH
        self.stories_path = Path(stories_path) if stories_path else DEFAULT_STORIES_PATH
        self.creators_path = Path(creators_path) if creators_path else DEFAULT_CREATORS_PATH
        self.experiences_path = Path(experiences_path) if experiences_path else DEFAULT_EXPERIENCES_PATH

    def validate(self) -> ValidationReport:
        """Run dry-run validation on the configured YAML inventory files."""
        inv_data = load_yaml_file(self.inventory_path)
        sf_data = load_yaml_file(self.sketchfab_path)
        cr_data = load_yaml_file(self.creators_path) if self.creators_path.is_file() else None
        exp_data = load_yaml_file(self.experiences_path) if self.experiences_path.is_file() else None
        st_data = load_yaml_file(self.stories_path) if self.stories_path.is_file() else None

        existing_slugs: set[str] = set()
        existing_cr_slugs: set[str] = set()
        existing_exp_slugs: set[str] = set()
        if self.db is not None:
            try:
                existing = self.db.execute(select(HeritagePlace.slug)).scalars().all()
                existing_slugs = set(existing)
                existing_cr = self.db.execute(select(RbpcCreator.slug)).scalars().all()
                existing_cr_slugs = set(existing_cr)
                existing_exp = self.db.execute(select(RbpcExperience.slug)).scalars().all()
                existing_exp_slugs = set(existing_exp)
            except Exception as e:
                logger.debug("Could not query existing slugs from DB: %s", e)
                try:
                    self.db.rollback()
                except Exception:
                    pass

        return validate_heritage_import(
            inv_data,
            sf_data,
            stories_data=st_data,
            creators_data=cr_data,
            experiences_data=exp_data,
            existing_slugs=existing_slugs,
            existing_creator_slugs=existing_cr_slugs,
            existing_experience_slugs=existing_exp_slugs,
        )

    def execute(self, dry_run: bool = True) -> tuple[ValidationReport, ImportStats]:
        """Execute validation and optionally commit the ingestion to the database."""
        if not dry_run and self.db is None:
            raise ValueError("A valid database Session is required to execute in commit mode (dry_run=False).")

        return import_heritage_data(
            db=self.db,  # type: ignore[arg-type]
            inventory_path=self.inventory_path,
            sketchfab_path=self.sketchfab_path,
            stories_path=self.stories_path,
            creators_path=self.creators_path,
            experiences_path=self.experiences_path,
            dry_run=dry_run,
        )
