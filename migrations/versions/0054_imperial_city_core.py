"""imperial city core — zones, sites, aerial map assets, annotations, paths, activities, media

STTTNNĐ (Lưu Niên — Đại Nội Huế) Phase 1:
Creates the 13 core domain model tables for the Imperial City of Hue:
- imperial_zones               — monumental zones / axes within the Imperial City
- imperial_sites               — architectural monuments / sites with pedagogical metadata
- imperial_map_assets          — high-resolution aerial photographic/reconstructed maps
- imperial_map_annotations     — normalized UV marker and polygon annotations
- imperial_annotation_links    — links between annotations and pedagogical targets
- imperial_annotation_audit    — append-only audit trail for map curation actions
- imperial_lenses              — pedagogical thematic lenses
- imperial_lens_sites          — associations between lenses and monument sites
- imperial_learning_paths      — curated thematic walking and learning trails
- imperial_path_steps          — step-by-step tasks along a learning path
- imperial_activities          — pedagogical inquiry activities / assignments
- imperial_submissions         — student submissions for activities
- imperial_media               — verified historical photographs, drawings, and media

All additive and strictly scoped to content_scope = 'STTT_IMPERIAL_CITY'.

Revision ID: 0054_imperial_city_core
Revises: 0053_user_mission_quest_compound_indexes
Create Date: 2026-10-15
"""
from __future__ import annotations

from alembic import op


