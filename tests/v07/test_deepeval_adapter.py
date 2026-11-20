from __future__ import annotations

from industrialops.diagnosis.schemas import WorkflowEvent
from industrialops.evaluation.v07.deepeval_adapter import to_trace_spans


def test_deepeval_span_projection_keeps_only_observable_event_fields() -> None:
    spans = to_trace_spans((WorkflowEvent(node="evidence_retriever", status="completed", duration_ms=1.2, input_count=1, output_count=3),))

    assert spans == ({"name": "evidence_retriever", "type": "retriever", "status": "completed", "duration_ms": 1.2, "input_count": 1, "output_count": 3, "reason": None},)
