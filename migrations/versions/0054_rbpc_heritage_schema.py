"""RBPC Heritage Knowledge Catalogue and Commercial Slice Schema

Additive migration introducing tables for LƯU NIÊN — RBPC 2026:
- heritage_places
- heritage_heritage_relations
- heritage_source_evidence
- heritage_media_assets
- rbpc_creators
- rbpc_experiences
- rbpc_stories
- rbpc_claim_evidence
- rbpc_inquiries
- rbpc_events
- rbpc_content_audit

Content Scope: RBPC_HUE (isolated from legacy CUU_DINH).
Strictly additive: Uses CREATE TABLE IF NOT EXISTS and CREATE INDEX IF NOT EXISTS.
All enum-like fields are stored as TEXT to prevent DDL locks.

Revision ID: 0054_rbpc_heritage_schema
Revises: 0053_user_mission_quest_compound_indexes
Create Date: 2026-10-17
"""
from __future__ import annotations

from alembic import op

revision = "0054_rbpc_heritage_schema"
down_revision = "0053_user_mission_quest_compound_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. heritage_places
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS heritage_places (
            id UUID PRIMARY KEY,
            slug VARCHAR(160) NOT NULL UNIQUE,
            name_vi VARCHAR(255) NOT NULL,
            name_en VARCHAR(255),
            name_han_nom VARCHAR(255),
            entity_type VARCHAR(64) NOT NULL,
            heritage_category VARCHAR(64) NOT NULL,
            parent_id UUID REFERENCES heritage_places(id) ON DELETE SET NULL,
            official_designation VARCHAR(120),
            official_reference_id VARCHAR(64),
            period_label VARCHAR(120),
            historical_state VARCHAR(64),
            location_lat NUMERIC(10, 7),
            location_lon NUMERIC(10, 7),
            geo_precision VARCHAR(32) NOT NULL DEFAULT 'approximate',
            current_access_status VARCHAR(64) NOT NULL DEFAULT 'unknown',
            access_notes TEXT,
            visitor_summary_vi TEXT,
            visitor_summary_en TEXT,
            historical_summary_vi TEXT,
            historical_summary_en TEXT,
            editorial_status VARCHAR(32) NOT NULL DEFAULT 'candidate',
            content_scope VARCHAR(32) NOT NULL DEFAULT 'RBPC_HUE',
            thumbnail_url TEXT,
            published_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT ck_heritage_places_lat CHECK (location_lat IS NULL OR (location_lat >= -90.0 AND location_lat <= 90.0)),
            CONSTRAINT ck_heritage_places_lon CHECK (location_lon IS NULL OR (location_lon >= -180.0 AND location_lon <= 180.0))
        )
        """
    )
    op.execute("ALTER TABLE heritage_places ADD COLUMN IF NOT EXISTS thumbnail_url TEXT;")
    op.execute("CREATE INDEX IF NOT EXISTS idx_heritage_places_editorial ON heritage_places(editorial_status, content_scope)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_heritage_places_category ON heritage_places(heritage_category, editorial_status)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_heritage_places_type ON heritage_places(entity_type, editorial_status)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_heritage_places_parent ON heritage_places(parent_id)")

    # 2. heritage_heritage_relations
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS heritage_heritage_relations (
            id UUID PRIMARY KEY,
            from_place_id UUID NOT NULL REFERENCES heritage_places(id) ON DELETE CASCADE,
            to_place_id UUID NOT NULL REFERENCES heritage_places(id) ON DELETE CASCADE,
            relationship_type VARCHAR(64) NOT NULL,
            claim_id UUID,
            review_state VARCHAR(32) NOT NULL DEFAULT 'draft',
            description_vi TEXT,
            description_en TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_heritage_relations UNIQUE (from_place_id, to_place_id, relationship_type)
        )
        """
    )
    op.execute("ALTER TABLE heritage_heritage_relations ADD COLUMN IF NOT EXISTS claim_id UUID;")
    op.execute("CREATE INDEX IF NOT EXISTS idx_heritage_rel_from ON heritage_heritage_relations(from_place_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_heritage_rel_to ON heritage_heritage_relations(to_place_id)")

    # 3. heritage_source_evidence
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS heritage_source_evidence (
            id UUID PRIMARY KEY,
            place_id UUID NOT NULL REFERENCES heritage_places(id) ON DELETE CASCADE,
            source_url VARCHAR(1024),
            source_title VARCHAR(255) NOT NULL,
            source_author VARCHAR(255),
            publisher VARCHAR(255),
            cited_section VARCHAR(255),
            cited_page VARCHAR(64),
            statement TEXT NOT NULL,
            interpretation_note TEXT,
            evidence_status VARCHAR(32) NOT NULL DEFAULT 'needs_review',
            reuse_rights VARCHAR(32) NOT NULL DEFAULT 'unknown',
            content_scope VARCHAR(32) NOT NULL DEFAULT 'RBPC_HUE',
            reviewed_by UUID,
            reviewed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_heritage_evidence_place ON heritage_source_evidence(place_id, evidence_status)")

    # 4. heritage_media_assets
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS heritage_media_assets (
            id UUID PRIMARY KEY,
            place_id UUID REFERENCES heritage_places(id) ON DELETE CASCADE,
            media_type VARCHAR(32) NOT NULL,
            source_platform VARCHAR(64),
            original_url VARCHAR(1024) NOT NULL,
            title VARCHAR(255),
            creator_name VARCHAR(255),
            creator_url VARCHAR(1024),
            model_uid VARCHAR(64),
            license_label VARCHAR(64),
            license_url VARCHAR(1024),
            noai BOOLEAN NOT NULL DEFAULT FALSE,
            commercial_use_status VARCHAR(32) NOT NULL DEFAULT 'unreviewed',
            embed_permission_status VARCHAR(32) NOT NULL DEFAULT 'unreviewed',
            accuracy_grade VARCHAR(32) NOT NULL DEFAULT 'unreviewed',
            provenance_notes TEXT,
            attribution_text TEXT,
            content_status VARCHAR(32) NOT NULL DEFAULT 'candidate',
            content_scope VARCHAR(32) NOT NULL DEFAULT 'RBPC_HUE',
            rights_reviewed_by UUID,
            rights_reviewed_at TIMESTAMPTZ,
            checked_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT ck_heritage_media_uid CHECK (model_uid IS NULL OR model_uid ~ '^[a-f0-9]{32}$')
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_heritage_media_place ON heritage_media_assets(place_id, content_status)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_heritage_media_uid ON heritage_media_assets(model_uid) WHERE model_uid IS NOT NULL")

    # 5. rbpc_creators
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS rbpc_creators (
            id UUID PRIMARY KEY,
            slug VARCHAR(160) NOT NULL UNIQUE,
            public_name VARCHAR(255) NOT NULL,
            craft_tradition VARCHAR(120) NOT NULL,
            approved_bio_vi TEXT,
            approved_bio_en TEXT,
            portrait_asset_url VARCHAR(1024),
            public_region VARCHAR(120),
            workshop_address_approx VARCHAR(255),
            lineage_notes TEXT,
            display_consent_ref VARCHAR(120),
            consent_status VARCHAR(32) NOT NULL DEFAULT 'pending_review',
            is_verified BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_rbpc_creators_consent ON rbpc_creators(consent_status, is_verified)")

    # 6. rbpc_experiences
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS rbpc_experiences (
            id UUID PRIMARY KEY,
            slug VARCHAR(160) NOT NULL UNIQUE,
            creator_id UUID NOT NULL REFERENCES rbpc_creators(id) ON DELETE CASCADE,
            provider_name VARCHAR(255) NOT NULL,
            title_vi VARCHAR(255) NOT NULL,
            title_en VARCHAR(255),
            description_vi TEXT,
            description_en TEXT,
            duration_minutes INTEGER,
            pricing_display VARCHAR(64),
            currency VARCHAR(8) NOT NULL DEFAULT 'VND',
            area_public VARCHAR(120),
            availability_mode VARCHAR(32) NOT NULL DEFAULT 'inquiry_only',
            cancellation_policy_text TEXT,
            published_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_rbpc_exp_creator ON rbpc_experiences(creator_id, availability_mode)")

    # 7. rbpc_stories
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS rbpc_stories (
            id UUID PRIMARY KEY,
            slug VARCHAR(160) NOT NULL UNIQUE,
            title_vi VARCHAR(255) NOT NULL,
            title_en VARCHAR(255),
            intro_vi TEXT,
            intro_en TEXT,
            place_id UUID REFERENCES heritage_places(id) ON DELETE SET NULL,
            primary_asset_url VARCHAR(1024),
            status VARCHAR(32) NOT NULL DEFAULT 'draft',
            estimated_reading_minutes INTEGER NOT NULL DEFAULT 3,
            version INTEGER NOT NULL DEFAULT 1,
            reviewed_by UUID,
            reviewed_at TIMESTAMPTZ,
            published_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_rbpc_stories_status ON rbpc_stories(status, published_at)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_rbpc_stories_place ON rbpc_stories(place_id)")

    # 8. rbpc_claim_evidence
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS rbpc_claim_evidence (
            id UUID PRIMARY KEY,
            story_id UUID NOT NULL REFERENCES rbpc_stories(id) ON DELETE CASCADE,
            statement TEXT NOT NULL,
            locale VARCHAR(8) NOT NULL DEFAULT 'vi',
            claim_category VARCHAR(64) NOT NULL DEFAULT 'factual',
            source_title VARCHAR(255) NOT NULL,
            source_url VARCHAR(1024),
            support_type VARCHAR(32) NOT NULL DEFAULT 'direct',
            epistemic_certainty VARCHAR(32) NOT NULL DEFAULT 'verified_source',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_rbpc_claim_story ON rbpc_claim_evidence(story_id)")

    # 9. rbpc_inquiries
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS rbpc_inquiries (
            id UUID PRIMARY KEY,
            public_ref VARCHAR(64) NOT NULL UNIQUE,
            opaque_token VARCHAR(128) NOT NULL UNIQUE,
            experience_id UUID NOT NULL REFERENCES rbpc_experiences(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            contact_channel VARCHAR(32) NOT NULL DEFAULT 'email',
            contact_value VARCHAR(255) NOT NULL,
            desired_date DATE,
            party_size INTEGER,
            message VARCHAR(1000),
            consent_version VARCHAR(32) NOT NULL,
            consent_time_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            privacy_accepted BOOLEAN NOT NULL DEFAULT TRUE,
            state VARCHAR(32) NOT NULL DEFAULT 'new',
            internal_note TEXT,
            idempotency_key VARCHAR(128) NOT NULL UNIQUE,
            retention_due_at TIMESTAMPTZ,
            ip_hash VARCHAR(64),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_rbpc_inquiries_exp ON rbpc_inquiries(experience_id, state)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_rbpc_inquiries_token ON rbpc_inquiries(opaque_token)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_rbpc_inquiries_ref ON rbpc_inquiries(public_ref)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_rbpc_inquiries_retention ON rbpc_inquiries(retention_due_at)")

    # 10. rbpc_events
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS rbpc_events (
            id UUID PRIMARY KEY,
            event_name VARCHAR(64) NOT NULL,
            anonymous_session_id VARCHAR(64) NOT NULL,
            story_id UUID REFERENCES rbpc_stories(id) ON DELETE SET NULL,
            experience_id UUID REFERENCES rbpc_experiences(id) ON DELETE SET NULL,
            occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            consent_scope VARCHAR(32) NOT NULL DEFAULT 'anonymous_telemetry'
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_rbpc_events_name ON rbpc_events(event_name, occurred_at)")

    # 11. rbpc_content_audit
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS rbpc_content_audit (
            id UUID PRIMARY KEY,
            entity_type VARCHAR(64) NOT NULL,
            entity_id UUID NOT NULL,
            action VARCHAR(64) NOT NULL,
            actor_id UUID,
            previous_hash VARCHAR(64),
            new_hash VARCHAR(64),
            diff_payload JSONB,
            approved_scope VARCHAR(32) NOT NULL DEFAULT 'RBPC_HUE',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_rbpc_audit_entity ON rbpc_content_audit(entity_type, entity_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_rbpc_audit_action ON rbpc_content_audit(action)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_rbpc_audit_created ON rbpc_content_audit(created_at)")


def downgrade() -> None:
    # Strictly additive migration in production; rollback supported for testing
    op.execute("DROP TABLE IF EXISTS rbpc_content_audit")
    op.execute("DROP TABLE IF EXISTS rbpc_events")
    op.execute("DROP TABLE IF EXISTS rbpc_inquiries")
    op.execute("DROP TABLE IF EXISTS rbpc_claim_evidence")
    op.execute("DROP TABLE IF EXISTS rbpc_stories")
    op.execute("DROP TABLE IF EXISTS rbpc_experiences")
    op.execute("DROP TABLE IF EXISTS rbpc_creators")
    op.execute("DROP TABLE IF EXISTS heritage_media_assets")
    op.execute("DROP TABLE IF EXISTS heritage_source_evidence")
    op.execute("DROP TABLE IF EXISTS heritage_heritage_relations")
    op.execute("DROP TABLE IF EXISTS heritage_places")
