"""Contracts for separately versioned, human-reviewed v0.7 scenarios."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable, Mapping


class ScenarioContractError(ValueError):
    """A scenario cannot enter an official v0.7 metric denominator."""


@dataclass(frozen=True)
class EvidenceExpectation:
    evidence_id: str
    source_id: str
    page_number: int
    document_revision: str


@dataclass(frozen=True)
class EvaluationScenario:
    scenario_id: str
    suite_version: str
    knowledge_pack_version: str
    question: str
    expected_intent: str
    expected_workflow_state: str
    expected_evidence: tuple[EvidenceExpectation, ...]
    evidence_reviewed_by: str


_REQUIRED_FIELDS = (
    "scenario_id",
    "suite_version",
    "knowledge_pack_version",
    "question",
    "expected_intent",
    "expected_workflow_state",
    "evidence_review_status",
)


def load_approved_scenarios(records: Iterable[Mapping[str, object]]) -> tuple[EvaluationScenario, ...]:
    """Load only reviewed scenarios; candidate data is retained but never scored."""

    approved: list[EvaluationScenario] = []
    for record in records:
        missing = tuple(field for field in _REQUIRED_FIELDS if not isinstance(record.get(field), str) or not record[field])
        if missing:
            raise ScenarioContractError(f"SCENARIO_REQUIRED_FIELD_MISSING: {','.join(missing)}")
        status = record["evidence_review_status"]
        if status != "approved":
            continue
        reviewer = record.get("evidence_reviewed_by")
        if not isinstance(reviewer, str) or not reviewer:
            raise ScenarioContractError("SCENARIO_REVIEWER_REQUIRED")
        raw_evidence = record.get("expected_evidence")
        if not isinstance(raw_evidence, list):
            raise ScenarioContractError("SCENARIO_EXPECTED_EVIDENCE_REQUIRED")
        evidence = tuple(_load_evidence(item) for item in raw_evidence)
        approved.append(
            EvaluationScenario(
                scenario_id=str(record["scenario_id"]),
                suite_version=str(record["suite_version"]),
                knowledge_pack_version=str(record["knowledge_pack_version"]),
                question=str(record["question"]),
                expected_intent=str(record["expected_intent"]),
                expected_workflow_state=str(record["expected_workflow_state"]),
                expected_evidence=evidence,
                evidence_reviewed_by=reviewer,
            )
        )
    return tuple(approved)


def _load_evidence(value: object) -> EvidenceExpectation:
    if not isinstance(value, Mapping):
        raise ScenarioContractError("SCENARIO_EVIDENCE_SCHEMA_INVALID")
    revision = value.get("document_revision")
    if not isinstance(revision, str) or not revision:
        raise ScenarioContractError("SCENARIO_EVIDENCE_REVISION_REQUIRED")
    evidence_id, source_id, page_number = value.get("evidence_id"), value.get("source_id"), value.get("page_number")
    if not isinstance(evidence_id, str) or not evidence_id or not isinstance(source_id, str) or not source_id:
        raise ScenarioContractError("SCENARIO_EVIDENCE_LOCATOR_INVALID")
    if not isinstance(page_number, int) or page_number < 1:
        raise ScenarioContractError("SCENARIO_EVIDENCE_PAGE_REQUIRED")
    return EvidenceExpectation(evidence_id, source_id, page_number, revision)
