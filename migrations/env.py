from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
import sqlalchemy as sa
from sqlalchemy import engine_from_config
from sqlalchemy import pool

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend.models import Base  # noqa: E402


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
