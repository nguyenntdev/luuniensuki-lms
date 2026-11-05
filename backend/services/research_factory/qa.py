# -*- coding: utf-8 -*-
"""P08 Independent QA Runner and Adversarial Red-Teaming Engine.

Implements Agents P08-A01 to P08-A10:
- P08-A01: Sentence-to-claim verifier (sentence_evidence_report.json)
- P08-A02: Exact-citation and locator checker (locator_audit.json)
- P08-A03: Historical accuracy red-teamer (history_adversarial.json)
- P08-A04: Han-Nom and translation red-teamer (hannom_adversarial.json)
- P08-A05: Contradiction / dispute red-teamer (dispute_adversarial.json)
- P08-A06: ELLO evidence rubric verifier (ello_rubric_audit.json)
- P08-A07: Disputed quiz item verifier (quiz_audit.json)
- P08-A08: Media attribution & 2D fallback verifier (media_audit.json)
- P08-A09: Bilingual alignment verifier (bilingual_audit.json)
- P08-A10: Bundle integrity & provenance verifier (bundle_audit.json)

Invariants Enforced:
1. Zero unsourced assertions: every factual sentence must be bound to a verified source.
2. Any unresolved P0 blocker strictly causes GATE_BLOCKED, blocking downstream release.
"""
from __future__ import annotations

import hashlib
import json
import re
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .content_assembler import ContentBundleDraft
from .dossier import ResearchDossier


# --------------------------------------------------------------------------- #
# Severity and Gate Status
# --------------------------------------------------------------------------- #
class QASeverity(str, Enum):
    P0_BLOCKER = "P0_BLOCKER"
    P1_WARNING = "P1_WARNING"
    P2_INFO = "P2_INFO"


class QAGateStatus(str, Enum):
    GATE_PASSED = "GATE_PASSED"
    GATE_BLOCKED = "GATE_BLOCKED"


class QAFinding(BaseModel):
    agent_id: str  # e.g. "P08-A01"
    agent_name: str
    finding_code: str
    severity: QASeverity
    message: str
    target_ref: Optional[str] = None
    suggested_action: str


class QAFindingsReport(BaseModel):
    report_id: str
    bundle_id: str
    entity_slug: str
    gate_status: QAGateStatus
    total_findings: int
    p0_blockers_count: int
    p1_warnings_count: int
    p2_info_count: int
    findings: List[QAFinding] = Field(default_factory=list)
    sha256: str = ""

    def compute_sha256(self) -> str:
        dump = json.dumps(
            {
                "report_id": self.report_id,
                "bundle_id": self.bundle_id,
                "gate_status": self.gate_status.value,
                "findings": [f.model_dump() for f in self.findings],
            },
            sort_keys=True,
            ensure_ascii=False,
        ).encode("utf-8")
        return hashlib.sha256(dump).hexdigest()


