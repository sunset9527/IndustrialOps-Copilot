"""Safe storage rules for user-uploaded documents."""

from __future__ import annotations

from pathlib import Path


_ALLOWED_SUFFIXES = {".pdf", ".docx", ".txt"}
_PROTECTED_DATA_ROOTS = (
    Path("data/packs"),
    Path("data/raw_archive"),
    Path("data/derived_corpus"),
    Path("data/structured"),
)


class UploadValidationError(ValueError):
    """Raised when an upload location or filename violates storage boundaries."""


def ensure_upload_root(project_root: Path, upload_root: Path) -> Path:
    """Reject roots that would let uploads overwrite protected project data."""

    resolved_project_root = project_root.resolve()
    resolved_upload_root = upload_root.resolve()
    try:
        relative_root = resolved_upload_root.relative_to(resolved_project_root)
    except ValueError:
        return resolved_upload_root

    for protected_root in _PROTECTED_DATA_ROOTS:
        if relative_root == protected_root or protected_root in relative_root.parents:
            raise UploadValidationError("Upload root is inside a protected data directory")
    return resolved_upload_root


def store_upload(upload_root: Path, filename: str, content: bytes) -> Path:
    """Store one permitted flat filename below an explicitly selected upload root."""

    candidate = Path(filename)
    if candidate.name != filename or candidate.suffix.casefold() not in _ALLOWED_SUFFIXES:
        raise UploadValidationError("Upload filename or extension is not allowed")

    upload_root.mkdir(parents=True, exist_ok=True)
    destination = upload_root / candidate.name
    destination.write_bytes(content)
    return destination
