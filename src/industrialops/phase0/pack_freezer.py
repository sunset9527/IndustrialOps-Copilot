"""Build deterministic, local-only manifests for frozen Phase 0 knowledge packs."""

from __future__ import annotations

import hashlib
import json


_PACKS = ("cnc_pack_v1.0.0", "dry_vacuum_pump_pack_v1.0.0")


def build_pack_manifests(sources: list[dict[str, object]], corpus: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    """Verify corpus provenance and return deterministic per-pack freeze manifests."""
    source_by_id = {str(source["source_id"]): source for source in sources}
    manifests: dict[str, dict[str, object]] = {}
    for pack_id in _PACKS:
        records = [record for record in corpus if record.get("pack_id") == pack_id]
        if not records:
            raise ValueError(f"pack has no corpus records: {pack_id}")
        source_ids = sorted({str(record["source_id"]) for record in records})
        missing = [source_id for source_id in source_ids if source_id not in source_by_id]
        if missing:
            raise ValueError(f"corpus source missing from registry: {', '.join(missing)}")
        source_summary = [
            {
                "source_id": source_id,
                "sha256": source_by_id[source_id]["sha256"],
                "relative_path": source_by_id[source_id]["relative_path"],
                "url": source_by_id[source_id]["url"],
                "rights_boundary": source_by_id[source_id].get("rights_boundary", "local_evidence_only"),
            }
            for source_id in source_ids
        ]
        manifests[pack_id] = {
            "pack_id": pack_id,
            "freeze_status": "read_only_local_evidence",
            "rights_boundary": "local_evidence_only",
            "corpus_record_count": len(records),
            "source_count": len(source_summary),
            "sources": source_summary,
            "content_sha256": _canonical_hash(records),
        }
    return manifests


def _canonical_hash(records: list[dict[str, object]]) -> str:
    payload = "\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) for record in records)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
