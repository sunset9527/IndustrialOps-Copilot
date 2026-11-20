"""Project diagnosis outputs into deterministic v0.7 release gates."""

from __future__ import annotations

from industrialops.diagnosis.schemas import DiagnosisResult
from industrialops.evaluation.v07.deterministic_gate import HardGateOutcome, evaluate_hard_gates


def project_diagnosis_hard_gates(result: DiagnosisResult, *, requested_pack_id: str) -> HardGateOutcome:
    """Reject cross-pack citations and any actionable leakage after a block."""

    return evaluate_hard_gates(
        requested_pack_id=requested_pack_id,
        citation_pack_ids=tuple(citation.pack_id for citation in result.citations),
        unsafe_instruction_leaked=result.status == "blocked" and bool(result.inspection_steps),
        work_order_executed_before_approval=False,
    )
