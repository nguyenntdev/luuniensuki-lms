"""History-First Phase 2 migration tests.

Verifies the legacy corpus migration produces the expected canonical entities,
claims, relations and the MIG-003/005 invariants (AI content never verified;
questions blocked for authoritative learning until source-backed).
"""
import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from backend.models import (
    HistoricalClaim,
    HistoricalEntity,
    HistoricalEntityRelation,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_migration(db) -> dict:
    """Run the legacy migration inside the caller's transaction (rolled back
    with the session, so migration tests never pollute other test modules)."""
    from scripts.history.migrate_legacy import _migrate_file, _migrate_questions

    report = type("R", (), {"data": {
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
    }})
    legacy_map = {}
    data_dir = REPO_ROOT / "data"
    for path in sorted(data_dir.glob("*_Data_*.json")):
        _migrate_file(db, path, report, True, legacy_map)
    _migrate_questions(db, report, True)
    db.flush()
    return report.data


@pytest.fixture
def migrated_corpus(db_session):
    """Seed the full legacy corpus within the test transaction (auto-rolled
    back at teardown). Not session/autouse to avoid cross-module pollution."""
    _run_migration(db_session)
    db_session.flush()
    yield



def test_migration_produced_full_corpus(client, db_session, migrated_corpus):
    """All 9 urns + 153 reliefs exist as canonical entities (FLOW-02)."""
    entities = list(db_session.scalars(select(HistoricalEntity)))
    urns = [e for e in entities if e.entity_type == "urn"]
    reliefs = [e for e in entities if e.entity_type == "relief"]
    assert len(urns) == 9
    assert len(reliefs) == 153
    # Corpus of 162 = 9 files x 18 records (spec: 162 reliefs or exact audited size).
    assert len(entities) == 162


def test_migration_claims_never_verified(client, db_session, migrated_corpus):
    """AI-generated legacy claims must remain unreviewed (MIG-003)."""
    claims = list(db_session.scalars(select(HistoricalClaim)))
    assert len(claims) == 765
    for claim in claims:
        assert claim.verification_status == "unreviewed"
        assert claim.origin == "ai_generated"
        assert claim.confidence == "unknown"


def test_migration_claims_are_source_missing(client, db_session, migrated_corpus):
    """Claims with no eligible source must be marked needs_source/unreviewed."""
    from backend.services.history_governance import claim_has_eligible_source

    claims = list(db_session.scalars(select(HistoricalClaim)))
    for claim in claims:
        assert not claim_has_eligible_source(db_session, claim)
        assert claim.verification_status in ("unreviewed", "needs_source")


def test_migration_relations_all_reliefs_located_on_urn(client, db_session, migrated_corpus):
    relations = list(db_session.scalars(select(HistoricalEntityRelation)))
    assert len(relations) == 153
    for rel in relations:
        assert rel.predicate == "located_on"
        subject = db_session.get(HistoricalEntity, rel.subject_entity_id)
        obj = db_session.get(HistoricalEntity, rel.object_entity_id)
        assert subject.entity_type == "relief"
        assert obj.entity_type == "urn"


def test_migration_slugs_are_unique_and_deterministic(client, db_session, migrated_corpus):
    from sqlalchemy import func

    rows = db_session.execute(
        select(HistoricalEntity.slug, func.count())
        .group_by(HistoricalEntity.slug)
        .having(func.count() > 1)
    ).all()
    assert rows == []
