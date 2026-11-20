"""Command-line deterministic v0.7 guardrail baseline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from industrialops.diagnosis.context import EquipmentContextResolver
from industrialops.diagnosis.deepseek import DeepSeekAnswerGenerator
from industrialops.diagnosis.workflow import DiagnosisWorkflow
from industrialops.evaluation.v07.diagnosis_projection import project_diagnosis_hard_gates
from industrialops.evaluation.v07.runner import run_deterministic_evaluation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output-root", type=Path, default=Path("data/evaluation/reports/v07"))
    args = parser.parse_args()
    root = args.project_root.resolve()
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
    run_deterministic_evaluation(output_root=(root / args.output_root), run_id=args.run_id, frozen_inputs=(root / "data/evaluation/scenario_eval_v1.jsonl", root / "data/evaluation/guardrail_eval_v1.jsonl"), case_results=cases)


if __name__ == "__main__":
    main()
