from __future__ import annotations

import hashlib
import json
from pathlib import Path

from industrialops.release.manifest import load_release_manifest, validate_release_manifest


def test_manifest_validation_accepts_frozen_public_inputs(tmp_path: Path) -> None:
    tracked_file = tmp_path / "README.md"
    tracked_file.write_text("public release material\n", encoding="utf-8")
    manifest_path = _write_manifest(tmp_path, tracked_file)

    result = validate_release_manifest(
        project_root=tmp_path,
        manifest=load_release_manifest(manifest_path),
        package_version="1.0.0",
        migration_heads=("v04_assets_work_orders",),
    )

    assert result.passed
    assert result.reason_codes == ()


def test_manifest_validation_fails_closed_for_version_hash_and_migration_mismatch(tmp_path: Path) -> None:
    tracked_file = tmp_path / "README.md"
    tracked_file.write_text("public release material\n", encoding="utf-8")
    manifest_path = _write_manifest(tmp_path, tracked_file, expected_hash="0" * 64)

    result = validate_release_manifest(
        project_root=tmp_path,
        manifest=load_release_manifest(manifest_path),
        package_version="0.1.0",
        migration_heads=("v01_baseline", "v04_assets_work_orders"),
    )

    assert not result.passed
    assert result.reason_codes == (
        "RELEASE_VERSION_MISMATCH",
        "RELEASE_MIGRATION_HEAD_INVALID",
        "RELEASE_FILE_HASH_MISMATCH",
    )


def _write_manifest(root: Path, tracked_file: Path, *, expected_hash: str | None = None) -> Path:
    file_hash = expected_hash or hashlib.sha256(tracked_file.read_bytes()).hexdigest()
    payload = {
        "schema_version": 1,
        "product_version": "1.0.0",
        "migration_head": "v04_assets_work_orders",
        "equipment_pack_ids": ["cnc_pack_v1.0.0", "dry_vacuum_pump_pack_v1.0.0"],
        "frozen_files": [{"path": "README.md", "sha256": file_hash}],
        "required_documents": ["README.md"],
        "skipped_items": ["demo_video_recording_by_user_decision"],
    }
    manifest_path = root / "release_manifest.json"
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")
    return manifest_path
