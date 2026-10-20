"""imperial v5.1 extensions — learning media, hotspots, art details, clues, questions, assignments

STTTNNĐ (Lưu Niên — Đại Nội Huế) Phase V5.1:
Creates 9 domain model tables for V5.1 modules:
- imperial_learning_media             — photos, 360 panoramas, and 3D models for sites
- imperial_art_details                — decorative art details, carvings, patterns, mosaics
- imperial_media_hotspots             — UV hotspot points/regions on learning media linking to art details
- imperial_art_detail_claim_sources   — primary source evidence and citations for art details
- imperial_art_detail_questions       — inquiry questions attached to art details
- imperial_clues                      — heritage detective clues and riddles
- imperial_clue_attempts              — student attempts at solving detective clues
- imperial_questions                  — interactive gamified quiz questions
- imperial_assignment_releases        — teacher assignments and journey releases for classrooms

All additive and strictly scoped to content_scope = 'STTT_IMPERIAL_CITY'.

Revision ID: 0055_imperial_v51_extensions
Revises: 0054_imperial_city_core
Create Date: 2026-10-16
"""
from __future__ import annotations

from alembic import op


revision = "0055_imperial_v51_extensions"
down_revision = "0054_imperial_city_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # 1. imperial_learning_media
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS imperial_learning_media (
            id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            content_scope  TEXT NOT NULL DEFAULT 'STTT_IMPERIAL_CITY',
            site_id        UUID NOT NULL REFERENCES imperial_sites(id) ON DELETE CASCADE,
            kind           TEXT NOT NULL DEFAULT 'image',
            media_url      TEXT NOT NULL,
            thumbnail_url  TEXT,
            asset_revision INTEGER NOT NULL DEFAULT 1,
            width_px       INTEGER,
            height_px      INTEGER,
            license_status TEXT NOT NULL DEFAULT 'pending',
            review_status  TEXT NOT NULL DEFAULT 'draft',
            alt_text       TEXT,
            credit_text    TEXT,
            asset_context  TEXT NOT NULL DEFAULT 'extant',
            created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
            row_version    INTEGER NOT NULL DEFAULT 1,
            CONSTRAINT ck_imperial_learning_media_scope CHECK (content_scope = 'STTT_IMPERIAL_CITY'),
            CONSTRAINT ck_imperial_learning_media_kind CHECK (kind IN ('image', 'panorama360', 'model3d')),
            CONSTRAINT ck_imperial_learning_media_license CHECK (license_status IN ('pending', 'approved', 'rejected')),
            CONSTRAINT ck_imperial_learning_media_review CHECK (review_status IN ('draft', 'in_review', 'approved', 'published', 'archived')),
            CONSTRAINT ck_imperial_learning_media_context CHECK (asset_context IN ('extant', 'historical_photo', 'restoration_drawing'))
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_learning_media_site ON imperial_learning_media(site_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_learning_media_review ON imperial_learning_media(review_status);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_learning_media_kind ON imperial_learning_media(kind);")

    # ------------------------------------------------------------------ #
    # 2. imperial_art_details
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS imperial_art_details (
            id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            content_scope           TEXT NOT NULL DEFAULT 'STTT_IMPERIAL_CITY',
            site_id                 UUID NOT NULL REFERENCES imperial_sites(id) ON DELETE CASCADE,
            title                   TEXT NOT NULL,
            slug                    TEXT NOT NULL,
            kind                    TEXT NOT NULL DEFAULT 'carving',
            motif                   TEXT,
            material                TEXT,
            technique               TEXT,
            description_observation TEXT,
            story_body              TEXT,
            story_type              TEXT NOT NULL DEFAULT 'documented_event',
            meaning_body            TEXT,
            historical_value_body   TEXT,
            cultural_value_body     TEXT,
            art_value_body          TEXT,
            review_status           TEXT NOT NULL DEFAULT 'draft',
            content_revision        INTEGER NOT NULL DEFAULT 1,
            created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
            row_version             INTEGER NOT NULL DEFAULT 1,
            CONSTRAINT ck_imperial_art_details_scope CHECK (content_scope = 'STTT_IMPERIAL_CITY'),
            CONSTRAINT ck_imperial_art_details_kind CHECK (kind IN ('carving', 'pattern', 'painting', 'mosaic', 'relief')),
            CONSTRAINT ck_imperial_art_details_story_type CHECK (story_type IN ('documented_event', 'legend', 'oral_account', 'interpretation')),
            CONSTRAINT ck_imperial_art_details_review CHECK (review_status IN ('draft', 'in_review', 'approved', 'published', 'archived')),
            CONSTRAINT uq_imperial_art_details_slug UNIQUE (slug)
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_art_details_site ON imperial_art_details(site_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_art_details_slug ON imperial_art_details(slug);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_art_details_kind ON imperial_art_details(kind);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_art_details_review ON imperial_art_details(review_status);")

    # ------------------------------------------------------------------ #
    # 3. imperial_media_hotspots
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS imperial_media_hotspots (
            id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            content_scope    TEXT NOT NULL DEFAULT 'STTT_IMPERIAL_CITY',
            media_id         UUID NOT NULL REFERENCES imperial_learning_media(id) ON DELETE CASCADE,
            point_kind       TEXT NOT NULL DEFAULT 'point',
            u                NUMERIC(9, 7) NOT NULL,
            v                NUMERIC(9, 7) NOT NULL,
            position_payload JSONB,
            title            TEXT NOT NULL,
            description      TEXT,
            detail_id        UUID REFERENCES imperial_art_details(id) ON DELETE SET NULL,
            review_status    TEXT NOT NULL DEFAULT 'draft',
            created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
            row_version      INTEGER NOT NULL DEFAULT 1,
            CONSTRAINT ck_imperial_media_hotspots_scope CHECK (content_scope = 'STTT_IMPERIAL_CITY'),
            CONSTRAINT ck_imperial_media_hotspots_point_kind CHECK (point_kind IN ('point', 'rect', 'polygon')),
            CONSTRAINT ck_imperial_media_hotspots_u_range CHECK (u >= 0.0 AND u <= 1.0),
            CONSTRAINT ck_imperial_media_hotspots_v_range CHECK (v >= 0.0 AND v <= 1.0),
            CONSTRAINT ck_imperial_media_hotspots_review CHECK (review_status IN ('draft', 'in_review', 'approved', 'published', 'archived'))
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_media_hotspots_media ON imperial_media_hotspots(media_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_media_hotspots_detail ON imperial_media_hotspots(detail_id);")

    # ------------------------------------------------------------------ #
    # 4. imperial_art_detail_claim_sources
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS imperial_art_detail_claim_sources (
            id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            content_scope     TEXT NOT NULL DEFAULT 'STTT_IMPERIAL_CITY',
            detail_id         UUID NOT NULL REFERENCES imperial_art_details(id) ON DELETE CASCADE,
            section           TEXT NOT NULL,
            claim_text        TEXT NOT NULL,
            source_title      TEXT NOT NULL,
            source_locator    TEXT,
            evidence_strength TEXT NOT NULL DEFAULT 'verified',
            created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_imperial_art_detail_claim_sources_scope CHECK (content_scope = 'STTT_IMPERIAL_CITY'),
            CONSTRAINT ck_imperial_art_detail_claim_sources_strength CHECK (evidence_strength IN ('verified', 'probable', 'traditional'))
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_art_detail_claim_sources_detail ON imperial_art_detail_claim_sources(detail_id);")

    # ------------------------------------------------------------------ #
    # 5. imperial_art_detail_questions
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS imperial_art_detail_questions (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            content_scope TEXT NOT NULL DEFAULT 'STTT_IMPERIAL_CITY',
            detail_id     UUID NOT NULL REFERENCES imperial_art_details(id) ON DELETE CASCADE,
            question_type TEXT NOT NULL DEFAULT 'multiple_choice',
            prompt        TEXT NOT NULL,
            options       JSONB NOT NULL DEFAULT '[]'::jsonb,
            answer_key    TEXT NOT NULL,
            explanation   TEXT,
            display_order INTEGER NOT NULL DEFAULT 0,
            created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_imperial_art_detail_questions_scope CHECK (content_scope = 'STTT_IMPERIAL_CITY')
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_art_detail_questions_detail ON imperial_art_detail_questions(detail_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_art_detail_questions_order ON imperial_art_detail_questions(display_order);")

    # ------------------------------------------------------------------ #
    # 6. imperial_clues
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS imperial_clues (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            content_scope TEXT NOT NULL DEFAULT 'STTT_IMPERIAL_CITY',
            title         TEXT NOT NULL,
            clue_text     TEXT NOT NULL,
            target_type   TEXT NOT NULL,
            target_id     UUID NOT NULL,
            hint_steps    JSONB NOT NULL DEFAULT '[]'::jsonb,
            grade_level   TEXT,
            difficulty    TEXT,
            review_status TEXT NOT NULL DEFAULT 'draft',
            created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
            row_version   INTEGER NOT NULL DEFAULT 1,
            CONSTRAINT ck_imperial_clues_scope CHECK (content_scope = 'STTT_IMPERIAL_CITY'),
            CONSTRAINT ck_imperial_clues_target_type CHECK (target_type IN ('site', 'art_detail')),
            CONSTRAINT ck_imperial_clues_review CHECK (review_status IN ('draft', 'in_review', 'approved', 'published', 'archived'))
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_clues_target ON imperial_clues(target_type, target_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_clues_review ON imperial_clues(review_status);")

    # ------------------------------------------------------------------ #
    # 7. imperial_clue_attempts
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS imperial_clue_attempts (
            id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            content_scope      TEXT NOT NULL DEFAULT 'STTT_IMPERIAL_CITY',
            clue_id            UUID NOT NULL REFERENCES imperial_clues(id) ON DELETE CASCADE,
            user_id            UUID REFERENCES users(id) ON DELETE SET NULL,
            selected_target_id UUID NOT NULL,
            is_correct         BOOLEAN NOT NULL,
            attempt_number     INTEGER NOT NULL DEFAULT 1,
            created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_imperial_clue_attempts_scope CHECK (content_scope = 'STTT_IMPERIAL_CITY')
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_clue_attempts_clue ON imperial_clue_attempts(clue_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_clue_attempts_user ON imperial_clue_attempts(user_id);")

    # ------------------------------------------------------------------ #
    # 8. imperial_questions
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS imperial_questions (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            content_scope   TEXT NOT NULL DEFAULT 'STTT_IMPERIAL_CITY',
            site_id         UUID REFERENCES imperial_sites(id) ON DELETE SET NULL,
            detail_id       UUID REFERENCES imperial_art_details(id) ON DELETE SET NULL,
            question_type   TEXT NOT NULL DEFAULT 'multiple_choice',
            prompt          TEXT NOT NULL,
            options         JSONB NOT NULL DEFAULT '[]'::jsonb,
            answer_key      TEXT NOT NULL,
            explanation_why TEXT,
            source_citation TEXT,
            review_status   TEXT NOT NULL DEFAULT 'draft',
            created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            row_version     INTEGER NOT NULL DEFAULT 1,
            CONSTRAINT ck_imperial_questions_scope CHECK (content_scope = 'STTT_IMPERIAL_CITY'),
            CONSTRAINT ck_imperial_questions_type CHECK (question_type IN ('multiple_choice', 'matching', 'hotspot_identify')),
            CONSTRAINT ck_imperial_questions_review CHECK (review_status IN ('draft', 'in_review', 'approved', 'published', 'archived'))
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_questions_site ON imperial_questions(site_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_questions_detail ON imperial_questions(detail_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_questions_review ON imperial_questions(review_status);")

    # ------------------------------------------------------------------ #
    # 9. imperial_assignment_releases
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS imperial_assignment_releases (
            id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            content_scope  TEXT NOT NULL DEFAULT 'STTT_IMPERIAL_CITY',
            teacher_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            class_name     TEXT NOT NULL,
            journey_slug   TEXT NOT NULL,
            title          TEXT NOT NULL,
            due_date       TIMESTAMPTZ,
            rubric_weights JSONB NOT NULL DEFAULT '{}'::jsonb,
            is_active      BOOLEAN NOT NULL DEFAULT TRUE,
            created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
            row_version    INTEGER NOT NULL DEFAULT 1,
            CONSTRAINT ck_imperial_assignment_releases_scope CHECK (content_scope = 'STTT_IMPERIAL_CITY')
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_assignment_releases_teacher ON imperial_assignment_releases(teacher_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_assignment_releases_journey ON imperial_assignment_releases(journey_slug);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_imperial_assignment_releases_active ON imperial_assignment_releases(is_active);")


def downgrade() -> None:
    # Additive-only policy per Spec Requirement 6.2 and lint-migration-safety.sh
    pass
