# -*- coding: utf-8 -*-
"""Research Factory Service Orchestrator (P07 Educational Drafting & P08 Independent QA).

Wires together drafting agents (P07-A01..A10), independent QA checkers (P08-A01..A10),
and persistence into ResearchRun, ResearchPhase, ResearchJob, and ResearchEvidenceResult.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...research_factory_models import (
    ResearchEvidenceResult,
    ResearchJob,
    ResearchJobStatus,
    ResearchPhase,
    ResearchPhaseCode,
    ResearchPhaseStatus,
    ResearchRun,
)
from .content_assembler import ContentBundleDraft, assemble_content_bundle
from .dossier import ResearchDossier, build_dossier_from_entity
from .lesson_writer import AssessmentRubricPack, ELLOLessonDraft, P07LessonWriter
from .qa import P08IndependentQARunner, QAFindingsReport, QAGateStatus, QASeverity
from .writers import P07NarrativeWriter


def generate_narrative_and_lesson_draft(
    dossier: ResearchDossier,
    allow_unsourced: bool = False,
) -> ContentBundleDraft:
    """Executes P07 drafting workflow to generate verified bilingual narratives, 3D scripts, and ELLO lessons."""
    writer = P07NarrativeWriter(dossier, allow_unsourced=allow_unsourced)
    narrative_vi = writer.write_vietnamese_narrative()
    narrative_en = writer.write_english_narrative()
    museum_label = writer.write_museum_label()
    hannom_notes = writer.write_hannom_notes()
    interactive_3d = writer.write_interactive_script()

    lesson_writer = P07LessonWriter(dossier)
    ello_lesson = lesson_writer.generate_ello_lesson()
    assessment_pack = lesson_writer.generate_assessment_rubric_pack()

    bundle = assemble_content_bundle(
        dossier=dossier,
        narrative_vi=narrative_vi,
        narrative_en=narrative_en,
        museum_label=museum_label,
        hannom_notes=hannom_notes,
        interactive_script_3d=interactive_3d,
        ello_lesson=ello_lesson,
        assessment_pack=assessment_pack,
    )
    return bundle


def run_p08_independent_qa(
    bundle: ContentBundleDraft,
    dossier: ResearchDossier,
) -> QAFindingsReport:
    """Executes P08 independent QA checks across all 10 checkers and computes release gate status."""
    return P08IndependentQARunner.run_qa(bundle, dossier)


def persist_factory_phase_results(
    db: Session,
    run_id: uuid.UUID,
    bundle: ContentBundleDraft,
    qa_report: Optional[QAFindingsReport] = None,
) -> Dict[str, Any]:
    """Persists P07 content bundle and P08 QA findings into database research tables."""
    run = db.get(ResearchRun, run_id)
    if not run:
        raise ValueError(f"ResearchRun '{run_id}' not found.")

    # 1. P07 Phase
    p07_phase = db.scalars(
        select(ResearchPhase).where(
            ResearchPhase.run_id == run.id,
            ResearchPhase.phase_code == ResearchPhaseCode.P07.value,
        )
    ).first()

    if not p07_phase:
        p07_phase = ResearchPhase(
            run_id=run.id,
            phase_code=ResearchPhaseCode.P07.value,
            phase_order=7,
            wave=1,
            status=ResearchPhaseStatus.COMPLETED.value,
            input_manifest_sha256=bundle.bundle_sha256,
            output_snapshot_sha256=bundle.bundle_sha256,
            barrier_passed=True,
        )
        db.add(p07_phase)
        db.flush()

    # Create/update P07 Job slot 10 (Content Assembler)
    job_p07 = db.scalars(
        select(ResearchJob).where(
            ResearchJob.phase_id == p07_phase.id,
            ResearchJob.agent_index == 10,
        )
    ).first()

    if not job_p07:
        job_p07 = ResearchJob(
            phase_id=p07_phase.id,
            agent_index=10,
            agent_role="P07-A10 Citation editor and content assembler",
            idempotency_key=f"run_{run.id}_P07_A10_{bundle.bundle_id}",
            status=ResearchJobStatus.SUCCEEDED.value,
            input_payload={"entity_slug": bundle.entity_slug},
        )
        db.add(job_p07)
        db.flush()

    # Evidence result for P07
    ev_p07 = ResearchEvidenceResult(
        job_id=job_p07.id,
        schema_version="full_content_drafts/v1",
        output_schema="ContentBundleDraft",
        artifact_sha256=bundle.bundle_sha256,
        status="SUCCEEDED",
        source_ids=[s.source_id for s in bundle.source_bibliography],
        claim_ids=[r.claim_id for r in bundle.aggregated_sentence_claim_refs],
        evidence_locator_ids=[r.locator for r in bundle.aggregated_sentence_claim_refs],
        raw_envelope=bundle.model_dump(),
    )
    db.add(ev_p07)
    db.flush()

    # 2. P08 QA Phase (if report provided)
    result_meta = {"p07_evidence_id": str(ev_p07.id), "bundle_sha256": bundle.bundle_sha256}

    if qa_report:
        p08_phase = db.scalars(
            select(ResearchPhase).where(
                ResearchPhase.run_id == run.id,
                ResearchPhase.phase_code == ResearchPhaseCode.P08.value,
            )
        ).first()

        gate_passed = qa_report.gate_status == QAGateStatus.GATE_PASSED
        phase_status = ResearchPhaseStatus.COMPLETED.value if gate_passed else ResearchPhaseStatus.BLOCKED.value

        if not p08_phase:
            p08_phase = ResearchPhase(
                run_id=run.id,
                phase_code=ResearchPhaseCode.P08.value,
                phase_order=8,
                wave=1,
                status=phase_status,
                input_manifest_sha256=bundle.bundle_sha256,
                output_snapshot_sha256=qa_report.sha256,
                barrier_passed=gate_passed,
                gate_checks={"gate_status": qa_report.gate_status.value, "p0_blockers": qa_report.p0_blockers_count},
            )
            db.add(p08_phase)
            db.flush()
        else:
            p08_phase.status = phase_status
            p08_phase.barrier_passed = gate_passed
            p08_phase.gate_checks = {"gate_status": qa_report.gate_status.value, "p0_blockers": qa_report.p0_blockers_count}
            db.flush()

        job_p08 = db.scalars(
            select(ResearchJob).where(
                ResearchJob.phase_id == p08_phase.id,
                ResearchJob.agent_index == 1,
            )
        ).first()

        if not job_p08:
            job_p08 = ResearchJob(
                phase_id=p08_phase.id,
                agent_index=1,
                agent_role="P08 Independent QA Runner",
                idempotency_key=f"run_{run.id}_P08_A01_{qa_report.report_id}",
                status=ResearchJobStatus.SUCCEEDED.value,
                input_payload={"bundle_id": bundle.bundle_id},
            )
            db.add(job_p08)
            db.flush()

        ev_p08 = ResearchEvidenceResult(
            job_id=job_p08.id,
            schema_version="qa_findings/v1",
            output_schema="QAFindingsReport",
            artifact_sha256=qa_report.sha256,
            status="SUCCEEDED",
            warnings=[f.model_dump() for f in qa_report.findings if f.severity == QASeverity.P1_WARNING],
            failures=[f.model_dump() for f in qa_report.findings if f.severity == QASeverity.P0_BLOCKER],
            raw_envelope=qa_report.model_dump(),
        )
        db.add(ev_p08)
        db.flush()

        result_meta["p08_evidence_id"] = str(ev_p08.id)
        result_meta["gate_status"] = qa_report.gate_status.value
        result_meta["p0_blockers_count"] = qa_report.p0_blockers_count

    return result_meta
