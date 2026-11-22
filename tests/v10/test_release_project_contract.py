from __future__ import annotations

from pathlib import Path
from pathlib import PurePosixPath

from industrialops.release.manifest import load_release_manifest
from industrialops.release.run import package_version, tracked_files


def test_project_declares_v1_release_identity_and_explicit_demo_video_skip() -> None:
    root = Path(__file__).resolve().parents[2]

    manifest = load_release_manifest(root / "config" / "release_manifest_v1.json")

    assert package_version(root) == "1.0.0"
    assert manifest.product_version == "1.0.0"
    assert manifest.equipment_pack_ids == ("cnc_pack_v1.0.0", "dry_vacuum_pump_pack_v1.0.0")
    assert manifest.skipped_items == ("demo_video_recording_by_user_decision",)
    assert {item.path for item in manifest.frozen_files} >= {
        "README.md",
        "RELEASE_NOTES_v1.0.0.md",
        "docs/architecture.md",
        "docs/data/v1.0-release-data-boundary.md",
        "docs/evaluation/v1.0-release-summary.md",
        "data/evaluation/guardrail_eval_v1.jsonl",
        "data/evaluation/scenario_eval_v1.jsonl",
    }


def test_repository_does_not_track_local_only_release_inputs() -> None:
    root = Path(__file__).resolve().parents[2]
    local_only_prefixes = (
        "data/derived_corpus/",
        "data/indexes/",
        "data/models/",
        "data/packs/",
        "data/private_manuals/",
        "data/raw_archive/",
    )

    tracked = {PurePosixPath(path).as_posix() for path in tracked_files(root)}

    assert not any(path.startswith(local_only_prefixes) for path in tracked)
