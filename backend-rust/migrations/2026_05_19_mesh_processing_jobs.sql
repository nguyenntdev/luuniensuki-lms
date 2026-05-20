-- Gap 1: LiDAR scan ingest pipeline — audit table for mesh-processor jobs.
-- Spec: docs/CONFERENCE_PAPER_MATCH_ANALYSIS.md Gap 1.
--
-- Apply on prod:
--   docker exec -i luuniensuki-lms-db-1 psql -U postgres -d luuniensuki \
--     < backend-rust/migrations/2026_05_19_mesh_processing_jobs.sql

CREATE TABLE IF NOT EXISTS mesh_processing_jobs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_user_id uuid NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    urn_slug text,
    input_path text NOT NULL,
    output_path text NOT NULL,
    lod_label text NOT NULL CHECK (lod_label IN ('512','1k','2k')),
    fill_holes boolean NOT NULL DEFAULT true,
    smooth_iter integer NOT NULL DEFAULT 5,
    status text NOT NULL CHECK (status IN ('pending','running','succeeded','failed')),
    started_at timestamptz NOT NULL DEFAULT NOW(),
    completed_at timestamptz,
    input_bytes bigint,
    output_bytes bigint,
    size_reduction_pct numeric(5,2),
    faces_initial bigint,
    faces_final bigint,
    elapsed_ms integer,
    summary_json jsonb,
    error_message text,
    created_at timestamptz NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mesh_jobs_actor   ON mesh_processing_jobs(actor_user_id);
CREATE INDEX IF NOT EXISTS idx_mesh_jobs_started ON mesh_processing_jobs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_mesh_jobs_status  ON mesh_processing_jobs(status);
