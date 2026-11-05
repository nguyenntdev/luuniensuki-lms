# -*- coding: utf-8 -*-
"""P05/P06 Multi-Source Corroboration, Contradiction Detection, & Scholarly Disputes.

Implements AIR-021, AIR-022, AIR-023 contracts:
1. Normalizes editions and identifies duplicate / mirror sources (no double-counting).
2. Detects contradictions across sources and claims.
3. Maintains the scholarly dispute ledger (disagreements cannot be suppressed).
4. Resolves date and place disagreements with temporal and precision reasoning.
"""
from __future__ import annotations

import re
import uuid
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from pydantic import BaseModel, Field

from ...history_models import (
    HistoricalClaim,
    HistoricalClaimSource,
    HistoricalConfidence,
    HistoricalEntity,
    HistoricalSource,
    HistoricalSupportType,
    HistoricalVerificationStatus,
)
from .citations import (
    MismatchedPageCitationError,
    ResearchFactoryCitationError,
    UncorroboratedClaimCitationError,
    validate_citation_locator,
)


class ContradictionStatus(str, Enum):
    OPEN = "OPEN"
    SCHOLARLY_DISPUTED = "SCHOLARLY_DISPUTED"
    RESOLVED = "RESOLVED"


class DisputeCategory(str, Enum):
    EPIGRAPHIC_READING = "epigraphic_reading"
    CHRONOLOGY = "chronology"
    GEOGRAPHIC_BOUNDARY = "geographic_boundary"
    IDENTIFICATION_NAMING = "identification_naming"
    MATERIAL_TECHNIQUE = "material_technique"
    SYMBOLISM = "symbolism"


# --------------------------------------------------------------------------- #
# Typed Exceptions
# --------------------------------------------------------------------------- #
class DisputedClaimCannotAutoVerifyError(ResearchFactoryCitationError):
    """Raised when an active, unresolved contradiction or dispute is attempted to be verified."""
    pass


class OverpreciseChronologyError(ResearchFactoryCitationError):
    """Raised when a claim asserts exact date precision not supported by its underlying source."""
    pass


class AnachronisticGeographyError(ResearchFactoryCitationError):
    """Raised when modern boundaries or names are projected onto historical dynasties without temporal mapping."""
    pass


# --------------------------------------------------------------------------- #
# Data Schemas
# --------------------------------------------------------------------------- #
class CanonicalWork(BaseModel):
    work_code: str
    canonical_title: str
    work_type: str
    original_era: str
    known_aliases: List[str] = Field(default_factory=list)


class NormalizedEdition(BaseModel):
    work_code: str
    canonical_title: str
    edition_label: str
    publisher: Optional[str] = None
    publication_year: Optional[int] = None
    volume: Optional[str] = None
    is_canonical_match: bool = False
    is_derivative: bool = False


class MirrorDetectionResult(BaseModel):
    total_sources_evaluated: int
    independent_origin_count: int
    mirror_groups: Dict[str, List[str]]
    warnings: List[str] = Field(default_factory=list)


class ContradictionRecord(BaseModel):
    contradiction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subject_id: str
    conflict_category: str
    claim_a_id: str
    claim_b_id: str
    statement_a: str
    statement_b: str
    source_a_id: Optional[str] = None
    source_b_id: Optional[str] = None
    status: ContradictionStatus = ContradictionStatus.OPEN
    resolution_rationale: Optional[str] = None
    resolved_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ScholarlyDispute(BaseModel):
    dispute_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic: str
    category: DisputeCategory
    subject_slug: str
    contending_claims: List[Dict[str, Any]] = Field(default_factory=list)
    contending_sources: List[Dict[str, Any]] = Field(default_factory=list)
    scholarly_positions: List[Dict[str, Any]] = Field(default_factory=list)
    status: ContradictionStatus = ContradictionStatus.SCHOLARLY_DISPUTED
    epistemic_certainty: str = "contested"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# --------------------------------------------------------------------------- #