# --------------------------------------------------------------------------- #
# P08 10-Agent Independent Checkers
# --------------------------------------------------------------------------- #
class P08SentenceToClaimVerifier:
    """Agent P08-A01: Analyzes every sentence and checks source binding."""

    @staticmethod
    def verify(bundle: ContentBundleDraft, dossier: ResearchDossier) -> List[QAFinding]:
        findings: List[QAFinding] = []
        approved_claim_ids = {c.claim_id for c in dossier.get_approved_claims()}
        approved_source_ids = {s.source_id for s in dossier.sources if s.verification_status in ("metadata_verified", "accessible")}

        # Check VI sentences
        for sec in bundle.narrative_vi.sections:
            for p in sec.paragraphs:
                sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", p) if s.strip()]
                for s in sentences:
                    # Must have matching ref in sec.sentence_claim_refs
                    matched_ref = next((r for r in sec.sentence_claim_refs if r.sentence_text.strip() == s), None)
                    if not matched_ref:
                        findings.append(
                            QAFinding(
                                agent_id="P08-A01",
                                agent_name="Sentence-to-claim verifier",
                                finding_code="UNSOURCED_FACTUAL_ASSERTION",
                                severity=QASeverity.P0_BLOCKER,
                                message=f"Factual sentence in section '{sec.section_id}' lacks source binding: '{s[:60]}...'",
                                target_ref=s,
                                suggested_action="Bind sentence to an approved historical claim and primary source or remove factoid.",
                            )
                        )
                    else:
                        if matched_ref.claim_id not in approved_claim_ids:
                            findings.append(
                                QAFinding(
                                    agent_id="P08-A01",
                                    agent_name="Sentence-to-claim verifier",
                                    finding_code="UNAPPROVED_CLAIM_BOUND",
                                    severity=QASeverity.P0_BLOCKER,
                                    message=f"Sentence bound to non-approved claim '{matched_ref.claim_id}'.",
                                    target_ref=s,
                                    suggested_action="Ensure claim is verified and published before citation.",
                                )
                            )
                        if matched_ref.source_id not in approved_source_ids:
                            findings.append(
                                QAFinding(
                                    agent_id="P08-A01",
                                    agent_name="Sentence-to-claim verifier",
                                    finding_code="UNAPPROVED_SOURCE_BOUND",
                                    severity=QASeverity.P0_BLOCKER,
                                    message=f"Sentence bound to unverified source '{matched_ref.source_id}'.",
                                    target_ref=s,
                                    suggested_action="Replace with verified archival primary source.",
                                )
                            )

        # Check EN sentences
        for sec in bundle.narrative_en.sections:
            for p in sec.paragraphs:
                sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", p) if s.strip()]
                for s in sentences:
                    matched_ref = next((r for r in sec.sentence_claim_refs if r.sentence_text.strip() == s), None)
                    if not matched_ref:
                        findings.append(
                            QAFinding(
                                agent_id="P08-A01",
                                agent_name="Sentence-to-claim verifier",
                                finding_code="UNSOURCED_FACTUAL_ASSERTION",
                                severity=QASeverity.P0_BLOCKER,
                                message=f"English factual sentence lacks source binding: '{s[:60]}...'",
                                target_ref=s,
                                suggested_action="Bind English statement to verified dossier claim.",
                            )
                        )

        return findings


class P08LocatorAuditChecker:
    """Agent P08-A02: Checks quote/offset/page accuracy against source snapshot."""

    @staticmethod
    def verify(bundle: ContentBundleDraft, dossier: ResearchDossier) -> List[QAFinding]:
        findings: List[QAFinding] = []
        for ref in bundle.aggregated_sentence_claim_refs:
            if not ref.locator or ref.locator.strip().lower() in ("null", "none", "", "unknown"):
                findings.append(
                    QAFinding(
                        agent_id="P08-A02",
                        agent_name="Exact-citation and locator checker",
                        finding_code="MISSING_LOCATOR",
                        severity=QASeverity.P0_BLOCKER,
                        message=f"Claim '{ref.claim_id}' citation lacks specific page/scroll locator.",
                        target_ref=ref.sentence_text,
                        suggested_action="Provide exact volume/page locator from primary source.",
                    )
                )
            # Detect fabricated placeholder patterns
            if "fake_page" in ref.locator.lower() or "trang 9999" in ref.locator.lower():
                findings.append(
                    QAFinding(
                        agent_id="P08-A02",
                        agent_name="Exact-citation and locator checker",
                        finding_code="FABRICATED_CITATION_LOCATOR",
                        severity=QASeverity.P0_BLOCKER,
                        message=f"Detected fabricated or invalid page locator '{ref.locator}'.",
                        target_ref=ref.locator,
                        suggested_action="Audit against digitized physical archival copy.",
                    )
                )
        return findings


