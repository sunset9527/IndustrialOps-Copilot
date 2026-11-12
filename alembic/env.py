"""Alembic environment for IndustrialOps database schema migrations."""

from __future__ import annotations

from logging.config import fileConfig
import os

from alembic import context
from sqlalchemy import engine_from_config, pool

from industrialops.database import Base
import industrialops.models  # noqa: F401  # register every mapped table on Base.metadata


config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The checked-in URL is deliberately a non-working placeholder.  A caller may
# override it with the same namespaced setting used by the application, while
# tests and programmatic callers can still provide an explicit Alembic URL.
if config.get_main_option("sqlalchemy.url") == "mysql+pymysql://root:change-me@localhost:3306/industrialops":
    runtime_database_url = os.environ.get("INDUSTRIALOPS_DATABASE_URL")
    if runtime_database_url:
        config.set_main_option("sqlalchemy.url", runtime_database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without an Engine."""

    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against the configured database."""

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
