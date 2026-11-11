from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


ROOT = Path(__file__).resolve().parents[2]


def _config(database_path: Path) -> Config:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path.as_posix()}")
    return config


def test_upgrade_from_empty_database_creates_v01_and_v04_tables(tmp_path: Path) -> None:
    database_path = tmp_path / "industrialops.db"

    command.upgrade(_config(database_path), "head")

    table_names = set(inspect(create_engine(f"sqlite:///{database_path.as_posix()}")).get_table_names())
    assert {
        "users",
        "audit_events",
        "equipment_models",
        "assets",
        "auth_sessions",
        "diagnosis_records",
        "work_orders",
        "approval_decisions",
        "work_order_transitions",
        "langgraph_checkpoints",
        "langgraph_checkpoint_writes",
    } <= table_names


def test_downgrade_to_v01_baseline_preserves_existing_v01_tables(tmp_path: Path) -> None:
    database_path = tmp_path / "industrialops.db"
    config = _config(database_path)
    command.upgrade(config, "head")

    command.downgrade(config, "v01_baseline")

    table_names = set(inspect(create_engine(f"sqlite:///{database_path.as_posix()}")).get_table_names())
    assert {"users", "audit_events"} <= table_names
    assert "work_orders" not in table_names
    assert "assets" not in table_names
