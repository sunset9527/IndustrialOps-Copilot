"""Reconcile archived PDFs with their official-source metadata."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from industrialops.phase0.source_audit import audit_archive


class SourceRegistryError(ValueError):
    """Raised when an archived source has no traceable official metadata."""


def build_source_registry(
    archive_root: Path,
    download_manifest_path: Path,
    overrides: list[dict[str, str]],
) -> list[dict[str, object]]:
    """Return one traceable source record for each actual archived PDF.

    The archive is authoritative for file existence. Historical download status is
    intentionally ignored because browser-assisted downloads can succeed after
    an earlier direct-download attempt failed.
    """
    root = archive_root.resolve()
    metadata_by_path = _metadata_from_download_manifest(root, download_manifest_path)
    for override in overrides:
        metadata_by_path[override["relative_path"]] = dict(override)

    records: list[dict[str, object]] = []
    for audit_record in audit_archive(root):
        relative_path = str(audit_record["relative_path"])
        metadata = metadata_by_path.get(relative_path)
        if metadata is None:
            raise SourceRegistryError(f"No source metadata for archived PDF: {relative_path}")
        records.append({**audit_record, **metadata})
    return records


def write_source_registry(
    archive_root: Path,
    download_manifest_path: Path,
    overrides: list[dict[str, str]],
    registry_path: Path,
) -> None:
    """Write a deterministic, actual-file-first source registry as JSONL."""
    records = build_source_registry(archive_root, download_manifest_path, overrides)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        "".join(
            json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
            for record in records
        ),
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    """Run actual-file-first source registration as a module command."""
    parser = argparse.ArgumentParser(description="Create the phase-0 source registry.")
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--download-manifest", type=Path, required=True)
    parser.add_argument("--overrides", type=Path, required=True)
    parser.add_argument("--registry-path", type=Path, required=True)
    arguments = parser.parse_args(argv)
    overrides = json.loads(arguments.overrides.read_text(encoding="utf-8"))
    write_source_registry(
        arguments.archive_root,
        arguments.download_manifest,
        overrides,
        arguments.registry_path,
    )
    return 0


def _metadata_from_download_manifest(
    archive_root: Path,
    download_manifest_path: Path,
) -> dict[str, dict[str, str]]:
    metadata: dict[str, dict[str, str]] = {}
    with download_manifest_path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            local_path = Path(row["local_path"])
            try:
                relative_path = local_path.resolve().relative_to(archive_root).as_posix()
            except ValueError:
                continue
            metadata[relative_path] = {
                "relative_path": relative_path,
                "source_id": row["source_id"],
                "language": row["language"],
                "kind": row["kind"],
                "url": row["url"],
                "accessed_at": row["accessed_at"],
            }
    return metadata


if __name__ == "__main__":
    raise SystemExit(main())
