#!/bin/bash
# One-shot helper to record a manual mesh-processor run in mesh_processing_jobs.
# Reads /tmp/mesh_run.json (the last summary from process_mesh.py) and inserts
# a 'succeeded' audit row. Used after Phase D for seeding the admin dashboard.
set -euo pipefail
ACTOR_ID="${ACTOR_ID:-1df31222-3934-471c-8624-a87034fd017d}"
INPUT_PATH="${INPUT_PATH:-/opt/luuniensuki-lms/models_upload/CAO-DINH-v1-2k.glb}"
OUTPUT_PATH="${OUTPUT_PATH:-/opt/luuniensuki-lms/models_upload/processed/cao-dinh-v1-512.glb}"
SUMMARY_FILE="${SUMMARY_FILE:-/tmp/mesh_run.json}"

cd "$(dirname "$0")/.."

SUMMARY="$(tr -d '\n' < "$SUMMARY_FILE")"
INPUT_BYTES=$(python3 -c "import json,sys; print(json.load(open('$SUMMARY_FILE')).get('input_bytes',0))")
OUTPUT_BYTES=$(python3 -c "import json,sys; print(json.load(open('$SUMMARY_FILE')).get('output_bytes',0))")
SIZE_RED=$(python3 -c "import json,sys; print(json.load(open('$SUMMARY_FILE')).get('size_reduction_pct',0))")
FACES_INIT=$(python3 -c "import json,sys; print(json.load(open('$SUMMARY_FILE')).get('faces_initial',0))")
FACES_FINAL=$(python3 -c "import json,sys; print(json.load(open('$SUMMARY_FILE')).get('faces_final',0))")
ELAPSED=$(python3 -c "import json,sys; print(json.load(open('$SUMMARY_FILE')).get('elapsed_ms',0))")
URN_SLUG="${URN_SLUG:-cao-dinh}"
LOD_LABEL="${LOD_LABEL:-512}"

# Escape single quotes for SQL.
SUMMARY_SQL="${SUMMARY//\'/\'\'}"

docker compose exec -T db psql -U postgres -d luuniensuki <<SQL
INSERT INTO mesh_processing_jobs
    (actor_user_id, urn_slug, input_path, output_path,
     lod_label, fill_holes, smooth_iter, status,
     started_at, completed_at,
     input_bytes, output_bytes, size_reduction_pct,
     faces_initial, faces_final, elapsed_ms,
     summary_json, error_message)
VALUES
    ('${ACTOR_ID}'::uuid, '${URN_SLUG}', '${INPUT_PATH}', '${OUTPUT_PATH}',
     '${LOD_LABEL}', true, 5, 'succeeded',
     NOW() - (${ELAPSED} || ' milliseconds')::interval, NOW(),
     ${INPUT_BYTES}, ${OUTPUT_BYTES}, ${SIZE_RED},
     ${FACES_INIT}, ${FACES_FINAL}, ${ELAPSED},
     '${SUMMARY_SQL}'::jsonb, NULL);
SELECT id, urn_slug, lod_label, status, size_reduction_pct, faces_initial, faces_final, elapsed_ms
FROM mesh_processing_jobs
ORDER BY created_at DESC
LIMIT 1;
SQL
