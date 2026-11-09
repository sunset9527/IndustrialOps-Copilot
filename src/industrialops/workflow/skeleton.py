"""Build the v0.1 workflow and return its capability boundary."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Literal

from industrialops.services.error_sanitizer import public_error


@dataclass(frozen=True)
class WorkflowEvent:
    name: Literal["workflow_unavailable", "workflow_failed"]
    request_id: str


@dataclass(frozen=True)
class WorkflowState:
    request_id: str
    evidence: tuple[str, ...] = ()
    events: tuple[WorkflowEvent, ...] = ()
    error: dict[str, str] | None = None


@dataclass(frozen=True)
class WorkflowResult:
    status: Literal["unavailable", "error"]
    message: str
    state: WorkflowState


def _unavailable_node(state: WorkflowState) -> WorkflowState:
    event = WorkflowEvent(name="workflow_unavailable", request_id=state.request_id)
    return replace(state, events=(*state.events, event))


class Workflow:
    """Run the v0.1 workflow with independent state for each request."""

    def invoke(self, request: Mapping[str, str]) -> WorkflowResult:
        """Run the placeholder node using the caller's request ID."""

        state = WorkflowState(request_id=request["request_id"])
        try:
            state = _unavailable_node(state)
        except Exception as exc:
            error = public_error(exc, request_id=state.request_id)["error"]
            event = WorkflowEvent(name="workflow_failed", request_id=state.request_id)
            state = replace(state, events=(event,), error=error)
            return WorkflowResult(status="error", message=error["message"], state=state)

        return WorkflowResult(
            status="unavailable",
            message="Industrial diagnosis is unavailable in v0.1.",
            state=state,
        )


def build_workflow() -> Workflow:
    """Construct the runnable workflow."""

    return Workflow()
