# -*- coding: utf-8 -*-
"""Phase P01: Multi-Channel Historical Source Discovery — V5 Wave W07 Slot A04.

Spec references:
- LUU_NIEN_V6_MODULAR_IMPLEMENTATION_SPECS/03_AI_FACTORY/PHASE_P01_TEN_RESEARCH_AGENTS.md
- AIR-011: Build source candidate registry
- Canonicalizes DOIs, ISBNs, URLs; deduplicates candidates against in-flight batch and database.
"""
from __future__ import annotations

import hashlib
import re
import uuid
from typing import Any, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from uuid import UUID

from sqlalchemy.orm import Session

from backend.services.history_governance import (
    find_duplicate_source,
    normalize_bibliographic_text,
    normalize_doi,
    normalize_isbn,
)

from .contracts import (
    LegalRightsStatus,
    ScoutRole,
    SourceCandidate,
)
from .providers.registry import provider_registry


def canonicalize_url(url: Optional[str]) -> Optional[str]:
    """Canonicalize URL by stripping tracking parameters, normalizing protocol & host."""
    if not url:
        return None
    url_str = str(url).strip()
    if not url_str:
        return None

    if "://" not in url_str:
        url_str = f"https://{url_str}"

    parsed = urlparse(url_str)
    # Strip tracking parameters (utm_*, ref, fbclid, gclid, session_id, etc.)
    query_params = parse_qs(parsed.query, keep_blank_values=False)
    filtered_params = {
        k: v for k, v in query_params.items()
        if not (k.lower().startswith("utm_") or k.lower() in ("ref", "fbclid", "gclid", "session_id", "source"))
    }
    # Sort query parameters for deterministic canonical form
    sorted_query = urlencode(filtered_params, doseq=True)
    
    # Strip trailing slash from path unless it's just '/'
    path = parsed.path
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")

    canonical = urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        path,
        parsed.params,
        sorted_query,
        "",  # drop fragment
    ))
    return canonical


