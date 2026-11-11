"""HTTP response helpers for the diagnosis API."""

from __future__ import annotations

from fastapi.responses import JSONResponse

from industrialops.diagnosis.schemas import DiagnosisResult


def diagnosis_json_response(result: DiagnosisResult) -> JSONResponse:
    """Serialize a diagnosis result with an explicit UTF-8 media type.

    Windows PowerShell 5.1 can otherwise decode application/json responses that
    omit a charset using the active ANSI code page, corrupting Chinese fields.
    """

    return JSONResponse(
        content=result.model_dump(mode="json"),
        media_type="application/json; charset=utf-8",
    )
