from __future__ import annotations

import hashlib
from pathlib import Path
import zipfile

import pytest

from industrialops.release.packager import ReleasePackageError, build_release_archive


def test_packager_builds_a_public_archive_with_checksum(tmp_path: Path) -> None:
    source = tmp_path / "README.md"
    source.write_text("# IndustrialOps Copilot\n", encoding="utf-8")
    output_directory = tmp_path / "dist"

    result = build_release_archive(
        project_root=tmp_path,
        tracked_files=("README.md",),
        product_version="1.0.0",
        output_directory=output_directory,
    )

    assert result.archive_path.name == "IndustrialOps-Copilot-v1.0.0.zip"
    assert result.checksum_path.read_text(encoding="utf-8") == (
        f"{hashlib.sha256(result.archive_path.read_bytes()).hexdigest()}  {result.archive_path.name}\n"
    )
    with zipfile.ZipFile(result.archive_path) as archive:
        assert archive.namelist() == ["IndustrialOps-Copilot-v1.0.0/README.md"]
        assert archive.read("IndustrialOps-Copilot-v1.0.0/README.md") == source.read_bytes()


def test_packager_rejects_sensitive_tracked_paths_without_leaving_artifacts(tmp_path: Path) -> None:
    secret = tmp_path / ".env"
    secret.write_text("API_TOKEN=private\n", encoding="utf-8")
    output_directory = tmp_path / "dist"

    with pytest.raises(ReleasePackageError, match="RELEASE_ARCHIVE_SENSITIVE_PATH"):
        build_release_archive(
            project_root=tmp_path,
            tracked_files=(".env",),
            product_version="1.0.0",
            output_directory=output_directory,
        )

    assert not list(output_directory.glob("*")) if output_directory.exists() else True


def test_packager_rejects_sensitive_content_during_archive_scan(tmp_path: Path) -> None:
    source = tmp_path / "docs" / "local-note.md"
    source.parent.mkdir()
    source.write_text("INDUSTRIALOPS_DATABASE_URL=mysql+pymysql://user:password@localhost/db\n", encoding="utf-8")
    output_directory = tmp_path / "dist"

    with pytest.raises(ReleasePackageError, match="RELEASE_ARCHIVE_SENSITIVE_CONTENT"):
        build_release_archive(
            project_root=tmp_path,
            tracked_files=("docs/local-note.md",),
            product_version="1.0.0",
            output_directory=output_directory,
        )

    assert not list(output_directory.glob("*")) if output_directory.exists() else True
