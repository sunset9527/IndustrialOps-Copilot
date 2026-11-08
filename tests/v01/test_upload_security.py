from __future__ import annotations

from pathlib import Path

import pytest

from industrialops.services.upload_security import UploadValidationError, ensure_upload_root, store_upload


def test_store_upload_writes_an_allowed_document_inside_the_upload_root(tmp_path: Path) -> None:
    upload_root = tmp_path / "uploads" / "documents"

    stored = store_upload(upload_root, "manual.pdf", b"document bytes")

    assert stored == upload_root / "manual.pdf"
    assert stored.read_bytes() == b"document bytes"


@pytest.mark.parametrize("filename", ["../raw_archive/manual.pdf", "nested/manual.pdf", "manual.exe"])
def test_store_upload_rejects_paths_and_disallowed_extensions(tmp_path: Path, filename: str) -> None:
    with pytest.raises(UploadValidationError):
        store_upload(tmp_path / "uploads", filename, b"content")


def test_upload_root_cannot_be_a_frozen_or_derived_data_directory(tmp_path: Path) -> None:
    project_root = tmp_path

    with pytest.raises(UploadValidationError, match="protected"):
        ensure_upload_root(project_root, project_root / "data" / "packs" / "cnc_pack_v1.0.0")
