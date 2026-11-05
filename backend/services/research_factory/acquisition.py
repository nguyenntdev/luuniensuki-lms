# -*- coding: utf-8 -*-
"""Phase P02: Candidate Metadata, Rights and Legal Source Acquisition — V5 Wave W07 Slot A04.

Spec references:
- LUU_NIEN_V6_MODULAR_IMPLEMENTATION_SPECS/03_AI_FACTORY/PHASE_P02_TEN_RESEARCH_AGENTS.md
- AIR-012, AIR-014, AIR-015
- Invariants:
  - Unknown rights != granted (strictly quarantined).
  - Forbidden copyrighted scans are strictly blocked.
  - Paywall bypass and captcha evasion are strictly blocked.
  - Robots.txt disallowances are strictly respected.
  - Malicious files disguised as PDFs are strictly rejected.
  - Impersonating museum blogs are strictly detected and blocked.
  - Idempotent and deduplicated database ingestion into HistoricalSource.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from backend.history_models import HistoricalSource
from backend.services.history_governance import (
    compute_source_checksum,
    find_duplicate_source,
    normalize_doi,
    normalize_isbn,
)

from .contracts import (
    AcquisitionDecision,
    AcquisitionResult,
    AuthorityImpersonationError,
    ForbiddenCopyrightedScanError,
    ForbiddenDomainError,
    LegalRightsStatus,
    MaliciousPayloadError,
    PaywallBypassError,
    RobotsDisallowedError,
    SourceCandidate,
    SourceSnapshot,
    UnapprovedSourceQuarantinedError,
)
from .providers.registry import provider_registry


class LegalSourceAcquisitionService:
    """Service governing legal source acquisition, rights validation, and snapshot integrity."""

    def __init__(self, registry=None):
        self.registry = registry or provider_registry

    def evaluate_and_acquire(
        self,
        candidate: SourceCandidate,
        payload_bytes: Optional[bytes] = None,
        declared_mime_type: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
        is_full_scan_download: bool = False,
    ) -> AcquisitionResult:
        """Evaluate legal terms, validate domain/robots/paywall, and acquire source snapshot.
        
        Raises typed exceptions when abuse or illegal acquisition is detected.
        """
        audit_trail: list[dict[str, Any]] = []

        # 1. Authority Impersonation Check (P02-A03)
        self.registry.validate_authority(candidate.authority_name, candidate.url or candidate.domain)
        audit_trail.append({"check": "authority_verification", "status": "passed"})

        # 2. Domain & Paywall Validation (P02-A07, AIR-012)
        target_domain = candidate.domain or (self.registry.extract_domain(candidate.url) if candidate.url else "unknown")
        connector = self.registry.validate_domain_access(candidate.url or target_domain, headers)
        audit_trail.append({"check": "domain_policy", "domain": target_domain, "approved": connector.is_approved})

        # 3. Robots.txt Compliance Check (P02-A07)
        if candidate.url:
            from urllib.parse import urlparse
            path = urlparse(candidate.url).path or "/"
            is_robots_ok, robots_reason = connector.check_robots(path)
            if not is_robots_ok:
                raise RobotsDisallowedError(
                    f"Robots.txt forbids access to path '{path}': {robots_reason}",
                    details={"url": candidate.url, "domain": target_domain, "path": path},
                )
            audit_trail.append({"check": "robots_compliance", "path": path, "status": "passed"})

        # 4. Document / Malware Sanitization Check (P02-A08, AIR-014)
        if payload_bytes:
            mime = declared_mime_type or "application/octet-stream"
            self.registry.sanitize_payload(payload_bytes, mime)
            audit_trail.append({"check": "malware_sanitization", "mime_type": mime, "byte_size": len(payload_bytes)})

        # 5. Copyright & Rights Matrix Assessment (P02-A05, AIR-015)
        rights = candidate.claimed_rights

        # NEGATIVE CASE 1: Forbidden copyrighted scan
        # If payload_bytes or full scan download is requested for an in-copyright book without permission
        if rights in (LegalRightsStatus.COPYRIGHTED_ALL_RIGHTS_RESERVED, LegalRightsStatus.FORBIDDEN_PIRATED):
            if payload_bytes or is_full_scan_download:
                raise ForbiddenCopyrightedScanError(
                    f"Forbidden copyrighted scan: Ingesting full digitized scans of copyrighted work '{candidate.title}' "
                    "without explicit publisher permission or open license is strictly blocked.",
                    details={
                        "candidate_id": str(candidate.id),
                        "title": candidate.title,
                        "rights_status": rights.value,
                        "is_scan": True,
                    },
                )

        # 6. Rights Decision Determination
        decision: AcquisitionDecision
        public_display: bool = False
        derivative_ok: bool = False
        is_redacted: bool = True
        quarantine: bool = False
        reason: str = ""

        if not connector.is_approved:
            # Unapproved domain or unknown source -> Quarantine for human review
            decision = AcquisitionDecision.QUARANTINED_PENDING_REVIEW
            quarantine = True
            reason = f"Source originates from unapproved domain '{target_domain}' — quarantined for human review"
        elif rights == LegalRightsStatus.UNKNOWN_UNREVIEWED:
            # Rule: Unknown rights != granted!
            decision = AcquisitionDecision.QUARANTINED_PENDING_REVIEW
            quarantine = True
            reason = "Rights status is unknown/unreviewed; strictly quarantined until rights clearance"
        elif rights in (LegalRightsStatus.PUBLIC_DOMAIN, LegalRightsStatus.CC0):
            decision = AcquisitionDecision.ALLOWED_FULL
            public_display = True
            derivative_ok = True
            is_redacted = False
            reason = f"Source is in {rights.value.upper()}; full text and excerpts legally cleared"
        elif rights in (LegalRightsStatus.CC_BY, LegalRightsStatus.CC_BY_SA):
            decision = AcquisitionDecision.ALLOWED_FULL
            public_display = True
            derivative_ok = True
            is_redacted = False
            reason = f"Source licensed under {rights.value.upper()}; attribution preserved"
        elif rights == LegalRightsStatus.CC_BY_NC:
            decision = AcquisitionDecision.ALLOWED_FULL
            public_display = True
            derivative_ok = True
            is_redacted = False
            reason = "Source licensed under CC-BY-NC; non-commercial educational LMS usage authorized"
        elif rights in (LegalRightsStatus.COPYRIGHTED_ALL_RIGHTS_RESERVED, LegalRightsStatus.RESTRICTED_ARCHIVAL):
            # Metadata-only citation allowed without scan
            decision = AcquisitionDecision.ALLOWED_METADATA_ONLY
            public_display = False
            derivative_ok = False
            is_redacted = True
            reason = "Copyrighted or restricted source; metadata citation authorized with excerpt redaction"
        else:
            decision = AcquisitionDecision.QUARANTINED_PENDING_REVIEW
            quarantine = True
            reason = f"Unclassified rights status '{rights.value}' quarantined"

        # 7. Create Snapshot if payload provided or generate canonical metadata snapshot (P02-A09)
        snapshot: Optional[SourceSnapshot] = None
        if payload_bytes:
            sha256 = hashlib.sha256(payload_bytes).hexdigest()
            snapshot = SourceSnapshot(
                candidate_id=candidate.id,
                sha256_hash=sha256,
                byte_size=len(payload_bytes),
                mime_type=declared_mime_type or "application/octet-stream",
                content_bytes=payload_bytes if decision == AcquisitionDecision.ALLOWED_FULL else None,
                text_excerpt=candidate.provenance_notes if public_display else None,
            )
        else:
            # Metadata snapshot hash
            meta_hash = candidate.candidate_hash or hashlib.sha256(
                f"{candidate.title}|{candidate.author_text}|{candidate.publication_year}".encode("utf-8")
            ).hexdigest()
            snapshot = SourceSnapshot(
                candidate_id=candidate.id,
                sha256_hash=meta_hash,
                byte_size=0,
                mime_type="application/json",
                text_excerpt=candidate.provenance_notes if public_display else None,
            )

        audit_trail.append({
            "check": "rights_decision",
            "decision": decision.value,
            "rights_status": rights.value,
            "quarantine": quarantine,
        })

        return AcquisitionResult(
            candidate_id=candidate.id,
            decision=decision,
            rights_status=rights,
            reason=reason,
            public_display_allowed=public_display,
            derivative_allowed=derivative_ok,
            is_excerpt_redacted=is_redacted,
            quarantine_required=quarantine,
            snapshot=snapshot,
            audit_trail=audit_trail,
        )

    def ingest_approved_source(
        self,
        db: Session,
        acquisition: AcquisitionResult,
        candidate: SourceCandidate,
        actor_id: Optional[UUID] = None,
    ) -> HistoricalSource:
        """Persist cleared source into HistoricalSource table idempotently."""
        # Check eligibility: only ALLOWED_FULL and ALLOWED_METADATA_ONLY can be ingested
        if acquisition.decision not in (AcquisitionDecision.ALLOWED_FULL, AcquisitionDecision.ALLOWED_METADATA_ONLY):
            raise UnapprovedSourceQuarantinedError(
                f"Cannot ingest source with decision '{acquisition.decision.value}': {acquisition.reason}",
                details={"candidate_id": str(candidate.id), "decision": acquisition.decision.value},
            )

        # Check existing database duplicates
        existing, matched_by = find_duplicate_source(
            db,
            isbn=candidate.isbn,
            doi=candidate.doi,
            title=candidate.title,
            author_text=candidate.author_text,
            publication_year=candidate.publication_year,
            checksum=acquisition.snapshot.sha256_hash if acquisition.snapshot else None,
        )
        if existing:
            # Idempotent return of existing source
            return existing

        # Determine verification_status
        verif_status = "accessible" if acquisition.decision == AcquisitionDecision.ALLOWED_FULL else "metadata_verified"
        if acquisition.rights_status == LegalRightsStatus.COPYRIGHTED_ALL_RIGHTS_RESERVED:
            verif_status = "rights_restricted"

        # Checksum calculation
        source_checksum = (
            acquisition.snapshot.sha256_hash
            if acquisition.snapshot
            else compute_source_checksum({
                "source_type": candidate.source_type,
                "title": candidate.title,
                "author_text": candidate.author_text,
                "publication_year": candidate.publication_year,
                "edition": candidate.edition,
                "isbn": candidate.isbn,
                "doi": candidate.doi,
            })
        )

        source = HistoricalSource(
            id=uuid.uuid4(),
            source_type=candidate.source_type,
            title=candidate.title,
            author_text=candidate.author_text,
            publisher=candidate.publisher,
            publication_year=candidate.publication_year,
            edition=candidate.edition,
            isbn=normalize_isbn(candidate.isbn),
            doi=normalize_doi(candidate.doi),
            url=candidate.canonical_url or candidate.url,
            repository_identifier=candidate.archive_locator,
            license=candidate.claimed_rights.value,
            rights_status=candidate.claimed_rights.value,
            public_display_allowed=acquisition.public_display_allowed,
            derivative_allowed=acquisition.derivative_allowed,
            verification_status=verif_status,
            created_by=actor_id,
            checksum=source_checksum,
            excerpt=candidate.provenance_notes if acquisition.public_display_allowed else None,
        )

        db.add(source)
        db.flush()
        return source


# Global instance
legal_acquisition_service = LegalSourceAcquisitionService()