# Canonical Works Registry (Cửu Đỉnh Historiography)
# --------------------------------------------------------------------------- #
CANONICAL_WORKS: Dict[str, CanonicalWork] = {
    "WORK-DNTL": CanonicalWork(
        work_code="WORK-DNTL",
        canonical_title="Đại Nam thực lục",
        work_type="royal_chronicle",
        original_era="Nhà Nguyễn (Quốc sử quán)",
        known_aliases=["Đại Nam thực lục chính biên", "DNTL", "Veritable Records of Dai Nam"],
    ),
    "WORK-DNNTC": CanonicalWork(
        work_code="WORK-DNNTC",
        canonical_title="Đại Nam nhất thống chí",
        work_type="geographical_gazetteer",
        original_era="Nhà Nguyễn (Quốc sử quán)",
        known_aliases=["DNNTC", "Dai Nam Nhat Thong Chi"],
    ),
    "WORK-KDHDSL": CanonicalWork(
        work_code="WORK-KDHDSL",
        canonical_title="Khâm định Đại Nam hội điển sự lệ",
        work_type="administrative_statute",
        original_era="Nhà Nguyễn (Nội các)",
        known_aliases=["Hội điển sự lệ", "KDHDSL", "Hoi Dien Su Le"],
    ),
    "WORK-DKDDC": CanonicalWork(
        work_code="WORK-DKDDC",
        canonical_title="Đồng Khánh địa dư chí",
        work_type="geographical_gazetteer",
        original_era="Thời Đồng Khánh (Quốc sử quán)",
        known_aliases=["DKDDC", "Dong Khanh Dia Du Chi"],
    ),
    "WORK-CDH-2012": CanonicalWork(
        work_code="WORK-CDH-2012",
        canonical_title="Cửu Đỉnh Huế - Bảo tàng Cổ vật Cung đình Huế",
        work_type="museum_catalog",
        original_era="Hiện đại (Trung tâm BTTD Cố đô Huế)",
        known_aliases=["Cửu Đỉnh Huế", "Cuu Dinh Hue 2012"],
    ),
}

# Known temporal correspondence: reign year -> Western Gregorian calendar
REIGN_YEAR_MAP = {
    ("minh mạng", 16): 1835,
    ("minh mạng", 17): 1836,
    ("minh mạng", 18): 1837,
    ("minh mạng", 19): 1838,
    ("minh mạng", 20): 1839,
    ("minh mạng", 21): 1840,
    ("thiệu trị", 1): 1841,
    ("thiệu trị", 2): 1842,
    ("tự đức", 1): 1848,
    ("đồng khánh", 1): 1886,
}

# Historical place mapping to modern correspondence
HISTORICAL_GEOGRAPHY_REGISTRY = {
    "trấn hải đài": {
        "modern_name": "Cửa Thuận An, Thừa Thiên Huế",
        "historical_province": "Thừa Thiên phủ",
        "precision": "settlement",
    },
    "hải vân quan": {
        "modern_name": "Đèo Hải Vân, ranh giới Đà Nẵng và Thừa Thiên Huế",
        "historical_province": "Thừa Thiên phủ",
        "precision": "exact",
    },
    "bạch đằng giang": {
        "modern_name": "Sông Bạch Đằng, Quảng Ninh và Hải Phòng",
        "historical_province": "Hải Dương / Quảng Yên",
        "precision": "water_body",
    },
    "thừa thiên phủ": {
        "modern_name": "Tỉnh Thừa Thiên Huế",
        "historical_province": "Kinh kỳ Thừa Thiên",
        "precision": "region",
    },
    "kinh thành huế": {
        "modern_name": "Hoàng thành và Kinh thành Huế",
        "historical_province": "Thừa Thiên phủ",
        "precision": "exact",
    },
}


