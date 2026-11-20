"""Framework-neutral construction of audited Ragas single-turn rows."""

from __future__ import annotations

from collections.abc import Iterable


def to_ragas_row(
    *,
    scenario_id: str,
    question: str,
    response: str,
    retrieved_contexts: Iterable[str],
    reference_contexts: Iterable[str],
    reference: str,
    pack_id: str,
    evidence_ids: Iterable[str],
) -> dict[str, object]:
    """Map only already-reviewed evidence into Ragas-compatible field names."""

    return {
        "user_input": question,
        "response": response,
        "retrieved_contexts": list(retrieved_contexts),
        "reference_contexts": list(reference_contexts),
        "reference": reference,
        "metadata": {"scenario_id": scenario_id, "pack_id": pack_id, "evidence_ids": list(evidence_ids)},
    }