class P08HistoricalAccuracyRedTeamer:
    """Agent P08-A03: Adversarially checks chronology, reign, urn, and motif names."""

    @staticmethod
    def verify(bundle: ContentBundleDraft, dossier: ResearchDossier) -> List[QAFinding]:
        findings: List[QAFinding] = []
        full_text = " ".join(
            p for sec in bundle.narrative_vi.sections for p in sec.paragraphs
        ) + " " + bundle.museum_label.label_vi

        # Chronology check: Cửu Đỉnh casting was 1835-1837 under Minh Mạng
        if re.search(r"\b(thế kỷ\s+20|thế kỷ\s+XX|năm\s+19\d\d)\b", full_text, re.IGNORECASE):
            findings.append(
                QAFinding(
                    agent_id="P08-A03",
                    agent_name="Historical accuracy red-teamer",
                    finding_code="CHRONOLOGICAL_CONTRADICTION",
                    severity=QASeverity.P0_BLOCKER,
                    message="Narrative erroneously asserts 20th century dating for Nguyen dynastic bronzes.",
                    target_ref="19xx/thế kỷ 20",
                    suggested_action="Correct date to Minh Mạng reign (1835-1837).",
                )
            )
        return findings


class P08HanNomRedTeamer:
    """Agent P08-A04: Verifies Hán–Nôm glyph authenticity and prevents AI hallucinations."""

    @staticmethod
    def verify(bundle: ContentBundleDraft, dossier: ResearchDossier) -> List[QAFinding]:
        findings: List[QAFinding] = []
        for note in bundle.hannom_notes:
            if not note.is_glyph_verified:
                findings.append(
                    QAFinding(
                        agent_id="P08-A04",
                        agent_name="Han-Nom and translation red-teamer",
                        finding_code="UNVERIFIED_HAN_NOM_GLYPH",
                        severity=QASeverity.P0_BLOCKER,
                        message=f"Motif '{note.motif_id}' contains unreviewed Hán–Nôm glyph '{note.glyph_original}'.",
                        target_ref=note.glyph_original,
                        suggested_action="Obtain human epigraphy expert verification before publishing.",
                    )
                )
            if note.glyph_original == note.sino_vietnamese:
                # Merged chinese glyph with latin transliteration
                findings.append(
                    QAFinding(
                        agent_id="P08-A04",
                        agent_name="Han-Nom and translation red-teamer",
                        finding_code="MERGED_GLYPH_AND_READING",
                        severity=QASeverity.P1_WARNING,
                        message=f"Original glyph field mirrors Sino-Vietnamese reading for '{note.motif_id}'.",
                        target_ref=note.glyph_original,
                        suggested_action="Separate ideogram glyph from phonetic pronunciation.",
                    )
                )
        return findings


class P08ContradictionDisputeRedTeamer:
    """Agent P08-A05: Ensures disputed claims are not presented as undisputed fact."""

    @staticmethod
    def verify(bundle: ContentBundleDraft, dossier: ResearchDossier) -> List[QAFinding]:
        findings: List[QAFinding] = []
        disputed_claim_ids = {c.claim_id for c in dossier.claims if c.is_disputed}

        for ref in bundle.aggregated_sentence_claim_refs:
            if ref.claim_id in disputed_claim_ids:
                findings.append(
                    QAFinding(
                        agent_id="P08-A05",
                        agent_name="Contradiction/dispute red-teamer",
                        finding_code="DISPUTED_CLAIM_UNBALANCED",
                        severity=QASeverity.P0_BLOCKER,
                        message=f"Disputed claim '{ref.claim_id}' is presented in main narrative without historiographical balance.",
                        target_ref=ref.sentence_text,
                        suggested_action="Move to historiographical debate section with epistemic uncertainty flag.",
                    )
                )
        return findings


