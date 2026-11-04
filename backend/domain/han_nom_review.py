# -*- coding: utf-8 -*-
"""Hán–Nôm Script, Reading, Romanization & Translation Review Domain (V5-T026 / Wave W02).

Implements strict validation and epigraphic review lifecycle for Hán–Nôm attributes:
- Script glyphs (Hán–Nôm text).
- Sino-Vietnamese reading (phiên âm Hán-Việt).
- Modern Vietnamese gloss / translation.
- English translation / meaning.
- Epigraphic review status: unreviewed, provisional, uncertain, human_verified, verified, rejected.
- Uncertainty tracking: flagging disputed / provisional / uncertain readings.
- Negative abuse guardrail: AI-generated or guessed glyphs MUST NEVER be promoted
  to verified without a human epigrapher / expert review sign-off and valid source citation.
- Missing Hán-Nôm tracking for the 4 known motifs lacking glyphs:
  `urn_nghi_dinh_03`, `urn_thuan_dinh_13`, `urn_tuyen_dinh_11`, `urn_huyen_dinh_12`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
import re
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class HanNomReviewStatus(str, Enum):
    """Controlled vocabulary for Hán–Nôm glyph & reading review status."""
    missing = "missing"
    provisional = "provisional"
    uncertain = "uncertain"
    unreviewed = "unreviewed"
    human_verified = "human_verified"
    verified = "verified"
    rejected = "rejected"


VERIFIED_REVIEW_STATUSES: frozenset[str] = frozenset({
    HanNomReviewStatus.human_verified.value,
    HanNomReviewStatus.verified.value,
    "human_verified",
    "verified",
})

UNREVIEWED_REVIEW_STATUSES: frozenset[str] = frozenset({
    HanNomReviewStatus.unreviewed.value,
    HanNomReviewStatus.provisional.value,
    HanNomReviewStatus.uncertain.value,
    HanNomReviewStatus.missing.value,
    "unreviewed",
    "provisional",
    "uncertain",
    "missing",
})

# Disqualified placeholder / fabricated citation markers
DISQUALIFIED_CITATION_MARKERS: frozenset[str] = frozenset({
    "unknown",
    "none",
    "n/a",
    "na",
    "null",
    "undefined",
    "citation",
    "needed",
    "citation needed",
    "tbd",
    "todo",
    "placeholder",
    "fake",
    "fabricated",
    "unverified",
    "test",
    "dummy",
})


def is_valid_source_citation(source_citation: Optional[str]) -> bool:
    """Validate that a source citation is substantive, present, and not placeholder/fabricated."""
    if not source_citation or not str(source_citation).strip():
        return False
    sc = str(source_citation).strip().lower()
    if len(sc) < 4:
        return False
    if sc in DISQUALIFIED_CITATION_MARKERS:
        return False
    if sc in {"?", "-", "--", "...", "n/a", "none"}:
        return False
    words = set(re.findall(r"\w+", sc))
    if words and (words.issubset(DISQUALIFIED_CITATION_MARKERS) or any(w in {"dummy", "fake", "placeholder", "tbd", "todo"} for w in words)):
        return False
    if any(marker in sc for marker in ("citation needed", "dummy citation", "unknown source", "placeholder source")):
        return False
    return True


class HanNomProvenanceOrigin(str, Enum):
    """Provenance origin of the glyph or reading candidate."""
    epigrapher_verified = "epigrapher_verified"
    historical_record = "historical_record"
    scholarly_edition = "scholarly_edition"
    ai_generated = "ai_generated"
    ai_ocr_candidate = "ai_ocr_candidate"
    unspecified_seed = "unspecified_seed"


class HanNomReviewError(ValueError):
    """Raised when epigraphic review or promotion rules are violated."""
    pass


class UnverifiedPromotionForbiddenError(HanNomReviewError):
    """Raised when an unverified or AI-guessed glyph/reading attempts to promote to verified."""
    pass


@dataclass(frozen=True)
class HanNomMotifReviewRecord:
    """Represents a canonical motif's Hán-Nôm script and reading review status."""
    motif_id: str
    urn_slug: str
    name_vi: str
    name_en: Optional[str]
    han_nom_glyphs: Optional[str]
    sino_vietnamese_reading: Optional[str]
    modern_vi_meaning: Optional[str]
    english_translation: Optional[str]
    review_status: HanNomReviewStatus
    origin: HanNomProvenanceOrigin
    reference_image_url: Optional[str] = None
    epigrapher_signoff: Optional[str] = None
    notes: Optional[str] = None
    is_uncertain: bool = False
    is_ai_guessed: bool = False
    source_citation: Optional[str] = None

    @property
    def han_nom_text(self) -> Optional[str]:
        return self.han_nom_glyphs

    @property
    def reading_quoc_ngu(self) -> Optional[str]:
        return self.sino_vietnamese_reading

    @property
    def translation_vi(self) -> Optional[str]:
        return self.modern_vi_meaning

    @property
    def translation_en(self) -> Optional[str]:
        return self.english_translation


