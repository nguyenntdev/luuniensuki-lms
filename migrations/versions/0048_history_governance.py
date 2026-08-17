"""historical governance — entities, claims, sources, relations, geography, assets, audit

History-First Phase 1: creates the historical domain model tables described in
docs/specs/HISTORY_FIRST_MASTER_SPEC.md Part III:

- historical_entities            — canonical historical entity (urn, relief, person, place, ...)
- historical_claims             — decomposable historical assertions with epistemic metadata
- historical_sources            — bibliographic / provenance records
- historical_claim_sources      — claim<->source bindings with locators and support type
- historical_entity_relations   — typed relations between entities (with claim/source trace)
- historical_geographies        — historical geography per entity (precision + mapping status)
- historical_assets             — media/asset model with rights metadata
- historical_content_audit_log  — append-only audit trail for governance actions

All additive and reversible.

Revision ID: 0048_history_governance
Revises: 0047_revoked_refresh_tokens
Create Date: 2026-08-17
"""
from __future__ import annotations

from alembic import op


revision = "0048_history_governance"
down_revision = "0047_revoked_refresh_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        """
        CREATE OR REPLACE FUNCTION public.f_unaccent(text)
        RETURNS text AS
        'SELECT unaccent($1)'
        LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE
        """
    )

    # ------------------------------------------------------------------ #
    # historical_entities
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS historical_entities (
            id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            entity_type       TEXT NOT NULL,
            slug              TEXT NOT NULL,
            name_vi           TEXT NOT NULL,
            name_en           TEXT,
            name_han_nom      TEXT,
            alternative_names JSONB NOT NULL DEFAULT '[]'::jsonb,
            summary_vi        TEXT,
            summary_en        TEXT,
            start_date        DATE,
            end_date          DATE,
            date_precision    TEXT,
            latitude          DOUBLE PRECISION,
            longitude         DOUBLE PRECISION,
            geo_precision     TEXT,
            thumbnail_asset_id UUID,
            publication_status TEXT NOT NULL DEFAULT 'draft',
            content_version   INTEGER NOT NULL DEFAULT 1,
            created_by        UUID REFERENCES users(id),
            updated_by        UUID REFERENCES users(id),
            created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
            deleted_at        TIMESTAMPTZ
        );
        """
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_historical_entities_slug ON historical_entities(lower(slug))")
    op.execute("CREATE INDEX IF NOT EXISTS idx_historical_entities_type ON historical_entities(entity_type)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_historical_entities_pub ON historical_entities(publication_status)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_historical_entities_name_vi ON historical_entities(name_vi)")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_historical_entities_search
        ON historical_entities USING gin (
            (public.f_unaccent(name_vi)) gin_trgm_ops,
            (public.f_unaccent(COALESCE(name_en, ''))) gin_trgm_ops
        )
        """
    )

    # ------------------------------------------------------------------ #
    # historical_sources
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS historical_sources (
            id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source_type           TEXT NOT NULL,
            title                 TEXT NOT NULL,
            subtitle              TEXT,
            author_text           TEXT,
            editor_text           TEXT,
            publisher             TEXT,
            publication_year      INTEGER,
            publication_date      DATE,
            edition               TEXT,
            volume                TEXT,
            issue                 TEXT,
            pages                 TEXT,
            isbn                  TEXT,
            issn                  TEXT,
            doi                   TEXT,
            url                   TEXT,
            archive_url           TEXT,
            repository_identifier TEXT,
            language              TEXT,
            citation_text         TEXT,
            rights_status         TEXT,
            license               TEXT,
            attribution_text      TEXT,
            public_display_allowed BOOLEAN,
            derivative_allowed    BOOLEAN,
            verification_status   TEXT NOT NULL DEFAULT 'unreviewed',
            accessed_at           TIMESTAMPTZ,
            created_by            UUID REFERENCES users(id),
            created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_historical_sources_type ON historical_sources(source_type)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_historical_sources_year ON historical_sources(publication_year)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_historical_sources_title ON historical_sources USING gin ((public.f_unaccent(title)) gin_trgm_ops)")

    # ------------------------------------------------------------------ #
    # historical_claims
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS historical_claims (
            id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            entity_id           UUID NOT NULL REFERENCES historical_entities(id) ON DELETE CASCADE,
            claim_key           TEXT,
            claim_type          TEXT NOT NULL,
            statement_vi        TEXT NOT NULL,
            statement_en        TEXT,
            valid_from          DATE,
            valid_to            DATE,
            date_precision      TEXT,
            confidence          TEXT NOT NULL DEFAULT 'unknown',
            verification_status TEXT NOT NULL DEFAULT 'unreviewed',
            origin              TEXT NOT NULL,
            risk_level          TEXT NOT NULL DEFAULT 'normal',
            review_notes        TEXT,
            created_by          UUID REFERENCES users(id),
            reviewed_by         UUID REFERENCES users(id),
            reviewed_at         TIMESTAMPTZ,
            verified_by         UUID REFERENCES users(id),
            verified_at         TIMESTAMPTZ,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
            supersedes_claim_id UUID REFERENCES historical_claims(id),
            is_current          BOOLEAN NOT NULL DEFAULT true
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_historical_claims_entity ON historical_claims(entity_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_historical_claims_entity_ver ON historical_claims(entity_id, verification_status)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_historical_claims_type ON historical_claims(claim_type)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_historical_claims_current ON historical_claims(entity_id, is_current) WHERE is_current")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_historical_claims_search
        ON historical_claims USING gin (public.f_unaccent(statement_vi) gin_trgm_ops)
        """
    )

    # ------------------------------------------------------------------ #
    # historical_claim_sources
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS historical_claim_sources (
            claim_id             UUID NOT NULL REFERENCES historical_claims(id) ON DELETE CASCADE,
            source_id            UUID NOT NULL REFERENCES historical_sources(id) ON DELETE CASCADE,
            support_type         TEXT NOT NULL,
            locator_type         TEXT,
            page_start           TEXT,
            page_end             TEXT,
            chapter              TEXT,
            section              TEXT,
            figure               TEXT,
            folio                TEXT,
            inscription_location TEXT,
            quotation_excerpt    TEXT,
            quotation_language   TEXT,
            editor_note          TEXT,
            created_by           UUID REFERENCES users(id),
            created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (claim_id, source_id, support_type)
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_historical_claim_sources_source ON historical_claim_sources(source_id)")

    # ------------------------------------------------------------------ #
    # historical_entity_relations
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS historical_entity_relations (
            id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            subject_entity_id   UUID NOT NULL REFERENCES historical_entities(id) ON DELETE CASCADE,
            predicate           TEXT NOT NULL,
            object_entity_id    UUID NOT NULL REFERENCES historical_entities(id) ON DELETE CASCADE,
            claim_id            UUID REFERENCES historical_claims(id),
            source_id           UUID REFERENCES historical_sources(id),
            confidence          TEXT NOT NULL DEFAULT 'unknown',
            verification_status TEXT NOT NULL DEFAULT 'unreviewed',
            valid_from          DATE,
            valid_to            DATE,
            created_by          UUID REFERENCES users(id),
            created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_historical_entity_relations
                UNIQUE (subject_entity_id, predicate, object_entity_id)
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_historical_relations_subject ON historical_entity_relations(subject_entity_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_historical_relations_object ON historical_entity_relations(object_entity_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_historical_relations_predicate ON historical_entity_relations(predicate)")

    # ------------------------------------------------------------------ #
    # historical_geographies
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS historical_geographies (
            entity_id         UUID PRIMARY KEY REFERENCES historical_entities(id) ON DELETE CASCADE,
            historical_name   TEXT,
            modern_name       TEXT,
            historical_geometry JSONB,
            modern_geometry   JSONB,
            valid_from        DATE,
            valid_to          DATE,
            geo_precision     TEXT NOT NULL,
            mapping_status    TEXT NOT NULL,
            source_claim_id   UUID REFERENCES historical_claims(id),
            notes             TEXT
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_historical_geographies_mapping ON historical_geographies(mapping_status)")

    # ------------------------------------------------------------------ #
    # historical_assets
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS historical_assets (
            id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            asset_type            TEXT NOT NULL,
            storage_url           TEXT NOT NULL,
            thumbnail_url         TEXT,
            mime_type             TEXT,
            width                 INTEGER,
            height                INTEGER,
            duration              DOUBLE PRECISION,
            byte_size             BIGINT,
            sha256                TEXT,
            rights_status         TEXT,
            license               TEXT,
            attribution           TEXT,
            source_origin         TEXT,
            public_display_allowed BOOLEAN,
            derivative_allowed    BOOLEAN,
            entity_id             UUID REFERENCES historical_entities(id) ON DELETE SET NULL,
            created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_historical_assets_entity ON historical_assets(entity_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_historical_assets_type ON historical_assets(asset_type)")

    # ------------------------------------------------------------------ #
    # historical_content_audit_log
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS historical_content_audit_log (
            id            BIGSERIAL PRIMARY KEY,
            actor_id      UUID REFERENCES users(id),
            action        TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            resource_id   UUID,
            before_json   JSONB,
            after_json    JSONB,
            reason        TEXT,
            request_id    TEXT,
            created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_history_audit_resource ON historical_content_audit_log(resource_type, resource_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_history_audit_created ON historical_content_audit_log(created_at)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS historical_content_audit_log")
    op.execute("DROP TABLE IF EXISTS historical_assets")
    op.execute("DROP TABLE IF EXISTS historical_geographies")
    op.execute("DROP TABLE IF EXISTS historical_entity_relations")
    op.execute("DROP TABLE IF EXISTS historical_claim_sources")
    op.execute("DROP TABLE IF EXISTS historical_claims")
    op.execute("DROP TABLE IF EXISTS historical_sources")
    op.execute("DROP TABLE IF EXISTS historical_entities")