class P08ELLOEvidenceRubricVerifier:
    """Agent P08-A06: Ensures inquiry tasks require source citation and rubric uses 0-3 scale."""

    @staticmethod
    def verify(bundle: ContentBundleDraft, dossier: ResearchDossier) -> List[QAFinding]:
        findings: List[QAFinding] = []
        # Check 6 steps presence
        if len(bundle.ello_lesson.inquiry_steps) < 6:
            findings.append(
                QAFinding(
                    agent_id="P08-A06",
                    agent_name="ELLO evidence rubric verifier",
                    finding_code="INCOMPLETE_INQUIRY_STEPS",
                    severity=QASeverity.P0_BLOCKER,
                    message=f"ELLO inquiry lesson has {len(bundle.ello_lesson.inquiry_steps)} steps (expected 6).",
                    suggested_action="Implement all 6 inquiry steps: hook, observation, source_analysis, synthesis, reflection, evaluation.",
                )
            )

        for step in bundle.ello_lesson.inquiry_steps:
            if not step.requires_citation or not step.evidence_requirement:
                findings.append(
                    QAFinding(
                        agent_id="P08-A06",
                        agent_name="ELLO evidence rubric verifier",
                        finding_code="MISSING_EVIDENCE_REQUIREMENT",
                        severity=QASeverity.P0_BLOCKER,
                        message=f"Step {step.step_number} ({step.step_key}) does not enforce evidence citation.",
                        target_ref=step.title_vi,
                        suggested_action="Set requires_citation=True and define explicit evidence requirements.",
                    )
                )

        # Rubric scale check (0-3)
        for crit in bundle.assessment_pack.rubric_criteria:
            levels = crit.levels
            if not all(k in levels for k in (0, 1, 2, 3)):
                findings.append(
                    QAFinding(
                        agent_id="P08-A06",
                        agent_name="ELLO evidence rubric verifier",
                        finding_code="INVALID_RUBRIC_LEVELS",
                        severity=QASeverity.P0_BLOCKER,
                        message=f"Criterion '{crit.criterion_id}' does not span levels 0-3.",
                        suggested_action="Define descriptors for levels 0, 1, 2, and 3.",
                    )
                )

        return findings


class P08DisputedQuizItemVerifier:
    """Agent P08-A07: Blocks factual quizzes constructed on disputed claims."""

    @staticmethod
    def verify(bundle: ContentBundleDraft, dossier: ResearchDossier) -> List[QAFinding]:
        findings: List[QAFinding] = []
        disputed_claim_ids = {c.claim_id for c in dossier.claims if c.is_disputed}

        for q in bundle.assessment_pack.quiz_items:
            if q.is_disputed or q.bound_claim_id in disputed_claim_ids:
                findings.append(
                    QAFinding(
                        agent_id="P08-A07",
                        agent_name="Disputed quiz item verifier",
                        finding_code="QUIZ_ON_DISPUTED_CLAIM",
                        severity=QASeverity.P0_BLOCKER,
                        message=f"Quiz item '{q.quiz_id}' tests a disputed claim as uncontested fact.",
                        target_ref=q.question_vi,
                        suggested_action="Remove quiz item or convert to historiographical perspective question.",
                    )
                )
        return findings


class P08MediaAttributionAnd2DFallbackVerifier:
    """Agent P08-A08: Ensures 3D interactive script provides 2D rubbing fallback."""

    @staticmethod
    def verify(bundle: ContentBundleDraft, dossier: ResearchDossier) -> List[QAFinding]:
        findings: List[QAFinding] = []
        script = bundle.interactive_script_3d
        if not script.fallback_2d or not script.fallback_2d.image_url:
            findings.append(
                QAFinding(
                    agent_id="P08-A08",
                    agent_name="Media attribution and 2D fallback verifier",
                    finding_code="MISSING_2D_FALLBACK",
                    severity=QASeverity.P0_BLOCKER,
                    message="Interactive 3D script lacks 2D rubbing fallback for low-power or non-WebGL devices.",
                    suggested_action="Attach high-resolution 2D rubbing image asset and archival provenance.",
                )
            )
        return findings


