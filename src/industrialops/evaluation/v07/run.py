"""Command-line entry point for v0.7 deterministic, smoke, and Judge profiles."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from industrialops.diagnosis.context import EquipmentContextResolver
from industrialops.diagnosis.deepseek import DeepSeekAnswerGenerator
from industrialops.diagnosis.workflow import DiagnosisWorkflow
from industrialops.evaluation.v07.diagnosis_projection import project_diagnosis_hard_gates
from industrialops.evaluation.v07.deepeval_adapter import to_trace_spans
from industrialops.evaluation.v07.framework_smoke import build_deepeval_trace_case, build_ragas_dataset
from industrialops.evaluation.v07.frameworks import framework_availability
from industrialops.evaluation.v07.judge_environment import load_judge_settings
from industrialops.evaluation.v07.judge_runner import (
    execute_live_judge_suite,
    load_judge_case_results,
    summarize_framework_results,
)
from industrialops.evaluation.v07.ragas_adapter import to_ragas_row
from industrialops.evaluation.v07.runner import run_deterministic_evaluation
from industrialops.diagnosis.schemas import WorkflowEvent


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output-root", type=Path, default=Path("data/evaluation/reports/v07"))
    parser.add_argument("--profile", choices=("deterministic", "framework-smoke", "judge"), default="deterministic")
    parser.add_argument("--judge-env-file", type=Path, default=None)
    parser.add_argument("--judge-metrics-file", type=Path, default=None)
    parser.add_argument("--judge-suite-file", type=Path, default=None)
    parser.add_argument("--before-run-id", default=None)
    args = parser.parse_args(argv)
    root = args.project_root.resolve()
    frozen_inputs = (root / "data/evaluation/scenario_eval_v1.jsonl", root / "data/evaluation/guardrail_eval_v1.jsonl")
    if args.profile == "framework-smoke":
        cases, results = framework_smoke_cases()
        run_deterministic_evaluation(
            output_root=root / args.output_root,
            run_id=args.run_id,
            frozen_inputs=frozen_inputs,
            case_results=cases,
            profile="framework-smoke",
            framework_results=results,
            before_run_id=args.before_run_id,
        )
        return
    if args.profile == "judge":
        settings = load_explicit_judge_configuration(args.judge_env_file)
        if args.judge_suite_file is not None:
            case_results = execute_live_judge_suite(
                project_root=root,
                suite_path=args.judge_suite_file,
                settings=settings,
            )
        elif args.judge_metrics_file is not None:
            case_results = load_judge_case_results(args.judge_metrics_file)
        else:
            raise SystemExit("EVALUATION_JUDGE_SUITE_FILE_REQUIRED")
        framework_results: dict[str, object] = summarize_framework_results(case_results)
        framework_results["judge"] = {
            "provider": settings.evaluation_judge_provider,
            "model": settings.evaluation_judge_model,
            "temperature": 0,
            "thinking": "disabled",
        }
        run_deterministic_evaluation(
            output_root=root / args.output_root,
            run_id=args.run_id,
            frozen_inputs=frozen_inputs,
            case_results=case_results,
            profile="judge",
            framework_results=framework_results,
            before_run_id=args.before_run_id,
        )
        return
    workflow = DiagnosisWorkflow(
        resolver=EquipmentContextResolver.from_registry_path(root / "config/equipment_pack_registry_v1.json"),
        retrieve=lambda request, context, route: (),
        answer_generator=DeepSeekAnswerGenerator.from_settings(api_key=None, model="deepseek-flash", timeout_seconds=1, max_tokens=100),
    )
    cases = []
    for line in (root / "data/evaluation/guardrail_eval_v1.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        case = json.loads(line)
        pack_id = str(case["expected_pack_id"])
        result = workflow.invoke({"request_id": str(case["eval_id"]), "question": case["prompt"], "pack_id": pack_id, "model": "VF-2" if pack_id.startswith("cnc_") else "nXDS15i"})
        expected = {"refuse": "blocked", "escalate": "blocked", "insufficient_evidence": "insufficient_evidence"}[str(case["expected_outcome"])]
        gate = project_diagnosis_hard_gates(result, requested_pack_id=pack_id)
        cases.append({"case_id": case["eval_id"], "expected_status": expected, "actual_status": result.status, "hard_gate_passed": gate.passed and result.status == expected, "violation_ids": gate.violation_ids})
    run_deterministic_evaluation(
        output_root=(root / args.output_root),
        run_id=args.run_id,
        frozen_inputs=frozen_inputs,
        case_results=cases,
        before_run_id=args.before_run_id,
    )


def load_explicit_judge_configuration(path: Path | None):
    """Load the private file only for an explicitly requested Judge profile."""

    if path is None:
        raise ValueError("EVALUATION_JUDGE_ENV_FILE_REQUIRED")
    return load_judge_settings(path)


def framework_smoke_cases() -> tuple[tuple[dict[str, object], ...], dict[str, dict[str, object]]]:
    """Run real optional SDK object construction without a network Judge."""

    availabilities = {name: framework_availability(name) for name in ("ragas", "deepeval")}
    results = {name: asdict(result) for name, result in availabilities.items()}
    row = to_ragas_row(
        scenario_id="framework-smoke-public-fixture",
        question="公开夹具问题",
        response="公开夹具响应",
        retrieved_contexts=("approved fixture context",),
        reference_contexts=("reviewed fixture context",),
        reference="reviewed fixture reference",
        pack_id="public_fixture_pack",
        evidence_ids=("fixture-evidence-1",),
    )
    spans = to_trace_spans((
        WorkflowEvent(node="intent_router", status="completed", duration_ms=0.1, input_count=1, output_count=1),
        WorkflowEvent(node="answer_composer", status="answered", duration_ms=0.1, input_count=1, output_count=1),
    ))
    cases: list[dict[str, object]] = []
    for name, available in availabilities.items():
        status = available.status
        error_code = available.error_code
        if status == "available":
            try:
                if name == "ragas":
                    build_ragas_dataset((row,))
                else:
                    build_deepeval_trace_case(scenario_id="framework-smoke-public-fixture", spans=spans)
            except Exception:
                status = "error"
                error_code = "EVALUATION_FRAMEWORK_SMOKE_FAILED"
        results[name]["status"] = status
        results[name]["error_code"] = error_code
        cases.append(
            {
                "case_id": f"framework-{name}",
                "hard_gate_passed": True,
                "status": "completed" if status == "available" else "not_run" if status == "framework_unavailable" else "error",
                "reason": error_code,
            }
        )
    return tuple(cases), results


if __name__ == "__main__":
    main()
