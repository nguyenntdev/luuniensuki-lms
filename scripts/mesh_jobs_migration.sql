-- Mesh processing jobs audit (Phase D — Gap 1: LiDAR scan ingest pipeline)
-- Tracks every invocation of tools/mesh-processor/process_mesh.py

BEGIN;

CREATE TABLE IF NOT EXISTS mesh_processing_jobs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    initiated_by_user_id uuid NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    urn_slug text,
    input_path text NOT NULL,
    input_bytes bigint NOT NULL,
    output_path text,
    output_bytes bigint,
    target_lod text,
    target_ratio numeric(5,4),
    status text NOT NULL CHECK (status IN ('pending','running','succeeded','failed')),
    error_message text,
    elapsed_ms integer,
    size_reduction_pct numeric(5,2),
    faces_initial integer,
    faces_final integer,
    vertices_initial integer,
    vertices_final integer,
    pipeline_summary jsonb,
    started_at timestamptz NOT NULL DEFAULT NOW(),
    finished_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mesh_jobs_user ON mesh_processing_jobs(initiated_by_user_id);
CREATE INDEX IF NOT EXISTS idx_mesh_jobs_status ON mesh_processing_jobs(status);
CREATE INDEX IF NOT EXISTS idx_mesh_jobs_started_at ON mesh_processing_jobs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_mesh_jobs_urn ON mesh_processing_jobs(urn_slug);

COMMIT;
