"""Normalize completed v0.7 Judge metrics for the unified report writer."""
from __future__ import annotations
import json
from pathlib import Path

def load_judge_case_results(path: Path) -> tuple[dict[str, object], ...]:
    report = json.loads(path.read_text(encoding="utf-8"))
    metrics = report.get("metrics")
    if not isinstance(metrics, list) or not metrics:
        raise ValueError("EVALUATION_JUDGE_METRICS_REQUIRED")
    cases = []
    for item in metrics:
        if not isinstance(item, dict) or not isinstance(item.get("scenario_id"), str):
            raise ValueError("EVALUATION_JUDGE_METRICS_INVALID")
        cases.append({"case_id": item["scenario_id"], "hard_gate_passed": item.get("status") == "answered", "judge_metrics": {key: item.get(key) for key in ("ragas_faithfulness", "deepeval_faithfulness")}, "answer_provider": item.get("answer_provider", "evidence_fallback"), "citation_count": item.get("citation_count", 0)})
    return tuple(cases)
