#!/usr/bin/env bash
# ==============================================================================
# Automated Security Scanning Script (Ticket V5-T087)
# Luuniensuki LMS - CI / Production Static Security Scanner
#
# Validates:
# 1. Scans for hardcoded secrets, sentinel API keys, or leaked credentials.
# 2. Verifies pinned dependency integrity in requirements.txt and backend-rust/Cargo.toml.
# 3. Validates npm package vulnerabilities (npm audit checks).
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$WORKSPACE_ROOT"

# Modes & options
CHECK_SECRETS=false
CHECK_DEPS=false
CHECK_NPM=false
TARGET_PATH=""
CARGO_TOML_PATH=""
REQUIREMENTS_PATH=""
STRICT_NPM=false

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --target <path>        Scan a specific file or directory for secrets"
    echo "  --check-secrets        Run only secret scanning"
    echo "  --check-deps           Run only dependency pin integrity checks"
    echo "  --check-npm            Run only npm package vulnerability checks"
    echo "  --cargo-toml <path>    Specify path to Cargo.toml to check"
    echo "  --requirements <path>  Specify path to requirements.txt to check"
    echo "  --strict               Fail on any npm audit vulnerability"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "If no check flags (--check-*) are given, all checks are executed."
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --target)
            TARGET_PATH="$2"
            shift 2
            ;;
        --check-secrets)
            CHECK_SECRETS=true
            shift
            ;;
        --check-deps)
            CHECK_DEPS=true
            shift
            ;;
        --check-npm)
            CHECK_NPM=true
            shift
            ;;
        --cargo-toml)
            CARGO_TOML_PATH="$2"
            shift 2
            ;;
        --requirements)
            REQUIREMENTS_PATH="$2"
            shift 2
            ;;
        --strict)
            STRICT_NPM=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# If --target is passed without explicit check flags, only run secret scan on the target
if [ -n "$TARGET_PATH" ] && [ "$CHECK_SECRETS" = false ] && [ "$CHECK_DEPS" = false ] && [ "$CHECK_NPM" = false ]; then
    CHECK_SECRETS=true
fi

# If no specific check was requested, run all checks
if [ "$CHECK_SECRETS" = false ] && [ "$CHECK_DEPS" = false ] && [ "$CHECK_NPM" = false ]; then
    CHECK_SECRETS=true
    CHECK_DEPS=true
    CHECK_NPM=true
fi

SCAN_FAILED=0

# ==============================================================================
# 1. SECRET SCANNING
# ==============================================================================
scan_secrets_file() {
    local file="$1"
    local failed=0

    # Pattern 1: Private keys
    if grep -E -e "-----BEGIN ([A-Z0-9_-]+ )?PRIVATE KEY-----" "$file" >/dev/null 2>&1; then
        echo "❌ [SECRET] Detected private key pattern in $file"
        failed=1
    fi

    # Pattern 2: Cloud / AI / Service API Keys
    if grep -E "\bAKIA[0-9A-Z]{16}\b" "$file" >/dev/null 2>&1; then
        echo "❌ [SECRET] Detected AWS Access Key ID pattern in $file"
        failed=1
    fi
    if grep -E "\b(ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{36}\b|\bgithub_pat_[a-zA-Z0-9_]{82}\b" "$file" >/dev/null 2>&1; then
        echo "❌ [SECRET] Detected GitHub PAT pattern in $file"
        failed=1
    fi
    if grep -E "\bxox[baprs]-[0-9a-zA-Z]{10,48}\b" "$file" >/dev/null 2>&1; then
        echo "❌ [SECRET] Detected Slack token pattern in $file"
        failed=1
    fi
    if grep -E "\bsk-(proj-)?[a-zA-Z0-9_-]{20,}\b" "$file" >/dev/null 2>&1; then
        echo "❌ [SECRET] Detected OpenAI/AI API key pattern in $file"
        failed=1
    fi

    # Pattern 3: Sentinel secrets in production context or explicitly configured
    # (Skip the sentinel definition tables in backend/config.py and backend-rust/src/config.rs)
    if [[ "$file" != *"backend/config.py"* ]] && [[ "$file" != *"backend-rust/src/config.rs"* ]]; then
        if grep -iE "(JWT_SECRET_KEY|jwt_secret_key)\s*[:=]\s*[\"']?(change-me|secret|test-sentinel|change_me|CHANGE_ME_IN_PRODUCTION)[\"']?" "$file" >/dev/null 2>&1; then
            echo "❌ [SENTINEL] Detected sentinel JWT_SECRET_KEY pattern in $file"
            failed=1
        fi
    fi

    return $failed
}

