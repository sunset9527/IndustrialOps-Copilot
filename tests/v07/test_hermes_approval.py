from __future__ import annotations

import json

from industrialops.evaluation.v07.hermes_approval import build_owner_approved_suite
from industrialops.evaluation.v07.scenarios import load_approved_scenarios


def test_hermes_approval_promotes_only_evidence_bound_candidates(tmp_path) -> None:
    candidates = tmp_path / "candidates.jsonl"
    packets = tmp_path / "packets.jsonl"
    output = tmp_path / "owner-approved.jsonl"
    candidates.write_text(
        "\n".join(
            (
                json.dumps(_candidate("bound")),
                json.dumps(_candidate("unbound")),
            )
        ),
        encoding="utf-8",
    )
    packets.write_text(
        "\n".join(
            (
                json.dumps({"scenario_id": "bound", "evidence_anchors": [_anchor()]}),
                json.dumps({"scenario_id": "unbound", "evidence_anchors": []}),
            )
        ),
        encoding="utf-8",
    )

    summary = build_owner_approved_suite(
        candidates_path=candidates,
        packets_path=packets,
        output_path=output,
        reviewer_id="project-owner:test",
    )

    records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert summary.approved_scenario_ids == ("bound",)
    assert summary.excluded_scenario_ids == ("unbound",)
    assert records[0]["evidence_review_status"] == "approved"
    assert records[0]["evidence_reviewed_by"] == "project-owner:test"
    assert records[0]["review_method"] == "machine_assisted_owner_approval"
    assert load_approved_scenarios(records)[0].expected_evidence[0].page_number == 7


def _candidate(scenario_id: str) -> dict[str, object]:
    return {
        "scenario_id": scenario_id,
        "suite_version": "v1",
        "knowledge_pack_version": "pack-v1",
        "question": "test question",
        "expected_intent": "alarm_lookup",
        "expected_workflow_state": "answered",
        "evidence_review_status": "candidate",
        "expected_evidence": [],
    }


def _anchor() -> dict[str, object]:
    return {
        "evidence_id": "evidence-1",
        "source_id": "manual-1",
        "page_number": 7,
        "document_revision": "rev-a",
    }
