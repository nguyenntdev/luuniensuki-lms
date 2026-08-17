#!/usr/bin/env python3
"""History-First Phase 2 — Legacy corpus migration into the historical domain.

Reads the enriched motif JSON files in ``data/`` and migrates them into the
historical governance model (Phase 1 tables):

- each urn file's item 0  -> a ``urn`` HistoricalEntity
- each urn file's items 1..17 -> ``relief`` HistoricalEntities
- legacy prose fields (description_short, description_educational,
  historical_context, symbolism, fun_fact) -> candidate HistoricalClaims with
  ``origin=ai_generated`` and ``verification_status=unreviewed`` (MIG-003)
- embedded quiz questions -> migrated to the legacy ``quiz_questions`` model
  and flagged ``blocked_for_authoritative_learning`` (MIG-005) until the
  Phase 8 question model V2 exists
- relations (relief ``located_on`` urn) -> HistoricalEntityRelation

CRITICAL historical-integrity rules (Spec 15, MIG-001..005):
- No invented sources/citations/authors/DOIs.
- AI-generated legacy content is NEVER marked verified.
- Missing sources stay ``needs_source``/``unreviewed``.
- Idempotent + dry-run capable + resumable.

Usage:
    python -m scripts.history.migrate_legacy --data-dir data --dry-run
    python -m scripts.history.migrate_legacy --data-dir data --write
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

if __package__ in (None, ""):
    REPO_ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(REPO_ROOT))

from backend.config import settings  # noqa: E402
from backend.models import (  # noqa: E402
    Base,
    HistoricalClaim,
    HistoricalEntity,
    HistoricalEntityRelation,
    Motif,
    MotifCategory,
    QuizQuestion,
    Urn,
)
from backend.services import history_governance as gov  # noqa: E402

URN_ORDER: dict[str, int] = {
    "cao-dinh": 1,
    "nhan-dinh": 2,
    "chuong-dinh": 3,
    "anh-dinh": 4,
    "nghi-dinh": 5,
    "thuan-dinh": 6,
    "tuyen-dinh": 7,
    "du-dinh": 8,
    "huyen-dinh": 9,
}


def _slugify(name: str) -> str:
    import unicodedata

    normalized = unicodedata.normalize("NFD", name)
    stripped = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    ascii_low = (
        stripped.lower()
        .replace("đ", "d")
        .replace(" ", "-")
        .replace("'", "")
    )
    import re

    return re.sub(r"[^a-z0-9-]+", "-", ascii_low).strip("-")


def _legacy_file_id_to_slug(legacy_id: str) -> str:
    # e.g. urn_cao_dinh_02 -> cao-dinh-02; urn_cao_dinh_01 (the urn itself) -> cao-dinh
    parts = legacy_id.split("_")
    if len(parts) >= 4 and parts[0] == "urn":
        urn_slug = f"{parts[1]}-{parts[2]}"
        n = int(parts[3])
        if n == 1:
            return urn_slug
        return f"{urn_slug}-{n:02d}"
    return _slugify(legacy_id)


def _report_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MigrationReport:
    def __init__(self) -> None:
        self.data: dict[str, Any] = {
            "legacy_files_scanned": 0,
            "legacy_records_scanned": 0,
            "urn_entities_created": 0,
            "relief_entities_created": 0,
            "other_entities_created": 0,
            "claims_created": 0,
            "ai_generated_claims": 0,
            "claims_needing_source": 0,
            "sources_created": 0,
            "relations_created": 0,
            "questions_migrated": 0,
            "questions_blocked_for_verification": 0,
            "duplicates": [],
            "invalid_records": [],
            "unmapped_records": [],
        }

    def to_json(self) -> dict[str, Any]:
        return self.data


def _category_to_claim_type(category: str) -> str:
    # Legacy motif categories map onto claim types conservatively. All remain
    # unreviewed; this is only a coarse label, never verification.
    mapping = {
        MotifCategory.linh_thu.value: "classification",
        MotifCategory.dong_vat.value: "classification",
        MotifCategory.thao_moc.value: "classification",
        MotifCategory.dia_ly.value: "geographic",
        MotifCategory.nong_nghiep.value: "classification",
        MotifCategory.vo_bi.value: "classification",
        MotifCategory.giao_thuong.value: "classification",
        MotifCategory.thien_van.value: "classification",
        MotifCategory.kien_truc.value: "classification",
    }
    return mapping.get(category, "classification")


def _migrate_file(
    db: Session,
    path: Path,
    report: MigrationReport,
    write: bool,
    legacy_map: dict[str, str],
) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    report.data["legacy_files_scanned"] += 1
    if not isinstance(data, list):
        report.data["invalid_records"].append(f"{path.name}: not a list")
        return

    urn_record = data[0]
    urn_legacy_id = str(urn_record.get("id", ""))
    urn_slug = _legacy_file_id_to_slug(urn_legacy_id)
    urn_name_vi = str(urn_record.get("name_vi", urn_slug))
    urn_location = str(urn_record.get("urn_location", urn_name_vi))

    # ---- Urn entity ----
    existing_urn = db.scalar(
        select(HistoricalEntity).where(HistoricalEntity.slug == urn_slug)
    )
    if existing_urn is None:
        report.data["urn_entities_created"] += 1
        if write:
            entity = gov.create_entity(
                db,
                data={
                    "entity_type": "urn",
                    "slug": urn_slug,
                    "name_vi": urn_name_vi,
                    "name_en": urn_record.get("name_en"),
                    "alternative_names": [urn_location],
                    "summary_vi": urn_record.get("description_short"),
                    "publication_status": "public_unverified",
                    "content_version": 1,
                },
                actor_id=None,
            )
            legacy_map[urn_legacy_id] = str(entity.id)
            db.flush()
    else:
        legacy_map[urn_legacy_id] = str(existing_urn.id)

    report.data["legacy_records_scanned"] += 1  # urn record

    # ---- Relief entities + claims ----
    for idx, item in enumerate(data[1:], start=2):
        legacy_id = str(item.get("id", f"{urn_legacy_id}_{idx}"))
        report.data["legacy_records_scanned"] += 1
        relief_slug = _legacy_file_id_to_slug(legacy_id)
        if not relief_slug:
            report.data["invalid_records"].append(legacy_id)
            continue

        name_vi = str(item.get("name_vi", relief_slug))
        category = str(item.get("category", ""))

        relief_entity = db.scalar(
            select(HistoricalEntity).where(HistoricalEntity.slug == relief_slug)
        )
        if relief_entity is None:
            report.data["relief_entities_created"] += 1
            if write:
                entity = gov.create_entity(
                    db,
                    data={
                        "entity_type": "relief",
                        "slug": relief_slug,
                        "name_vi": name_vi,
                        "name_en": item.get("name_en"),
                        "alternative_names": [urn_location],
                        "summary_vi": item.get("description_short"),
                        "publication_status": "public_unverified",
                        "content_version": 1,
                    },
                    actor_id=None,
                )
                relief_entity = entity
                legacy_map[legacy_id] = str(entity.id)
                db.flush()
            else:
                relief_entity = None
        else:
            legacy_map[legacy_id] = str(relief_entity.id)

        # ---- Claims from legacy prose (MIG-004) ----
        claim_sources = [
            ("description_short", "factual"),
            ("description_educational", "factual"),
            ("historical_context", "contextual"),
            ("symbolism", "interpretation"),
            ("fun_fact", "traditional_account"),
        ]
        # In dry-run, relief_entity is None when it would be created; claims are
        # planned against the intended relief regardless (no DB lookup needed).
        planned_relief = relief_entity is not None
        for field, claim_type in claim_sources:
            text = item.get(field)
            if not text or not str(text).strip():
                continue
            claim_type = "interpretation" if claim_type == "contextual" else claim_type
            # Coarse category-based type for factual-like fields.
            effective_type = (
                _category_to_claim_type(category) if claim_type == "factual" else claim_type
            )
            if not write:
                # Plan-only: count claims that would be created for this relief.
                report.data["claims_created"] += 1
                report.data["ai_generated_claims"] += 1
                report.data["claims_needing_source"] += 1
                continue
            if relief_entity is None:
                continue
            existing_claim = db.scalar(
                select(HistoricalClaim).where(
                    HistoricalClaim.entity_id == relief_entity.id,
                    HistoricalClaim.claim_key == f"legacy_{field}",
                )
            )
            if existing_claim is None:
                gov.create_claim(
                    db,
                    data={
                        "entity_id": relief_entity.id,
                        "claim_key": f"legacy_{field}",
                        "claim_type": effective_type,
                        "statement_vi": str(text).strip(),
                        "confidence": "unknown",
                        "verification_status": "unreviewed",
                        "origin": "ai_generated" if item.get("is_ai_generated") else "legacy_import",
                        "risk_level": "normal",
                    },
                    actor_id=None,
                )
                report.data["claims_created"] += 1
                report.data["ai_generated_claims"] += 1
                report.data["claims_needing_source"] += 1
                db.flush()

        # ---- located_on relation (relief -> urn) ----
        if write:
            if relief_entity is not None:
                urn_entity = db.scalar(
                    select(HistoricalEntity).where(HistoricalEntity.slug == urn_slug)
                )
                if urn_entity is not None:
                    rel_exists = db.scalar(
                        select(HistoricalEntityRelation).where(
                            HistoricalEntityRelation.subject_entity_id == relief_entity.id,
                            HistoricalEntityRelation.predicate == "located_on",
                            HistoricalEntityRelation.object_entity_id == urn_entity.id,
                        )
                    )
                    if rel_exists is None:
                        gov.create_relation(
                            db,
                            data={
                                "subject_entity_id": relief_entity.id,
                                "predicate": "located_on",
                                "object_entity_id": urn_entity.id,
                                "confidence": "medium",
                                "verification_status": "unreviewed",
                            },
                            actor_id=None,
                        )
                        report.data["relations_created"] += 1
                        db.flush()
        else:
            # Plan-only: one located_on relation per relief to be created.
            report.data["relations_created"] += 1


def _migrate_questions(
    db: Session,
    report: MigrationReport,
    write: bool,
) -> None:
    """Flag legacy quiz questions that depend on unverified claims (MIG-005).

    The legacy ``quiz_questions`` table is left in place (preserve working
    quiz/learning) but every question whose lesson is AI-generated is marked
    ``blocked_for_authoritative_learning`` so it does not enter authoritative
    learning until its backing claims are source-verified.
    """
    from backend.models import LessonContent

    lessons = list(db.scalars(select(LessonContent)))
    for lesson in lessons:
        if not lesson.is_ai_generated:
            continue
        qs = list(db.scalars(select(QuizQuestion).where(QuizQuestion.motif_id == lesson.motif_id)))
        for q in qs:
            if getattr(q, "content_validation_status", None) != "blocked_for_authoritative_learning":
                if write:
                    q.content_validation_status = "blocked_for_authoritative_learning"  # type: ignore[attr-defined]
                report.data["questions_migrated"] += 1
                report.data["questions_blocked_for_verification"] += 1
    if write:
        db.flush()


def main() -> int:
    parser = argparse.ArgumentParser(description="Legacy history migration")
    parser.add_argument("--data-dir", default="data", help="Path to data/ dir")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Persist changes (default is dry-run / plan-only)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Explicit dry-run (default behavior; kept for symmetry)",
    )
    parser.add_argument("--report-out", default="artifacts/history-migration-report.json")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.is_dir():
        print(f"Data dir not found: {data_dir}", file=sys.stderr)
        return 2

    engine = create_engine(settings.database_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    report = MigrationReport()
    legacy_map: dict[str, str] = {}

    files = sorted(data_dir.glob("*_Data_*.json"))
    with SessionLocal() as db:
        for path in files:
            try:
                _migrate_file(db, path, report, args.write, legacy_map)
            except Exception as exc:  # noqa: BLE001
                report.data["invalid_records"].append(f"{path.name}: {exc}")
                db.rollback()
        _migrate_questions(db, report, args.write)
        if args.write:
            db.commit()

    report.data["unmapped_records"] = [
        fid
        for fid in legacy_map
        if legacy_map[fid] is None
    ]
    report.data["timestamp"] = _report_now()

    report_out = Path(args.report_out)
    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(
        json.dumps(report.to_json(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report.to_json(), ensure_ascii=False, indent=2))
    print(f"\n[{'WRITE' if args.write else 'DRY-RUN'}] report -> {report_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
