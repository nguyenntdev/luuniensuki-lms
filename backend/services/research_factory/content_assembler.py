# -*- coding: utf-8 -*-
"""P07 Content Bundle Assembler (Agent P07-A10).

Integrates all 9 drafting outputs into a single canonical, verified
educational content bundle draft with cryptographic SHA-256 lineage and
audit metadata.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .dossier import DossierSource, ResearchDossier
from .lesson_writer import AssessmentRubricPack, ELLOLessonDraft
from .writers import (
    DraftNarrativeEN,
    DraftNarrativeVI,
    HanNomEditorialNote,
    InteractiveScript3D,
    MuseumLabel,
    SentenceClaimRef,
    UnsourcedAssertionError,
)


class ContentBundleDraft(BaseModel):
    """Authoritative educational and narrative content bundle draft produced by P07."""

    bundle_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_slug: str
    schema_version: str = "v1.0"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    narrative_vi: DraftNarrativeVI
    narrative_en: DraftNarrativeEN
    museum_label: MuseumLabel
    hannom_notes: List[HanNomEditorialNote] = Field(default_factory=list)
    interactive_script_3d: InteractiveScript3D
    ello_lesson: ELLOLessonDraft
    assessment_pack: AssessmentRubricPack

    source_bibliography: List[DossierSource] = Field(default_factory=list)
    aggregated_sentence_claim_refs: List[SentenceClaimRef] = Field(default_factory=list)

    bundle_sha256: str = ""
    status: str = "DRAFT_PENDING_QA"

    def compute_bundle_sha256(self) -> str:
        dump = json.dumps(
            {
                "bundle_id": self.bundle_id,
                "entity_slug": self.entity_slug,
                "narrative_vi_sha": self.narrative_vi.sha256,
                "narrative_en_sha": self.narrative_en.sha256,
                "interactive_script_sha": self.interactive_script_3d.sha256,
                "ello_lesson_sha": self.ello_lesson.sha256,
                "assessment_pack_sha": self.assessment_pack.sha256,
                "total_claims_bound": len(self.aggregated_sentence_claim_refs),
            },
            sort_keys=True,
            ensure_ascii=False,
        ).encode("utf-8")
        return hashlib.sha256(dump).hexdigest()


def assemble_content_bundle(
    dossier: ResearchDossier,
    narrative_vi: DraftNarrativeVI,
    narrative_en: DraftNarrativeEN,
    museum_label: MuseumLabel,
    hannom_notes: List[HanNomEditorialNote],
    interactive_script_3d: InteractiveScript3D,
    ello_lesson: ELLOLessonDraft,
    assessment_pack: AssessmentRubricPack,
) -> ContentBundleDraft:
    """Assembles and verifies all P07 outputs into a ContentBundleDraft."""
    # Check that every narrative section has at least one source citation
    for sec in narrative_vi.sections:
        if sec.paragraphs and not sec.sentence_claim_refs:
            raise UnsourcedAssertionError(
                f"Vietnamese narrative section '{sec.section_id}' contains text without source citations."
            )

    for sec in narrative_en.sections:
        if sec.paragraphs and not sec.sentence_claim_refs:
            raise UnsourcedAssertionError(
                f"English narrative section '{sec.section_id}' contains text without source citations."
            )

    # Aggregate all sentence refs
    aggregated: List[SentenceClaimRef] = []
    aggregated.extend(narrative_vi.all_sentences)
    aggregated.extend(narrative_en.all_sentences)
    aggregated.extend(museum_label.sentence_claim_refs)

    bundle = ContentBundleDraft(
        entity_slug=dossier.entity_slug,
        narrative_vi=narrative_vi,
        narrative_en=narrative_en,
        museum_label=museum_label,
        hannom_notes=hannom_notes,
        interactive_script_3d=interactive_script_3d,
        ello_lesson=ello_lesson,
        assessment_pack=assessment_pack,
        source_bibliography=dossier.sources,
        aggregated_sentence_claim_refs=aggregated,
    )
    bundle.bundle_sha256 = bundle.compute_bundle_sha256()
    return bundle
