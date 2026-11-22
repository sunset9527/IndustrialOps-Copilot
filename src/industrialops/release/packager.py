"""Safe construction of a local public release archive."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path, PurePosixPath
import re
from uuid import uuid4
import zipfile


_SENSITIVE_NAMES = {".env", "judge.env"}
_SENSITIVE_PARTS = {
    "backups",
    "data/indexes",
    "data/models",
    "data/packs",
    "data/private_manuals",
    "data/raw_archive",
    "data/derived_corpus",
    "dist",
    "node_modules",
    "tmp",
}
_SENSITIVE_CONTENT_PATTERN = re.compile(
    r"(?:mysql(?:\+\w+)?|postgres(?:ql)?(?:\+\w+)?)://(?!<)[^\s'\"]+", re.IGNORECASE
)


class ReleasePackageError(ValueError):
    """The requested archive violates the public-release boundary."""


@dataclass(frozen=True)
class ReleaseArchive:
    """Public archive and its adjacent SHA-256 checksum file."""

    archive_path: Path
    checksum_path: Path


def build_release_archive(
    *,
    project_root: Path,
    tracked_files: tuple[str, ...],
    product_version: str,
    output_directory: Path,
) -> ReleaseArchive:
    """Build a public ZIP from preselected Git-tracked file paths only."""

    _validate_tracked_files(project_root, tracked_files)
    archive_name = f"IndustrialOps-Copilot-v{product_version}.zip"
    archive_path = output_directory / archive_name
    checksum_path = output_directory / f"{archive_name}.sha256"
    temporary_path = output_directory / f".{uuid4().hex}-{archive_name}"
    output_directory.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(temporary_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for relative_path in sorted(tracked_files):
                archive.write(
                    project_root / relative_path,
                    arcname=f"IndustrialOps-Copilot-v{product_version}/{relative_path}",
                )
        _scan_archive_content(temporary_path)
        temporary_path.replace(archive_path)
        checksum_path.write_text(f"{_sha256(archive_path)}  {archive_name}\n", encoding="utf-8")
        return ReleaseArchive(archive_path=archive_path, checksum_path=checksum_path)
    except Exception:
        for path in (temporary_path, archive_path, checksum_path):
            if path.exists():
                path.unlink()
        raise


def _validate_tracked_files(project_root: Path, tracked_files: tuple[str, ...]) -> None:
    for relative_path in tracked_files:
        normalized = PurePosixPath(relative_path.replace("\\", "/"))
        if normalized.is_absolute() or ".." in normalized.parts:
            raise ReleasePackageError("RELEASE_ARCHIVE_PATH_INVALID")
        if normalized.name in _SENSITIVE_NAMES or _has_sensitive_prefix(normalized):
            raise ReleasePackageError("RELEASE_ARCHIVE_SENSITIVE_PATH")
        if not (project_root / normalized).is_file():
            raise ReleasePackageError("RELEASE_ARCHIVE_TRACKED_FILE_MISSING")


def _has_sensitive_prefix(path: PurePosixPath) -> bool:
    value = path.as_posix().lower()
    return any(value == prefix or value.startswith(f"{prefix}/") for prefix in _SENSITIVE_PARTS)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _scan_archive_content(archive_path: Path) -> None:
    """Reject archives that contain an actual database connection string."""

    with zipfile.ZipFile(archive_path) as archive:
        for name in archive.namelist():
            relative_name = name.split("/", maxsplit=1)[-1]
            if relative_name.startswith("tests/"):
                continue
            try:
                content = archive.read(name).decode("utf-8")
            except UnicodeDecodeError:
                continue
            if any(not _is_documented_placeholder(match.group()) for match in _SENSITIVE_CONTENT_PATTERN.finditer(content)):
                raise ReleasePackageError("RELEASE_ARCHIVE_SENSITIVE_CONTENT")


def _is_documented_placeholder(connection_url: str) -> bool:
    """Allow explicit non-secret example values used in public setup documentation."""

    return "change-me@" in connection_url or "${" in connection_url or ":<" in connection_url
