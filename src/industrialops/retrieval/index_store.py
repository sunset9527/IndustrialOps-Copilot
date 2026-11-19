"""Immutable, local-only vector index artifacts for frozen knowledge packs."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
from uuid import uuid4

from industrialops.knowledge.pack_loader import EquipmentPack


INDEX_FORMAT_VERSION = "v1"
TEXT_PREPROCESSING_VERSION = "text-plus-zh-v1"


class IndexIntegrityError(RuntimeError):
    """A local index is absent, stale, partial, or internally inconsistent."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True)
class IndexArtifact:
    """The immutable location and identity of one finished pack index."""

    index_id: str
    path: Path
    manifest: dict[str, object]


class IndexStore:
    """Build and read finished indexes without mutating frozen pack inputs."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def prepare(
        self,
        pack: EquipmentPack,
        *,
        registry_sha256: str,
        model_fingerprint: str,
        encode: Callable[[list[str]], Sequence[Sequence[float]]],
    ) -> IndexArtifact:
        """Reuse a validated artifact or atomically build a new immutable one."""

        artifact = self.expected_artifact(pack, registry_sha256=registry_sha256, model_fingerprint=model_fingerprint)
        manifest = artifact.manifest
        target = artifact.path
        if target.exists():
            return self.load(IndexArtifact(str(manifest["index_id"]), target, manifest))

        texts = [f"{document.text} {document.text_zh}" for document in pack.documents]
        vectors = [list(vector) for vector in encode(texts)]
        self._validate_vectors(vectors, len(pack.documents))
        manifest["document_count"] = len(pack.documents)
        manifest["vector_dimensions"] = len(vectors[0]) if vectors else 0

        # Windows still applies a shorter practical limit to directory creation
        # on some systems. The final immutable ID stays complete; only the
        # disposable sibling name is compacted.
        temporary = target.parent / f".tmp-{uuid4().hex[:8]}"
        temporary.mkdir(parents=True, exist_ok=False)
        try:
            self._write_json(temporary / "manifest.json", manifest)
            self._write_json(temporary / "document_ids.json", [item.document_id for item in pack.documents])
            self._write_json(temporary / "vectors.json", vectors)
            if target.exists():
                return self.load(IndexArtifact(str(manifest["index_id"]), target, manifest))
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(temporary, target)
        finally:
            if temporary.exists():
                _remove_empty_directory(temporary)
        return self.load(IndexArtifact(str(manifest["index_id"]), target, manifest))

    def expected_artifact(
        self, pack: EquipmentPack, *, registry_sha256: str, model_fingerprint: str
    ) -> IndexArtifact:
        """Return the deterministic location without reading or creating it."""

        manifest = self._expected_manifest(pack, registry_sha256, model_fingerprint)
        return IndexArtifact(str(manifest["index_id"]), self._root / pack.pack_id / str(manifest["index_id"]), manifest)

    def load(self, artifact: IndexArtifact) -> IndexArtifact:
        """Read and validate a completed artifact; never repair or overwrite it."""

        manifest_path = artifact.path / "manifest.json"
        ids_path = artifact.path / "document_ids.json"
        vectors_path = artifact.path / "vectors.json"
        if not all(path.is_file() for path in (manifest_path, ids_path, vectors_path)):
            raise IndexIntegrityError("INDEX_ARTIFACT_INCOMPLETE", "a required index file is missing")
        manifest = self._read_object(manifest_path)
        if any(manifest.get(key) != value for key, value in artifact.manifest.items()):
            raise IndexIntegrityError("INDEX_MANIFEST_MISMATCH", "index manifest differs from expected frozen inputs")
        ids = self._read_list(ids_path, "INDEX_DOCUMENT_IDS_INVALID")
        vectors = self._read_list(vectors_path, "INDEX_VECTORS_INVALID")
        expected_count = manifest.get("document_count")
        if not isinstance(expected_count, int) or len(ids) != expected_count:
            raise IndexIntegrityError("INDEX_DOCUMENT_COUNT_MISMATCH", "document ID count differs from manifest")
        if len(vectors) != expected_count:
            raise IndexIntegrityError("INDEX_VECTOR_COUNT_MISMATCH", "vector count differs from manifest")
        if not all(isinstance(item, str) and item for item in ids) or len(ids) != len(set(ids)):
            raise IndexIntegrityError("INDEX_DOCUMENT_IDS_INVALID", "document IDs must be non-empty and unique")
        expected_dimensions = manifest.get("vector_dimensions")
        if not isinstance(expected_dimensions, int):
            raise IndexIntegrityError("INDEX_MANIFEST_INVALID", "vector dimensions are missing")
        self._validate_vectors(vectors, expected_count, expected_dimensions=expected_dimensions)
        return IndexArtifact(str(manifest["index_id"]), artifact.path, manifest)

    def read_vectors(self, artifact: IndexArtifact) -> dict[str, tuple[float, ...]]:
        """Return vectors only after full artifact validation."""

        validated = self.load(artifact)
        ids = self._read_list(validated.path / "document_ids.json", "INDEX_DOCUMENT_IDS_INVALID")
        vectors = self._read_list(validated.path / "vectors.json", "INDEX_VECTORS_INVALID")
        return {str(document_id): tuple(float(value) for value in vector) for document_id, vector in zip(ids, vectors, strict=True)}

    @staticmethod
    def _expected_manifest(pack: EquipmentPack, registry_sha256: str, model_fingerprint: str) -> dict[str, object]:
        identity = {
            "format_version": INDEX_FORMAT_VERSION,
            "text_preprocessing_version": TEXT_PREPROCESSING_VERSION,
            "pack_id": pack.pack_id,
            "pack_content_sha256": pack.content_sha256,
            "pack_registry_version": pack.registry_version,
            "registry_sha256": registry_sha256,
            "model_fingerprint": model_fingerprint,
        }
        encoded = json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return {"index_id": hashlib.sha256(encoded).hexdigest(), **identity}

    @staticmethod
    def _write_json(path: Path, value: object) -> None:
        path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")), encoding="utf-8")

    @staticmethod
    def _read_object(path: Path) -> dict[str, object]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise IndexIntegrityError("INDEX_MANIFEST_INVALID", "index manifest cannot be read") from error
        if not isinstance(value, dict):
            raise IndexIntegrityError("INDEX_MANIFEST_INVALID", "index manifest must be an object")
        return value

    @staticmethod
    def _read_list(path: Path, code: str) -> list[object]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise IndexIntegrityError(code, "index JSON cannot be read") from error
        if not isinstance(value, list):
            raise IndexIntegrityError(code, "index JSON must be a list")
        return value

    @staticmethod
    def _validate_vectors(
        vectors: Sequence[object], expected_count: int, *, expected_dimensions: int | None = None
    ) -> None:
        if len(vectors) != expected_count:
            raise IndexIntegrityError("INDEX_VECTOR_COUNT_MISMATCH", "vector count differs from expected documents")
        dimensions = expected_dimensions
        for vector in vectors:
            if not isinstance(vector, list) or not vector:
                raise IndexIntegrityError("INDEX_VECTOR_INVALID", "every vector must be a non-empty list")
            if dimensions is None:
                dimensions = len(vector)
            if len(vector) != dimensions or not all(isinstance(value, (int, float)) and math.isfinite(value) for value in vector):
                raise IndexIntegrityError("INDEX_VECTOR_INVALID", "vectors must have finite matching dimensions")
        if expected_count == 0 and expected_dimensions not in {None, 0}:
            raise IndexIntegrityError("INDEX_VECTOR_INVALID", "empty indexes must have zero dimensions")


def _remove_empty_directory(path: Path) -> None:
    """Best-effort cleanup of an uncommitted temporary artifact directory."""

    for child in path.iterdir():
        if child.is_file():
            child.unlink()
    path.rmdir()
