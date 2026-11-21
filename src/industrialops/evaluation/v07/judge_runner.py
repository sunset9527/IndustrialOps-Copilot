"""Execute approved v0.7 Judge cases and normalize their report records."""
from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
import json
from pathlib import Path

from industrialops.evaluation.v07.scenarios import EvaluationScenario, load_approved_scenarios


@dataclass(frozen=True)
class JudgeObservation:
    """Evidence-bound system output supplied to both semantic judges."""

    question: str
    status: str
    intent: str
    answer: str
    retrieved_contexts: tuple[str, ...]
    reference_contexts: tuple[str, ...]
    citation_count: int
    answer_provider: str
    violation_ids: tuple[str, ...] = ()


JudgeScorer = Callable[[JudgeObservation], float]
DiagnoseScenario = Callable[[EvaluationScenario], JudgeObservation]


def build_pack_scoped_diagnoser(
    *,
    workflow: object,
    model_by_pack: Mapping[str, str],
    evidence_text_by_pack: Mapping[str, Mapping[str, str]],
) -> DiagnoseScenario:
    """Bind approved scenarios to the real diagnosis workflow and frozen evidence."""

    def diagnose(scenario: EvaluationScenario) -> JudgeObservation:
        from industrialops.evaluation.v07.diagnosis_projection import project_diagnosis_hard_gates

        pack_id = scenario.knowledge_pack_version
        model = model_by_pack.get(pack_id)
        if model is None:
            raise ValueError(f"EVALUATION_PACK_MODEL_MISSING:{pack_id}")
        result = workflow.invoke(
            {
                "request_id": f"judge-{scenario.scenario_id}",
                "question": scenario.question,
                "pack_id": pack_id,
                "model": model,
            }
        )
        gate = project_diagnosis_hard_gates(result, requested_pack_id=pack_id)
        evidence = evidence_text_by_pack.get(pack_id, {})
        retrieved_contexts = tuple(
            _require_evidence_text(
                evidence_text_by_pack.get(item.pack_id, {}),
                item.evidence_id,
            )
            for item in result.citations
        )
        reference_contexts = tuple(
            _require_evidence_text(evidence, item.evidence_id) for item in scenario.expected_evidence
        )
        return JudgeObservation(
            question=scenario.question,
            status=result.status,
            intent=result.intent,
            answer=_answer_text(result),
            retrieved_contexts=retrieved_contexts,
            reference_contexts=reference_contexts,
            citation_count=len(result.citations),
            answer_provider=str(result.generation.get("provider", "unknown")),
            violation_ids=gate.violation_ids,
        )

    return diagnose


def _require_evidence_text(evidence: Mapping[str, str], evidence_id: str) -> str:
    text = evidence.get(evidence_id)
    if not text:
        raise ValueError(f"EVALUATION_EVIDENCE_TEXT_MISSING:{evidence_id}")
    return text


def _answer_text(result: object) -> str:
    sections = (
        *result.confirmed_facts,
        *result.candidate_causes,
        *result.inspection_steps,
        *result.safety_prerequisites,
        *result.uncertainties,
        *result.required_information,
        *result.escalation_conditions,
    )
    if result.recommended_next_action:
        sections = (*sections, result.recommended_next_action)
    answer = "\n".join(text.strip() for text in sections if text.strip())
    if not answer:
        raise ValueError("EVALUATION_ANSWER_TEXT_REQUIRED")
    return answer


