#!/usr/bin/env bash
# =============================================================================
# Automated PostgreSQL Database Backup Script for Luuniensuki LMS
# Dumps PostgreSQL schema and data, compresses with gzip, computes SHA-256
# checksum, and optionally encrypts with AES-256-CBC passphrase protection.
# =============================================================================
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

DB_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/luuniensuki_test}"
OUTPUT_DIR="${BACKUP_DIR:-${REPO_ROOT}/backups}"
PREFIX="lms_backup"
PASSPHRASE="${BACKUP_PASSPHRASE:-}"
CONTAINER="${POSTGRES_CONTAINER:-}"

usage() {
  cat <<'EOF'
Usage: ./scripts/backup/backup-database.sh [options]

Options:
  -d, --db-url <url>          Database URL (default: $DATABASE_URL or postgresql://postgres:postgres@localhost:5432/luuniensuki_test)
  -o, --output-dir <path>     Directory to store backup (default: ./backups)
  -p, --passphrase <secret>   Passphrase for AES-256-CBC encryption (optional)
  -c, --container <name>      Docker container name (auto-detected if omitted)
  --prefix <prefix>           Backup filename prefix (default: lms_backup)
  -h, --help                  Show this help

Environment variables:
  DATABASE_URL                PostgreSQL connection URL
  BACKUP_DIR                  Target directory for archives
  BACKUP_PASSPHRASE           Passphrase for encryption
  POSTGRES_CONTAINER          Docker container name
EOF
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -d|--db-url)
      DB_URL="$2"
      shift 2
      ;;
    -o|--output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    -p|--passphrase)
      PASSPHRASE="$2"
      shift 2
      ;;
    -c|--container)
      CONTAINER="$2"
      shift 2
      ;;
    --prefix)
      PREFIX="$2"
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

export DATABASE_URL="${DB_URL}"
export PYTHONPATH="${REPO_ROOT}:${PYTHONPATH:-}"

CMD=(
  python3 "${SCRIPT_DIR}/backup_engine.py" backup
  --db-url "${DB_URL}"
  --output-dir "${OUTPUT_DIR}"
  --prefix "${PREFIX}"
)

if [[ -n "${PASSPHRASE}" ]]; then
  CMD+=(--passphrase "${PASSPHRASE}")
fi

if [[ -n "${CONTAINER}" ]]; then
  CMD+=(--container "${CONTAINER}")
fi

exec "${CMD[@]}"
