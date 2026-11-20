from __future__ import annotations

import pytest

from industrialops.evaluation.v07.scenarios import ScenarioContractError, load_approved_scenarios


def test_approved_content_scenario_requires_reviewed_evidence_locator() -> None:
    record = {
        "scenario_id": "v07-cnc-manual-001",
        "suite_version": "v07-candidate-v1",
        "knowledge_pack_version": "cnc_pack_v1.0.0",
        "question": "查询 VF-2 的冷却液资料",
        "expected_intent": "manual_query",
        "expected_workflow_state": "answered",
        "evidence_review_status": "approved",
        "evidence_reviewed_by": "reviewer-a",
        "expected_evidence": [{"evidence_id": "e-1", "source_id": "HAAS-TEST", "page_number": 3}],
    }

    with pytest.raises(ScenarioContractError, match="SCENARIO_EVIDENCE_REVISION_REQUIRED"):
        load_approved_scenarios((record,))


def test_unreviewed_candidate_is_excluded_from_official_metric_denominator() -> None:
    candidate = {
        "scenario_id": "v07-cnc-candidate-001",
        "suite_version": "v07-candidate-v1",
        "knowledge_pack_version": "cnc_pack_v1.0.0",
        "question": "查询 VF-2 的冷却液资料",
        "expected_intent": "manual_query",
        "expected_workflow_state": "answered",
        "evidence_review_status": "candidate",
        "expected_evidence": [],
    }

    assert load_approved_scenarios((candidate,)) == ()


def test_approved_scenario_exposes_a_complete_evidence_locator() -> None:
    approved = {
        "scenario_id": "v07-cnc-manual-002",
        "suite_version": "v07-approved-v1",
        "knowledge_pack_version": "cnc_pack_v1.0.0",
        "question": "查询 VF-2 的冷却液资料",
        "expected_intent": "manual_query",
        "expected_workflow_state": "answered",
        "evidence_review_status": "approved",
        "evidence_reviewed_by": "reviewer-a",
        "expected_evidence": [
            {
                "evidence_id": "e-1",
                "source_id": "HAAS-TEST",
                "page_number": 3,
                "document_revision": "2025",
            }
        ],
    }

    scenarios = load_approved_scenarios((approved,))

    assert scenarios[0].scenario_id == "v07-cnc-manual-002"
    assert scenarios[0].expected_evidence[0].document_revision == "2025"