def run_judge_suite(
    *,
    suite_path: Path,
    diagnose: DiagnoseScenario,
    ragas_score: JudgeScorer,
    deepeval_score: JudgeScorer,
) -> tuple[dict[str, object], ...]:
    """Run diagnosis before scoring every explicitly approved scenario."""

    records = tuple(
        json.loads(line)
        for line in suite_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    scenarios = load_approved_scenarios(records)
    if not scenarios:
        raise ValueError("EVALUATION_APPROVED_SCENARIOS_REQUIRED")
    cases: list[dict[str, object]] = []
    for scenario in scenarios:
        observation = diagnose(scenario)
        status_matches = observation.status == scenario.expected_workflow_state
        intent_matches = observation.intent == scenario.expected_intent
        violation_ids = list(observation.violation_ids)
        if not status_matches:
            violation_ids.append("WORKFLOW_STATUS_MISMATCH")
        if not intent_matches:
            violation_ids.append("INTENT_MISMATCH")
        hard_gate_passed = not violation_ids
        judge_errors: dict[str, str] = {}
        if hard_gate_passed:
            ragas_value = _safe_score(
                ragas_score,
                observation,
                error_code="EVALUATION_RAGAS_JUDGE_FAILED",
                error_key="ragas",
                errors=judge_errors,
            )
            deepeval_value = _safe_score(
                deepeval_score,
                observation,
                error_code="EVALUATION_DEEPEVAL_JUDGE_FAILED",
                error_key="deepeval",
                errors=judge_errors,
            )
            judge_status = "error" if judge_errors else "completed"
            judge_metrics = {
                "ragas_faithfulness": ragas_value,
                "deepeval_faithfulness": deepeval_value,
            }
        else:
            judge_status = "not_run"
            judge_metrics = {
                "ragas_faithfulness": None,
                "deepeval_faithfulness": None,
            }
        cases.append(
            {
                "case_id": scenario.scenario_id,
                "hard_gate_passed": hard_gate_passed,
                "status": observation.status,
                "expected_intent": scenario.expected_intent,
                "actual_intent": observation.intent,
                "violation_ids": violation_ids,
                "judge_status": judge_status,
                "judge_metrics": judge_metrics,
                "answer_provider": observation.answer_provider,
                "citation_count": observation.citation_count,
            }
        )
        if judge_errors:
            cases[-1]["judge_errors"] = judge_errors
    return tuple(cases)


def _safe_score(
    scorer: JudgeScorer,
    observation: JudgeObservation,
    *,
    error_code: str,
    error_key: str,
    errors: dict[str, str],
) -> float | None:
    try:
        return scorer(observation)
    except Exception:
        errors[error_key] = error_code
        return None


def summarize_framework_results(
    cases: Iterable[Mapping[str, object]],
) -> dict[str, str]:
    """Report framework completion without hiding per-case errors or skips."""

    observed = tuple(cases)
    summary: dict[str, str] = {}
    for framework, metric_name in (
        ("ragas", "ragas_faithfulness"),
        ("deepeval", "deepeval_faithfulness"),
    ):
        if any(
            isinstance(case.get("judge_errors"), Mapping)
            and framework in case["judge_errors"]
            for case in observed
        ):
            summary[framework] = "error"
            continue
        completed = any(
            isinstance(case.get("judge_metrics"), Mapping)
            and case["judge_metrics"].get(metric_name) is not None
            for case in observed
        )
        summary[framework] = "completed" if completed else "not_run"
    return summary


def execute_live_judge_suite(
    *,
    project_root: Path,
    suite_path: Path,
    settings: object,
) -> tuple[dict[str, object], ...]:
    """Assemble pack-scoped diagnosis and both real Judge frameworks."""

    if settings.evaluation_judge_provider.casefold() != "deepseek":
        raise ValueError("EVALUATION_JUDGE_PROVIDER_UNSUPPORTED")

    from industrialops.diagnosis.context import EquipmentContextResolver
    from industrialops.diagnosis.deepseek import DeepSeekAnswerGenerator
    from industrialops.diagnosis.runtime import PackScopedEvidenceRetriever
    from industrialops.diagnosis.workflow import DiagnosisWorkflow
    from industrialops.evaluation.v07.deepseek_deepeval import create_deepseek_deepeval_model
    from industrialops.evaluation.v07.deepseek_ragas import create_deepseek_ragas_llm
    from industrialops.evaluation.v07.judge_metrics import (
        score_deepeval_faithfulness,
        score_ragas_faithfulness,
    )
    from industrialops.knowledge.pack_loader import EquipmentPackLoader

    registry_path = _resolve_project_path(project_root, settings.pack_registry_path)
    packs_root = _resolve_project_path(project_root, settings.packs_root)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registered = registry.get("packs")
    if not isinstance(registered, dict) or not registered:
        raise ValueError("EVALUATION_PACK_REGISTRY_INVALID")
    loader = EquipmentPackLoader(packs_root, registry_path)
    packs = {pack_id: loader.load(pack_id) for pack_id in registered}
    model_by_pack = {
        pack_id: str(pack_config["models"][0])
        for pack_id, pack_config in registered.items()
        if isinstance(pack_config, dict)
        and isinstance(pack_config.get("models"), list)
        and pack_config["models"]
    }
    evidence_text_by_pack = {
        pack_id: {item.evidence_id: item.evidence_text for item in pack.structured_evidence}
        for pack_id, pack in packs.items()
    }
    workflow = DiagnosisWorkflow(
        resolver=EquipmentContextResolver.from_registry_path(registry_path),
        retrieve=PackScopedEvidenceRetriever(packs),
        answer_generator=DeepSeekAnswerGenerator.from_settings(
            api_key=None,
            model="evidence-fallback",
            timeout_seconds=1,
            max_tokens=100,
            offline_mode=True,
        ),
    )
    diagnose = build_pack_scoped_diagnoser(
        workflow=workflow,
        model_by_pack=model_by_pack,
        evidence_text_by_pack=evidence_text_by_pack,
    )
    ragas_llm = create_deepseek_ragas_llm(
        base_url=settings.evaluation_judge_base_url,
        api_key=settings.evaluation_judge_api_key,
        model=settings.evaluation_judge_model,
    )
    deepeval_model = create_deepseek_deepeval_model(
        base_url=settings.evaluation_judge_base_url,
        api_key=settings.evaluation_judge_api_key,
        model=settings.evaluation_judge_model,
    )
    return run_judge_suite(
        suite_path=suite_path,
        diagnose=diagnose,
        ragas_score=lambda observation: score_ragas_faithfulness(observation, llm=ragas_llm),
        deepeval_score=lambda observation: score_deepeval_faithfulness(
            observation, model=deepeval_model
        ),
    )


def _resolve_project_path(project_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else project_root / path

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