# Known incomplete motifs from W00 / baseline audit lacking Hán–Nôm glyphs
KNOWN_MISSING_HAN_NOM_MOTIF_IDS: frozenset[str] = frozenset({
    "urn_nghi_dinh_03",   # Đàn Mộc
    "urn_thuan_dinh_13",  # Đăng Sơn Ngư
    "urn_tuyen_dinh_11",  # Đại Lãnh
    "urn_huyen_dinh_12",  # Thao Hà
})


class HanNomTranslationReview(BaseModel):
    """Structured Hán-Nôm review schema (V5-T026).
    
    Fields:
    - han_nom_text: Original Chinese/Nom glyphs
    - reading_quoc_ngu: Standard Sino-Vietnamese reading
    - translation_vi: Modern Vietnamese semantic translation
    - translation_en: English translation
    - is_uncertain: Boolean flag preserving doubtful/unconfirmed readings
    - review_status: verified or unreviewed (or other valid statuses)
    - source_citation: Epigraphic/historical bibliographic source citation
    - epigrapher_signoff: Expert reviewer identification/signature
    """
    motif_id: str
    urn_slug: Optional[str] = None
    han_nom_text: Optional[str] = None
    reading_quoc_ngu: Optional[str] = None
    translation_vi: Optional[str] = None
    translation_en: Optional[str] = None
    is_uncertain: bool = False
    review_status: HanNomReviewStatus = HanNomReviewStatus.unreviewed
    origin: HanNomProvenanceOrigin = HanNomProvenanceOrigin.ai_generated
    is_ai_guessed: bool = False
    source_citation: Optional[str] = None
    epigrapher_signoff: Optional[str] = None
    reference_image_url: Optional[str] = None
    review_notes: Optional[str] = None

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def normalize_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "han_nom_glyphs" in data and "han_nom_text" not in data:
                data["han_nom_text"] = data["han_nom_glyphs"]
            if "sino_vietnamese_reading" in data and "reading_quoc_ngu" not in data:
                data["reading_quoc_ngu"] = data["sino_vietnamese_reading"]
            if "modern_vi_meaning" in data and "translation_vi" not in data:
                data["translation_vi"] = data["modern_vi_meaning"]
            if "english_translation" in data and "translation_en" not in data:
                data["translation_en"] = data["english_translation"]
        return data

    @model_validator(mode="after")
    def validate_review_invariants(self) -> HanNomTranslationReview:
        status_val = self.review_status.value if isinstance(self.review_status, Enum) else str(self.review_status)
        is_verified = status_val in VERIFIED_REVIEW_STATUSES

        if is_verified:
            # 1. Glyphs must be present and non-empty
            if not self.han_nom_text or not self.han_nom_text.strip():
                raise HanNomReviewError("Cannot mark review as verified with empty or missing han_nom_text.")

            # 2. Reading and translations must be valid
            if not self.reading_quoc_ngu or not self.reading_quoc_ngu.strip():
                raise HanNomReviewError("Verified review must include a valid reading_quoc_ngu.")
            if not self.translation_vi or not self.translation_vi.strip():
                raise HanNomReviewError("Verified review must include a valid translation_vi.")

            # 3. Cannot be marked uncertain while verified
            if self.is_uncertain:
                raise HanNomReviewError("Uncertain or doubtful reading cannot be marked as verified.")

            # 4. Expert human review signoff is mandatory
            if not self.epigrapher_signoff or not self.epigrapher_signoff.strip():
                raise UnverifiedPromotionForbiddenError(
                    "Negative Abuse: No unverified or guessed glyph can be marked as verified "
                    "without expert human review."
                )

            # 5. Source citation is mandatory for verified
            if not is_valid_source_citation(self.source_citation):
                raise UnverifiedPromotionForbiddenError(
                    "Negative Abuse: Guessing glyph without source citation is blocked or flagged."
                )

        # Negative abuse: If guessed or machine-generated, verify requires both signoff and valid citation
        if self.is_ai_guessed or self.origin in (
            HanNomProvenanceOrigin.ai_generated,
            HanNomProvenanceOrigin.ai_ocr_candidate,
            HanNomProvenanceOrigin.unspecified_seed,
        ):
            if is_verified:
                if not is_valid_source_citation(self.source_citation):
                    raise UnverifiedPromotionForbiddenError(
                        "Negative Abuse: Guessing glyph without source citation is blocked or flagged."
                    )
                if not self.epigrapher_signoff or not self.epigrapher_signoff.strip():
                    raise UnverifiedPromotionForbiddenError(
                        "AI-guessed or machine-generated glyphs must never be promoted to verified "
                        "without human epigrapher sign-off."
                    )
        return self