# --------------------------------------------------------------------------- #
# Edition Normalization & Mirror Detection (P04 / P05)
# --------------------------------------------------------------------------- #
def normalize_edition(
    raw_title: str,
    publisher: Optional[str] = None,
    publication_year: Optional[int] = None,
    volume: Optional[str] = None,
) -> NormalizedEdition:
    """Normalizes raw bibliographic citation into canonical work and standardized edition."""
    norm_title = raw_title.strip()
    clean_lower = norm_title.lower()

    matched_work_code: Optional[str] = None
    canonical_title = norm_title

    for code, work in CANONICAL_WORKS.items():
        if work.canonical_title.lower() in clean_lower:
            matched_work_code = code
            canonical_title = work.canonical_title
            break
        for alias in work.known_aliases:
            if alias.lower() in clean_lower:
                matched_work_code = code
                canonical_title = work.canonical_title
                break
        if matched_work_code:
            break

    if not matched_work_code:
        # Generic slug
        matched_work_code = f"WORK-CUSTOM-{hash(norm_title) & 0xFFFFFF}"

    # Normalize volume
    norm_vol = None
    if volume:
        v_str = str(volume).strip()
        v_match = re.search(r'(\d+|[IVXLCDM]+)', v_str, re.IGNORECASE)
        norm_vol = v_match.group(1).upper() if v_match else v_str

    # Build standardized edition label
    label_parts = [canonical_title]
    if norm_vol:
        label_parts.append(f"Tập {norm_vol}")
    if publisher:
        label_parts.append(publisher.strip())
    if publication_year:
        label_parts.append(f"({publication_year})")

    edition_label = ", ".join(label_parts)
    is_derivative = publication_year is not None and publication_year > 1945 and matched_work_code.startswith("WORK-DN")

    return NormalizedEdition(
        work_code=matched_work_code,
        canonical_title=canonical_title,
        edition_label=edition_label,
        publisher=publisher,
        publication_year=publication_year,
        volume=norm_vol,
        is_canonical_match=matched_work_code in CANONICAL_WORKS,
        is_derivative=is_derivative,
    )


def detect_duplicate_or_mirror_sources(
    sources: List[HistoricalSource | Dict[str, Any]]
) -> MirrorDetectionResult:
    """Detects duplicate or mirror editions of the same primary root work.
    
    Prevents counting reprint/derivative mirrors twice as independent corroborating witnesses (P05 Gate).
    """
    origin_map: Dict[str, List[str]] = {}
    warnings: List[str] = []

    for s in sources:
        if isinstance(s, dict):
            s_id = str(s.get("id", "unknown"))
            title = s.get("title", "")
            pub = s.get("publisher")
            year = s.get("publication_year")
            vol = s.get("volume")
        else:
            s_id = str(getattr(s, "id", "unknown"))
            title = getattr(s, "title", "")
            pub = getattr(s, "publisher", None)
            year = getattr(s, "publication_year", None)
            vol = getattr(s, "volume", None)


        norm = normalize_edition(title, pub, year, vol)
        if norm.work_code not in origin_map:
            origin_map[norm.work_code] = []
        origin_map[norm.work_code].append(s_id)

    mirror_groups = {k: v for k, v in origin_map.items() if len(v) > 1}
    for code, group in mirror_groups.items():
        work_name = CANONICAL_WORKS[code].canonical_title if code in CANONICAL_WORKS else code
        warnings.append(
            f"Detected {len(group)} mirror editions of canonical work '{work_name}' (ids={group}). Counted as 1 independent origin."
        )

    return MirrorDetectionResult(
        total_sources_evaluated=len(sources),
        independent_origin_count=len(origin_map),
        mirror_groups=mirror_groups,
        warnings=warnings,
    )


