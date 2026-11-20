from __future__ import annotations

import pytest

from industrialops.diagnosis.schemas import WorkflowEvent
from industrialops.evaluation.v07.deepeval_adapter import to_trace_spans
from industrialops.evaluation.v07.framework_smoke import build_deepeval_trace_case, build_ragas_dataset
from industrialops.evaluation.v07.ragas_adapter import to_ragas_row


def test_framework_smoke_builds_real_ragas_and_deepeval_objects_without_a_judge() -> None:
    pytest.importorskip("ragas")
    pytest.importorskip("deepeval")
    row = to_ragas_row(
        scenario_id="v07-framework-smoke",
        question="检查冷却液报警。",
        response="请按已引用手册执行检查。",
        retrieved_contexts=("approved excerpt",),
        reference_contexts=("reviewed excerpt",),
        reference="经人工审核的参考要点",
        pack_id="cnc_pack_v1.0.0",
        evidence_ids=("e-1",),
    )
    spans = to_trace_spans((WorkflowEvent(node="evidence_retriever", status="completed", duration_ms=1.2, input_count=1, output_count=1),))

    dataset = build_ragas_dataset((row,))
    trace_case = build_deepeval_trace_case(scenario_id="v07-framework-smoke", spans=spans)

    assert len(dataset.samples) == 1
    assert dataset.samples[0].user_input == "检查冷却液报警。"
    assert trace_case.metadata == {"scenario_id": "v07-framework-smoke", "spans": list(spans)}
