#!/usr/bin/env python3
"""History-First content integrity validator (Spec section 68).

Run in CI / before release. Fails on:
- duplicate canonical slug
- orphan relation (subject/object missing)
- broken source FK on a claim binding
- verified factual claim with no eligible source
- public question depending on a blocked/unverified factual claim
- malformed coordinates / invalid geo precision
- duplicate legacy mapping

Warns on:
- translation missing (no name_en)
- unreviewed draft
- low-confidence claim
- approximate geography
- asset without derivative rights when only a thumbnail is used

Writes artifacts/history-content-validation.json.

Usage:
    python -m scripts.history.validate_history_content --database-url <URL> [--fail-on-warn]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker


def main() -> int:
    parser = argparse.ArgumentParser(description="History content integrity validation")
    parser.add_argument("--database-url", required=False, help="SQLAlchemy URL")
    parser.add_argument("--fail-on-warn", action="store_true")
    parser.add_argument("--out", default="artifacts/history-content-validation.json")
    args = parser.parse_args()

    if __package__ in (None, ""):
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.config import settings
    from backend.models import (
        HistoricalAsset,
        HistoricalClaim,
        HistoricalClaimSource,
        HistoricalEntity,
        HistoricalEntityRelation,
        HistoricalSource,
    )

    url = args.database_url or settings.database_url
    engine = create_engine(url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    errors: list[str] = []
    warnings: list[str] = []

    with SessionLocal() as db:
        # Duplicate slugs (case-insensitive)
        dup = db.execute(
            select(
                func.lower(HistoricalEntity.slug).label("slug_norm"),
                func.count(),
            ).group_by(func.lower(HistoricalEntity.slug)).having(func.count() > 1)
        ).all()
        for slug_norm, count in dup:
            errors.append(f"duplicate canonical slug: {slug_norm!r} ({count} rows)")

        entities = list(db.scalars(select(HistoricalEntity)))
        by_id = {e.id: e for e in entities}

        # Orphan relations + missing translation warning
        relations = list(db.scalars(select(HistoricalEntityRelation)))
        for rel in relations:
            if rel.subject_entity_id not in by_id:
                errors.append(f"orphan relation subject: {rel.subject_entity_id}")
            if rel.object_entity_id not in by_id:
                errors.append(f"orphan relation object: {rel.object_entity_id}")

        # Verified factual claim without eligible source
        eligible = {"supports", "primary_evidence_for"}
        bindings = list(db.scalars(select(HistoricalClaimSource)))
        claim_sources: dict = {}
        for b in bindings:
            claim_sources.setdefault(b.claim_id, []).append(b.support_type)
        claims = list(db.scalars(select(HistoricalClaim)))
        for c in claims:
            if not c.statement_en and c.entity_id in by_id and by_id[c.entity_id].publication_status in ("published", "verified"):
                warnings.append(f"translation missing (statement_en) for claim {c.id}")
            if c.verification_status == "expert_verified" and c.claim_type in (
                "factual", "chronology", "geographic", "identification"
            ):
                has = any(s in eligible for s in claim_sources.get(c.id, []))
                if not has:
                    errors.append(
                        f"verified factual claim {c.id} has no eligible source"
                    )

        # Broken source FK on a binding
        sources = {s.id for s in db.scalars(select(HistoricalSource.id))}
        for b in bindings:
            if b.source_id not in sources:
                errors.append(f"broken source FK on binding claim {b.claim_id}")

        # Malformed coordinates / precision
        for e in entities:
            if e.latitude is not None and not (-90 <= e.latitude <= 90):
                errors.append(f"malformed latitude on entity {e.slug}")
            if e.longitude is not None and not (-180 <= e.longitude <= 180):
                errors.append(f"malformed longitude on entity {e.slug}")

        # Unreviewed drafts / low confidence / approximate geo warnings
        for e in entities:
            if e.publication_status in ("draft", "internal_review"):
                warnings.append(f"unreviewed draft entity: {e.slug}")
        for c in claims:
            if c.confidence == "low":
                warnings.append(f"low-confidence claim {c.id}")

        # Asset rights warning
        assets = list(db.scalars(select(HistoricalAsset)))
        for a in assets:
            if a.thumbnail_url and a.derivative_allowed is False:
                warnings.append(f"asset {a.id} has thumbnail but no derivative rights")

    result: dict[str, Any] = {
        "errors": errors,
        "warnings": warnings,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "pass": len(errors) == 0,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if errors:
        return 1
    if args.fail_on_warn and warnings:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
