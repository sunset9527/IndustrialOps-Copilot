from __future__ import annotations

import pytest

from industrialops.services.task_state import TaskStateError, UploadTask


def test_upload_task_moves_through_the_successful_lifecycle() -> None:
    task = UploadTask.create("upload-1")

    task.start()
    task.complete(result_reference="uploads/manual.pdf")

    assert task.status == "completed"
    assert task.result_reference == "uploads/manual.pdf"
    assert task.error is None


def test_upload_task_cannot_transition_out_of_a_terminal_state() -> None:
    task = UploadTask.create("upload-1")
    task.fail("parse failed")

    with pytest.raises(TaskStateError, match="terminal"):
        task.start()
