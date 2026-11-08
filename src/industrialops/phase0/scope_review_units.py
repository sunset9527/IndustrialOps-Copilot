"""Create the smallest auditable units for scope decisions."""

from __future__ import annotations

from industrialops.phase0.candidate_segmenter import segment_candidate


_EVIDENCE_FIELDS = (
    "source_id",
    "source_sha256",
    "source_file",
    "page_number",
    "evidence_locator",
    "text",
)

_OPTIONAL_EVIDENCE_FIELDS = ("pack_id", "language")


def _unit(
    unit_id: str,
    parent_candidate_id: str,
    record: dict[str, object],
    review_reason: str,
    priority: str,
) -> dict[str, object]:
    return {
        "unit_id": unit_id,
        "parent_candidate_id": parent_candidate_id,
        **{field: record[field] for field in _EVIDENCE_FIELDS},
        **{field: record[field] for field in _OPTIONAL_EVIDENCE_FIELDS if field in record},
        "review_reason": review_reason,
        "priority": priority,
    }


def build_scope_review_units(
    records: list[dict[str, object]],
    max_characters: int,
) -> list[dict[str, object]]:
    """Use chunks for mixed pages and whole pages for broad manual decisions."""
    units: list[dict[str, object]] = []
    for record in records:
        candidate_id = str(record["candidate_id"])
        if record["applicability"] == "mixed_scope_review":
            for segment in segment_candidate(record, max_characters):
                units.append(
                    _unit(
                        str(segment["chunk_id"]),
                        candidate_id,
                        segment,
                        "mixed_scope_requires_chunk_decision",
                        "high",
                    )
                )
        elif record["applicability"] == "review_required":
            units.append(
                _unit(
                    candidate_id,
                    candidate_id,
                    record,
                    "broad_manual_requires_page_decision",
                    "normal",
                )
            )
    return units


def build_scope_review_units_from_segments(
    segments: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Turn only unresolved classified segments into review units."""
    units: list[dict[str, object]] = []
    for segment in segments:
        applicability = segment["applicability"]
        if applicability == "mixed_scope_review":
            review_reason = "mixed_scope_requires_chunk_decision"
            priority = "high"
        elif applicability == "review_required":
            review_reason = "broad_manual_requires_chunk_decision"
            priority = "normal"
        else:
            continue
        units.append(
            _unit(
                str(segment["chunk_id"]),
                str(segment["parent_candidate_id"]),
                segment,
                review_reason,
                priority,
            )
        )
    return units