# --------------------------------------------------------------------------- #
# Contradiction Detection & Scholarly Dispute Ledger (P05 / P06)
# --------------------------------------------------------------------------- #
class ScholarlyDisputeLedger:
    """In-memory and persistent ledger tracking historical contradictions and scholarly debates."""

    def __init__(self) -> None:
        self._disputes: Dict[str, ScholarlyDispute] = {}
        self._contradictions: Dict[str, ContradictionRecord] = {}

    def register_contradiction(
        self,
        subject_id: str,
        conflict_category: str,
        claim_a: HistoricalClaim | Dict[str, Any],
        claim_b: HistoricalClaim | Dict[str, Any],
        source_a: Optional[HistoricalSource | Dict[str, Any]] = None,
        source_b: Optional[HistoricalSource | Dict[str, Any]] = None,
        status: ContradictionStatus = ContradictionStatus.OPEN,
    ) -> ContradictionRecord:
        """Records a detected contradiction between two claims."""
        cid = str(uuid.uuid4())
        claim_a_id = str(getattr(claim_a, "id", None) or claim_a.get("id"))
        claim_b_id = str(getattr(claim_b, "id", None) or claim_b.get("id"))
        stmt_a = getattr(claim_a, "statement_vi", None) or claim_a.get("statement_vi", "")
        stmt_b = getattr(claim_b, "statement_vi", None) or claim_b.get("statement_vi", "")

        src_a_id = str(getattr(source_a, "id", None) or (source_a.get("id") if isinstance(source_a, dict) else None)) if source_a else None
        src_b_id = str(getattr(source_b, "id", None) or (source_b.get("id") if isinstance(source_b, dict) else None)) if source_b else None

        record = ContradictionRecord(
            contradiction_id=cid,
            subject_id=subject_id,
            conflict_category=conflict_category,
            claim_a_id=claim_a_id,
            claim_b_id=claim_b_id,
            statement_a=stmt_a,
            statement_b=stmt_b,
            source_a_id=src_a_id,
            source_b_id=src_b_id,
            status=status,
        )
        self._contradictions[cid] = record
        return record

    def register_dispute(
        self,
        topic: str,
        category: DisputeCategory,
        subject_slug: str,
        contending_claims: List[Dict[str, Any]],
        contending_sources: List[Dict[str, Any]],
        scholarly_positions: List[Dict[str, Any]],
    ) -> ScholarlyDispute:
        """Enforces scholarly dispute tracking without suppressing disagreement (P06-A07)."""
        dispute_id = f"DISP-{subject_slug}-{len(self._disputes) + 1:03d}"
        dispute = ScholarlyDispute(
            dispute_id=dispute_id,
            topic=topic,
            category=category,
            subject_slug=subject_slug,
            contending_claims=contending_claims,
            contending_sources=contending_sources,
            scholarly_positions=scholarly_positions,
            status=ContradictionStatus.SCHOLARLY_DISPUTED,
            epistemic_certainty="contested",
        )
        self._disputes[dispute_id] = dispute
        return dispute

    def list_disputes_for_subject(self, subject_slug: str) -> List[ScholarlyDispute]:
        return [d for d in self._disputes.values() if d.subject_slug == subject_slug]

    def has_unresolved_dispute(self, subject_slug: str) -> bool:
        return any(
            d.status in (ContradictionStatus.OPEN, ContradictionStatus.SCHOLARLY_DISPUTED)
            for d in self._disputes.values()
            if d.subject_slug == subject_slug
        )

    def assert_can_verify(self, claim: HistoricalClaim | Dict[str, Any], subject_slug: str) -> None:
        """Gate check: A disputed claim cannot auto-verify without explicit resolution."""
        claim_type = getattr(claim, "claim_type", None) or claim.get("claim_type")
        claim_conf = getattr(claim, "confidence", None) or claim.get("confidence")

        if claim_type == "disputed" or claim_conf in ("disputed", "contested"):
            raise DisputedClaimCannotAutoVerifyError(
                f"Cannot verify claim '{getattr(claim, 'statement_vi', '')[:30]}': marked disputed in dispute ledger.",
                {"subject_slug": subject_slug},
            )

        if self.has_unresolved_dispute(subject_slug):
            # Check if this claim is one of the disputed ones
            claim_id = str(getattr(claim, "id", None) or claim.get("id", ""))
            for d in self.list_disputes_for_subject(subject_slug):
                for c in d.contending_claims:
                    if str(c.get("id")) == claim_id and d.status != ContradictionStatus.RESOLVED:
                        raise DisputedClaimCannotAutoVerifyError(
                            f"Cannot verify claim '{claim_id}': subject '{subject_slug}' has unresolved scholarly dispute '{d.topic}'",
                            {"dispute_id": d.dispute_id, "topic": d.topic},
                        )


# Global singleton instance for runtime ledger
dispute_ledger = ScholarlyDisputeLedger()