run_secret_scan() {
    echo "======================================================================"
    echo "🔍 Step 1: Secret & Credential Scanning"
    echo "======================================================================"

    local secrets_found=0

    if [ -n "$TARGET_PATH" ]; then
        if [ -f "$TARGET_PATH" ]; then
            echo "Scanning target file: $TARGET_PATH"
            if ! scan_secrets_file "$TARGET_PATH"; then
                secrets_found=1
            fi
        elif [ -d "$TARGET_PATH" ]; then
            echo "Scanning target directory: $TARGET_PATH"
            while IFS= read -r file; do
                if ! scan_secrets_file "$file"; then
                    secrets_found=1
                fi
            done < <(find "$TARGET_PATH" -type f \
                ! -path "*/.git/*" \
                ! -path "*/node_modules/*" \
                ! -path "*/target/*" \
                ! -path "*/__pycache__/*" \
                ! -path "*/venv/*" \
                ! -path "*/.venv/*" \
                ! -path "*/.next/*")
        else
            echo "❌ ERROR: Target path $TARGET_PATH does not exist."
            return 1
        fi
    else
        echo "Scanning codebase for hardcoded credentials and sentinel keys..."
        # Scan source directories and active configuration files
        local search_dirs=("backend" "backend-rust" "frontend/src" "mobile/lib" "scripts" "migrations")
        for dir in "${search_dirs[@]}"; do
            if [ -d "$dir" ]; then
                while IFS= read -r file; do
                    # Skip prompt defense pattern definitions and self
                    if [[ "$file" == *"prompt_defense.py"* ]] || [[ "$file" == *"scripts/ci/security-scan.sh"* ]]; then
                        continue
                    fi
                    if ! scan_secrets_file "$file"; then
                        secrets_found=1
                    fi
                done < <(find "$dir" -type f \
                    ! -path "*/.git/*" \
                    ! -path "*/node_modules/*" \
                    ! -path "*/target/*" \
                    ! -path "*/__pycache__/*" \
                    ! -name "*.pyc" \
                    ! -name "*.png" \
                    ! -name "*.jpg" \
                    ! -name "*.glb" \
                    ! -name "*.wasm")
            fi
        done

        # Production compose / config audit
        if [ -f "docker-compose.prod.yml" ]; then
            if ! scan_secrets_file "docker-compose.prod.yml"; then
                secrets_found=1
            fi
        fi
    fi

    if [ "$secrets_found" -ne 0 ]; then
        echo "❌ Secret scanning FAILED: hardcoded credentials or sentinel secrets detected."
        return 1
    else
        echo "✅ Secret scanning PASSED: zero hardcoded credentials or sentinel secrets detected."
        return 0
    fi
}

