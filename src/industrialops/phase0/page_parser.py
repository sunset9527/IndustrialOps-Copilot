"""Page-level PDF extraction with source evidence preserved."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from collections.abc import Callable
import sys

from pypdf import PdfReader


class SourceHashMismatchError(ValueError):
    """Raised when a source differs from the audited, immutable record."""


def extract_source_pages(
    archive_root: Path,
    source_records: list[dict[str, object]],
    progress_callback: Callable[[dict[str, object]], None] | None = None,
) -> list[dict[str, object]]:
    """Extract every PDF page while retaining the source registry evidence fields."""
    pages: list[dict[str, object]] = []
    root = archive_root.resolve()
    total_pages = sum(int(source.get("pages", 0)) for source in source_records)
    extracted_pages = 0
    empty_pages = 0

    for completed_sources, source in enumerate(source_records, start=1):
        relative_path = str(source["relative_path"])
        source_id = str(source["source_id"])
        source_hash = str(source["sha256"])
        language = str(source["language"])
        source_path = root / relative_path
        actual_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
        if actual_hash != source_hash:
            raise SourceHashMismatchError(f"Source hash mismatch: {relative_path}")
        reader = PdfReader(source_path)
        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            extraction_status = "extracted" if text.strip() else "empty"
            if extraction_status == "extracted":
                extracted_pages += 1
            else:
                empty_pages += 1
            pages.append(
                {
                    "pack_id": _pack_id(relative_path),
                    "source_id": source_id,
                    "source_file": relative_path,
                    "source_sha256": source_hash,
                    "language": language,
                    "page_number": page_number,
                    "text": text,
                    "text_extraction_status": extraction_status,
                    "evidence_locator": f"{source_id}:p.{page_number}",
                }
            )
        if progress_callback is not None:
            progress_callback(
                {
                    "status": "completed" if completed_sources == len(source_records) else "running",
                    "total_sources": len(source_records),
                    "completed_sources": completed_sources,
                    "total_pages": total_pages,
                    "processed_pages": len(pages),
                    "current_source_id": source_id,
                    "current_source_file": relative_path,
                    "extracted_pages": extracted_pages,
                    "empty_pages": empty_pages,
                    "failed_sources": 0,
                    "error": None,
                }
            )
    return pages


def write_page_corpus(
    archive_root: Path,
    source_records: list[dict[str, object]],
    output_path: Path,
    progress_callback: Callable[[dict[str, object]], None] | None = None,
) -> None:
    """Extract pages and write deterministic JSONL without touching raw sources."""
    pages = extract_source_pages(archive_root, source_records, progress_callback)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "".join(
            json.dumps(page, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
            for page in pages
        ),
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    """Extract the registered source PDFs into a page-level JSONL corpus."""
    parser = argparse.ArgumentParser(description="Create a stage-0 page-level source corpus.")
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--source-registry", type=Path, required=True)
    parser.add_argument("--output-path", type=Path, required=True)
    parser.add_argument("--status-path", type=Path, required=True)
    arguments = parser.parse_args(argv)
    source_records = [
        json.loads(line)
        for line in arguments.source_registry.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    def report(progress: dict[str, object]) -> None:
        arguments.status_path.parent.mkdir(parents=True, exist_ok=True)
        arguments.status_path.write_text(
            json.dumps(progress, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        print(
            f"[{progress['completed_sources']}/{progress['total_sources']} sources | "
            f"{progress['processed_pages']}/{progress['total_pages']} pages] "
            f"{progress['current_source_file']}",
            file=sys.stderr,
            flush=True,
        )

    write_page_corpus(arguments.archive_root, source_records, arguments.output_path, report)
    return 0


def _pack_id(relative_path: str) -> str:
    if relative_path.startswith("cnc_haas_vf2_ngc/"):
        return "cnc_pack_v1.0.0"
    if relative_path.startswith("dry_vacuum_edwards_nxds/"):
        return "dry_vacuum_pump_pack_v1.0.0"
    raise ValueError(f"Unsupported source-pack directory: {relative_path}")


if __name__ == "__main__":
    raise SystemExit(main())
