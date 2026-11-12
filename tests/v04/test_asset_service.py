from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from industrialops.database import Base
from industrialops.models.assets import Asset, EquipmentModel
from industrialops.services.assets import AssetNotFoundError, AssetVersionConflictError, create_asset, list_assets, update_asset


def _session() -> Session:
    engine = create_engine("sqlite://", poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return Session(engine)


def _model(db: Session) -> EquipmentModel:
    model = EquipmentModel(
        equipment_model_id="haas-vf2-ngc", pack_id="cnc_pack_v1.0.0", manufacturer="Haas", model_name="VF-2"
    )
    db.add(model)
    db.commit()
    return model


def test_create_and_filter_concrete_assets_without_conflating_model_identifiers() -> None:
    db = _session()
    _model(db)
    create_asset(db, asset_id="cnc-demo-001", equipment_model_id="haas-vf2-ngc", display_name="CNC 001", site="A")
    create_asset(db, asset_id="cnc-demo-002", equipment_model_id="haas-vf2-ngc", display_name="CNC 002", site="B")
    db.commit()

    assets, total = list_assets(db, pack_id="cnc_pack_v1.0.0", limit=1, offset=0)

    assert total == 2
    assert [asset.asset_id for asset in assets] == ["cnc-demo-001"]
    assert assets[0].equipment_model_id == "haas-vf2-ngc"


def test_update_requires_matching_version_and_uses_soft_retirement() -> None:
    db = _session()
    _model(db)
    asset = create_asset(db, asset_id="cnc-demo-001", equipment_model_id="haas-vf2-ngc", display_name="CNC 001")
    db.commit()

    updated = update_asset(db, "cnc-demo-001", expected_version=1, status="out_of_service")
    db.commit()

    assert updated.status == "out_of_service"
    assert updated.version == 2
    with pytest.raises(AssetVersionConflictError) as conflict:
        update_asset(db, "cnc-demo-001", expected_version=1, display_name="stale")
    assert conflict.value.code == "stale_resource_version"
    with pytest.raises(AssetNotFoundError) as missing:
        update_asset(db, "missing", expected_version=1, display_name="none")
    assert missing.value.code == "asset_not_found"
