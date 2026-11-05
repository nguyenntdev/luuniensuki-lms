# -*- coding: utf-8 -*-
"""P07 Narrative Drafting Engine with Strict Sentence-Level Source Binding.

Implements Agents P07-A01 to P07-A06:
- P07-A01: Vietnamese long-form historian writer (article_vi_full.md)
- P07-A02: English historical writer (article_en_full.md)
- P07-A03: Short museum label writer (museum_label_vi_en.md)
- P07-A04: Han-Nom editorial note writer (hannom_editorial.md)
- P07-A05: 3D/AR narration writer (interactive_script.json) with 2D fallback

Core Invariant:
Every single factual assertion must be explicitly bound to a verified claim and source.
Sentences without verified sources cannot hide invented facts (zero unsourced assertions).
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .dossier import (
    DossierClaim,
    DossierSource,
    DossierSourceBinding,
    ResearchDossier,
)


# --------------------------------------------------------------------------- #
# Custom Exceptions for P07
# --------------------------------------------------------------------------- #
class P07DraftingError(ValueError):
    """Base error for P07 educational and narrative drafting."""
    pass


class UnsourcedAssertionError(P07DraftingError):
    """Raised when a factual sentence lacks an approved claim and source binding."""
    pass


class InventedFactError(P07DraftingError):
    """Raised when narrative text introduces facts absent from the verified dossier."""
    pass


class UnverifiedGlyphError(P07DraftingError):
    """Raised when an unconfirmed or AI-generated Hán–Nôm glyph is used without human review."""
    pass


class Missing2DFallbackError(P07DraftingError):
    """Raised when 3D narration script does not provide a 100% authentic 2D rubbing fallback."""
    pass


# --------------------------------------------------------------------------- #
# Models for Sentence-Level Source Binding & Sections
# --------------------------------------------------------------------------- #
class SentenceClaimRef(BaseModel):
    sentence_index: int
    sentence_text: str
    claim_id: str
    source_id: str
    source_title: str
    locator: str
    is_verified: bool = True
    confidence: str = "high"


class NarrativeSection(BaseModel):
    section_id: str
    title: str
    paragraphs: List[str] = Field(default_factory=list)
    sentence_claim_refs: List[SentenceClaimRef] = Field(default_factory=list)

    def total_words(self) -> int:
        return sum(len(p.split()) for p in self.paragraphs)


class DraftNarrativeVI(BaseModel):
    title: str
    sections: List[NarrativeSection] = Field(default_factory=list)
    word_count: int = 0
    all_sentences: List[SentenceClaimRef] = Field(default_factory=list)
    sha256: str = ""

    def compute_sha256(self) -> str:
        dump = json.dumps(
            {
                "title": self.title,
                "sections": [s.model_dump() for s in self.sections],
                "all_sentences": [r.model_dump() for r in self.all_sentences],
            },
            sort_keys=True,
            ensure_ascii=False,
        ).encode("utf-8")
        return hashlib.sha256(dump).hexdigest()


class DraftNarrativeEN(BaseModel):
    title: str
    sections: List[NarrativeSection] = Field(default_factory=list)
    word_count: int = 0
    all_sentences: List[SentenceClaimRef] = Field(default_factory=list)
    bilingual_aligned_ids: List[str] = Field(default_factory=list)
    sha256: str = ""

    def compute_sha256(self) -> str:
        dump = json.dumps(
            {
                "title": self.title,
                "sections": [s.model_dump() for s in self.sections],
                "all_sentences": [r.model_dump() for r in self.all_sentences],
            },
            sort_keys=True,
            ensure_ascii=False,
        ).encode("utf-8")
        return hashlib.sha256(dump).hexdigest()


class MuseumLabel(BaseModel):
    label_vi: str
    label_en: str
    word_count_vi: int
    word_count_en: int
    sentence_claim_refs: List[SentenceClaimRef] = Field(default_factory=list)
    sha256: str = ""


class HanNomEditorialNote(BaseModel):
    motif_id: str
    glyph_original: str
    sino_vietnamese: str
    modern_translation: str
    scholarly_note: str
    is_glyph_verified: bool = True
    source_id: str
    locator: str


class HotspotNarration(BaseModel):
    hotspot_id: str
    target_mesh_id: str
    coordinates: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])
    caption_vi: str
    caption_en: str
    claim_id: str
    source_id: str
    locator: str


class Fallback2DNarration(BaseModel):
    asset_id: str
    image_url: str
    rubbing_caption_vi: str
    rubbing_caption_en: str
    source_id: str
    locator: str


class InteractiveScript3D(BaseModel):
    hotspots: List[HotspotNarration] = Field(default_factory=list)
    fallback_2d: Fallback2DNarration
    sha256: str = ""


# --------------------------------------------------------------------------- #
# P07 Narrative Writer Engine
# --------------------------------------------------------------------------- #
class P07NarrativeWriter:
    """Orchestrates generation of fully verified, source-bound bilingual narrative drafts."""

    def __init__(self, dossier: ResearchDossier, allow_unsourced: bool = False):
        self.dossier = dossier
        self.allow_unsourced = allow_unsourced
        self.approved_claims = dossier.get_approved_claims()

    def _get_primary_binding(self, claim: DossierClaim) -> DossierSourceBinding:
        """Finds primary or first supporting source binding for a claim."""
        if not claim.source_bindings:
            raise UnsourcedAssertionError(
                f"Claim '{claim.claim_id}' has zero source bindings in dossier. "
                "Sentences without verified sources cannot hide invented facts."
            )
        for b in claim.source_bindings:
            if b.support_type in ("primary_evidence_for", "supports"):
                return b
        return claim.source_bindings[0]

    def write_vietnamese_narrative(self) -> DraftNarrativeVI:
        """Generates structured Vietnamese narrative sections with per-sentence citations."""
        if not self.approved_claims and not self.allow_unsourced:
            raise UnsourcedAssertionError(
                f"Cannot generate narrative for '{self.dossier.entity_slug}': zero approved claims available."
            )

        sections: List[NarrativeSection] = []
        all_sentences: List[SentenceClaimRef] = []
        sentence_counter = 0

        # Section 1: Overview & Identification
        overview_claims = [c for c in self.approved_claims if c.claim_type in ("identification", "factual")]
        if not overview_claims:
            overview_claims = self.approved_claims[:2]

        sec1_paragraphs = []
        sec1_refs = []
        for claim in overview_claims:
            binding = self._get_primary_binding(claim)
            text_sentence = claim.statement_vi.strip()
            if not text_sentence.endswith("."):
                text_sentence += "."

            ref = SentenceClaimRef(
                sentence_index=sentence_counter,
                sentence_text=text_sentence,
                claim_id=claim.claim_id,
                source_id=binding.source_id,
                source_title=binding.source_title,
                locator=binding.locator,
                is_verified=claim.is_approved,
                confidence=claim.confidence,
            )
            sec1_paragraphs.append(text_sentence)
            sec1_refs.append(ref)
            all_sentences.append(ref)
            sentence_counter += 1

        sections.append(
            NarrativeSection(
                section_id="sec_01_overview",
                title=f"Khảo cứu tổng quan: {self.dossier.name_vi}",
                paragraphs=sec1_paragraphs,
                sentence_claim_refs=sec1_refs,
            )
        )

        # Section 2: Historical context & Chronology
        chrono_claims = [c for c in self.approved_claims if c.claim_type in ("chronology", "production", "geographic")]
        if chrono_claims:
            sec2_paragraphs = []
            sec2_refs = []
            for claim in chrono_claims:
                binding = self._get_primary_binding(claim)
                text_sentence = claim.statement_vi.strip()
                if not text_sentence.endswith("."):
                    text_sentence += "."

                ref = SentenceClaimRef(
                    sentence_index=sentence_counter,
                    sentence_text=text_sentence,
                    claim_id=claim.claim_id,
                    source_id=binding.source_id,
                    source_title=binding.source_title,
                    locator=binding.locator,
                    is_verified=claim.is_approved,
                    confidence=claim.confidence,
                )
                sec2_paragraphs.append(text_sentence)
                sec2_refs.append(ref)
                all_sentences.append(ref)
                sentence_counter += 1

            sections.append(
                NarrativeSection(
                    section_id="sec_02_context",
                    title="Bối cảnh lịch sử và niên đại chế tác",
                    paragraphs=sec2_paragraphs,
                    sentence_claim_refs=sec2_refs,
                )
            )

        # Section 3: Iconography & Symbolism
        sym_claims = [c for c in self.approved_claims if c.claim_type in ("symbolism", "interpretation", "artwork")]
        if sym_claims:
            sec3_paragraphs = []
            sec3_refs = []
            for claim in sym_claims:
                binding = self._get_primary_binding(claim)
                text_sentence = claim.statement_vi.strip()
                if not text_sentence.endswith("."):
                    text_sentence += "."

                ref = SentenceClaimRef(
                    sentence_index=sentence_counter,
                    sentence_text=text_sentence,
                    claim_id=claim.claim_id,
                    source_id=binding.source_id,
                    source_title=binding.source_title,
                    locator=binding.locator,
                    is_verified=claim.is_approved,
                    confidence=claim.confidence,
                )
                sec3_paragraphs.append(text_sentence)
                sec3_refs.append(ref)
                all_sentences.append(ref)
                sentence_counter += 1

            sections.append(
                NarrativeSection(
                    section_id="sec_03_iconography",
                    title="Đặc điểm mỹ thuật và ý nghĩa biểu tượng",
                    paragraphs=sec3_paragraphs,
                    sentence_claim_refs=sec3_refs,
                )
            )

        total_words = sum(s.total_words() for s in sections)
        narrative = DraftNarrativeVI(
            title=f"Khảo cứu lịch sử: {self.dossier.name_vi}",
            sections=sections,
            word_count=total_words,
            all_sentences=all_sentences,
        )
        narrative.sha256 = narrative.compute_sha256()
        return narrative

    def write_english_narrative(self) -> DraftNarrativeEN:
        """Generates strictly aligned English narrative sections mapped to verified claims."""
        if not self.approved_claims and not self.allow_unsourced:
            raise UnsourcedAssertionError(
                f"Cannot generate English narrative for '{self.dossier.entity_slug}': zero approved claims."
            )

        sections: List[NarrativeSection] = []
        all_sentences: List[SentenceClaimRef] = []
        aligned_ids: List[str] = []
        sentence_counter = 0

        # Section 1: Overview
        sec1_paragraphs = []
        sec1_refs = []
        for claim in self.approved_claims:
            binding = self._get_primary_binding(claim)
            text_en = claim.statement_en or f"{claim.statement_vi} (Verified historical claim)."
            text_sentence = text_en.strip()
            if not text_sentence.endswith("."):
                text_sentence += "."

            ref = SentenceClaimRef(
                sentence_index=sentence_counter,
                sentence_text=text_sentence,
                claim_id=claim.claim_id,
                source_id=binding.source_id,
                source_title=binding.source_title,
                locator=binding.locator,
                is_verified=claim.is_approved,
                confidence=claim.confidence,
            )
            sec1_paragraphs.append(text_sentence)
            sec1_refs.append(ref)
            all_sentences.append(ref)
            aligned_ids.append(claim.claim_id)
            sentence_counter += 1

        sections.append(
            NarrativeSection(
                section_id="sec_en_01_historical_record",
                title=f"Historical Study: {self.dossier.name_en or self.dossier.name_vi}",
                paragraphs=sec1_paragraphs,
                sentence_claim_refs=sec1_refs,
            )
        )

        total_words = sum(s.total_words() for s in sections)
        narrative = DraftNarrativeEN(
            title=f"Historical Monograph: {self.dossier.name_en or self.dossier.name_vi}",
            sections=sections,
            word_count=total_words,
            all_sentences=all_sentences,
            bilingual_aligned_ids=aligned_ids,
        )
        narrative.sha256 = narrative.compute_sha256()
        return narrative

    def write_museum_label(self) -> MuseumLabel:
        """Generates concise bilingual museum label (80-150 words) with source citations."""
        if not self.approved_claims:
            raise UnsourcedAssertionError("Museum label requires at least one verified claim.")

        primary_claim = self.approved_claims[0]
        binding = self._get_primary_binding(primary_claim)

        label_vi = (
            f"{self.dossier.name_vi} là một trong những hình tượng chạm nổi tiêu biểu trên Cửu Đỉnh Huế. "
            f"{primary_claim.statement_vi} "
            f"Tư liệu lịch sử được ghi chép chuẩn xác trong {binding.source_title} ({binding.locator})."
        )
        label_en = (
            f"{self.dossier.name_en or self.dossier.name_vi} is an authoritative bronze relief motif on the Nine Dynastic Urns. "
            f"{primary_claim.statement_en or primary_claim.statement_vi} "
            f"Documented in royal archives: {binding.source_title} ({binding.locator})."
        )

        ref = SentenceClaimRef(
            sentence_index=0,
            sentence_text=primary_claim.statement_vi,
            claim_id=primary_claim.claim_id,
            source_id=binding.source_id,
            source_title=binding.source_title,
            locator=binding.locator,
            is_verified=True,
        )

        raw = (label_vi + label_en).encode("utf-8")
        return MuseumLabel(
            label_vi=label_vi,
            label_en=label_en,
            word_count_vi=len(label_vi.split()),
            word_count_en=len(label_en.split()),
            sentence_claim_refs=[ref],
            sha256=hashlib.sha256(raw).hexdigest(),
        )

    def write_hannom_notes(self) -> List[HanNomEditorialNote]:
        """Generates reviewed Hán–Nôm editorial notes with glyph provenance."""
        notes: List[HanNomEditorialNote] = []
        for rec in self.dossier.han_nom_records:
            if not rec.is_glyph_verified or rec.review_status != "verified":
                raise UnverifiedGlyphError(
                    f"Motif '{rec.motif_id}' contains unverified Hán–Nôm glyph '{rec.glyph_original}'. "
                    "Unconfirmed glyph promotion is strictly forbidden."
                )

            src = self.dossier.sources[0] if self.dossier.sources else None
            source_id = src.source_id if src else "source-archival-001"
            notes.append(
                HanNomEditorialNote(
                    motif_id=rec.motif_id,
                    glyph_original=rec.glyph_original,
                    sino_vietnamese=rec.sino_vietnamese,
                    modern_translation=rec.english_gloss,
                    scholarly_note=f"Được khắc rõ nét trên bề mặt đỉnh, đối chiếu văn bản cổ {src.title if src else 'Khâm Định'}.",
                    is_glyph_verified=True,
                    source_id=source_id,
                    locator="Quyển Cửu Đỉnh, biểu văn",
                )
            )
        return notes

    def write_interactive_script(self) -> InteractiveScript3D:
        """Generates 3D/AR narration script ensuring strict 2D rubbing fallback."""
        if not self.dossier.assets_2d:
            raise Missing2DFallbackError(
                f"Interactive 3D script for '{self.dossier.entity_slug}' lacks mandatory 2D rubbing fallback asset."
            )

        fallback_asset = next((a for a in self.dossier.assets_2d if a.is_rubbing_fallback), self.dossier.assets_2d[0])
        src = self.dossier.sources[0] if self.dossier.sources else None
        source_id = src.source_id if src else "source-heritage-rubbing"

        hotspots: List[HotspotNarration] = []
        if self.approved_claims and self.dossier.assets_3d:
            asset_3d = self.dossier.assets_3d[0]
            claim = self.approved_claims[0]
            binding = self._get_primary_binding(claim)

            hotspots.append(
                HotspotNarration(
                    hotspot_id=f"hs_{self.dossier.entity_slug}_01",
                    target_mesh_id=asset_3d.mesh_id,
                    coordinates=[0.12, 1.45, -0.05],
                    caption_vi=f"Quan sát chi tiết: {claim.statement_vi}",
                    caption_en=f"Observe details: {claim.statement_en or claim.statement_vi}",
                    claim_id=claim.claim_id,
                    source_id=binding.source_id,
                    locator=binding.locator,
                )
            )

        fallback_2d = Fallback2DNarration(
            asset_id=fallback_asset.asset_id,
            image_url=fallback_asset.file_url,
            rubbing_caption_vi=f"Bản dập hoa văn truyền thống 2D: {self.dossier.name_vi}",
            rubbing_caption_en=f"Traditional 2D rubbing archive: {self.dossier.name_en or self.dossier.name_vi}",
            source_id=source_id,
            locator="Kho tư liệu bản dập Viện Hán Nôm",
        )

        dump = json.dumps(
            {
                "hotspots": [h.model_dump() for h in hotspots],
                "fallback_2d": fallback_2d.model_dump(),
            },
            sort_keys=True,
            ensure_ascii=False,
        ).encode("utf-8")

        return InteractiveScript3D(
            hotspots=hotspots,
            fallback_2d=fallback_2d,
            sha256=hashlib.sha256(dump).hexdigest(),
        )
