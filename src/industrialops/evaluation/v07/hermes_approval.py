"""Create an explicitly labelled owner-approved suite from Hermes packets."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class HermesApprovalSummary:
    approved_scenario_ids: tuple[str, ...]
    excluded_scenario_ids: tuple[str, ...]


def build_owner_approved_suite(
    *,
    candidates_path: Path,
    packets_path: Path,
    output_path: Path,
    reviewer_id: str,
) -> HermesApprovalSummary:
    """Write an append-only suite from candidates with complete Hermes anchors.

    This records a project-owner, machine-assisted decision.  It is not a
    substitute for two independent human labels, so callers must not infer a
    Kappa result from this suite.
    """

    if output_path.exists():
        raise FileExistsError("EVALUATION_HERMES_APPROVED_SUITE_EXISTS")
    if not reviewer_id.strip():
        raise ValueError("EVALUATION_HERMES_OWNER_REVIEWER_REQUIRED")

    packets_by_id = _records_by_scenario_id(packets_path)
    approved_records: list[dict[str, object]] = []
    approved_ids: list[str] = []
    excluded_ids: list[str] = []
    for candidate in _records(candidates_path):
        scenario_id = _scenario_id(candidate)
        packet = packets_by_id.get(scenario_id)
        anchors = packet.get("evidence_anchors") if packet else None
        evidence = _complete_evidence(anchors)
        if not evidence:
            excluded_ids.append(scenario_id)
            continue
        approved_record = dict(candidate)
        approved_record.update(
            {
                "expected_evidence": evidence,
                "evidence_review_status": "approved",
                "evidence_reviewed_by": reviewer_id.strip(),
                "review_method": "machine_assisted_owner_approval",
                "review_source": "hermes_review_packet",
            }
        )
        approved_records.append(approved_record)
        approved_ids.append(scenario_id)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in approved_records),
        encoding="utf-8",
    )
    return HermesApprovalSummary(tuple(approved_ids), tuple(excluded_ids))


def _records(path: Path) -> tuple[dict[str, object], ...]:
    return tuple(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def _records_by_scenario_id(path: Path) -> dict[str, dict[str, object]]:
    records: dict[str, dict[str, object]] = {}
    for record in _records(path):
        scenario_id = _scenario_id(record)
        if scenario_id in records:
            raise ValueError("EVALUATION_HERMES_DUPLICATE_SCENARIO")
        records[scenario_id] = record
    return records


def _scenario_id(record: dict[str, object]) -> str:
    scenario_id = record.get("scenario_id")
    if not isinstance(scenario_id, str) or not scenario_id.strip():
        raise ValueError("EVALUATION_HERMES_SCENARIO_ID_REQUIRED")
    return scenario_id


def _complete_evidence(anchors: object) -> list[dict[str, object]]:
    if not isinstance(anchors, list):
        return []
    evidence: list[dict[str, object]] = []
    for anchor in anchors:
        if not isinstance(anchor, dict):
            continue
        evidence_id = anchor.get("evidence_id")
        source_id = anchor.get("source_id")
        page_number = anchor.get("page_number")
        document_revision = anchor.get("document_revision")
        if not (
            isinstance(evidence_id, str)
            and evidence_id
            and isinstance(source_id, str)
            and source_id
            and isinstance(page_number, int)
            and page_number >= 1
            and isinstance(document_revision, str)
            and document_revision
        ):
            continue
        evidence.append(
            {
                "evidence_id": evidence_id,
                "source_id": source_id,
                "page_number": page_number,
                "document_revision": document_revision,
            }
        )
    return evidence
