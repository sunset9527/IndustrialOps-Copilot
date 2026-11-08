from __future__ import annotations

from industrialops.phase0.structured_candidate_review import (
    generate_review_ledger,
    project_included_candidates,
    review_structured_candidates,
)


def _candidate(**overrides: object) -> dict[str, object]:
    candidate: dict[str, object] = {
        "candidate_id": "candidate-001",
        "candidate_type": "safety_rules",
        "candidate_status": "review_required",
        "pack_id": "dry_vacuum_pump_pack_v1.0.0",
        "label": "lockout_tagout",
        "source_record_id": "source-001",
        "source_id": "EDW-NXDS-MANUAL-EN-L",
        "source_file": "manual.pdf",
        "source_sha256": "a" * 64,
        "page_number": 12,
        "evidence_locator": "EDW-NXDS-MANUAL-EN-L:p.12",
        "evidence_text": "WARNING: Lock out electrical power before inspecting the pump.",
        "text_zh": "警告：检查泵前锁定电源。",
        "extraction_reason": "matched explicit safety_rules pattern: lock out",
    }
    candidate.update(overrides)
    return candidate


def test_includes_explicit_in_scope_candidate_with_complete_evidence() -> None:
    decision = review_structured_candidates([_candidate()])[0]

    assert decision["decision"] == "include"
    assert decision["candidate_id"] == "candidate-001"
    assert decision["evidence_locator"] == "EDW-NXDS-MANUAL-EN-L:p.12"


def test_holds_candidate_with_out_of_scope_option_marker() -> None:
    decision = review_structured_candidates([_candidate(evidence_text="Use the SMTC arm procedure.")])[0]

    assert decision["decision"] == "not_retrievable"
    assert "SMTC" in decision["decision_rationale"]


def test_excludes_navigation_only_candidate() -> None:
    decision = review_structured_candidates(
        [_candidate(candidate_type="components", label="spindle", evidence_text="Table of Contents\nSpindle ........ 12")]
    )[0]

    assert decision["decision"] == "exclude"


def test_review_is_deterministic_and_covers_every_candidate_once() -> None:
    candidates = [_candidate(), _candidate(candidate_id="candidate-002", label="inspection", candidate_type="maintenance_tasks")]

    first = review_structured_candidates(candidates)
    second = review_structured_candidates(candidates)

    assert first == second
    assert [decision["candidate_id"] for decision in first] == ["candidate-001", "candidate-002"]
    assert len({decision["decision_id"] for decision in first}) == 2


def test_generate_review_ledger_writes_every_decision_and_manifest(tmp_path) -> None:
    import json

    input_path = tmp_path / "candidates.jsonl"
    input_path.write_text(json.dumps(_candidate(), ensure_ascii=False) + "\n", encoding="utf-8")

    manifest = generate_review_ledger(input_path, tmp_path / "review")

    assert manifest["total_candidates"] == 1
    assert manifest["decision_counts"] == {"include": 1}
    assert (tmp_path / "review" / "structured_candidate_decision_ledger_v1.jsonl").is_file()
    assert (tmp_path / "review" / "structured_candidate_review_manifest_v1.json").is_file()


def test_project_included_candidates_keeps_only_include_decisions() -> None:
    included = _candidate()
    held = _candidate(candidate_id="candidate-002", evidence_text="Use the SMTC arm procedure.")
    decisions = review_structured_candidates([included, held])

    projected = project_included_candidates([included, held], decisions)

    assert len(projected) == 1
    assert projected[0]["candidate_id"] == "candidate-001"
    assert projected[0]["candidate_status"] == "auto_reviewed_include"
    assert projected[0]["review_decision_id"] == decisions[0]["decision_id"]
