from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from pypdf import PdfWriter

import pytest

from industrialops.phase0.page_parser import SourceHashMismatchError, extract_source_pages


def _write_one_page_pdf(path: Path) -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with path.open("wb") as stream:
        writer.write(stream)


def test_extract_source_pages_preserves_source_evidence_for_empty_page(tmp_path: Path) -> None:
    archive = tmp_path / "raw_archive"
    source = archive / "cnc_haas_vf2_ngc" / "manual.pdf"
    source.parent.mkdir(parents=True)
    _write_one_page_pdf(source)
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()

    pages = extract_source_pages(
        archive,
        [
            {
                "relative_path": "cnc_haas_vf2_ngc/manual.pdf",
                "source_id": "HAAS-TEST",
                "sha256": source_hash,
                "language": "zh-CN",
            }
        ],
    )

    assert pages == [
        {
            "pack_id": "cnc_pack_v1.0.0",
            "source_id": "HAAS-TEST",
            "source_file": "cnc_haas_vf2_ngc/manual.pdf",
            "source_sha256": source_hash,
            "language": "zh-CN",
            "page_number": 1,
            "text": "",
            "text_extraction_status": "empty",
            "evidence_locator": "HAAS-TEST:p.1",
        }
    ]


def test_extract_source_pages_rejects_source_hash_drift(tmp_path: Path) -> None:
    archive = tmp_path / "raw_archive"
    source = archive / "cnc_haas_vf2_ngc" / "manual.pdf"
    source.parent.mkdir(parents=True)
    _write_one_page_pdf(source)

    with pytest.raises(SourceHashMismatchError, match="manual.pdf"):
        extract_source_pages(
            archive,
            [
                {
                    "relative_path": "cnc_haas_vf2_ngc/manual.pdf",
                    "source_id": "HAAS-TEST",
                    "sha256": "0" * 64,
                    "language": "zh-CN",
                }
            ],
        )


def test_extract_source_pages_reports_file_level_progress(tmp_path: Path) -> None:
    archive = tmp_path / "raw_archive"
    source = archive / "cnc_haas_vf2_ngc" / "manual.pdf"
    source.parent.mkdir(parents=True)
    _write_one_page_pdf(source)
    progress_events: list[dict[str, object]] = []

    extract_source_pages(
        archive,
        [
            {
                "relative_path": "cnc_haas_vf2_ngc/manual.pdf",
                "source_id": "HAAS-TEST",
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "pages": 1,
                    "language": "zh-CN",
            }
        ],
        progress_events.append,
    )

    assert progress_events == [
        {
            "status": "completed",
            "total_sources": 1,
            "completed_sources": 1,
            "total_pages": 1,
            "processed_pages": 1,
            "current_source_id": "HAAS-TEST",
            "current_source_file": "cnc_haas_vf2_ngc/manual.pdf",
            "extracted_pages": 0,
            "empty_pages": 1,
            "failed_sources": 0,
            "error": None,
        }
    ]


def test_module_cli_writes_page_corpus(tmp_path: Path) -> None:
    archive = tmp_path / "raw_archive"
    source = archive / "cnc_haas_vf2_ngc" / "manual.pdf"
    source.parent.mkdir(parents=True)
    _write_one_page_pdf(source)
    registry = tmp_path / "source-registry.jsonl"
    registry.write_text(
        json.dumps(
            {
                "relative_path": "cnc_haas_vf2_ngc/manual.pdf",
                "source_id": "HAAS-TEST",
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "language": "zh-CN",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    corpus = tmp_path / "pages.jsonl"
    status = tmp_path / "parse-status.json"
    project_root = Path(__file__).parents[2]
    environment = os.environ | {"PYTHONPATH": str(project_root / "src")}

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "industrialops.phase0.page_parser",
            "--archive-root",
            str(archive),
            "--source-registry",
            str(registry),
            "--output-path",
            str(corpus),
            "--status-path",
            str(status),
        ],
        check=False,
        capture_output=True,
        encoding="utf-8",
        env=environment,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(corpus.read_text(encoding="utf-8").strip())["evidence_locator"] == "HAAS-TEST:p.1"
    assert json.loads(status.read_text(encoding="utf-8"))["status"] == "completed"
    assert "1/1 sources" in result.stderr