revision = "0054_imperial_city_core"
down_revision = "0053_user_mission_quest_compound_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # 1. imperial_zones
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS imperial_zones (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            content_scope TEXT NOT NULL DEFAULT 'STTT_IMPERIAL_CITY',
            slug          TEXT NOT NULL,
            title_vi      TEXT NOT NULL,
            title_en      TEXT,
            description   TEXT,
            display_order INTEGER NOT NULL DEFAULT 0,
            created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
            row_version   INTEGER NOT NULL DEFAULT 1,
            CONSTRAINT ck_imperial_zones_scope CHECK (content_scope = 'STTT_IMPERIAL_CITY'),
            CONSTRAINT uq_imperial_zones_slug UNIQUE (slug)
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_zones_order ON imperial_zones(display_order);")

    # ------------------------------------------------------------------ #
    # 2. imperial_sites
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS imperial_sites (
            id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            content_scope          TEXT NOT NULL DEFAULT 'STTT_IMPERIAL_CITY',
            zone_id                UUID NOT NULL REFERENCES imperial_zones(id) ON DELETE RESTRICT,
            slug                   TEXT NOT NULL,
            name_vi                TEXT NOT NULL,
            name_en                TEXT,
            name_han_nom           TEXT,
            alternative_names      JSONB NOT NULL DEFAULT '[]'::jsonb,
            site_type              TEXT NOT NULL DEFAULT 'palace',
            condition              TEXT NOT NULL DEFAULT 'extant',
            learning_level         TEXT NOT NULL DEFAULT 'L1_DOCUMENTED',
            summary_vi             TEXT,
            summary_en             TEXT,
            historical_context     TEXT,
            architectural_features TEXT,
            construction_year      INTEGER,
            latitude               DOUBLE PRECISION,
            longitude              DOUBLE PRECISION,
            is_published           BOOLEAN NOT NULL DEFAULT FALSE,
            published_at           TIMESTAMPTZ,
            display_order          INTEGER NOT NULL DEFAULT 0,
            created_by             UUID REFERENCES users(id) ON DELETE SET NULL,
            updated_by             UUID REFERENCES users(id) ON DELETE SET NULL,
            created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
            row_version            INTEGER NOT NULL DEFAULT 1,
            CONSTRAINT ck_imperial_sites_scope CHECK (content_scope = 'STTT_IMPERIAL_CITY'),
            CONSTRAINT uq_imperial_sites_slug UNIQUE (slug)
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_sites_zone ON imperial_sites(zone_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_sites_published ON imperial_sites(is_published);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_sites_level ON imperial_sites(learning_level);")

    # ------------------------------------------------------------------ #
    # 3. imperial_map_assets
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS imperial_map_assets (
            id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            content_scope        TEXT NOT NULL DEFAULT 'STTT_IMPERIAL_CITY',
            title_vi             TEXT NOT NULL,
            title_en             TEXT,
            slug                 TEXT NOT NULL,
            version              INTEGER NOT NULL DEFAULT 1,
            image_storage_key    TEXT NOT NULL,
            preview_storage_key  TEXT,
            image_sha256         CHAR(64) NOT NULL,
            mime_type            TEXT NOT NULL,
            width_px             INTEGER NOT NULL,
            height_px            INTEGER NOT NULL,
            source_title         TEXT NOT NULL,
            source_locator       TEXT,
            copyright_holder     TEXT,
            credit_text          TEXT NOT NULL,
            license_kind         TEXT NOT NULL,
            license_evidence_key TEXT,
            license_status       TEXT NOT NULL DEFAULT 'pending',
            review_status        TEXT NOT NULL DEFAULT 'draft',
            is_active            BOOLEAN NOT NULL DEFAULT FALSE,
            created_by           UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            approved_by          UUID REFERENCES users(id) ON DELETE SET NULL,
            created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
            published_at         TIMESTAMPTZ,
            row_version          INTEGER NOT NULL DEFAULT 1,
            CONSTRAINT ck_imperial_map_assets_scope CHECK (content_scope = 'STTT_IMPERIAL_CITY'),
            CONSTRAINT ck_imperial_map_assets_version CHECK (version > 0),
            CONSTRAINT ck_imperial_map_assets_mime CHECK (mime_type IN ('image/jpeg','image/png','image/webp')),
            CONSTRAINT ck_imperial_map_assets_width CHECK (width_px BETWEEN 1 AND 100000),
            CONSTRAINT ck_imperial_map_assets_height CHECK (height_px BETWEEN 1 AND 100000),
            CONSTRAINT ck_imperial_map_assets_license_status CHECK (license_status IN ('pending','approved','rejected')),
            CONSTRAINT ck_imperial_map_assets_review_status CHECK (review_status IN ('draft','in_review','approved','published','archived')),
            CONSTRAINT uq_imperial_map_assets_scope_slug_version UNIQUE (content_scope, slug, version)
        );
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_imperial_active_map
        ON imperial_map_assets (content_scope)
        WHERE is_active = TRUE;
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_map_assets_review ON imperial_map_assets(review_status);")

    # ------------------------------------------------------------------ #
    # 4. imperial_map_annotations
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS imperial_map_annotations (
            id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            content_scope       TEXT NOT NULL DEFAULT 'STTT_IMPERIAL_CITY',
            map_asset_id        UUID NOT NULL REFERENCES imperial_map_assets(id) ON DELETE RESTRICT,
            site_id             UUID NOT NULL REFERENCES imperial_sites(id) ON DELETE RESTRICT,
            shape_type          TEXT NOT NULL DEFAULT 'point',
            u                   NUMERIC(9,7) NOT NULL,
            v                   NUMERIC(9,7) NOT NULL,
            polygon_uv          JSONB,
            label               TEXT,
            marker_style        TEXT NOT NULL DEFAULT 'monument',
            z_index             INTEGER NOT NULL DEFAULT 0,
            is_visible          BOOLEAN NOT NULL DEFAULT TRUE,
            review_status       TEXT NOT NULL DEFAULT 'draft',
            position_confidence TEXT NOT NULL DEFAULT 'approximate',
            position_source_ref TEXT,
            editorial_notes     TEXT,
            created_by          UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            updated_by          UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            approved_by         UUID REFERENCES users(id) ON DELETE SET NULL,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
            published_at        TIMESTAMPTZ,
            row_version         INTEGER NOT NULL DEFAULT 1,
            CONSTRAINT ck_imperial_map_annotations_scope CHECK (content_scope = 'STTT_IMPERIAL_CITY'),
            CONSTRAINT ck_imperial_map_annotations_shape CHECK (shape_type IN ('point','polygon','bbox')),
            CONSTRAINT ck_imperial_map_annotations_u_range CHECK (u >= 0.0 AND u <= 1.0),
            CONSTRAINT ck_imperial_map_annotations_v_range CHECK (v >= 0.0 AND v <= 1.0),
            CONSTRAINT ck_imperial_map_annotations_review_status CHECK (review_status IN ('draft','in_review','approved','published','archived')),
            CONSTRAINT ck_imperial_map_annotations_confidence CHECK (position_confidence IN ('verified','approximate','uncertain')),
            CONSTRAINT uq_imperial_map_annotations_asset_site UNIQUE (map_asset_id, site_id)
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_map_annotations_asset ON imperial_map_annotations(map_asset_id, review_status);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_map_annotations_site ON imperial_map_annotations(site_id);")

    # ------------------------------------------------------------------ #
    # 5. imperial_annotation_links
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS imperial_annotation_links (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            content_scope TEXT NOT NULL DEFAULT 'STTT_IMPERIAL_CITY',
            annotation_id UUID NOT NULL REFERENCES imperial_map_annotations(id) ON DELETE CASCADE,
            target_type   TEXT NOT NULL,
            target_id     UUID NOT NULL,
            sort_order    INTEGER NOT NULL DEFAULT 0,
            CONSTRAINT ck_imperial_annotation_links_scope CHECK (content_scope = 'STTT_IMPERIAL_CITY'),
            CONSTRAINT ck_imperial_annotation_links_target_type CHECK (target_type IN ('story','lesson','source','quiz','activity','trail')),
            CONSTRAINT uq_imperial_annotation_links_target UNIQUE (annotation_id, target_type, target_id)
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_annotation_links_target ON imperial_annotation_links(target_type, target_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_annotation_links_annotation ON imperial_annotation_links(annotation_id);")

    # ------------------------------------------------------------------ #
    # 6. imperial_annotation_audit
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS imperial_annotation_audit (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            content_scope TEXT NOT NULL DEFAULT 'STTT_IMPERIAL_CITY',
            annotation_id UUID NOT NULL REFERENCES imperial_map_annotations(id) ON DELETE CASCADE,
            actor_id      UUID REFERENCES users(id) ON DELETE SET NULL,
            action        TEXT NOT NULL,
            before_json   JSONB,
            after_json    JSONB,
            created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_imperial_annotation_audit_scope CHECK (content_scope = 'STTT_IMPERIAL_CITY')
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_annotation_audit_annotation ON imperial_annotation_audit(annotation_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_annotation_audit_created ON imperial_annotation_audit(created_at);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_annotation_audit_actor ON imperial_annotation_audit(actor_id);")

    # ------------------------------------------------------------------ #
    # 7. imperial_lenses
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS imperial_lenses (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            content_scope TEXT NOT NULL DEFAULT 'STTT_IMPERIAL_CITY',
            code          TEXT NOT NULL,
            title         TEXT NOT NULL,
            title_en      TEXT,
            description   TEXT,
            prompt        TEXT,
            icon          TEXT,
            color         TEXT,
            display_order INTEGER NOT NULL DEFAULT 0,
            is_active     BOOLEAN NOT NULL DEFAULT TRUE,
            created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
            row_version   INTEGER NOT NULL DEFAULT 1,
            CONSTRAINT ck_imperial_lenses_scope CHECK (content_scope = 'STTT_IMPERIAL_CITY'),
            CONSTRAINT uq_imperial_lenses_code UNIQUE (code)
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_lenses_active ON imperial_lenses(is_active);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_lenses_order ON imperial_lenses(display_order);")

    # ------------------------------------------------------------------ #
    # 8. imperial_lens_sites
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS imperial_lens_sites (
            id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            content_scope    TEXT NOT NULL DEFAULT 'STTT_IMPERIAL_CITY',
            lens_id          UUID NOT NULL REFERENCES imperial_lenses(id) ON DELETE CASCADE,
            site_id          UUID NOT NULL REFERENCES imperial_sites(id) ON DELETE CASCADE,
            relevance_score  DOUBLE PRECISION NOT NULL DEFAULT 1.0,
            sequence         INTEGER NOT NULL DEFAULT 0,
            curatorial_notes TEXT,
            CONSTRAINT ck_imperial_lens_sites_scope CHECK (content_scope = 'STTT_IMPERIAL_CITY'),
            CONSTRAINT uq_imperial_lens_sites_lens_site UNIQUE (lens_id, site_id)
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_lens_sites_lens ON imperial_lens_sites(lens_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_lens_sites_site ON imperial_lens_sites(site_id);")

    # ------------------------------------------------------------------ #
    # 9. imperial_learning_paths
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS imperial_learning_paths (
            id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            content_scope       TEXT NOT NULL DEFAULT 'STTT_IMPERIAL_CITY',
            slug                TEXT NOT NULL,
            title               TEXT NOT NULL,
            title_en            TEXT,
            description         TEXT,
            kind                TEXT NOT NULL DEFAULT 'standard',
            duration_min        INTEGER NOT NULL DEFAULT 45,
            age_group           TEXT NOT NULL DEFAULT 'all',
            learning_objectives JSONB NOT NULL DEFAULT '[]'::jsonb,
            prerequisites       TEXT,
            review_status       TEXT NOT NULL DEFAULT 'draft',
            is_published        BOOLEAN NOT NULL DEFAULT FALSE,
            display_order       INTEGER NOT NULL DEFAULT 0,
            created_by          UUID REFERENCES users(id) ON DELETE SET NULL,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
            row_version         INTEGER NOT NULL DEFAULT 1,
            CONSTRAINT ck_imperial_learning_paths_scope CHECK (content_scope = 'STTT_IMPERIAL_CITY'),
            CONSTRAINT ck_imperial_learning_paths_review CHECK (review_status IN ('draft','published','archived')),
            CONSTRAINT uq_imperial_learning_paths_slug UNIQUE (slug)
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_learning_paths_published ON imperial_learning_paths(is_published);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_learning_paths_order ON imperial_learning_paths(display_order);")

    # ------------------------------------------------------------------ #
    # 10. imperial_path_steps
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS imperial_path_steps (
            id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            content_scope      TEXT NOT NULL DEFAULT 'STTT_IMPERIAL_CITY',
            path_id            UUID NOT NULL REFERENCES imperial_learning_paths(id) ON DELETE CASCADE,
            site_id            UUID NOT NULL REFERENCES imperial_sites(id) ON DELETE RESTRICT,
            step_order         INTEGER NOT NULL DEFAULT 0,
            title              TEXT,
            prompt             TEXT NOT NULL,
            source_requirement TEXT,
            rubrics            JSONB,
            estimated_minutes  INTEGER NOT NULL DEFAULT 10,
            CONSTRAINT ck_imperial_path_steps_scope CHECK (content_scope = 'STTT_IMPERIAL_CITY'),
            CONSTRAINT uq_imperial_path_steps_order UNIQUE (path_id, step_order)
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_path_steps_path ON imperial_path_steps(path_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_path_steps_site ON imperial_path_steps(site_id);")

    # ------------------------------------------------------------------ #
    # 11. imperial_activities
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS imperial_activities (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            content_scope TEXT NOT NULL DEFAULT 'STTT_IMPERIAL_CITY',
            site_id       UUID REFERENCES imperial_sites(id) ON DELETE SET NULL,
            path_id       UUID REFERENCES imperial_learning_paths(id) ON DELETE SET NULL,
            activity_type TEXT NOT NULL DEFAULT 'evidence_reflection',
            title         TEXT NOT NULL,
            instructions  TEXT NOT NULL,
            rubric_json   JSONB,
            max_points    INTEGER NOT NULL DEFAULT 100,
            is_active     BOOLEAN NOT NULL DEFAULT TRUE,
            created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
            row_version   INTEGER NOT NULL DEFAULT 1,
            CONSTRAINT ck_imperial_activities_scope CHECK (content_scope = 'STTT_IMPERIAL_CITY')
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_activities_site ON imperial_activities(site_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_activities_path ON imperial_activities(path_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_activities_active ON imperial_activities(is_active);")

    # ------------------------------------------------------------------ #
    # 12. imperial_submissions
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS imperial_submissions (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            content_scope TEXT NOT NULL DEFAULT 'STTT_IMPERIAL_CITY',
            activity_id   UUID NOT NULL REFERENCES imperial_activities(id) ON DELETE CASCADE,
            student_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            classroom_id  UUID REFERENCES classes(id) ON DELETE SET NULL,
            status        TEXT NOT NULL DEFAULT 'submitted',
            answer_text   TEXT NOT NULL,
            evidence_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
            score         DOUBLE PRECISION,
            rubric_scores JSONB NOT NULL DEFAULT '{}'::jsonb,
            feedback      TEXT,
            graded_by     UUID REFERENCES users(id) ON DELETE SET NULL,
            graded_at     TIMESTAMPTZ,
            submitted_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
            row_version   INTEGER NOT NULL DEFAULT 1,
            CONSTRAINT ck_imperial_submissions_scope CHECK (content_scope = 'STTT_IMPERIAL_CITY'),
            CONSTRAINT ck_imperial_submissions_status CHECK (status IN ('submitted','graded','resubmit_requested'))
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_submissions_student ON imperial_submissions(student_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_submissions_activity ON imperial_submissions(activity_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_submissions_classroom ON imperial_submissions(classroom_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_submissions_status ON imperial_submissions(status);")

    # ------------------------------------------------------------------ #
    # 13. imperial_media
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS imperial_media (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            content_scope   TEXT NOT NULL DEFAULT 'STTT_IMPERIAL_CITY',
            site_id         UUID NOT NULL REFERENCES imperial_sites(id) ON DELETE CASCADE,
            media_kind      TEXT NOT NULL DEFAULT 'photo',
            url             TEXT NOT NULL,
            thumbnail_url   TEXT,
            title           TEXT,
            description     TEXT,
            alt_text        TEXT,
            license         TEXT NOT NULL,
            owner           TEXT,
            credit          TEXT NOT NULL,
            historical_year INTEGER,
            is_published    BOOLEAN NOT NULL DEFAULT FALSE,
            display_order   INTEGER NOT NULL DEFAULT 0,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            row_version     INTEGER NOT NULL DEFAULT 1,
            CONSTRAINT ck_imperial_media_scope CHECK (content_scope = 'STTT_IMPERIAL_CITY')
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_media_site ON imperial_media(site_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_media_published ON imperial_media(is_published);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_media_order ON imperial_media(display_order);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS imperial_media;")
    op.execute("DROP TABLE IF EXISTS imperial_submissions;")
    op.execute("DROP TABLE IF EXISTS imperial_activities;")
    op.execute("DROP TABLE IF EXISTS imperial_path_steps;")
    op.execute("DROP TABLE IF EXISTS imperial_learning_paths;")
    op.execute("DROP TABLE IF EXISTS imperial_lens_sites;")
    op.execute("DROP TABLE IF EXISTS imperial_lenses;")
    op.execute("DROP TABLE IF EXISTS imperial_annotation_audit;")
    op.execute("DROP TABLE IF EXISTS imperial_annotation_links;")
    op.execute("DROP TABLE IF EXISTS imperial_map_annotations;")
    op.execute("DROP TABLE IF EXISTS imperial_map_assets;")
    op.execute("DROP TABLE IF EXISTS imperial_sites;")
    op.execute("DROP TABLE IF EXISTS imperial_zones;")
