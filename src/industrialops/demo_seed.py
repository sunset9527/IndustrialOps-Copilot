"""Explicit, idempotent initialization for v0.4 synthetic demo assets."""

from __future__ import annotations

import argparse
import os

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from industrialops.config import Settings
from industrialops.models.assets import Asset, EquipmentModel


_DEMO_MODELS = (
    {
        "equipment_model_id": "haas-vf2-ngc",
        "pack_id": "cnc_pack_v1.0.0",
        "manufacturer": "Haas",
        "model_name": "VF-2",
        "controller_or_firmware_scope": "NGC",
    },
    {
        "equipment_model_id": "edwards-nxds-standard",
        "pack_id": "dry_vacuum_pump_pack_v1.0.0",
        "manufacturer": "Edwards",
        "model_name": "nXDS",
        "controller_or_firmware_scope": None,
    },
)

_DEMO_ASSETS = (
    {
        "asset_id": "cnc-demo-001",
        "equipment_model_id": "haas-vf2-ngc",
        "display_name": "CNC 演示机 001",
        "site": "Demo Factory",
        "status": "available",
    },
    {
        "asset_id": "pump-demo-001",
        "equipment_model_id": "edwards-nxds-standard",
        "display_name": "真空泵演示机 001",
        "site": "Demo Factory",
        "status": "available",
    },
)


def seed_demo_assets(db: Session) -> int:
    """Add the two documented synthetic assets when they are absent, never at import time."""

    for model in _DEMO_MODELS:
        if db.scalar(select(EquipmentModel).where(EquipmentModel.equipment_model_id == model["equipment_model_id"])) is None:
            db.add(EquipmentModel(**model))
    db.flush()

    created = 0
    for asset in _DEMO_ASSETS:
        if db.scalar(select(Asset).where(Asset.asset_id == asset["asset_id"])) is None:
            db.add(Asset(**asset, synthetic=True))
            created += 1
    db.flush()
    return created


def main() -> None:
    """Run from PowerShell after ``alembic upgrade head`` to seed only synthetic records."""

    parser = argparse.ArgumentParser(description="Seed IndustrialOps v0.4 synthetic demo assets")
    parser.add_argument("--database-url", default=None, help="Overrides INDUSTRIALOPS_DATABASE_URL for this command")
    args = parser.parse_args()
    database_url = args.database_url or Settings.from_environment(os.environ).database_url
    factory = sessionmaker(bind=create_engine(database_url, pool_pre_ping=True))
    with factory() as db:
        created = seed_demo_assets(db)
        db.commit()
    print(f"seeded_synthetic_assets={created}")


if __name__ == "__main__":
    main()
