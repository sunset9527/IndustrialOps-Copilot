from __future__ import annotations

from industrialops.diagnosis.schemas import DiagnosisResult
from industrialops.diagnosis.response import diagnosis_json_response


def test_diagnosis_response_declares_utf8_for_powershell_clients() -> None:
    response = diagnosis_json_response(
        DiagnosisResult(
            request_id="request-1",
            status="answered",
            intent="fault_diagnosis",
            candidate_causes=("真空泵异常噪声",),
            generation={"provider": "deepseek", "fallback_used": False},
            workflow_trace=("answer_composer",),
        )
    )

    assert response.headers["content-type"] == "application/json; charset=utf-8"
    assert "真空泵异常噪声".encode("utf-8") in response.body
