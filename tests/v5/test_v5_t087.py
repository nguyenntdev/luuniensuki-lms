# -*- coding: utf-8 -*-
"""V5-T087: Secret, Dependency, and Static Security Scanning Test Suite.

Wave W08, Slot A07 (Priority: P0, Classification: PRODUCTION_COMPLETION).
Verifies security scanning and startup protection invariants:
1. Automated Security Scanning Script (scripts/ci/security-scan.sh):
   - Full scan execution across repository.
   - Individual check flags (--check-secrets, --check-deps, --check-npm).
   - Secret detection for private keys, AWS access keys, GitHub PATs, and AI API keys.
   - Detection of sentinel secrets in configurations (change-me, secret, test-sentinel).
2. Pinned Dependency Integrity Enforcement:
   - Cargo.toml exact version pinning (=x.y.z) enforcement.
   - requirements.txt version bounding/pinning operators enforcement.
   - Immediate rejection of unpinned or unconstrained dependencies.
3. Production Fail-Closed Startup on Sentinel Secret Keys:
   - Refusal of default sentinels ("change-me", "secret", "test-sentinel", "CHANGE_ME_IN_PRODUCTION", "")
     with fatal RuntimeError in Settings model validation.
   - Defense-in-depth enforcement in create_app() application factory.
   - Acceptance of strong non-sentinel secrets in production.
   - Permissive tolerance of sentinels in development mode.
4. NPM Package Vulnerability Inspection:
   - Execution and parsing of npm audit metadata.
   - Strict mode rejection when vulnerabilities are present.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Generator

import pytest

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKSPACE_ROOT))

from backend.app import create_app  # noqa: E402
from backend.config import SENTINELS, Settings  # noqa: E402

SCRIPT_PATH = WORKSPACE_ROOT / "scripts" / "ci" / "security-scan.sh"

_RELEVANT_ENV_VARS = (
    "ENVIRONMENT",
    "JWT_SECRET_KEY",
    "CORS_ORIGINS",
    "CORS_ALLOW_CREDENTIALS",
    "PASSWORD_RESET_RETURN_TOKEN",
    "COOKIE_SECURE",
    "COOKIE_SAMESITE",
)

STRONG_SECRET = "strong-random-prod-secret-9876543210-abcdefghijklmnopqrstuvwxyz"


def _make_settings(monkeypatch: pytest.MonkeyPatch, **overrides) -> Settings:
    """Build a hermetic Settings instance without ambient env vars."""
    for var in _RELEVANT_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    return Settings(_env_file=None, **overrides)


# ==============================================================================
# 1. SECURITY SCAN SCRIPT EXECUTION TESTS
# ==============================================================================
def test_security_scan_script_clean_run() -> None:
    """The security scanning script must pass cleanly on the repository."""
    result = subprocess.run(
        [str(SCRIPT_PATH)],
        cwd=str(WORKSPACE_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, f"Script failed:\n{result.stderr}\n{result.stdout}"
    assert "ALL SECURITY CHECKS PASSED" in result.stdout
    assert "Secret scanning PASSED" in result.stdout
    assert "Dependency pin integrity check PASSED" in result.stdout
    assert "NPM audit inspection completed" in result.stdout


@pytest.mark.parametrize("flag", ["--check-secrets", "--check-deps", "--check-npm"])
def test_security_scan_individual_modes(flag: str) -> None:
    """Each individual scan mode must execute independently and succeed on clean repo."""
    result = subprocess.run(
        [str(SCRIPT_PATH), flag],
        cwd=str(WORKSPACE_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, f"Mode {flag} failed:\n{result.stderr}\n{result.stdout}"
    assert "ALL SECURITY CHECKS PASSED" in result.stdout


# ==============================================================================
# 2. SECRET SCANNING NEGATIVE ABUSE TESTS
# ==============================================================================
def test_security_scan_detects_private_key(tmp_path: Path) -> None:
    """Script must immediately reject hardcoded private keys."""
    bad_file = tmp_path / "leaked_key.pem"
    bad_file.write_text("-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----\n")

    result = subprocess.run(
        [str(SCRIPT_PATH), "--target", str(bad_file)],
        cwd=str(WORKSPACE_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "Detected private key pattern" in result.stdout
    assert "SECURITY SCAN FAILED" in result.stdout


def test_security_scan_detects_aws_key(tmp_path: Path) -> None:
    """Script must detect leaked AWS Access Key IDs."""
    bad_file = tmp_path / "credentials.txt"
    bad_file.write_text("aws_access_key_id = AKIAIOSFODNN7EXAMPLE\n")

    result = subprocess.run(
        [str(SCRIPT_PATH), "--target", str(bad_file)],
        cwd=str(WORKSPACE_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "Detected AWS Access Key ID pattern" in result.stdout
    assert "SECURITY SCAN FAILED" in result.stdout


def test_security_scan_detects_ai_api_key(tmp_path: Path) -> None:
    """Script must detect leaked OpenAI / Anthropic style API keys."""
    bad_file = tmp_path / "api_keys.env"
    bad_file.write_text("OPENAI_API_KEY=sk-proj-0123456789abcdef0123456789abcdef0123456789\n")

    result = subprocess.run(
        [str(SCRIPT_PATH), "--target", str(bad_file)],
        cwd=str(WORKSPACE_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "Detected OpenAI/AI API key pattern" in result.stdout
    assert "SECURITY SCAN FAILED" in result.stdout


def test_security_scan_detects_github_pat(tmp_path: Path) -> None:
    """Script must detect leaked GitHub Personal Access Tokens."""
    bad_file = tmp_path / "github.txt"
    bad_file.write_text("GH_TOKEN=ghp_012345678901234567890123456789012345\n")

    result = subprocess.run(
        [str(SCRIPT_PATH), "--target", str(bad_file)],
        cwd=str(WORKSPACE_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "Detected GitHub PAT pattern" in result.stdout
    assert "SECURITY SCAN FAILED" in result.stdout


@pytest.mark.parametrize("sentinel_val", ["change-me", "secret", "test-sentinel", "CHANGE_ME_IN_PRODUCTION", "change_me"])
def test_security_scan_detects_sentinel_jwt_secrets(tmp_path: Path, sentinel_val: str) -> None:
    """Script must reject files configuring sentinel JWT secret keys."""
    bad_file = tmp_path / "app.env"
    bad_file.write_text(f"JWT_SECRET_KEY={sentinel_val}\n")

    result = subprocess.run(
        [str(SCRIPT_PATH), "--target", str(bad_file)],
        cwd=str(WORKSPACE_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "Detected sentinel JWT_SECRET_KEY pattern" in result.stdout
    assert "SECURITY SCAN FAILED" in result.stdout


# ==============================================================================
# 3. PRODUCTION STARTUP REFUSAL ON SENTINEL SECRETS
# ==============================================================================
@pytest.mark.parametrize("sentinel_val", ["change-me", "secret", "test-sentinel", "CHANGE_ME_IN_PRODUCTION", "", "   "])
def test_production_startup_refusal_on_sentinel_keys(
    monkeypatch: pytest.MonkeyPatch, sentinel_val: str
) -> None:
    """Production Settings instantiation must fail closed with RuntimeError on sentinel secrets."""
    with pytest.raises(RuntimeError) as exc_info:
        _make_settings(
            monkeypatch,
            environment="production",
            jwt_secret_key=sentinel_val,
            cors_origins="https://app.example.com",
            cors_allow_credentials=True,
            cookie_secure=True,
            cookie_samesite="lax",
        )

    message = str(exc_info.value)
    assert "JWT_SECRET_KEY" in message
    if sentinel_val.strip():
        assert sentinel_val.strip() not in message


@pytest.mark.parametrize("sentinel_val", ["change-me", "secret", "test-sentinel"])
def test_production_startup_refusal_at_create_app_level(
    monkeypatch: pytest.MonkeyPatch, sentinel_val: str
) -> None:
    """create_app() application factory must enforce defense-in-depth sentinel refusal in production."""
    from backend.config import settings as global_settings

    monkeypatch.setattr(global_settings, "environment", "production")
    monkeypatch.setattr(global_settings, "jwt_secret_key", sentinel_val)
    monkeypatch.setattr(global_settings, "cookie_secure", True)
    monkeypatch.setattr(global_settings, "cookie_samesite", "lax")

    with pytest.raises(RuntimeError) as exc_info:
        create_app()

    assert "JWT_SECRET_KEY" in str(exc_info.value)


def test_production_startup_allows_strong_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    """A valid, non-sentinel secret in production starts cleanly."""
    settings = _make_settings(
        monkeypatch,
        environment="production",
        jwt_secret_key=STRONG_SECRET,
        cors_origins="https://app.example.com",
        cors_allow_credentials=True,
        cookie_secure=True,
        cookie_samesite="lax",
    )
    assert settings.jwt_secret_key == STRONG_SECRET
    assert settings.is_production is True


def test_development_allows_sentinel_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    """Development mode tolerates sentinel keys to enable local development workflows."""
    settings = _make_settings(
        monkeypatch,
        environment="development",
        jwt_secret_key="change-me",
    )
    assert settings.jwt_secret_key == "change-me"
    assert settings.is_production is False


# ==============================================================================
# 4. DEPENDENCY PIN INTEGRITY TESTS
# ==============================================================================
def test_dependency_pin_check_validates_clean_repo() -> None:
    """Dependency pin scan must pass cleanly on repository dependencies."""
    result = subprocess.run(
        [str(SCRIPT_PATH), "--check-deps"],
        cwd=str(WORKSPACE_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    assert "Dependency pin integrity check PASSED" in result.stdout


def test_dependency_pin_check_rejects_unpinned_cargo_toml_shorthand(tmp_path: Path) -> None:
    """Cargo.toml with unpinned shorthand version must be rejected."""
    bad_cargo = tmp_path / "Cargo.toml"
    bad_cargo.write_text('[dependencies]\nserde = "1.0.0"\n')

    result = subprocess.run(
        [str(SCRIPT_PATH), "--check-deps", "--cargo-toml", str(bad_cargo)],
        cwd=str(WORKSPACE_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "Found unpinned shorthand dependency versions" in result.stdout
    assert "serde = \"1.0.0\"" in result.stdout


def test_dependency_pin_check_rejects_unpinned_cargo_toml_version(tmp_path: Path) -> None:
    """Cargo.toml with version attribute missing '=' prefix must be rejected."""
    bad_cargo = tmp_path / "Cargo.toml"
    bad_cargo.write_text('[dependencies]\ntokio = { version = "1.38.0", features = ["full"] }\n')

    result = subprocess.run(
        [str(SCRIPT_PATH), "--check-deps", "--cargo-toml", str(bad_cargo)],
        cwd=str(WORKSPACE_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "Found unpinned dependency versions" in result.stdout
    assert "version = \"1.38.0\"" in result.stdout


def test_dependency_pin_check_rejects_unpinned_requirements_txt(tmp_path: Path) -> None:
    """requirements.txt with unconstrained package names must be rejected."""
    bad_req = tmp_path / "requirements.txt"
    bad_req.write_text("fastapi>=0.110,<1.0\nunpinned-rogue-package\npydantic>=2.6\n")

    result = subprocess.run(
        [str(SCRIPT_PATH), "--check-deps", "--requirements", str(bad_req)],
        cwd=str(WORKSPACE_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "Found unpinned dependencies" in result.stdout
    assert "unpinned-rogue-package" in result.stdout


def test_dependency_pin_check_accepts_valid_bounded_requirements(tmp_path: Path) -> None:
    """requirements.txt with valid bounded/pinned operators must pass."""
    good_req = tmp_path / "requirements.txt"
    good_req.write_text("fastapi>=0.110,<1.0\npytest==8.2.0\nalembic~=1.13.0\n# comment line\n\n")

    result = subprocess.run(
        [str(SCRIPT_PATH), "--check-deps", "--requirements", str(good_req)],
        cwd=str(WORKSPACE_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    assert "Python requirements pinned with valid bounds" in result.stdout


# ==============================================================================
# 5. NPM PACKAGE VULNERABILITY SCANNING TESTS
# ==============================================================================
def test_npm_audit_execution_and_reporting() -> None:
    """NPM package vulnerability check must inspect package.json and summarize metrics."""
    result = subprocess.run(
        [str(SCRIPT_PATH), "--check-npm"],
        cwd=str(WORKSPACE_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0
    assert "NPM Audit Findings for frontend/package.json" in result.stdout
    assert "NPM audit inspection completed successfully" in result.stdout


def test_npm_audit_strict_mode_fails_on_vulnerabilities() -> None:
    """NPM check with --strict must fail if vulnerabilities are discovered."""
    result = subprocess.run(
        [str(SCRIPT_PATH), "--check-npm", "--strict"],
        cwd=str(WORKSPACE_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode != 0
    assert "Strict mode enabled" in result.stdout
    assert "npm vulnerabilities detected" in result.stdout
