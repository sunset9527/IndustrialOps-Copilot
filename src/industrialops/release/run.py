"""CLI for preparing, but never publishing, a local v1.0 release."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import tomllib

from alembic.config import Config
from alembic.script import ScriptDirectory

from industrialops.release.manifest import load_release_manifest, validate_release_manifest
from industrialops.release.packager import build_release_archive


def package_version(project_root: Path) -> str:
    """Read the declared project version from pyproject.toml."""

    payload = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))
    return str(payload["project"]["version"])


def migration_heads(project_root: Path) -> tuple[str, ...]:
    """Return sorted Alembic heads without connecting to a database."""

    config = Config(str(project_root / "alembic.ini"))
    config.set_main_option("script_location", str(project_root / "alembic"))
    return tuple(sorted(ScriptDirectory.from_config(config).get_heads()))


def tracked_files(project_root: Path) -> tuple[str, ...]:
    """List repository-tracked paths; no untracked local input is packaged."""

    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=project_root,
        check=True,
        capture_output=True,
    )
    return tuple(path for path in completed.stdout.decode("utf-8").split("\0") if path)


def working_tree_clean(project_root: Path) -> bool:
    """Return whether the source tree has no uncommitted tracked or untracked changes."""

    completed = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=project_root,
        check=True,
        capture_output=True,
    )
    return not completed.stdout.strip()


def main(arguments: list[str] | None = None) -> int:
    """Validate frozen public inputs and build a local release archive."""

    parser = argparse.ArgumentParser(description="Prepare IndustrialOps Copilot v1.0 local release artifacts")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, default=Path("dist"))
    parsed = parser.parse_args(arguments)
    root = parsed.project_root.resolve()
    output_directory = parsed.output_directory.resolve()
    manifest = load_release_manifest(parsed.manifest)
    report_path = output_directory / f"v{manifest.product_version}-release-build-report.json"
    if not working_tree_clean(root):
        _write_report(report_path, {"overall_status": "failed", "reason_codes": ["RELEASE_WORKTREE_DIRTY"]})
        return 1
    validation = validate_release_manifest(
        project_root=root,
        manifest=manifest,
        package_version=package_version(root),
        migration_heads=migration_heads(root),
    )
    if not validation.passed:
        _write_report(report_path, {"overall_status": "failed", "reason_codes": list(validation.reason_codes)})
        return 1
    archive = build_release_archive(
        project_root=root,
        tracked_files=tracked_files(root),
        product_version=manifest.product_version,
        output_directory=output_directory,
    )
    _write_report(
        report_path,
        {
            "overall_status": "passed",
            "product_version": manifest.product_version,
            "archive": archive.archive_path.name,
            "checksum": archive.checksum_path.name,
            "skipped_items": list(manifest.skipped_items),
        },
    )
    return 0


def _write_report(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
