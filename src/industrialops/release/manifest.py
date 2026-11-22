"""Validation for the public v1.0 release manifest."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path


@dataclass(frozen=True)
class FrozenFile:
    """One public file whose content is frozen for a release."""

    path: str
    sha256: str


@dataclass(frozen=True)
class ReleaseManifest:
    """The minimum facts required to freeze a local release."""

    schema_version: int
    product_version: str
    migration_head: str
    equipment_pack_ids: tuple[str, ...]
    frozen_files: tuple[FrozenFile, ...]
    required_documents: tuple[str, ...]
    skipped_items: tuple[str, ...]


@dataclass(frozen=True)
class ManifestValidation:
    """Fail-closed manifest validation result."""

    reason_codes: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.reason_codes


def load_release_manifest(path: Path) -> ReleaseManifest:
    """Load a JSON manifest without resolving any local private inputs."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    return ReleaseManifest(
        schema_version=payload["schema_version"],
        product_version=payload["product_version"],
        migration_head=payload["migration_head"],
        equipment_pack_ids=tuple(payload["equipment_pack_ids"]),
        frozen_files=tuple(FrozenFile(**item) for item in payload["frozen_files"]),
        required_documents=tuple(payload["required_documents"]),
        skipped_items=tuple(payload["skipped_items"]),
    )


def validate_release_manifest(
    *,
    project_root: Path,
    manifest: ReleaseManifest,
    package_version: str,
    migration_heads: tuple[str, ...],
) -> ManifestValidation:
    """Validate release facts and public file hashes in deterministic order."""

    reason_codes: list[str] = []
    if manifest.schema_version != 1:
        reason_codes.append("RELEASE_MANIFEST_SCHEMA_UNSUPPORTED")
    if manifest.product_version != package_version:
        reason_codes.append("RELEASE_VERSION_MISMATCH")
    if migration_heads != (manifest.migration_head,):
        reason_codes.append("RELEASE_MIGRATION_HEAD_INVALID")
    for document in manifest.required_documents:
        if not (project_root / document).is_file():
            reason_codes.append("RELEASE_REQUIRED_DOCUMENT_MISSING")
            break
    for frozen_file in manifest.frozen_files:
        path = project_root / frozen_file.path
        if not path.is_file() or _sha256(path) != frozen_file.sha256:
            reason_codes.append("RELEASE_FILE_HASH_MISMATCH")
            break
    return ManifestValidation(reason_codes=tuple(reason_codes))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