def compute_candidate_hash(candidate_data: dict[str, Any]) -> str:
    """Compute deterministic SHA-256 hash for candidate deduplication."""
    parts = [
        str(candidate_data.get("scout_role") or "").strip(),
        normalize_bibliographic_text(candidate_data.get("title")) or "",
        normalize_bibliographic_text(candidate_data.get("author_text")) or "",
        str(candidate_data.get("publication_year") or "").strip(),
        str(candidate_data.get("edition") or "").strip().lower(),
        normalize_isbn(candidate_data.get("isbn")) or "",
        normalize_doi(candidate_data.get("doi")) or "",
        canonicalize_url(candidate_data.get("url")) or "",
        str(candidate_data.get("archive_locator") or "").strip().lower(),
    ]
    raw = "|".join(parts).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class SourceDiscoveryScout:
    """Scout service managing candidate intake, canonicalization, and deduplication."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def create_candidate(
        self,
        *,
        scout_role: str,
        title: str,
        author_text: Optional[str] = None,
        publisher: Optional[str] = None,
        publication_year: Optional[int] = None,
        edition: Optional[str] = None,
        source_type: str = "archive",
        url: Optional[str] = None,
        doi: Optional[str] = None,
        isbn: Optional[str] = None,
        archive_locator: Optional[str] = None,
        claimed_rights: LegalRightsStatus = LegalRightsStatus.UNKNOWN_UNREVIEWED,
        is_paywalled: bool = False,
        provenance_notes: Optional[str] = None,
        authority_name: Optional[str] = None,
        is_official_registry: bool = False,
    ) -> SourceCandidate:
        """Create and canonicalize a source candidate."""
        canon_url = canonicalize_url(url)
        norm_doi = normalize_doi(doi)
        norm_isbn = normalize_isbn(isbn)
        domain = provider_registry.extract_domain(canon_url) if canon_url else None

        cand_data = {
            "scout_role": scout_role,
            "title": title,
            "author_text": author_text,
            "publisher": publisher,
            "publication_year": publication_year,
            "edition": edition,
            "source_type": source_type,
            "url": canon_url,
            "doi": norm_doi,
            "isbn": norm_isbn,
            "archive_locator": archive_locator,
        }
        cand_hash = compute_candidate_hash(cand_data)

        candidate = SourceCandidate(
            scout_role=scout_role,
            title=title,
            author_text=author_text,
            publisher=publisher,
            publication_year=publication_year,
            edition=edition,
            source_type=source_type,
            url=canon_url,
            canonical_url=canon_url,
            doi=norm_doi,
            isbn=norm_isbn,
            archive_locator=archive_locator,
            domain=domain,
            claimed_rights=claimed_rights,
            is_paywalled=is_paywalled,
            candidate_hash=cand_hash,
            provenance_notes=provenance_notes,
            authority_name=authority_name,
            is_official_registry=is_official_registry,
        )

        return candidate

    def deduplicate_batch(
        self,
        candidates: list[SourceCandidate],
        db: Optional[Session] = None,
    ) -> list[SourceCandidate]:
        """Deduplicate candidates within the batch and against the database.
        
        Annotates duplicate candidates with is_duplicate=True, duplicate_of_id, duplicate_matched_by.
        """
        active_db = db or self.db
        seen_dois: dict[str, UUID] = {}
        seen_isbns: dict[str, UUID] = {}
        seen_urls: dict[str, UUID] = {}
        seen_titles_authors: dict[tuple[str, str, Optional[int]], UUID] = {}
        seen_hashes: dict[str, UUID] = {}

        result: list[SourceCandidate] = []

        for cand in candidates:
            # 1. Intra-batch duplicate check
            matched_id: Optional[UUID] = None
            matched_by: Optional[str] = None

            if cand.candidate_hash and cand.candidate_hash in seen_hashes:
                matched_id = seen_hashes[cand.candidate_hash]
                matched_by = "candidate_hash"
            elif cand.doi and cand.doi in seen_dois:
                matched_id = seen_dois[cand.doi]
                matched_by = "doi"
            elif cand.isbn and cand.isbn in seen_isbns:
                matched_id = seen_isbns[cand.isbn]
                matched_by = "isbn"
            elif cand.canonical_url and cand.canonical_url in seen_urls:
                matched_id = seen_urls[cand.canonical_url]
                matched_by = "canonical_url"
            else:
                norm_title = normalize_bibliographic_text(cand.title)
                norm_author = normalize_bibliographic_text(cand.author_text)
                if norm_title and norm_author:
                    key = (norm_title, norm_author, cand.publication_year)
                    if key in seen_titles_authors:
                        matched_id = seen_titles_authors[key]
                        matched_by = "title_author"

            if matched_id:
                cand.is_duplicate = True
                cand.duplicate_of_id = matched_id
                cand.duplicate_matched_by = matched_by
                result.append(cand)
                continue

            # 2. Database duplicate check against HistoricalSource
            if active_db:
                dup_source, db_matched_by = find_duplicate_source(
                    active_db,
                    isbn=cand.isbn,
                    doi=cand.doi,
                    title=cand.title,
                    author_text=cand.author_text,
                    publication_year=cand.publication_year,
                )
                if dup_source:
                    cand.is_duplicate = True
                    cand.duplicate_of_id = dup_source.id
                    cand.duplicate_matched_by = f"db_{db_matched_by}"
                    result.append(cand)
                    continue

            # Not a duplicate -> register in seen tables
            if cand.candidate_hash:
                seen_hashes[cand.candidate_hash] = cand.id
            if cand.doi:
                seen_dois[cand.doi] = cand.id
            if cand.isbn:
                seen_isbns[cand.isbn] = cand.id
            if cand.canonical_url:
                seen_urls[cand.canonical_url] = cand.id
            norm_title = normalize_bibliographic_text(cand.title)
            norm_author = normalize_bibliographic_text(cand.author_text)
            if norm_title and norm_author:
                seen_titles_authors[(norm_title, norm_author, cand.publication_year)] = cand.id

            result.append(cand)

        return result
