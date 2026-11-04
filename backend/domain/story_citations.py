# -*- coding: utf-8 -*-
"""Story Footnote & Bibliographic Citation Domain Engine (V5-T028 / Wave W02).

Implements specification section 30 for block-based story citation resolution:
1. Footnote token extraction from bilingual prose (`[^1]`, `[^2]`, `[^dntl-01]`).
2. Footnote-to-citation mapping with bibliographic verification against HistoricalSource and HistoricalClaim.
3. Strict negative abuse guardrails:
   - Footnotes must strictly map to real source IDs in the database.
   - Claims without evidence cannot hide behind fake citations or claim verified status ('Sử liệu xác thực').
   - Contested or disputed claims must carry epistemic uncertainty indicators ('Đang khảo cứu').
4. Bilingual footnote reference alignment (Vietnamese and English text segments map to identical canonical citations).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..history_models import (
    HistoricalClaim,
    HistoricalConfidence,
    HistoricalSource,
    HistoricalVerificationStatus,
)

# Standard markdown footnote reference pattern: [^1], [^2], [^src_01], [^dntl-01]
FOOTNOTE_REGEX = re.compile(r"\[\^([a-zA-Z0-9_\-]+)\]")


@dataclass
class FootnoteReference:
    """An extracted footnote marker token in story prose."""

    key: str
    raw: str
    block_index: int
    field_name: str
    locale: str = "vi"


@dataclass
class FootnoteResolutionResult:
    """Outcome of resolving story footnotes and bibliographic citations."""

    citations: list[dict[str, Any]] = field(default_factory=list)
    footnote_map: dict[str, dict[str, Any]] = field(default_factory=dict)
    broken_references: list[dict[str, Any]] = field(default_factory=list)
    validation_errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.broken_references) == 0 and len(self.validation_errors) == 0


def extract_footnote_keys(text: str) -> list[str]:
    """Extract all footnote keys from a text string in appearance order."""
    if not text:
        return []
    return FOOTNOTE_REGEX.findall(text)


def extract_all_story_footnotes(blocks: list[dict[str, Any]]) -> list[FootnoteReference]:
    """Extract all footnote references across all text fields of all blocks in a story."""
    results: list[FootnoteReference] = []
    if not isinstance(blocks, list):
        return results

    text_fields = [
        ("body", "vi"),
        ("body_vi", "vi"),
        ("body_en", "en"),
        ("quote", "vi"),
        ("quote_vi", "vi"),
        ("quote_en", "en"),
        ("title", "vi"),
        ("title_vi", "vi"),
        ("title_en", "en"),
        ("caption", "vi"),
        ("summary", "vi"),
        ("question", "vi"),
    ]

    for idx, block in enumerate(blocks):
        if not isinstance(block, dict):
            continue
        for field_name, loc in text_fields:
            val = block.get(field_name)
            if isinstance(val, str) and val.strip():
                for match in FOOTNOTE_REGEX.finditer(val):
                    results.append(
                        FootnoteReference(
                            key=match.group(1),
                            raw=match.group(0),
                            block_index=idx,
                            field_name=field_name,
                            locale=loc,
                        )
                    )
    return results


class FootnoteMapper:
    """Resolves footnote references to primary sources and validates evidence integrity."""

    @staticmethod
    def _is_valid_uuid(val: Any) -> bool:
        try:
            UUID(str(val))
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _source_exists_in_db(db: Session, source_id: Any) -> bool:
        if not FootnoteMapper._is_valid_uuid(source_id):
            return False
        try:
            return db.get(HistoricalSource, UUID(str(source_id))) is not None
        except Exception:
            return False

    @classmethod
    def resolve_story_citations_and_footnotes(
        cls,
        blocks: list[dict[str, Any]],
        citations: Optional[list[dict[str, Any]]] = None,
        db: Optional[Session] = None,
    ) -> FootnoteResolutionResult:
        """Resolve all footnotes and bibliographic citations in a story.

        Maps each footnote `[^k]` to an authoritative citation, resolves backing DB
        records, verifies epistemic status, and flags broken references or evidence violations.
        """
        result = FootnoteResolutionResult()
        seen_keys: set[str] = set()
        resolved_citations: list[dict[str, Any]] = []

        def _format_locator(b: Any, src: Optional[HistoricalSource] = None) -> Optional[str]:
            if hasattr(b, "page_start") and b.page_start:
                if b.page_end and b.page_end != b.page_start:
                    return f"Tr. {b.page_start}-{b.page_end}"
                return f"Tr. {b.page_start}"
            if src and src.pages:
                return f"Tr. {src.pages}" if not str(src.pages).lower().startswith("tr.") else src.pages
            return None

        def _add_resolved_citation(item: dict[str, Any]) -> dict[str, Any]:
            key = f"{item.get('source_id')}:{item.get('claim_id')}:{item.get('locator')}:{item.get('footnote_key')}"
            if key in seen_keys:
                for existing in resolved_citations:
                    existing_key = f"{existing.get('source_id')}:{existing.get('claim_id')}:{existing.get('locator')}:{existing.get('footnote_key')}"
                    if existing_key == key:
                        return existing
            seen_keys.add(key)
            item_id = item.get("id") or f"cite-{len(resolved_citations) + 1}"
            item["id"] = item_id
            resolved_citations.append(item)
            return item

        # 1. Process top-level citations if explicitly supplied
        candidate_citations: list[dict[str, Any]] = []
        if isinstance(citations, list):
            for c in citations:
                if isinstance(c, dict):
                    candidate_citations.append(dict(c))

        # 2. Extract block-level citations, source_claim_ids, and source_id
        if isinstance(blocks, list):
            for b_idx, block in enumerate(blocks):
                if not isinstance(block, dict):
                    continue
                # Block citations list
                for b_cite in block.get("citations") or []:
                    if isinstance(b_cite, dict):
                        c_copy = dict(b_cite)
                        if "block_index" not in c_copy:
                            c_copy["block_index"] = b_idx
                        candidate_citations.append(c_copy)

                # Block source_id (e.g. source_excerpt block)
                if block.get("source_id"):
                    candidate_citations.append(
                        {
                            "source_id": str(block["source_id"]),
                            "locator": block.get("cited_section") or block.get("locator"),
                            "quote": block.get("quote"),
                            "claim_statement": block.get("quote"),
                            "epistemic_certainty": block.get("epistemic_certainty") or "su_lieu_xac_thuc",
                            "verification_status": "verified",
                            "block_index": b_idx,
                            "footnote_key": block.get("footnote_key"),
                        }
                    )

                # Block source_claim_ids
                for cid in block.get("source_claim_ids") or []:
                    candidate_citations.append(
                        {
                            "claim_id": str(cid),
                            "block_index": b_idx,
                        }
                    )

        # 3. Resolve candidate citations against DB
        for idx, candidate in enumerate(candidate_citations):
            src_id = candidate.get("source_id")
            claim_id = candidate.get("claim_id")
            source: Optional[HistoricalSource] = None
            claim: Optional[HistoricalClaim] = None

            if db is not None:
                if src_id and cls._is_valid_uuid(src_id):
                    source = db.get(HistoricalSource, UUID(str(src_id)))
                if claim_id and cls._is_valid_uuid(claim_id):
                    claim = db.get(HistoricalClaim, UUID(str(claim_id)))

            # If claim has source bindings, pick primary source
            if claim and not source and db is not None:
                bindings = claim.source_bindings or []
                if bindings:
                    primary_binding = bindings[0]
                    source = primary_binding.source or db.get(HistoricalSource, primary_binding.source_id)
                    if not candidate.get("locator"):
                        candidate["locator"] = _format_locator(primary_binding, source)

            has_source = bool(source or (src_id and db is None))
            raw_cert = str(
                candidate.get("epistemic_certainty")
                or (claim.verification_status if claim else "")
                or ""
            ).lower()

            is_disputed = (
                raw_cert in ("disputed", "rejected")
                or (
                    claim is not None
                    and (
                        claim.verification_status in ("disputed", "rejected")
                        or claim.confidence == "disputed"
                    )
                )
            )

            is_verified_requested = (
                raw_cert in ("su_lieu_xac_thuc", "verified", "sử liệu xác thực", "expert_verified", "editor_reviewed")
                or candidate.get("is_verified") is True
                or str(candidate.get("verification_status") or "").lower() in ("verified", "expert_verified")
            )

            # Epistemic resolution
            if is_disputed:
                epistemic = "dang_khao_cuu"
                warning = "CLAIM_DISPUTED_NOT_VERIFIED"
            elif not has_source:
                epistemic = "dang_khao_cuu"
                warning = "UNVERIFIED_EMPTY_EVIDENCE"
            elif raw_cert in ("truyen_thuyet_dan_gian", "traditional", "traditional_account", "legend"):
                epistemic = "truyen_thuyet_dan_gian"
                warning = None
            elif (
                raw_cert in ("su_lieu_xac_thuc", "verified", "sử liệu xác thực", "expert_verified", "editor_reviewed")
                or candidate.get("is_verified") is True
                or (claim and claim.verification_status in ("expert_verified", "editor_reviewed"))
            ):
                epistemic = "su_lieu_xac_thuc"
                warning = None
            else:
                epistemic = "dang_khao_cuu"
                warning = None

            # Determine locator
            locator = (
                candidate.get("locator")
                or (source.pages if source else None)
                or candidate.get("cited_section")
            )

            resolved_item = {
                "source_id": str(source.id) if source else (str(src_id) if src_id else None),
                "source_title": source.title if source else candidate.get("source_title", "Nguồn sử liệu"),
                "author": source.author_text if source else candidate.get("author"),
                "publication_year": source.publication_year if source else candidate.get("publication_year"),
                "locator": locator,
                "quote": candidate.get("quote") or candidate.get("claim_statement"),
                "citation_text": source.citation_text if source else candidate.get("citation_text"),
                "url": source.url if source else candidate.get("url"),
                "claim_id": str(claim.id) if claim else (str(claim_id) if claim_id else None),
                "claim_statement": claim.statement_vi if claim else candidate.get("claim_statement"),
                "epistemic_certainty": epistemic,
                "verification_status": (
                    claim.verification_status
                    if claim
                    else ("expert_verified" if has_source and not is_disputed else "unreviewed")
                ),
                "is_disputed": is_disputed,
                "support_type": candidate.get("support_type", "direct"),
                "has_source": has_source,
                "warning": warning,
                "footnote_key": str(candidate.get("footnote_key") or idx + 1),
                "requested_verified": is_verified_requested,
            }

            _add_resolved_citation(resolved_item)

        result.citations = resolved_citations

        # 4. Map footnotes found in block texts to citations
        extracted_footnotes = extract_all_story_footnotes(blocks)
        for ref in extracted_footnotes:
            k = ref.key
            matched_citation: Optional[dict[str, Any]] = None

            # Strategy A: Match by explicit footnote_key
            for c in resolved_citations:
                if str(c.get("footnote_key")) == k or str(c.get("id")) == k or str(c.get("id")) == f"cite-{k}":
                    matched_citation = c
                    break

            # Strategy B: If k is numeric (e.g. "1"), match 1-based index
            if not matched_citation and k.isdigit():
                idx_0 = int(k) - 1
                if 0 <= idx_0 < len(resolved_citations):
                    matched_citation = resolved_citations[idx_0]

            # Strategy C: Match by source_id or claim_id
            if not matched_citation:
                for c in resolved_citations:
                    if str(c.get("source_id")) == k or str(c.get("claim_id")) == k:
                        matched_citation = c
                        break

            if matched_citation:
                result.footnote_map[k] = matched_citation
                # Validate source existence if db is present
                src_id = matched_citation.get("source_id")
                if db is not None:
                    if not src_id or not cls._source_exists_in_db(db, src_id):
                        err_msg = (
                            f"Fake or non-existent source: footnote [^{k}] references source_id "
                            f"{src_id!r} which does not exist in the database."
                        )
                        result.broken_references.append(
                            {
                                "key": k,
                                "raw": ref.raw,
                                "block_index": ref.block_index,
                                "field": ref.field_name,
                                "error": "SOURCE_NOT_FOUND",
                                "message": err_msg,
                            }
                        )
                        result.validation_errors.append(err_msg)
                elif not src_id and not matched_citation.get("has_source"):
                    err_msg = (
                        f"Footnote [^{k}] references citation without a valid bibliographic source."
                    )
                    result.broken_references.append(
                        {
                            "key": k,
                            "raw": ref.raw,
                            "block_index": ref.block_index,
                            "field": ref.field_name,
                            "error": "EMPTY_SOURCE",
                            "message": err_msg,
                        }
                    )
                    result.validation_errors.append(err_msg)
            else:
                err_msg = (
                    f"Broken footnote reference: [^{k}] in block {ref.block_index} "
                    f"('{ref.field_name}') does not map to any bibliographic source."
                )
                result.broken_references.append(
                    {
                        "key": k,
                        "raw": ref.raw,
                        "block_index": ref.block_index,
                        "field": ref.field_name,
                        "error": "BROKEN_FOOTNOTE_REFERENCE",
                        "message": err_msg,
                    }
                )
                result.validation_errors.append(err_msg)

        # 5. Check negative abuse: claims without sources pretending to be verified
        for idx, cite in enumerate(resolved_citations):
            is_verified_claimed = (
                bool(cite.get("requested_verified"))
                or cite.get("epistemic_certainty") == "su_lieu_xac_thuc"
                or str(cite.get("verification_status")).lower() in ("verified", "expert_verified")
            )
            has_valid_source = bool(
                cite.get("has_source")
                and cite.get("source_id")
                and (db is None or cls._source_exists_in_db(db, cite.get("source_id")))
            )
            if is_verified_claimed and not has_valid_source:
                err_msg = (
                    f"Evidence abuse at citation {idx} ('{cite.get('source_title')}'): claim has no backing "
                    "source and cannot be presented as verified historical fact ('Sử liệu xác thực')."
                )
                result.validation_errors.append(err_msg)

            if cite.get("is_disputed") and is_verified_claimed:
                err_msg = (
                    f"Contested claim abuse at citation {idx} ('{cite.get('source_title')}'): disputed claim "
                    "cannot be presented as verified historical fact."
                )
                result.validation_errors.append(err_msg)

        return result

    @classmethod
    def validate_strict_citations(
        cls,
        blocks: list[dict[str, Any]],
        citations: Optional[list[dict[str, Any]]] = None,
        db: Optional[Session] = None,
    ) -> list[str]:
        """Validate footnote bindings and bibliographic integrity, returning all error messages."""
        res = cls.resolve_story_citations_and_footnotes(blocks=blocks, citations=citations, db=db)
        return res.validation_errors