# --------------------------------------------------------------------------- #
# Date & Chronology Disagreement Resolution (P05 / P06)
# --------------------------------------------------------------------------- #
def resolve_date_chronology(
    date_a_spec: Dict[str, Any],
    date_b_spec: Dict[str, Any],
    entity_slug: str = "cao-dinh",
) -> Dict[str, Any]:
    """Resolves chronology statements and enforces precision integrity (AIR-023).
    
    Negative abuse enforcement:
    - If source precision is 'decade' but claim specifies 'exact_day', raises OverpreciseChronologyError.
    - If milestones represent genuine distinct phases (start 1835 vs completion 1836/1837), reconciles them as sequential milestones.
    - If true conflicting years on same milestone, flags a chronological dispute.
    """
    prec_a = date_a_spec.get("date_precision", "approximate")
    prec_b = date_b_spec.get("date_precision", "approximate")

    year_a = date_a_spec.get("year")
    year_b = date_b_spec.get("year")
    milestone_a = date_a_spec.get("milestone", "event")
    milestone_b = date_b_spec.get("milestone", "event")

    # Negative check: Overprecise assertion
    source_precision = date_a_spec.get("source_precision")
    asserted_precision = date_a_spec.get("asserted_precision")
    if source_precision == "decade" and asserted_precision in ("exact_day", "exact"):
        raise OverpreciseChronologyError(
            f"Overprecise chronology error: source provides only decade precision, but claim asserted exact day.",
            {"source_precision": source_precision, "asserted_precision": asserted_precision},
        )


    # Convert reign years if provided
    reign_a = date_a_spec.get("reign_era")
    reign_num_a = date_a_spec.get("reign_year")
    if reign_a and reign_num_a:
        year_a = REIGN_YEAR_MAP.get((reign_a.lower(), reign_num_a), year_a)

    reign_b = date_b_spec.get("reign_era")
    reign_num_b = date_b_spec.get("reign_year")
    if reign_b and reign_num_b:
        year_b = REIGN_YEAR_MAP.get((reign_b.lower(), reign_num_b), year_b)

    # Milestone differentiation: e.g. 1835 (casting start) vs 1837 (installed before Thế Miếu)
    if milestone_a != milestone_b:
        return {
            "is_compatible": True,
            "status": "COMPATIBLE_SEQUENTIAL_MILESTONES",
            "milestone_sequence": [
                {"milestone": milestone_a, "year": year_a, "precision": prec_a},
                {"milestone": milestone_b, "year": year_b, "precision": prec_b},
            ],
            "narrative_vi": f"Tiến trình đúc Cửu Đỉnh diễn ra qua nhiều giai đoạn: {milestone_a} ({year_a}) và {milestone_b} ({year_b}).",
        }

    # Same milestone: check if year coincides
    if year_a == year_b:
        return {
            "is_compatible": True,
            "status": "CONCORDANT_CHRONOLOGY",
            "year": year_a,
            "precision": prec_a,
        }

    # Same milestone with conflicting years -> True contradiction
    return {
        "is_compatible": False,
        "status": "CHRONOLOGY_CONTRADICTION",
        "conflicting_years": [year_a, year_b],
        "dispute_summary": f"Bất đồng niên đại về '{milestone_a}': Nguồn 1 ghi năm {year_a}, nguồn 2 ghi năm {year_b}.",
    }


# --------------------------------------------------------------------------- #
# Place & Geography Temporal Mapping (P05 / P06)
# --------------------------------------------------------------------------- #
def resolve_place_geography(
    historical_place_name: str,
    modern_correspondence_claimed: Optional[str] = None,
    allow_anachronism: bool = False,
) -> Dict[str, Any]:
    """Resolves historical geography with temporal mapping and guards against anachronisms (AIR-023)."""
    clean_hist = historical_place_name.strip().lower()
    entry = HISTORICAL_GEOGRAPHY_REGISTRY.get(clean_hist)

    if not entry:
        return {
            "historical_place": historical_place_name,
            "mapping_status": "unreviewed",
            "modern_name": modern_correspondence_claimed or "Chưa đối soát vị trí hiện đại",
            "geo_precision": "approximate",
        }

    expected_modern = entry["modern_name"]
    expected_province = entry["historical_province"]

    if modern_correspondence_claimed:
        claimed_clean = modern_correspondence_claimed.strip().lower()
        # If user claims a modern province directly as the historical Nguyễn province without note
        if "tỉnh " in claimed_clean and "phủ" not in claimed_clean and not allow_anachronism:
            if not any(token in claimed_clean for token in ["ranh giới", "nay thuộc", "tương ứng", "hiện nay"]):
                raise AnachronisticGeographyError(
                    f"Anachronistic geography: modern province boundary '{modern_correspondence_claimed}' cannot be equated to historical 19th-century Nguyễn territory without temporal mapping.",
                    {"historical_name": historical_place_name, "claimed_modern": modern_correspondence_claimed},
                )

    return {
        "historical_place": historical_place_name,
        "mapping_status": "verified",
        "modern_name": expected_modern,
        "historical_province": expected_province,
        "geo_precision": entry["precision"],
        "temporal_mapping_note": f"Địa danh lịch sử '{historical_place_name}' dưới triều Nguyễn thuộc {expected_province}, nay tương ứng với {expected_modern}.",
    }
