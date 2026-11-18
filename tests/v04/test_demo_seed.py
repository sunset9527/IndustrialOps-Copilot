from __future__ import annotations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from industrialops.database import Base
from industrialops.models.assets import Asset, EquipmentModel


def test_explicit_demo_seed_creates_idempotent_synthetic_assets() -> None:
    from industrialops.demo_seed import seed_demo_assets

    engine = create_engine("sqlite://", poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = Session(engine)

    first_count = seed_demo_assets(db)
    second_count = seed_demo_assets(db)
    db.commit()

    assets = list(db.scalars(select(Asset).order_by(Asset.asset_id)))
    models = list(db.scalars(select(EquipmentModel).order_by(EquipmentModel.equipment_model_id)))
    assert first_count == 2
    assert second_count == 0
    assert [asset.asset_id for asset in assets] == ["cnc-demo-001", "pump-demo-001"]
    assert all(asset.synthetic for asset in assets)
    assert [model.pack_id for model in models] == ["dry_vacuum_pump_pack_v1.0.0", "cnc_pack_v1.0.0"]
    pump_model = next(model for model in models if model.equipment_model_id == "edwards-nxds-standard")
    assert pump_model.model_name == "nXDS10i"


def test_demo_seed_corrects_the_existing_pump_model_to_an_in_scope_variant() -> None:
    from industrialops.demo_seed import seed_demo_assets

    engine = create_engine("sqlite://", poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = Session(engine)
    db.add(EquipmentModel(
        equipment_model_id="edwards-nxds-standard",
        pack_id="dry_vacuum_pump_pack_v1.0.0",
        manufacturer="Edwards",
        model_name="nXDS",
    ))
    db.commit()

    seed_demo_assets(db)
    db.commit()

    pump_model = db.scalar(select(EquipmentModel).where(EquipmentModel.equipment_model_id == "edwards-nxds-standard"))
    assert pump_model.model_name == "nXDS10i"
