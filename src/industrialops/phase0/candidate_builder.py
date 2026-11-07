"""Build traceable, review-required candidates from extracted source pages."""

from __future__ import annotations

import hashlib


def build_candidates(page_records: list[dict[str, object]]) -> list[dict[str, object]]:
    """Create one review candidate per usable page without making it indexable."""
    candidates: list[dict[str, object]] = []
    for page in page_records:
        if page["text_extraction_status"] != "extracted":
            continue
        source_file = str(page["source_file"])
        if "/90_reference_only/" in source_file:
            continue

        evidence_locator = str(page["evidence_locator"])
        source_hash = str(page["source_sha256"])
        candidate_id = hashlib.sha256(f"{evidence_locator}:{source_hash}".encode()).hexdigest()[:24]
        candidates.append(
            {
                "candidate_id": candidate_id,
                "pack_id": page["pack_id"],
                "source_id": page["source_id"],
                "source_file": source_file,
                "source_sha256": source_hash,
                "language": page["language"],
                "page_number": page["page_number"],
                "text": page["text"],
                "evidence_locator": evidence_locator,
                "applicability": "review_required",
            }
        )
    return candidates
