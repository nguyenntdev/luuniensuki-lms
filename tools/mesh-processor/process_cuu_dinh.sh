#!/usr/bin/env bash
# Batch-reprocess the 9 Cửu Đỉnh GLBs at all 3 LOD levels.
#
# Reads from models_upload/CAO-DINH-v1-2k.glb (or any 2k baseline) and
# writes denoised + decimated outputs to a configurable target dir.
#
# Usage:
#   ./process_cuu_dinh.sh [INPUT_DIR] [OUTPUT_DIR]
#
# Defaults:
#   INPUT_DIR  = /opt/luuniensuki-lms/models_upload
#   OUTPUT_DIR = /opt/luuniensuki-lms/models_upload/processed
#
# This batches the paper's pipeline across all 9 dingsi (urns) at 3 LOD
# levels each. The output directory is created if it does not exist.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_DIR="${1:-/opt/luuniensuki-lms/models_upload}"
OUTPUT_DIR="${2:-/opt/luuniensuki-lms/models_upload/processed}"
PYTHON="${SCRIPT_DIR}/venv/bin/python"
PROCESS="${SCRIPT_DIR}/process_mesh.py"

if [[ ! -x "${PYTHON}" ]]; then
    echo "ERROR: venv missing at ${PYTHON}. Run setup first." >&2
    exit 1
fi

mkdir -p "${OUTPUT_DIR}"

# 9 Cửu Đỉnh slugs (matches DB urn slugs).
URNS=(cao-dinh nhan-dinh chuong-dinh anh-dinh nghi-dinh thuan-dinh tuyen-dinh du-dinh huyen-dinh)
LODS=(2k 1k 512)

processed=0
failed=0

for urn in "${URNS[@]}"; do
    # Look for any of these baseline patterns in the input dir.
    candidates=(
        "${INPUT_DIR}/${urn}-v1-2k.glb"
        "${INPUT_DIR}/${urn^^}-v1-2k.glb"
        "${INPUT_DIR}/${urn}.glb"
    )
    input_path=""
    for c in "${candidates[@]}"; do
        if [[ -f "${c}" ]]; then
            input_path="${c}"
            break
        fi
    done

    if [[ -z "${input_path}" ]]; then
        echo "[SKIP] no baseline GLB found for urn=${urn}" >&2
        continue
    fi

    for lod in "${LODS[@]}"; do
        out="${OUTPUT_DIR}/${urn}-v1-${lod}.glb"
        echo "→ Processing ${urn} @ LOD ${lod}: ${input_path} → ${out}"
        if "${PYTHON}" "${PROCESS}" "${input_path}" --output "${out}" --lod "${lod}" --fill-holes --quiet 2>&1; then
            processed=$((processed + 1))
        else
            failed=$((failed + 1))
            echo "  [FAIL] urn=${urn} lod=${lod}" >&2
        fi
    done
done

echo ""
echo "=== Batch complete ==="
echo "Processed: ${processed}"
echo "Failed:    ${failed}"
echo "Output:    ${OUTPUT_DIR}"
