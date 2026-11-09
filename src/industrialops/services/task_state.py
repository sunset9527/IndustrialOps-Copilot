"""In-memory state contract for upload processing tasks."""

from __future__ import annotations

from dataclasses import dataclass


class TaskStateError(ValueError):
    """Raised when a task lifecycle transition is invalid."""


@dataclass
class UploadTask:
    """A task state object that later queue and persistence adapters can share."""

    task_id: str
    status: str = "pending"
    result_reference: str | None = None
    error: str | None = None

    @classmethod
    def create(cls, task_id: str) -> "UploadTask":
        return cls(task_id=task_id)

    def start(self) -> None:
        self._transition("running", allowed_from={"pending"})

    def complete(self, *, result_reference: str) -> None:
        self._transition("completed", allowed_from={"running"})
        self.result_reference = result_reference

    def fail(self, error: str) -> None:
        self._transition("failed", allowed_from={"pending", "running"})
        self.error = error

    def _transition(self, target: str, *, allowed_from: set[str]) -> None:
        if self.status in {"completed", "failed"}:
            raise TaskStateError("Task is already in a terminal state")
        if self.status not in allowed_from:
            raise TaskStateError(f"Cannot transition from {self.status} to {target}")
        self.status = target
