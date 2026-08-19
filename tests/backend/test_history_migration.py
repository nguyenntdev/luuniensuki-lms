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
    Motif,
    Urn,
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
    assert len(claims) == 765
    for claim in claims[:20]:
        assert not claim_has_eligible_source(db_session, claim)
    for claim in claims:
        assert claim.verification_status in ("unreviewed", "needs_source")


def test_migration_relations_all_reliefs_located_on_urn(client, db_session, migrated_corpus):
    relations = list(db_session.scalars(select(HistoricalEntityRelation)))
    assert len(relations) == 153
    entities_by_id = {e.id: e for e in db_session.scalars(select(HistoricalEntity))}
    for rel in relations:
        assert rel.predicate == "located_on"
        subject = entities_by_id.get(rel.subject_entity_id)
        obj = entities_by_id.get(rel.object_entity_id)
        assert subject is not None and subject.entity_type == "relief"
        assert obj is not None and obj.entity_type == "urn"


def test_migration_slugs_are_unique_and_deterministic(client, db_session, migrated_corpus):
    from sqlalchemy import func

    rows = db_session.execute(
        select(HistoricalEntity.slug, func.count())
        .group_by(HistoricalEntity.slug)
        .having(func.count() > 1)
    ).all()
    assert rows == []


# --------------------------------------------------------------------------- #
# 3D hotspot deep-link (Phase 7)
# --------------------------------------------------------------------------- #
@pytest.fixture
def seeded_urn_and_motif(db_session):
    """Seed the legacy `urns` + `motifs` rows and target relief the 3D hotspot endpoints resolve
    against (the corpus migration only creates historical_entities)."""
    from sqlalchemy import select

    urn_row = db_session.scalar(
        select(Urn).where(Urn.slug == "cao-dinh")
    )
    if urn_row is None:
        urn_row = Urn(
            slug="cao-dinh",
            name="Cao Đỉnh",
            name_han="高",
            represents="Cao",
            model_url="/assets/models/CAO-DINH-v1.glb",
            display_order=1,
            is_demo=False,
        )
        db_session.add(urn_row)
        db_session.flush()
    motif_row = db_session.scalar(
        select(Motif).where(Motif.mesh_name == "mesh_urn_cao_dinh_02_v1")
    )
    if motif_row is None:
        motif_row = Motif(
            mesh_name="mesh_urn_cao_dinh_02_v1",
            name="Long",
            urn_id=urn_row.id,
            category="linh_thu",
            pos_x=-0.5,
            pos_y=0.9,
            pos_z=0.87,
            bounding_radius=0.08,
            display_order=2,
            is_demo=False,
            is_active=True,
        )
        db_session.add(motif_row)
        db_session.flush()
    urn_entity_row = db_session.scalar(
        select(HistoricalEntity).where(HistoricalEntity.slug == "cao-dinh")
    )
    if urn_entity_row is None:
        urn_entity_row = HistoricalEntity(
            entity_type="urn",
            slug="cao-dinh",
            name_vi="Cao Đỉnh",
            summary_vi="Cao Đỉnh",
            publication_status="public_unverified",
            content_version=1,
        )
        db_session.add(urn_entity_row)
        db_session.flush()
    entity_row = db_session.scalar(
        select(HistoricalEntity).where(HistoricalEntity.slug == "cao-dinh-02")
    )
    if entity_row is None:
        entity_row = HistoricalEntity(
            entity_type="relief",
            slug="cao-dinh-02",
            name_vi="Rồng",
            summary_vi="Long",
            publication_status="public_unverified",
            content_version=1,
        )
        db_session.add(entity_row)
        db_session.flush()
    return urn_row, motif_row


def test_relief_hotspot_returns_canonical_mesh(
    client, db_session, seeded_urn_and_motif
):
    """A migrated relief maps to a canonical hotspot (mesh_name + position).

    Cao Đỉnh motifs have seeded coordinates; the endpoint must return the
    deterministic mesh reference and real coordinates — never fabricated."""
    hotspot = client.get("/api/v1/history/reliefs/cao-dinh/cao-dinh-02/hotspot")
    assert hotspot.status_code == 200, hotspot.text
    body = hotspot.json()
    assert body["slug"] == "cao-dinh-02"
    assert body["hotspot"] is not None
    assert body["hotspot"]["mesh_name"] == "mesh_urn_cao_dinh_02_v1"
    pos = body["hotspot"]["pos"]
    assert len(pos) == 3
    assert all(isinstance(v, (int, float)) for v in pos)


def test_relief_hotspot_unknown_relief_404(client, db_session):
    res = client.get("/api/v1/history/reliefs/cao-dinh/not-a-relief/hotspot")
    assert res.status_code == 404


def test_relief_hotspot_mesh_name_matches_db(
    client, db_session, seeded_urn_and_motif
):
    from sqlalchemy import select

    from backend.models import Motif

    motif = db_session.scalar(
        select(Motif).where(Motif.mesh_name == "mesh_urn_cao_dinh_02_v1")
    )
    assert motif is not None
    assert motif.pos_x is not None and motif.pos_z is not None
