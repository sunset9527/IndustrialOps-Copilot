"""Public, stable request and response schemas for diagnosis."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DiagnosisRequest(BaseModel):
    """Explicit device context supplied by an API caller."""

    question: str = Field(min_length=1, max_length=8000)
    pack_id: str = Field(min_length=1)
    asset_id: str | None = None
    model: str | None = None
    controller: str | None = None
    document_revision: str | None = None


class Citation(BaseModel):
    evidence_id: str
    pack_id: str
    source_id: str
    document_revision: str
    page_number: int
    evidence_locator: str


class WorkflowEvent(BaseModel):
    """Observable workflow metadata; deliberately excludes prompts and evidence text."""

    node: str
    status: str
    duration_ms: float = Field(ge=0)
    input_count: int = Field(ge=0)
    output_count: int = Field(ge=0)
    reason: str | None = None


class DiagnosisResult(BaseModel):
    request_id: str
    status: str
    intent: str
    confirmed_facts: tuple[str, ...] = ()
    candidate_causes: tuple[str, ...] = ()
    inspection_steps: tuple[str, ...] = ()
    safety_prerequisites: tuple[str, ...] = ()
    uncertainties: tuple[str, ...] = ()
    required_information: tuple[str, ...] = ()
    escalation_conditions: tuple[str, ...] = ()
    recommended_next_action: str | None = None
    citations: tuple[Citation, ...] = ()
    generation: dict[str, object]
    workflow_trace: tuple[str, ...]
    workflow_events: tuple[WorkflowEvent, ...] = ()
