#!/usr/bin/env bash
# =============================================================================
# Database Restoration Rehearsal Script for Luuniensuki LMS
# Restores dump into disposable test database (luuniensuki_restore_drill),
# verifies exact table and row counts (users, heritage_places, historical_entities,
# rbpc_inquiries, etc.), enforces live DB protection, and generates a structured
# RPO / RTO verification report.
# =============================================================================
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

ARCHIVE=""
META=""
TARGET_DB="${RESTORE_DB:-luuniensuki_restore_drill}"
SOURCE_DB_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/luuniensuki_test}"
PASSPHRASE="${BACKUP_PASSPHRASE:-}"
REPORT_FILE="${REPORT_FILE:-}"
CONTAINER="${POSTGRES_CONTAINER:-}"

usage() {
  cat <<'EOF'
Usage: ./scripts/backup/restore-rehearsal.sh -a <archive_path> [options]

Required:
  -a, --archive <path>        Path to backup archive (.sql.gz or .sql.gz.enc)

Options:
  -t, --target-db <name>      Disposable drill database name (default: luuniensuki_restore_drill)
  -s, --source-db-url <url>   Source database URL to protect against accidental overwrite
  -m, --meta <path>           Path to metadata JSON file (auto-detected if omitted)
  -p, --passphrase <secret>   Passphrase for decryption (if backup is encrypted)
  -r, --report <path>         Path to write rehearsal report JSON
  -c, --container <name>      Docker container name (auto-detected if omitted)
  -h, --help                  Show this help

Safety Notice:
  This script will REFUSE to restore into any database matching the live source
  database name. Rehearsal restores are strictly isolated to disposable databases.
EOF
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -a|--archive)
      ARCHIVE="$2"
      shift 2
      ;;
    -t|--target-db)
      TARGET_DB="$2"
      shift 2
      ;;
    -s|--source-db-url)
      SOURCE_DB_URL="$2"
      shift 2
      ;;
    -m|--meta)
      META="$2"
      shift 2
      ;;
    -p|--passphrase)
      PASSPHRASE="$2"
      shift 2
      ;;
    -r|--report)
      REPORT_FILE="$2"
      shift 2
      ;;
    -c|--container)
      CONTAINER="$2"
      shift 2
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      ;;
  esac
done

if [[ -z "${ARCHIVE}" ]]; then
  echo "Error: --archive / -a is required." >&2
  usage
fi

export PYTHONPATH="${REPO_ROOT}:${PYTHONPATH:-}"

CMD=(
  python3 "${SCRIPT_DIR}/backup_engine.py" restore
  --archive "${ARCHIVE}"
  --target-db "${TARGET_DB}"
  --source-db-url "${SOURCE_DB_URL}"
)

if [[ -n "${META}" ]]; then
  CMD+=(--meta "${META}")
fi

if [[ -n "${PASSPHRASE}" ]]; then
  CMD+=(--passphrase "${PASSPHRASE}")
fi

if [[ -n "${REPORT_FILE}" ]]; then
  CMD+=(--report "${REPORT_FILE}")
fi

if [[ -n "${CONTAINER}" ]]; then
  CMD+=(--container "${CONTAINER}")
fi

exec "${CMD[@]}"
