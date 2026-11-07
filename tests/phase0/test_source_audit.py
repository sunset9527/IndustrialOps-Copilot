from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from pypdf import PdfWriter

import pytest

from industrialops.phase0.source_audit import SourceAuditError, audit_archive, write_manifest


def _write_one_page_pdf(path: Path) -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with path.open("wb") as stream:
        writer.write(stream)


def test_audit_archive_emits_page_count_hash_and_relative_path(tmp_path: Path) -> None:
    archive = tmp_path / "raw_archive"
    source = archive / "cnc_haas_vf2_ngc" / "01_operator" / "operator.pdf"
    source.parent.mkdir(parents=True)
    _write_one_page_pdf(source)

    records = audit_archive(archive)

    assert records == [
        {
            "relative_path": "cnc_haas_vf2_ngc/01_operator/operator.pdf",
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "pages": 1,
            "bytes": source.stat().st_size,
        }
    ]


def test_write_manifest_is_sorted_and_stable_jsonl(tmp_path: Path) -> None:
    archive = tmp_path / "raw_archive"
    archive.mkdir()
    _write_one_page_pdf(archive / "z.pdf")
    _write_one_page_pdf(archive / "a.pdf")
    manifest = tmp_path / "manifest.jsonl"

    write_manifest(archive, manifest)

    lines = manifest.read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["relative_path"] for line in lines] == ["a.pdf", "z.pdf"]


def test_audit_archive_rejects_an_unreadable_pdf(tmp_path: Path) -> None:
    archive = tmp_path / "raw_archive"
    archive.mkdir()
    bad_pdf = archive / "broken.pdf"
    bad_pdf.write_bytes(b"not a PDF")

    with pytest.raises(SourceAuditError, match="broken.pdf"):
        audit_archive(archive)


def test_module_cli_writes_a_manifest(tmp_path: Path) -> None:
    archive = tmp_path / "raw_archive"
    archive.mkdir()
    _write_one_page_pdf(archive / "source.pdf")
    manifest = tmp_path / "source-audit.jsonl"
    project_root = Path(__file__).parents[2]
    environment = os.environ | {"PYTHONPATH": str(project_root / "src")}

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "industrialops.phase0.source_audit",
            "--archive-root",
            str(archive),
            "--manifest-path",
            str(manifest),
        ],
        check=False,
        capture_output=True,
        encoding="utf-8",
        env=environment,
    )

    assert result.returncode == 0, result.stderr
    assert [json.loads(line)["relative_path"] for line in manifest.read_text(encoding="utf-8").splitlines()] == [
        "source.pdf"
    ]
