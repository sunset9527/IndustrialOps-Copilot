"""Synchronous upload-processing adapter used before queue integration."""

from __future__ import annotations

from pathlib import Path

from industrialops.services.document_parser import DocumentParseError, ParsedDocument, parse_document
from industrialops.services.task_state import UploadTask


def process_uploaded_document(task: UploadTask, path: Path) -> ParsedDocument | None:
    """Parse one uploaded document and reflect the result in its task state."""

    task.start()
    try:
        parsed = parse_document(path)
    except DocumentParseError:
        task.fail("document_parse_failed")
        return None
    task.complete(result_reference=str(path))
    return parsed
