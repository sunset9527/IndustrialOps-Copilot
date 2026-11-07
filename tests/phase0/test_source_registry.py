from __future__ import annotations

import csv
import json
import os
from pathlib import Path
import subprocess
import sys

from pypdf import PdfWriter

from industrialops.phase0.source_registry import build_source_registry


def _write_one_page_pdf(path: Path) -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with path.open("wb") as stream:
        writer.write(stream)


def _write_download_manifest(path: Path, source_path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["source_id", "language", "kind", "url", "local_path", "status", "message", "accessed_at"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "source_id": "EDW-MANUAL-L",
                "language": "en",
                "kind": "pdf",
                "url": "https://example.test/manual.pdf",
                "local_path": str(source_path),
                "status": "failed",
                "message": "old download state",
                "accessed_at": "2026-11-04",
            }
        )


def test_registry_uses_existing_pdf_even_when_old_download_status_failed(tmp_path: Path) -> None:
    archive = tmp_path / "raw_archive"
    source = archive / "pump" / "manual.pdf"
    source.parent.mkdir(parents=True)
    _write_one_page_pdf(source)
    download_manifest = tmp_path / "download.csv"
    _write_download_manifest(download_manifest, source)

    records = build_source_registry(archive, download_manifest, [])

    assert len(records) == 1
    assert records[0]["source_id"] == "EDW-MANUAL-L"
    assert records[0]["relative_path"] == "pump/manual.pdf"
    assert records[0]["url"] == "https://example.test/manual.pdf"
    assert records[0]["pages"] == 1
    assert records[0]["accessed_at"] == "2026-11-04"


def test_registry_uses_explicit_override_for_an_archived_pdf_missing_from_old_manifest(tmp_path: Path) -> None:
    archive = tmp_path / "raw_archive"
    source = archive / "cnc" / "alarm-help.pdf"
    source.parent.mkdir(parents=True)
    _write_one_page_pdf(source)
    download_manifest = tmp_path / "download.csv"
    _write_download_manifest(download_manifest, tmp_path / "not-in-archive.pdf")

    records = build_source_registry(
        archive,
        download_manifest,
        [
            {
                "relative_path": "cnc/alarm-help.pdf",
                "source_id": "HAAS-ALARM-HELP-EN",
                "language": "en",
                "kind": "page_snapshot",
                "url": "https://example.test/alarm-help",
                "accessed_at": "2026-11-04",
            }
        ],
    )

    assert records[0]["source_id"] == "HAAS-ALARM-HELP-EN"
    assert records[0]["kind"] == "page_snapshot"


def test_module_cli_writes_registry_with_overrides(tmp_path: Path) -> None:
    archive = tmp_path / "raw_archive"
    source = archive / "cnc" / "alarm-help.pdf"
    source.parent.mkdir(parents=True)
    _write_one_page_pdf(source)
    download_manifest = tmp_path / "download.csv"
    _write_download_manifest(download_manifest, tmp_path / "not-in-archive.pdf")
    overrides = tmp_path / "overrides.json"
    overrides.write_text(
        json.dumps(
            [
                {
                    "relative_path": "cnc/alarm-help.pdf",
                    "source_id": "HAAS-ALARM-HELP-EN",
                    "language": "en",
                    "kind": "page_snapshot",
                    "url": "https://example.test/alarm-help",
                    "accessed_at": "2026-11-04",
                }
            ]
        ),
        encoding="utf-8",
    )
    registry = tmp_path / "registry.jsonl"
    project_root = Path(__file__).parents[2]
    environment = os.environ | {"PYTHONPATH": str(project_root / "src")}

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "industrialops.phase0.source_registry",
            "--archive-root",
            str(archive),
            "--download-manifest",
            str(download_manifest),
            "--overrides",
            str(overrides),
            "--registry-path",
            str(registry),
        ],
        check=False,
        capture_output=True,
        encoding="utf-8",
        env=environment,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(registry.read_text(encoding="utf-8").strip())["source_id"] == "HAAS-ALARM-HELP-EN"
