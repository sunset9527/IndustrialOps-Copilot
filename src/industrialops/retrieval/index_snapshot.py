"""Immutable metadata for a declared retrieval-index input set."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from collections.abc import Iterable


@dataclass(frozen=True)
class IndexSnapshot:
    version: str
    document_ids: tuple[str, ...]
    content_sha256: str


def build_index_snapshot(version: str, document_ids: Iterable[str]) -> IndexSnapshot:
    """Build deterministic snapshot metadata without building an index."""

    ordered_ids = tuple(sorted(set(document_ids)))
    content = json.dumps({"version": version, "document_ids": ordered_ids}, separators=(",", ":"))
    return IndexSnapshot(
        version=version,
        document_ids=ordered_ids,
        content_sha256=hashlib.sha256(content.encode("utf-8")).hexdigest(),
    )