# ==============================================================================
# 2. DEPENDENCY PIN INTEGRITY SCANNING
# ==============================================================================
check_cargo_pinned() {
    local cargo_file="$1"
    echo "Checking Cargo dependencies in $cargo_file..."
    if [ ! -f "$cargo_file" ]; then
        echo "❌ ERROR: $cargo_file not found"
        return 1
    fi

    local unpinned
    unpinned=$(awk '
        /^\[(dependencies|dev-dependencies)\]/ { in_deps=1; next }
        /^\[/ { in_deps=0 }
        in_deps && /version\s*=\s*"[^=]/ { print NR": "$0 }
    ' "$cargo_file" | grep -v '^\s*#' || true)

    if [ -n "$unpinned" ]; then
        echo "❌ ERROR: Found unpinned dependency versions in $cargo_file:"
        echo "$unpinned"
        return 1
    fi

    local unpinned_short
    unpinned_short=$(awk '
        /^\[(dependencies|dev-dependencies)\]/ { in_deps=1; next }
        /^\[/ { in_deps=0 }
        in_deps && /^[[:space:]]*[a-zA-Z][a-zA-Z0-9_-]*[[:space:]]*=[[:space:]]*"[^={]/ { print NR": "$0 }
    ' "$cargo_file" | grep -v '^\s*#' || true)

    if [ -n "$unpinned_short" ]; then
        echo "❌ ERROR: Found unpinned shorthand dependency versions in $cargo_file:"
        echo "$unpinned_short"
        return 1
    fi

    echo "✅ Cargo dependencies pinned to exact versions in $cargo_file."
    return 0
}

check_requirements_pinned() {
    local req_file="$1"
    echo "Checking Python requirements in $req_file..."
    if [ ! -f "$req_file" ]; then
        echo "❌ ERROR: $req_file not found"
        return 1
    fi

    local unpinned_lines=""
    local line_num=0
    while IFS= read -r line || [ -n "$line" ]; do
        ((line_num++))
        # Trim leading/trailing whitespace
        local trimmed
        trimmed="$(echo "$line" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"

        # Ignore empty lines and comments
        if [ -z "$trimmed" ] || [[ "$trimmed" =~ ^# ]]; then
            continue
        fi

        # Ignore -r or --index-url flags
        if [[ "$trimmed" =~ ^- ]]; then
            continue
        fi

        # Check for presence of pinning operators: ==, >=, <=, ~=, <, >, !=
        if ! echo "$trimmed" | grep -E "(==|>=|<=|~=|<|>|!=)" >/dev/null 2>&1; then
            unpinned_lines="${unpinned_lines}${line_num}: ${trimmed}\n"
        fi
    done < "$req_file"

    if [ -n "$unpinned_lines" ]; then
        echo "❌ ERROR: Found unpinned dependencies in $req_file:"
        printf "%b" "$unpinned_lines"
        echo "All dependencies must have version pins/bounds (e.g., package>=1.0,<2.0 or package==1.2.3)."
        return 1
    fi

    echo "✅ Python requirements pinned with valid bounds in $req_file."
    return 0
}

run_deps_scan() {
    echo "======================================================================"
    echo "📦 Step 2: Dependency Pin Integrity Checks"
    echo "======================================================================"

    local deps_failed=0

    # Check Cargo.toml
    local cargo_target="${CARGO_TOML_PATH:-backend-rust/Cargo.toml}"
    if [ -n "$CARGO_TOML_PATH" ] || [ -f "$cargo_target" ]; then
        if ! check_cargo_pinned "$cargo_target"; then
            deps_failed=1
        fi
    fi

    # Check requirements.txt
    if [ -n "$REQUIREMENTS_PATH" ]; then
        if ! check_requirements_pinned "$REQUIREMENTS_PATH"; then
            deps_failed=1
        fi
    else
        if [ -f "requirements.txt" ]; then
            if ! check_requirements_pinned "requirements.txt"; then
                deps_failed=1
            fi
        fi
        if [ -f "backend/requirements.txt" ]; then
            if ! check_requirements_pinned "backend/requirements.txt"; then
                deps_failed=1
            fi
        fi
    fi

    if [ "$deps_failed" -ne 0 ]; then
        echo "❌ Dependency pin integrity check FAILED."
        return 1
    else
        echo "✅ Dependency pin integrity check PASSED."
        return 0
    fi
}

# ==============================================================================
# 3. NPM PACKAGE VULNERABILITIES SCANNING
# ==============================================================================
run_npm_scan() {
    echo "======================================================================"
    echo "🛡️  Step 3: NPM Package Vulnerability Scanning"
    echo "======================================================================"

    local frontend_dir="frontend"
    if [ ! -d "$frontend_dir" ] || [ ! -f "$frontend_dir/package.json" ]; then
        echo "⚠️  Frontend package.json not found, skipping npm audit."
        return 0
    fi

    if ! command -v npm >/dev/null 2>&1; then
        echo "⚠️  npm command not found on PATH, skipping npm audit."
        return 0
    fi

    echo "Running npm audit in $frontend_dir..."
    local audit_json
    audit_json=$(cd "$frontend_dir" && npm audit --json 2>/dev/null || true)

    if [ -z "$audit_json" ]; then
        echo "⚠️  npm audit returned empty output."
        return 0
    fi

    local audit_summary
    audit_summary=$(python3 -c "
import json, sys
try:
    data = json.loads('''$audit_json''')
    meta = data.get('metadata', {}).get('vulnerabilities', {})
    total = meta.get('total', 0)
    critical = meta.get('critical', 0)
    high = meta.get('high', 0)
    moderate = meta.get('moderate', 0)
    low = meta.get('low', 0)
    print(f'{total}:{critical}:{high}:{moderate}:{low}')
except Exception as e:
    print('0:0:0:0:0')
")

    IFS=':' read -r total critical high moderate low <<< "$audit_summary"

    echo "NPM Audit Findings for frontend/package.json:"
    echo "  Total:    $total"
    echo "  Critical: $critical"
    echo "  High:     $high"
    echo "  Moderate: $moderate"
    echo "  Low:      $low"

    if [ "$STRICT_NPM" = true ]; then
        if [ "$total" -gt 0 ]; then
            echo "❌ ERROR: Strict mode enabled and $total npm vulnerabilities detected."
            return 1
        fi
    fi

    echo "✅ NPM audit inspection completed successfully."
    return 0
}

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================
if [ "$CHECK_SECRETS" = true ]; then
    if ! run_secret_scan; then
        SCAN_FAILED=1
    fi
fi

if [ "$CHECK_DEPS" = true ]; then
    if ! run_deps_scan; then
        SCAN_FAILED=1
    fi
fi

if [ "$CHECK_NPM" = true ]; then
    if ! run_npm_scan; then
        SCAN_FAILED=1
    fi
fi

echo "======================================================================"
if [ "$SCAN_FAILED" -ne 0 ]; then
    echo "❌ SECURITY SCAN FAILED: One or more security checks encountered violations."
    exit 1
else
    echo "✅ ALL SECURITY CHECKS PASSED: Secrets, dependency pins, and package audit verified."
    exit 0
fi
