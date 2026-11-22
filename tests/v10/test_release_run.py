from __future__ import annotations

import hashlib
import json
from pathlib import Path

from industrialops.release import run


def test_local_release_run_writes_public_archive_checksum_and_sanitized_report(tmp_path: Path, monkeypatch) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("# IndustrialOps Copilot\n", encoding="utf-8")
    manifest_path = _write_manifest(tmp_path, readme)
    monkeypatch.setattr(run, "package_version", lambda _: "1.0.0")
    monkeypatch.setattr(run, "migration_heads", lambda _: ("v04_assets_work_orders",))
    monkeypatch.setattr(run, "tracked_files", lambda _: ("README.md",))
    monkeypatch.setattr(run, "working_tree_clean", lambda _: True)

    exit_code = run.main(
        [
            "--project-root",
            str(tmp_path),
            "--manifest",
            str(manifest_path),
            "--output-directory",
            str(tmp_path / "dist"),
        ]
    )

    report = json.loads((tmp_path / "dist" / "v1.0.0-release-build-report.json").read_text(encoding="utf-8"))
    assert exit_code == 0
    assert report["overall_status"] == "passed"
    assert (tmp_path / "dist" / "IndustrialOps-Copilot-v1.0.0.zip").is_file()
    assert (tmp_path / "dist" / "IndustrialOps-Copilot-v1.0.0.zip.sha256").is_file()
    assert "private" not in json.dumps(report)


def test_local_release_run_fails_without_creating_an_archive_when_manifest_is_invalid(tmp_path: Path, monkeypatch) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("# IndustrialOps Copilot\n", encoding="utf-8")
    manifest_path = _write_manifest(tmp_path, readme, expected_hash="0" * 64)
    monkeypatch.setattr(run, "package_version", lambda _: "1.0.0")
    monkeypatch.setattr(run, "migration_heads", lambda _: ("v04_assets_work_orders",))
    monkeypatch.setattr(run, "tracked_files", lambda _: ("README.md",))
    monkeypatch.setattr(run, "working_tree_clean", lambda _: True)

    exit_code = run.main(
        [
            "--project-root",
            str(tmp_path),
            "--manifest",
            str(manifest_path),
            "--output-directory",
            str(tmp_path / "dist"),
        ]
    )

    report = json.loads((tmp_path / "dist" / "v1.0.0-release-build-report.json").read_text(encoding="utf-8"))
    assert exit_code == 1
    assert report["overall_status"] == "failed"
    assert report["reason_codes"] == ["RELEASE_FILE_HASH_MISMATCH"]
    assert not (tmp_path / "dist" / "IndustrialOps-Copilot-v1.0.0.zip").exists()


def test_local_release_run_fails_closed_when_worktree_is_not_clean(tmp_path: Path, monkeypatch) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("# IndustrialOps Copilot\n", encoding="utf-8")
    manifest_path = _write_manifest(tmp_path, readme)
    monkeypatch.setattr(run, "package_version", lambda _: "1.0.0")
    monkeypatch.setattr(run, "migration_heads", lambda _: ("v04_assets_work_orders",))
    monkeypatch.setattr(run, "tracked_files", lambda _: ("README.md",))
    monkeypatch.setattr(run, "working_tree_clean", lambda _: False)

    exit_code = run.main(
        [
            "--project-root",
            str(tmp_path),
            "--manifest",
            str(manifest_path),
            "--output-directory",
            str(tmp_path / "dist"),
        ]
    )

    report = json.loads((tmp_path / "dist" / "v1.0.0-release-build-report.json").read_text(encoding="utf-8"))
    assert exit_code == 1
    assert report["reason_codes"] == ["RELEASE_WORKTREE_DIRTY"]
    assert not (tmp_path / "dist" / "IndustrialOps-Copilot-v1.0.0.zip").exists()


def _write_manifest(root: Path, readme: Path, *, expected_hash: str | None = None) -> Path:
    payload = {
        "schema_version": 1,
        "product_version": "1.0.0",
        "migration_head": "v04_assets_work_orders",
        "equipment_pack_ids": ["cnc_pack_v1.0.0", "dry_vacuum_pump_pack_v1.0.0"],
        "frozen_files": [
            {"path": "README.md", "sha256": expected_hash or hashlib.sha256(readme.read_bytes()).hexdigest()}
        ],
        "required_documents": ["README.md"],
        "skipped_items": ["demo_video_recording_by_user_decision"],
    }
    manifest_path = root / "release_manifest.json"
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")
    return manifest_path
