# -*- coding: utf-8 -*-
"""Research Factory P01/P02 Contracts & Types — V5 Wave W07 Slot A04.

Spec references:
- LUU_NIEN_V6_MODULAR_IMPLEMENTATION_SPECS/03_AI_FACTORY/PHASE_P01_TEN_RESEARCH_AGENTS.md
- LUU_NIEN_V6_MODULAR_IMPLEMENTATION_SPECS/03_AI_FACTORY/PHASE_P02_TEN_RESEARCH_AGENTS.md
- AIR-011, AIR-012, AIR-013, AIR-014, AIR-015
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# --------------------------------------------------------------------------- #
# Roles & Codes
# --------------------------------------------------------------------------- #
class ScoutRole(str, Enum):
    """P01 10-scout roles for historical source discovery."""
    P01_A01 = "P01-A01"  # Official heritage registry scout
    P01_A02 = "P01-A02"  # Dynastic chronicles scout
    P01_A03 = "P01-A03"  # Royal document scout
    P01_A04 = "P01-A04"  # Museum catalogue scout
    P01_A05 = "P01-A05"  # Peer-reviewed literature scout
    P01_A06 = "P01-A06"  # Historical maps scout
    P01_A07 = "P01-A07"  # Han-Nom editions scout
    P01_A08 = "P01-A08"  # Image and 3D rights scout
    P01_A09 = "P01-A09"  # Open scholarly metadata scout
    P01_A10 = "P01-A10"  # Contrarian/coverage scout


class AcquisitionRole(str, Enum):
    """P02 10-acquisition & verification roles."""
    P02_A01 = "P02-A01"  # Bibliography verifier
    P02_A02 = "P02-A02"  # Canonical URL resolver
    P02_A03 = "P02-A03"  # Authority verifier
    P02_A04 = "P02-A04"  # Duplicate lineage analyzer
    P02_A05 = "P02-A05"  # License analyst
    P02_A06 = "P02-A06"  # Access negotiator
    P02_A07 = "P02-A07"  # Fetch planner
    P02_A08 = "P02-A08"  # Malware & document sanitizer
    P02_A09 = "P02-A09"  # Asset hash controller
    P02_A10 = "P02-A10"  # Acquisition QA auditor


class LegalRightsStatus(str, Enum):
    """Legal rights and licensing status."""
    PUBLIC_DOMAIN = "public_domain"
    CC0 = "cc0"
    CC_BY = "cc_by"
    CC_BY_SA = "cc_by_sa"
    CC_BY_NC = "cc_by_nc"
    CC_BY_NC_ND = "cc_by_nc_nd"
    COPYRIGHTED_ALL_RIGHTS_RESERVED = "copyrighted_all_rights_reserved"
    RESTRICTED_ARCHIVAL = "restricted_archival"
    UNKNOWN_UNREVIEWED = "unknown_unreviewed"
    FORBIDDEN_PIRATED = "forbidden_pirated"


class AcquisitionDecision(str, Enum):
    """Acquisition decision outcomes."""
    ALLOWED_FULL = "allowed_full"
    ALLOWED_METADATA_ONLY = "allowed_metadata_only"
    QUARANTINED_PENDING_REVIEW = "quarantined_pending_review"
    BLOCKED_COPYRIGHT_VIOLATION = "blocked_copyright_violation"
    BLOCKED_PAYWALL_BYPASS = "blocked_paywall_bypass"
    BLOCKED_ROBOTS_DISALLOWED = "blocked_robots_disallowed"
    BLOCKED_FORBIDDEN_DOMAIN = "blocked_forbidden_domain"
    BLOCKED_MALICIOUS_PAYLOAD = "blocked_malicious_payload"
    BLOCKED_IMPERSONATION = "blocked_impersonation"


# --------------------------------------------------------------------------- #
# Typed Exceptions
# --------------------------------------------------------------------------- #
class ResearchFactoryError(Exception):
    """Base error for research factory operations."""
    code: str = "RESEARCH_FACTORY_ERROR"

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_envelope(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class ForbiddenCopyrightedScanError(ResearchFactoryError):
    code = "FORBIDDEN_COPYRIGHTED_SCAN"


class PaywallBypassError(ResearchFactoryError):
    code = "PAYWALL_BYPASS_FORBIDDEN"


class RobotsDisallowedError(ResearchFactoryError):
    code = "ROBOTS_DISALLOWED"


class ForbiddenDomainError(ResearchFactoryError):
    code = "FORBIDDEN_PROVIDER_DOMAIN"


class UnapprovedSourceQuarantinedError(ResearchFactoryError):
    code = "UNAPPROVED_SOURCE_QUARANTINED"


class MaliciousPayloadError(ResearchFactoryError):
    code = "MALICIOUS_PAYLOAD_DETECTED"


class AuthorityImpersonationError(ResearchFactoryError):
    code = "AUTHORITY_IMPERSONATION_DETECTED"


class DuplicateSourceError(ResearchFactoryError):
    code = "DUPLICATE_SOURCE_DETECTED"


# --------------------------------------------------------------------------- #
# Data Schemas
# --------------------------------------------------------------------------- #
class SourceCandidate(BaseModel):
    """P01 candidate schema representing discovered historical source."""
    model_config = ConfigDict(extra="ignore")

    id: UUID = Field(default_factory=uuid.uuid4)
    scout_role: str = ScoutRole.P01_A01.value
    title: str
    author_text: Optional[str] = None
    publisher: Optional[str] = None
    publication_year: Optional[int] = None
    edition: Optional[str] = None
    source_type: str = "archive"
    url: Optional[str] = None
    canonical_url: Optional[str] = None
    doi: Optional[str] = None
    isbn: Optional[str] = None
    archive_locator: Optional[str] = None
    domain: Optional[str] = None
    claimed_rights: LegalRightsStatus = LegalRightsStatus.UNKNOWN_UNREVIEWED
    is_paywalled: bool = False
    is_duplicate: bool = False
    duplicate_of_id: Optional[UUID] = None
    duplicate_matched_by: Optional[str] = None
    candidate_hash: Optional[str] = None
    provenance_notes: Optional[str] = None
    authority_name: Optional[str] = None
    is_official_registry: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SourceSnapshot(BaseModel):
    """P02 frozen snapshot of an acquired historical source."""
    model_config = ConfigDict(extra="ignore")

    snapshot_id: UUID = Field(default_factory=uuid.uuid4)
    candidate_id: UUID
    sha256_hash: str
    byte_size: int
    mime_type: str
    content_bytes: Optional[bytes] = None
    text_excerpt: Optional[str] = None
    captured_at: datetime = Field(default_factory=datetime.utcnow)
    storage_uri: Optional[str] = None


class AcquisitionResult(BaseModel):
    """P02 outcome of legal source acquisition and verification."""
    model_config = ConfigDict(extra="ignore")

    candidate_id: UUID
    decision: AcquisitionDecision
    rights_status: LegalRightsStatus
    reason: str
    public_display_allowed: bool = False
    derivative_allowed: bool = False
    is_excerpt_redacted: bool = True
    quarantine_required: bool = False
    snapshot: Optional[SourceSnapshot] = None
    audit_trail: list[dict[str, Any]] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
