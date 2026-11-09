from __future__ import annotations

from pathlib import Path

from industrialops.services.task_state import UploadTask
from industrialops.workers.upload_worker import process_uploaded_document


def test_worker_marks_task_completed_after_parsing_an_uploaded_document(tmp_path: Path) -> None:
    source = tmp_path / "manual.txt"
    source.write_text("Check lubrication.", encoding="utf-8")
    task = UploadTask.create("upload-1")

    parsed = process_uploaded_document(task, source)

    assert parsed.text == "Check lubrication."
    assert task.status == "completed"
    assert task.result_reference == str(source)


def test_worker_marks_task_failed_when_parsing_fails(tmp_path: Path) -> None:
    source = tmp_path / "manual.exe"
    source.write_bytes(b"unsupported")
    task = UploadTask.create("upload-1")

    result = process_uploaded_document(task, source)

    assert result is None
    assert task.status == "failed"
    assert task.error == "document_parse_failed"
