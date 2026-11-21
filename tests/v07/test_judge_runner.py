from __future__ import annotations

import json

from industrialops.diagnosis.schemas import Citation, DiagnosisResult
from industrialops.evaluation.v07 import judge_runner
from industrialops.evaluation.v07.judge_runner import load_judge_case_results
from industrialops.evaluation.v07.scenarios import EvaluationScenario, EvidenceExpectation


def test_loads_completed_metrics(tmp_path):
    p = tmp_path / "r.json"
    p.write_text(
        json.dumps(
            {
                "metrics": [
                    {
                        "scenario_id": "s",
                        "status": "answered",
                        "ragas_faithfulness": 1.0,
                        "deepeval_faithfulness": 0.9,
                    }
                ]
            }
        ),
        encoding="utf8",
    )
    assert load_judge_case_results(p)[0]["hard_gate_passed"] is True


def test_judge_suite_runs_diagnosis_and_both_frameworks_from_approved_scenarios(tmp_path) -> None:
    suite = tmp_path / "approved.jsonl"
    suite.write_text(
        json.dumps(
            {
                "scenario_id": "v07-cnc-manual-001",
                "suite_version": "v07-approved-v1",
                "knowledge_pack_version": "cnc_pack_v1.0.0",
                "question": "查询 VF-2 冷却液资料。",
                "expected_intent": "manual_query",
                "expected_workflow_state": "answered",
                "expected_evidence": [
                    {
                        "evidence_id": "e-1",
                        "source_id": "HAAS-FLOOD-COOLANT-ZH",
                        "page_number": 3,
                        "document_revision": "snapshot-2026-11-04",
                    }
                ],
                "evidence_review_status": "approved",
                "evidence_reviewed_by": "reviewer-a",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    calls: list[tuple[str, str]] = []

    def diagnose(scenario):
        calls.append(("diagnose", scenario.scenario_id))
        return judge_runner.JudgeObservation(
            question=scenario.question,
            status="answered",
            intent="manual_query",
            answer="请检查冷却液液位。",
            retrieved_contexts=("冷却液液位应在允许范围内。",),
            reference_contexts=("冷却液液位应在允许范围内。",),
            citation_count=1,
            answer_provider="evidence_fallback",
        )

    def ragas_score(observation):
        calls.append(("ragas", observation.answer))
        return 1.0

    def deepeval_score(observation):
        calls.append(("deepeval", observation.answer))
        return 0.875

    cases = judge_runner.run_judge_suite(
        suite_path=suite,
        diagnose=diagnose,
        ragas_score=ragas_score,
        deepeval_score=deepeval_score,
    )

    assert calls == [
        ("diagnose", "v07-cnc-manual-001"),
        ("ragas", "请检查冷却液液位。"),
        ("deepeval", "请检查冷却液液位。"),
    ]
    assert cases == (
        {
            "case_id": "v07-cnc-manual-001",
            "hard_gate_passed": True,
            "status": "answered",
            "expected_intent": "manual_query",
            "actual_intent": "manual_query",
            "violation_ids": [],
            "judge_status": "completed",
            "judge_metrics": {
                "ragas_faithfulness": 1.0,
                "deepeval_faithfulness": 0.875,
            },
            "answer_provider": "evidence_fallback",
            "citation_count": 1,
        },
    )


def test_pack_scoped_diagnoser_uses_system_result_and_resolves_retrieved_and_reference_evidence() -> None:
    captured: dict[str, object] = {}

    class Workflow:
        def invoke(self, request):
            captured.update(request)
            return DiagnosisResult(
                request_id=request["request_id"],
                status="answered",
                intent="alarm_lookup",
                confirmed_facts=("报警 552 与断路器有关。",),
                citations=(
                    Citation(
                        evidence_id="retrieved-1",
                        pack_id="cnc_pack_v1.0.0",
                        source_id="source-1",
                        document_revision="rev-1",
                        page_number=12,
                        evidence_locator="source-1#page=12",
                    ),
                ),
                generation={"provider": "evidence_fallback"},
                workflow_trace=("intent_router", "answer_composer"),
            )

    scenario = EvaluationScenario(
        scenario_id="alarm-552",
        suite_version="v07-approved-v1",
        knowledge_pack_version="cnc_pack_v1.0.0",
        question="VF-2 报警 552 代表什么？",
        expected_intent="alarm_lookup",
        expected_workflow_state="answered",
        expected_evidence=(EvidenceExpectation("reference-1", "source-1", 12, "rev-1"),),
        evidence_reviewed_by="reviewer-a",
    )
    diagnose = judge_runner.build_pack_scoped_diagnoser(
        workflow=Workflow(),
        model_by_pack={"cnc_pack_v1.0.0": "VF-2"},
        evidence_text_by_pack={
            "cnc_pack_v1.0.0": {
                "retrieved-1": "断路器证据。",
                "reference-1": "人工审核绑定的断路器证据。",
            }
        },
    )

    observation = diagnose(scenario)

    assert captured["pack_id"] == "cnc_pack_v1.0.0"
    assert captured["model"] == "VF-2"
    assert observation.answer == "报警 552 与断路器有关。"
    assert observation.question == "VF-2 报警 552 代表什么？"
    assert observation.retrieved_contexts == ("断路器证据。",)
    assert observation.reference_contexts == ("人工审核绑定的断路器证据。",)
    assert observation.citation_count == 1
    assert observation.answer_provider == "evidence_fallback"


def test_judge_suite_does_not_call_semantic_judges_when_a_hard_gate_fails(tmp_path) -> None:
    suite = tmp_path / "approved.jsonl"
    suite.write_text(
        json.dumps(
            {
                "scenario_id": "v07-cnc-manual-002",
                "suite_version": "v07-approved-v1",
                "knowledge_pack_version": "cnc_pack_v1.0.0",
                "question": "查询 VF-2 冷却液资料。",
                "expected_intent": "manual_query",
                "expected_workflow_state": "answered",
                "expected_evidence": [
                    {
                        "evidence_id": "e-1",
                        "source_id": "HAAS-FLOOD-COOLANT-ZH",
                        "page_number": 3,
                        "document_revision": "snapshot-2026-11-04",
                    }
                ],
                "evidence_review_status": "approved",
                "evidence_reviewed_by": "reviewer-a",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    def diagnose(scenario):
        return judge_runner.JudgeObservation(
            question=scenario.question,
            status="insufficient_evidence",
            intent="manual_query",
            answer="现有证据不足。",
            retrieved_contexts=(),
            reference_contexts=("人工审核参考证据。",),
            citation_count=0,
            answer_provider="evidence_fallback",
        )

    def must_not_run(_):
        raise AssertionError("semantic Judge must not run after a hard-gate failure")

    cases = judge_runner.run_judge_suite(
        suite_path=suite,
        diagnose=diagnose,
        ragas_score=must_not_run,
        deepeval_score=must_not_run,
    )

    assert cases[0]["hard_gate_passed"] is False
    assert cases[0]["violation_ids"] == ["WORKFLOW_STATUS_MISMATCH"]
    assert cases[0]["judge_status"] == "not_run"
    assert cases[0]["judge_metrics"] == {
        "ragas_faithfulness": None,
        "deepeval_faithfulness": None,
    }


def test_judge_suite_records_one_framework_error_without_losing_the_other_result(tmp_path) -> None:
    suite = tmp_path / "approved.jsonl"
    suite.write_text(
        json.dumps(
            {
                "scenario_id": "v07-cnc-alarm-001",
                "suite_version": "v07-approved-v1",
                "knowledge_pack_version": "cnc_pack_v1.0.0",
                "question": "VF-2 报警 552 代表什么？",
                "expected_intent": "alarm_lookup",
                "expected_workflow_state": "answered",
                "expected_evidence": [
                    {
                        "evidence_id": "e-1",
                        "source_id": "HAAS-NGC-BREAKER-ZH",
                        "page_number": 12,
                        "document_revision": "snapshot-2026-11-04",
                    }
                ],
                "evidence_review_status": "approved",
                "evidence_reviewed_by": "reviewer-a",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    def diagnose(scenario):
        return judge_runner.JudgeObservation(
            question=scenario.question,
            status="answered",
            intent="alarm_lookup",
            answer="报警 552 与断路器有关。",
            retrieved_contexts=("断路器证据。",),
            reference_contexts=("断路器证据。",),
            citation_count=1,
            answer_provider="evidence_fallback",
        )

    def failed_ragas(_):
        raise RuntimeError("private upstream detail")

    cases = judge_runner.run_judge_suite(
        suite_path=suite,
        diagnose=diagnose,
        ragas_score=failed_ragas,
        deepeval_score=lambda _: 0.8,
    )

    assert cases[0]["hard_gate_passed"] is True
    assert cases[0]["judge_status"] == "error"
    assert cases[0]["judge_metrics"] == {
        "ragas_faithfulness": None,
        "deepeval_faithfulness": 0.8,
    }
    assert cases[0]["judge_errors"] == {
        "ragas": "EVALUATION_RAGAS_JUDGE_FAILED"
    }
    assert "private upstream detail" not in repr(cases[0])


def test_framework_summary_does_not_report_a_failed_judge_as_completed() -> None:
    summary = judge_runner.summarize_framework_results(
        (
            {
                "judge_status": "error",
                "judge_metrics": {
                    "ragas_faithfulness": None,
                    "deepeval_faithfulness": 0.8,
                },
                "judge_errors": {"ragas": "EVALUATION_RAGAS_JUDGE_FAILED"},
            },
            {
                "judge_status": "not_run",
                "judge_metrics": {
                    "ragas_faithfulness": None,
                    "deepeval_faithfulness": None,
                },
            },
        )
    )

    assert summary == {"ragas": "error", "deepeval": "completed"}


def test_judge_suite_respects_deterministic_isolation_violations(tmp_path) -> None:
    suite = tmp_path / "approved.jsonl"
    suite.write_text(
        json.dumps(
            {
                "scenario_id": "v07-cnc-isolation-001",
                "suite_version": "v07-approved-v1",
                "knowledge_pack_version": "cnc_pack_v1.0.0",
                "question": "查询 VF-2 手册。",
                "expected_intent": "manual_query",
                "expected_workflow_state": "answered",
                "expected_evidence": [
                    {
                        "evidence_id": "e-1",
                        "source_id": "HAAS-FLOOD-COOLANT-ZH",
                        "page_number": 3,
                        "document_revision": "snapshot-2026-11-04",
                    }
                ],
                "evidence_review_status": "approved",
                "evidence_reviewed_by": "reviewer-a",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    def diagnose(scenario):
        return judge_runner.JudgeObservation(
            question=scenario.question,
            status="answered",
            intent="manual_query",
            answer="错误串包回答。",
            retrieved_contexts=("错误证据。",),
            reference_contexts=("正确证据。",),
            citation_count=1,
            answer_provider="evidence_fallback",
            violation_ids=("PACK_CONTAMINATION",),
        )

    cases = judge_runner.run_judge_suite(
        suite_path=suite,
        diagnose=diagnose,
        ragas_score=lambda _: (_ for _ in ()).throw(AssertionError("must not run")),
        deepeval_score=lambda _: (_ for _ in ()).throw(AssertionError("must not run")),
    )

    assert cases[0]["hard_gate_passed"] is False
    assert cases[0]["violation_ids"] == ["PACK_CONTAMINATION"]
    assert cases[0]["judge_status"] == "not_run"


def test_pack_scoped_diagnoser_preserves_cross_pack_citation_for_the_hard_gate() -> None:
    class Workflow:
        def invoke(self, request):
            return DiagnosisResult(
                request_id=request["request_id"],
                status="answered",
                intent="manual_query",
                confirmed_facts=("错误串包回答。",),
                citations=(
                    Citation(
                        evidence_id="pump-evidence",
                        pack_id="dry_vacuum_pump_pack_v1.0.0",
                        source_id="EDW-NXDS-MANUAL-EN-L",
                        document_revision="A73501880-L",
                        page_number=12,
                        evidence_locator="EDW-NXDS-MANUAL-EN-L#page=12",
                    ),
                ),
                generation={"provider": "evidence_fallback"},
                workflow_trace=("intent_router", "answer_composer"),
            )

    scenario = EvaluationScenario(
        scenario_id="cnc-cross-pack",
        suite_version="v07-approved-v1",
        knowledge_pack_version="cnc_pack_v1.0.0",
        question="查询 VF-2 手册。",
        expected_intent="manual_query",
        expected_workflow_state="answered",
        expected_evidence=(EvidenceExpectation("cnc-reference", "HAAS-VF2-SCOPE-ZH", 1, "rev"),),
        evidence_reviewed_by="reviewer-a",
    )
    diagnose = judge_runner.build_pack_scoped_diagnoser(
        workflow=Workflow(),
        model_by_pack={"cnc_pack_v1.0.0": "VF-2"},
        evidence_text_by_pack={
            "cnc_pack_v1.0.0": {"cnc-reference": "CNC 参考证据。"},
            "dry_vacuum_pump_pack_v1.0.0": {"pump-evidence": "错误泵证据。"},
        },
    )

    observation = diagnose(scenario)

    assert observation.retrieved_contexts == ("错误泵证据。",)
    assert observation.violation_ids == ("PACK_CONTAMINATION",)
