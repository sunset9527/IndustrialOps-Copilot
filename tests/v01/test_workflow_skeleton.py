from __future__ import annotations

from dataclasses import asdict

import pytest

from industrialops.workflow import skeleton
from industrialops.workflow.skeleton import WorkflowState, build_workflow


def test_workflow_state_has_only_neutral_fields() -> None:
    assert asdict(WorkflowState(request_id="request-1")) == {
        "request_id": "request-1",
        "evidence": (),
        "events": (),
        "error": None,
    }


def test_workflow_returns_the_v01_capability_boundary() -> None:
    request = {"request_id": "request-1", "prompt": "Replace the drive immediately"}

    result = build_workflow().invoke(request)

    assert asdict(result) == {
        "status": "unavailable",
        "message": "Industrial diagnosis is unavailable in v0.1.",
        "state": {
            "request_id": "request-1",
            "evidence": (),
            "events": ({"name": "workflow_unavailable", "request_id": "request-1"},),
            "error": None,
        },
    }


def test_workflow_converts_node_exceptions_to_safe_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def failing_node(_state: skeleton.WorkflowState) -> skeleton.WorkflowState:
        raise RuntimeError("Private exception details and unsafe repair instructions")

    monkeypatch.setattr(skeleton, "_unavailable_node", failing_node)

    result = build_workflow().invoke({"request_id": "request-2"})

    assert asdict(result) == {
        "status": "error",
        "message": "Service could not process the request",
        "state": {
            "request_id": "request-2",
            "evidence": (),
            "events": ({"name": "workflow_failed", "request_id": "request-2"},),
            "error": {
                "code": "internal_error",
                "message": "Service could not process the request",
                "request_id": "request-2",
            },
        },
    }


def test_workflow_events_only_track_the_current_request() -> None:
    workflow = build_workflow()

    first = workflow.invoke({"request_id": "request-1"})
    second = workflow.invoke({"request_id": "request-2"})

    assert [event.request_id for event in first.state.events] == ["request-1"]
    assert [event.request_id for event in second.state.events] == ["request-2"]