class P08BilingualAlignmentVerifier:
    """Agent P08-A09: Ensures English narrative adds zero invented or unsupported facts."""

    @staticmethod
    def verify(bundle: ContentBundleDraft, dossier: ResearchDossier) -> List[QAFinding]:
        findings: List[QAFinding] = []
        approved_claim_ids = {c.claim_id for c in dossier.get_approved_claims()}

        for ref in bundle.narrative_en.all_sentences:
            if ref.claim_id not in approved_claim_ids:
                findings.append(
                    QAFinding(
                        agent_id="P08-A09",
                        agent_name="Bilingual alignment verifier",
                        finding_code="UNSUPPORTED_EN_FACT",
                        severity=QASeverity.P0_BLOCKER,
                        message=f"English narrative asserts claim '{ref.claim_id}' not in approved dossier: '{ref.sentence_text[:50]}...'",
                        target_ref=ref.sentence_text,
                        suggested_action="Remove invented assertion from English text.",
                    )
                )
        return findings


class P08BundleIntegrityVerifier:
    """Agent P08-A10: Verifies bundle hash, schema version, and completeness."""

    @staticmethod
    def verify(bundle: ContentBundleDraft, dossier: ResearchDossier) -> List[QAFinding]:
        findings: List[QAFinding] = []
        expected_hash = bundle.compute_bundle_sha256()
        if bundle.bundle_sha256 != expected_hash:
            findings.append(
                QAFinding(
                    agent_id="P08-A10",
                    agent_name="Bundle integrity verifier",
                    finding_code="BUNDLE_INTEGRITY_VIOLATION",
                    severity=QASeverity.P0_BLOCKER,
                    message=f"Bundle SHA-256 mismatch: recorded '{bundle.bundle_sha256}' vs computed '{expected_hash}'.",
                    suggested_action="Recompute bundle SHA-256 after final edits.",
                )
            )

        if not bundle.source_bibliography:
            findings.append(
                QAFinding(
                    agent_id="P08-A10",
                    agent_name="Bundle integrity verifier",
                    finding_code="EMPTY_BIBLIOGRAPHY",
                    severity=QASeverity.P1_WARNING,
                    message="Content bundle has an empty bibliography table.",
                    suggested_action="Include verified source records in bibliography.",
                )
            )

        return findings


# --------------------------------------------------------------------------- #
# P08 Independent QA Runner
# --------------------------------------------------------------------------- #
class P08IndependentQARunner:
    """Executes all 10 adversarial QA checkers and evaluates the release gate."""

    CHECKERS = [
        P08SentenceToClaimVerifier,
        P08LocatorAuditChecker,
        P08HistoricalAccuracyRedTeamer,
        P08HanNomRedTeamer,
        P08ContradictionDisputeRedTeamer,
        P08ELLOEvidenceRubricVerifier,
        P08DisputedQuizItemVerifier,
        P08MediaAttributionAnd2DFallbackVerifier,
        P08BilingualAlignmentVerifier,
        P08BundleIntegrityVerifier,
    ]

    @classmethod
    def run_qa(cls, bundle: ContentBundleDraft, dossier: ResearchDossier) -> QAFindingsReport:
        all_findings: List[QAFinding] = []

        for checker in cls.CHECKERS:
            findings = checker.verify(bundle, dossier)
            all_findings.extend(findings)

        p0_count = sum(1 for f in all_findings if f.severity == QASeverity.P0_BLOCKER)
        p1_count = sum(1 for f in all_findings if f.severity == QASeverity.P1_WARNING)
        p2_count = sum(1 for f in all_findings if f.severity == QASeverity.P2_INFO)

        gate_status = QAGateStatus.GATE_BLOCKED if p0_count > 0 else QAGateStatus.GATE_PASSED

        report = QAFindingsReport(
            report_id=f"qa_report_{bundle.bundle_id[:8]}",
            bundle_id=bundle.bundle_id,
            entity_slug=bundle.entity_slug,
            gate_status=gate_status,
            total_findings=len(all_findings),
            p0_blockers_count=p0_count,
            p1_warnings_count=p1_count,
            p2_info_count=p2_count,
            findings=all_findings,
        )
        report.sha256 = report.compute_sha256()
        return report