class HanNomReviewInput(BaseModel):
    """Schema for validating and submitting epigraphic reviews and status transitions."""
    motif_id: str
    han_nom_glyphs: Optional[str] = None
    han_nom_text: Optional[str] = None
    sino_vietnamese_reading: Optional[str] = None
    reading_quoc_ngu: Optional[str] = None
    modern_vi_meaning: Optional[str] = None
    translation_vi: Optional[str] = None
    english_translation: Optional[str] = None
    translation_en: Optional[str] = None
    review_status: HanNomReviewStatus = HanNomReviewStatus.provisional
    origin: HanNomProvenanceOrigin = HanNomProvenanceOrigin.ai_generated
    is_ai_guessed: bool = False
    is_uncertain: bool = False
    source_citation: Optional[str] = None
    epigrapher_signoff: Optional[str] = None
    reference_image_url: Optional[str] = None
    review_notes: Optional[str] = None

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def sync_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "han_nom_text" in data and "han_nom_glyphs" not in data:
                data["han_nom_glyphs"] = data["han_nom_text"]
            elif "han_nom_glyphs" in data and "han_nom_text" not in data:
                data["han_nom_text"] = data["han_nom_glyphs"]
            if "reading_quoc_ngu" in data and "sino_vietnamese_reading" not in data:
                data["sino_vietnamese_reading"] = data["reading_quoc_ngu"]
            elif "sino_vietnamese_reading" in data and "reading_quoc_ngu" not in data:
                data["reading_quoc_ngu"] = data["sino_vietnamese_reading"]
            if "translation_vi" in data and "modern_vi_meaning" not in data:
                data["modern_vi_meaning"] = data["translation_vi"]
            elif "modern_vi_meaning" in data and "translation_vi" not in data:
                data["translation_vi"] = data["modern_vi_meaning"]
            if "translation_en" in data and "english_translation" not in data:
                data["english_translation"] = data["translation_en"]
            elif "english_translation" in data and "translation_en" not in data:
                data["translation_en"] = data["english_translation"]
        return data

    @model_validator(mode="after")
    def validate_promotion_guardrails(self) -> HanNomReviewInput:
        status_val = self.review_status.value if isinstance(self.review_status, Enum) else str(self.review_status)
        is_verified = status_val in VERIFIED_REVIEW_STATUSES

        if is_verified:
            effective_glyphs = self.han_nom_text or self.han_nom_glyphs
            if not effective_glyphs or not effective_glyphs.strip():
                raise HanNomReviewError("Cannot promote empty Hán-Nôm glyphs to verified.")

            if self.is_uncertain:
                raise HanNomReviewError("Uncertain or doubtful reading cannot be marked as verified.")

            if self.is_ai_guessed or self.origin in (
                HanNomProvenanceOrigin.ai_generated,
                HanNomProvenanceOrigin.ai_ocr_candidate,
                HanNomProvenanceOrigin.unspecified_seed,
            ):
                if not self.epigrapher_signoff or not self.epigrapher_signoff.strip():
                    raise UnverifiedPromotionForbiddenError(
                        "AI-guessed or machine-generated glyphs must never be promoted to verified "
                        "without human epigrapher sign-off."
                    )
                if not is_valid_source_citation(self.source_citation):
                    raise UnverifiedPromotionForbiddenError(
                        "Negative Abuse: Guessing glyph without source citation is blocked or flagged."
                    )
        return self


