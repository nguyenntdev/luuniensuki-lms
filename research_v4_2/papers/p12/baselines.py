"""P12: Baseline models for archival claim verification.

C0: Exact locator match (inflexible, fails on edition shifts or OCR jitter).
C1: Snippet retrieval + NLI (prone to false support on cross-reign paraphrases).
B*: Page-level source verifier with generic provenance chain (Champion).
"""
from __future__ import annotations

from typing import Dict, List, Optional
import numpy as np

from research_v4_2.papers.p12.method import (
    ArchivalClaim,
    ArchivalLocator,
    ArchivalPage,
    Verdict,
    VerificationResult,
)


class C0ExactLocatorBaseline:
    """C0: Requires byte-exact match of locator and span."""

    def __init__(self, pages: Dict[tuple, ArchivalPage]):
        self.pages = pages

    def verify_claim(self, claim: ArchivalClaim) -> VerificationResult:
        if not claim.locator:
            return VerificationResult(
                claim_id=claim.claim_id,
                verdict=Verdict.UNVERIFIED,
                confidence=0.0,
                matched_locator=None,
                matched_page_hash="",
                explanation="C0: No locator",
                rights_permitted=True,
            )

        loc = claim.locator
        key = (loc.source_id, loc.edition, loc.page_number)
        if key not in self.pages:
            return VerificationResult(
                claim_id=claim.claim_id,
                verdict=Verdict.UNVERIFIED,
                confidence=0.0,
                matched_locator=None,
                matched_page_hash="",
                explanation="C0: Exact page not found",
                rights_permitted=True,
            )

        page = self.pages[key]
        if loc.span_text in page.text_content:
            return VerificationResult(
                claim_id=claim.claim_id,
                verdict=Verdict.SUPPORT,
                confidence=1.0,
                matched_locator=loc,
                matched_page_hash=page.canonical_hash,
                explanation="C0: Exact span match",
                rights_permitted=True,
            )

        return VerificationResult(
            claim_id=claim.claim_id,
            verdict=Verdict.UNVERIFIED,
            confidence=0.0,
            matched_locator=None,
            matched_page_hash="",
            explanation="C0: Span not identical",
            rights_permitted=True,
        )


class C1SnippetNLIBaseline:
    """C1: Ungrounded snippet retrieval + NLI (ignores page boundary / edition constraints)."""

    def __init__(self, pages: Dict[tuple, ArchivalPage]):
        self.pages = pages

    def verify_claim(self, claim: ArchivalClaim) -> VerificationResult:
        # Lexical matching across all snippets in corpus
        claim_words = set(claim.statement.lower().split())
        best_overlap = 0.0
        best_page = None

        for page in self.pages.values():
            p_words = set(page.text_content.lower().split())
            overlap = len(claim_words.intersection(p_words)) / max(len(claim_words), 1)
            if overlap > best_overlap:
                best_overlap = overlap
                best_page = page

        # C1 easily produces FALSE SUPPORT because it doesn't verify locator or reign
        if best_overlap >= 0.35:
            return VerificationResult(
                claim_id=claim.claim_id,
                verdict=Verdict.SUPPORT,
                confidence=float(best_overlap),
                matched_locator=claim.locator,
                matched_page_hash=best_page.canonical_hash if best_page else "",
                explanation=f"C1 NLI: lexical overlap {best_overlap:.2f}",
                rights_permitted=True,
            )

        return VerificationResult(
            claim_id=claim.claim_id,
            verdict=Verdict.UNVERIFIED,
            confidence=float(best_overlap),
            matched_locator=None,
            matched_page_hash="",
            explanation="C1 NLI: low overlap",
            rights_permitted=True,
        )


class BaselineChampionBStarP12:
    """B*: Page-level verifier with generic provenance chain (Champion).
    
    Checks page exists and checks keyword overlap, but lacks edition alias resolution
    and explicit refutation handling.
    """

    def __init__(self, pages: Dict[tuple, ArchivalPage]):
        self.pages = pages

    def verify_claim(self, claim: ArchivalClaim) -> VerificationResult:
        if not claim.locator:
            return VerificationResult(
                claim_id=claim.claim_id,
                verdict=Verdict.UNVERIFIED,
                confidence=0.0,
                matched_locator=None,
                matched_page_hash="",
                explanation="B*: No locator",
                rights_permitted=True,
            )

        loc = claim.locator
        key = (loc.source_id, loc.edition, loc.page_number)
        if key not in self.pages:
            # Fails on cross-edition alias without mapping
            return VerificationResult(
                claim_id=claim.claim_id,
                verdict=Verdict.UNVERIFIED,
                confidence=0.0,
                matched_locator=None,
                matched_page_hash="",
                explanation="B*: Page not in repository",
                rights_permitted=True,
            )

        page = self.pages[key]
        # Basic overlap
        claim_words = set(claim.statement.lower().split())
        page_words = set(page.text_content.lower().split())
        overlap = len(claim_words.intersection(page_words)) / max(len(claim_words), 1)

        if loc.span_text.lower() in page.text_content.lower() or overlap >= 0.50:
            return VerificationResult(
                claim_id=claim.claim_id,
                verdict=Verdict.SUPPORT,
                confidence=0.80,
                matched_locator=loc,
                matched_page_hash=page.canonical_hash,
                explanation="B*: Page match confirmed",
                rights_permitted=True,
            )

        return VerificationResult(
            claim_id=claim.claim_id,
            verdict=Verdict.UNVERIFIED,
            confidence=0.30,
            matched_locator=None,
            matched_page_hash="",
            explanation="B*: Insufficient match",
            rights_permitted=True,
        )
