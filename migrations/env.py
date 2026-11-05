from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
import sqlalchemy as sa
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy.engine.mock import MockConnection

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend.models import Base  # noqa: E402


class _OfflineMockResult:
    def first(self):
        return None

    def fetchone(self):
        return None

    def fetchall(self):
        return []

    def all(self):
        return []

    def scalar(self):
        return None

    def __iter__(self):
        return iter([])


class _OfflineMockInspector:
    def get_columns(self, table_name, **kw):
        return []

    def get_table_names(self, **kw):
        return []

    def get_indexes(self, table_name, **kw):
        return []

    def has_table(self, table_name, **kw):
        return False

    def get_foreign_keys(self, table_name, **kw):
        return []

    def get_unique_constraints(self, table_name, **kw):
        return []


def _setup_offline_mock() -> None:
    if MockConnection not in getattr(sa.inspection, "_registrars", {}):
        try:
            sa.inspection._inspects(MockConnection)(lambda target: _OfflineMockInspector())
        except Exception:
            pass
    _orig_mock_exec = getattr(MockConnection, "_orig_execute", None)
    if _orig_mock_exec is None:
        _orig_exec = MockConnection.execute
        MockConnection._orig_execute = _orig_exec

        def _mock_execute(self, statement, *args, **kwargs):
            _orig_exec(self, statement, *args, **kwargs)
            return _OfflineMockResult()

        MockConnection.execute = _mock_execute


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
    return config.get_main_option("sqlalchemy.url")


def run_migrations_offline() -> None:
    _setup_offline_mock()
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def _ensure_alembic_version_length(connection) -> None:
    inspector = sa.inspect(connection)
    if "alembic_version" not in inspector.get_table_names():
        metadata = sa.MetaData()
        sa.Table(
            "alembic_version",
            metadata,
            sa.Column("version_num", sa.String(64), primary_key=True),
        ).create(bind=connection)
        connection.commit()
        return

    for column in inspector.get_columns("alembic_version"):
        if column["name"] != "version_num":
            continue
        length = getattr(column["type"], "length", None)
        if length is None or length >= 64:
            return
        connection.execute(
            sa.text("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(64)")
        )
        connection.commit()
        return


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        url=get_url(),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        _ensure_alembic_version_length(connection)
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