def validate_han_nom_promotion(
    current_status: HanNomReviewStatus,
    target_status: HanNomReviewStatus,
    origin: HanNomProvenanceOrigin,
    is_ai_guessed: bool,
    epigrapher_signoff: Optional[str] = None,
    glyphs: Optional[str] = None,
    source_citation: Optional[str] = None,
    reading: Optional[str] = None,
    translation_vi: Optional[str] = None,
) -> None:
    """Strictly validates whether a glyph / reading candidate can be promoted to target status.

    Rules:
    1. If target_status is 'human_verified' or 'verified':
       - Glyphs cannot be empty/whitespace.
       - If is_ai_guessed is True, promotion is strictly FORBIDDEN without an epigrapher sign-off.
       - If origin is AI or unverified seed, promotion is strictly FORBIDDEN without human epigrapher sign-off.
       - Source citation cannot be missing, empty, or placeholder.
    2. Uncertain or disputed readings MUST remain flagged with is_uncertain=True or status=uncertain/provisional/unreviewed.
    """
    target_val = target_status.value if isinstance(target_status, Enum) else str(target_status)
    if target_val in VERIFIED_REVIEW_STATUSES:
        if not glyphs or not glyphs.strip():
            raise HanNomReviewError("Cannot promote empty Hán-Nôm glyphs to verified.")

        if is_ai_guessed:
            if not epigrapher_signoff or not epigrapher_signoff.strip():
                raise UnverifiedPromotionForbiddenError(
                    "Violation: Guessed or unverified AI glyph cannot be marked verified "
                    "without human epigrapher review."
                )
            if not is_valid_source_citation(source_citation):
                raise UnverifiedPromotionForbiddenError(
                    "Violation: Guessing glyph without source citation is blocked or flagged."
                )

        if origin in (
            HanNomProvenanceOrigin.ai_generated,
            HanNomProvenanceOrigin.ai_ocr_candidate,
            HanNomProvenanceOrigin.unspecified_seed,
        ):
            if not epigrapher_signoff or not epigrapher_signoff.strip():
                raise UnverifiedPromotionForbiddenError(
                    "Violation: AI/machine candidate glyph cannot be marked verified "
                    "without human epigrapher review."
                )
            if not is_valid_source_citation(source_citation):
                raise UnverifiedPromotionForbiddenError(
                    "Violation: Guessing glyph without source citation is blocked or flagged."
                )

        if not epigrapher_signoff or not epigrapher_signoff.strip():
            raise UnverifiedPromotionForbiddenError(
                "Violation: Promotion to verified requires human epigrapher signoff."
            )


