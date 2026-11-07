"""Read-only source-file auditing for stage-0 knowledge packs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class SourceAuditError(RuntimeError):
    """Raised when an archived source cannot be verified for freezing."""


def audit_archive(archive_root: Path) -> list[dict[str, object]]:
    """Return deterministic provenance records for every PDF under ``archive_root``."""
    root = archive_root.resolve()
    records: list[dict[str, object]] = []

    for source_path in sorted(root.rglob("*.pdf"), key=lambda item: item.as_posix()):
        try:
            pages = len(PdfReader(source_path).pages)
        except PdfReadError as exc:
            raise SourceAuditError(f"Unreadable PDF: {source_path.name}") from exc

        records.append(
            {
                "relative_path": source_path.relative_to(root).as_posix(),
                "sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
                "pages": pages,
                "bytes": source_path.stat().st_size,
            }
        )

    return records


def write_manifest(archive_root: Path, manifest_path: Path) -> None:
    """Write the deterministic JSONL manifest without changing source files."""
    records = audit_archive(archive_root)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for record in records
    )
    manifest_path.write_text(content, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """Run the source audit as a module command."""
    parser = argparse.ArgumentParser(description="Create a stage-0 PDF source audit manifest.")
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--manifest-path", type=Path, required=True)
    arguments = parser.parse_args(argv)

    write_manifest(arguments.archive_root, arguments.manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
