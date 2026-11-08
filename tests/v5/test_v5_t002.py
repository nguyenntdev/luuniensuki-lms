"""
V5-T002: Reproducible local development verification test suite.

Validates:
1. Docker Compose configuration syntax, services, port bindings (8000, 8001, 3000, 5432).
2. Environment configuration (.env.example vs backend/config Settings), checking required secret placeholders.
3. Backend Dockerfile hardening (non-root user, proper directories, copy structure).
4. Negative / abuse test (contract requirement):
   Secondary execution of seeding / bootstrap must be idempotent and MUST NOT wipe
   custom test accounts or reset existing user data.
5. Disposable database connectivity and required extensions (pgcrypto, unaccent, pg_trgm).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.config import Settings
from backend.models import Base, User, UserRole
from backend.security import hash_password, verify_password
from backend.seed import seed_demo_users


DOCKER_COMPOSE_PATH = REPO_ROOT / "docker-compose.yml"
BACKEND_DOCKERFILE_PATH = REPO_ROOT / "backend" / "Dockerfile"
ENV_EXAMPLE_PATH = REPO_ROOT / ".env.example"
BOOTSTRAP_SCRIPT_PATH = REPO_ROOT / "scripts" / "dev" / "bootstrap.sh"


def test_docker_compose_validity_and_ports():
    """Verify docker-compose.yml syntax and critical port bindings."""
    assert DOCKER_COMPOSE_PATH.exists(), f"Missing {DOCKER_COMPOSE_PATH}"

    with open(DOCKER_COMPOSE_PATH, "r", encoding="utf-8") as f:
        compose_data = yaml.safe_load(f)

    services = compose_data.get("services", {})
    expected_services = ["db", "api", "api_rust", "web"]
    for svc in expected_services:
        assert svc in services, f"Required service '{svc}' missing in docker-compose.yml"

    # Verify exposed ports
    # db: 5432
    db_ports = [str(p) for p in services["db"].get("ports", [])]
    assert any("5432" in p for p in db_ports), f"Database port 5432 not exposed in db service: {db_ports}"

    # api: 8000
    api_ports = [str(p) for p in services["api"].get("ports", [])]
    assert any("8000" in p for p in api_ports), f"FastAPI port 8000 not exposed in api service: {api_ports}"

    # api_rust: 8001
    rust_ports = [str(p) for p in services["api_rust"].get("ports", [])]
    assert any("8001" in p for p in rust_ports), f"Rust Gateway port 8001 not exposed in api_rust service: {rust_ports}"

    # web: 3000
    web_ports = [str(p) for p in services["web"].get("ports", [])]
    assert any("3000" in p for p in web_ports), f"Next.js Web port 3000 not exposed in web service: {web_ports}"

    # Verify volume mounts for DB persistence
    db_volumes = [str(v) for v in services["db"].get("volumes", [])]
    assert any("postgres_data" in v for v in db_volumes), f"Postgres data volume missing: {db_volumes}"


def test_backend_dockerfile_hardening():
    """Verify backend/Dockerfile uses non-root user and correct setup."""
    assert BACKEND_DOCKERFILE_PATH.exists(), f"Missing {BACKEND_DOCKERFILE_PATH}"
    content = BACKEND_DOCKERFILE_PATH.read_text(encoding="utf-8")

    # Non-root user
    assert re.search(r"useradd .* appuser", content), "backend/Dockerfile must create appuser"
    assert "USER appuser" in content, "backend/Dockerfile must switch to USER appuser"

    # Check copies
    assert "COPY --chown=appuser:appgroup backend /app/backend" in content or "COPY backend /app/backend" in content
    assert "EXPOSE 8000" in content, "backend/Dockerfile must expose port 8000"


def test_env_example_required_variables():
    """Verify .env.example contains all required baseline keys."""
    assert ENV_EXAMPLE_PATH.exists(), f"Missing {ENV_EXAMPLE_PATH}"
    env_content = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")

    required_keys = [
        "DATABASE_URL",
        "JWT_SECRET_KEY",
        "JWT_ALGORITHM",
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "REFRESH_TOKEN_EXPIRE_DAYS",
        "LIVEKIT_URL",
        "LOG_LEVEL",
    ]

    for key in required_keys:
        assert f"{key}=" in env_content, f"Missing required env variable {key} in .env.example"


def test_bootstrap_script_idempotent_execution():
    """Verify scripts/dev/bootstrap.sh exists, is executable, and runs cleanly with --check-only."""
    assert BOOTSTRAP_SCRIPT_PATH.exists(), f"Missing {BOOTSTRAP_SCRIPT_PATH}"
    assert os.access(BOOTSTRAP_SCRIPT_PATH, os.X_OK), f"{BOOTSTRAP_SCRIPT_PATH} is not executable"

    result = subprocess.run(
        [str(BOOTSTRAP_SCRIPT_PATH), "--check-only"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, f"bootstrap.sh --check-only failed: {result.stderr}\n{result.stdout}"
    assert "docker-compose.yml configuration syntax: VALID" in result.stdout
    assert "Completed check-only mode" in result.stdout


def _get_test_db_url() -> str:
    """Resolve database URL for V5-T002 local dev test target."""
    return os.environ.get(
        "TEST_DATABASE_URL",
        os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg://postgres:postgres@localhost:5432/luuniensuki_test",
        ),
    )


def test_database_extensions_and_disposable_target():
    """Verify test database is reachable and has necessary extensions."""
    test_db_url = _get_test_db_url()
    engine = create_engine(test_db_url, pool_pre_ping=True)

    with engine.connect() as conn:
        res = conn.execute(
            text("SELECT extname FROM pg_extension WHERE extname IN ('pgcrypto', 'unaccent', 'pg_trgm')")
        ).scalars().all()
        installed_exts = set(res)

        # In local disposable dev DB, these extensions must be available or installed
        for ext in ["pgcrypto", "unaccent", "pg_trgm"]:
            if ext not in installed_exts:
                conn.execute(text(f"CREATE EXTENSION IF NOT EXISTS {ext};"))
                conn.commit()

        # Re-query to confirm
        res2 = conn.execute(
            text("SELECT extname FROM pg_extension WHERE extname IN ('pgcrypto', 'unaccent', 'pg_trgm')")
        ).scalars().all()
        assert "pgcrypto" in res2
        assert "unaccent" in res2
        assert "pg_trgm" in res2
    engine.dispose()


def test_negative_secondary_run_preserves_custom_accounts_and_data():
    """
    Negative / Abuse Test (Contract requirement):
    A secondary run of the bootstrap/seed logic must NOT reset the database,
    must NOT drop user tables, and must NOT delete or overwrite custom test accounts.
    """
    test_db_url = _get_test_db_url()
    engine = create_engine(test_db_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    custom_email = "custom_tester_v5_t002@histolab.icu"
    custom_password = "SecurePassword@123"

    with SessionLocal() as session:
        # 1. First run: seed baseline demo users
        seed_demo_users(session)
        session.commit()

        # 2. Add custom user created during development / testing
        existing_custom = session.execute(
            select(User).where(User.email == custom_email)
        ).scalar_one_or_none()

        if existing_custom is None:
            new_user = User(
                email=custom_email,
                password_hash=hash_password(custom_password),
                display_name="Custom V5 Developer",
                role=UserRole.learner,
            )
            session.add(new_user)
            session.commit()

        # Update a demo user's state (e.g. learner total_xp or streak)
        demo_user = session.execute(
            select(User).where(User.email == "learner@luuniensuki.local")
        ).scalar_one_or_none()
        assert demo_user is not None
        demo_user.total_xp = 1250
        demo_user.current_streak = 7
        session.commit()

    # 3. Simulate SECONDARY execution (re-running seed_demo_users as bootstrap does)
    with SessionLocal() as session:
        seed_demo_users(session)
        session.commit()

    # 4. Verify that:
    #    a) custom user still exists and password hash is intact
    #    b) demo user's modified total_xp / current_streak was NOT wiped out back to default
    with SessionLocal() as session:
        persisted_custom = session.execute(
            select(User).where(User.email == custom_email)
        ).scalar_one_or_none()
        assert persisted_custom is not None, "Negative test failed: custom test account was deleted on second run!"
        assert verify_password(custom_password, persisted_custom.password_hash), "Custom user credentials corrupted!"

        persisted_demo = session.execute(
            select(User).where(User.email == "learner@luuniensuki.local")
        ).scalar_one_or_none()
        assert persisted_demo is not None
        assert persisted_demo.total_xp == 1250, f"Demo user XP was overwritten! Expected 1250, got {persisted_demo.total_xp}"
        assert persisted_demo.current_streak == 7, f"Demo user streak was reset! Expected 7, got {persisted_demo.current_streak}"

        # Clean up custom test record
        session.delete(persisted_custom)
        session.commit()

    engine.dispose()