def audit_162_han_nom_dataset(
    data_dir: Path | str,
) -> dict[str, Any]:
    """Audit all 162 motif records across data/*Data*Dinh.json files for Hán-Nôm attributes.

    Returns structured summary with:
    - total_motifs (162)
    - with_han_nom (158)
    - missing_han_nom (4)
    - identified_missing_motifs list matching KNOWN_MISSING_HAN_NOM_MOTIF_IDS
    - list of audited motif review records
    """
    data_path = Path(data_dir)
    total_motifs = 0
    with_han_nom = 0
    missing_items: list[dict[str, Any]] = []
    audited_records: list[HanNomMotifReviewRecord] = []

    files = sorted(data_path.glob("*Data*Dinh.json"))
    for file_path in files:
        with open(file_path, "r", encoding="utf-8") as f:
            items = json.load(f)
            for item in items:
                total_motifs += 1
                motif_id = item.get("id", "")
                name_vi = item.get("name_vi", "")
                name_en = item.get("name_en")
                urn_location = item.get("urn_location", "")
                han_nom = item.get("name_han_nom")
                is_ai_gen = bool(item.get("is_ai_generated", True))
                thumb = item.get("thumbnail_url")

                if han_nom and str(han_nom).strip():
                    with_han_nom += 1
                    # In raw seed data, AI-generated seed glyphs are provisional / unreviewed by epigrapher
                    record = HanNomMotifReviewRecord(
                        motif_id=motif_id,
                        urn_slug=urn_location,
                        name_vi=name_vi,
                        name_en=name_en,
                        han_nom_glyphs=str(han_nom).strip(),
                        sino_vietnamese_reading=name_vi,
                        modern_vi_meaning=item.get("description_short"),
                        english_translation=name_en,
                        review_status=HanNomReviewStatus.provisional,
                        origin=HanNomProvenanceOrigin.ai_generated if is_ai_gen else HanNomProvenanceOrigin.historical_record,
                        reference_image_url=thumb,
                        epigrapher_signoff=None,
                        notes="Raw seed glyph - requires human epigrapher review before verified promotion.",
                        is_uncertain=False,
                        is_ai_guessed=is_ai_gen,
                        source_citation=None,
                    )
                else:
                    record = HanNomMotifReviewRecord(
                        motif_id=motif_id,
                        urn_slug=urn_location,
                        name_vi=name_vi,
                        name_en=name_en,
                        han_nom_glyphs=None,
                        sino_vietnamese_reading=None,
                        modern_vi_meaning=item.get("description_short"),
                        english_translation=name_en,
                        review_status=HanNomReviewStatus.missing,
                        origin=HanNomProvenanceOrigin.ai_generated if is_ai_gen else HanNomProvenanceOrigin.unspecified_seed,
                        reference_image_url=thumb,
                        epigrapher_signoff=None,
                        notes="Missing Hán-Nôm glyph in primary seed - tracked as pending epigrapher review.",
                        is_uncertain=True,
                        is_ai_guessed=False,
                        source_citation=None,
                    )
                    missing_items.append({
                        "id": motif_id,
                        "name_vi": name_vi,
                        "urn": urn_location,
                        "review_status": HanNomReviewStatus.missing.value,
                        "is_uncertain": True,
                    })

                audited_records.append(record)

    missing_ids = {m["id"] for m in missing_items}

    return {
        "total_motifs": total_motifs,
        "with_han_nom": with_han_nom,
        "missing_count": len(missing_items),
        "missing_ids": sorted(list(missing_ids)),
        "matches_expected_missing": missing_ids == KNOWN_MISSING_HAN_NOM_MOTIF_IDS,
        "missing_motifs": missing_items,
        "records": audited_records,
    }
