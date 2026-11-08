from __future__ import annotations

from industrialops.services.error_sanitizer import public_error, redact_sensitive_text


def test_redact_sensitive_text_removes_database_tokens_and_paths() -> None:
    value = (
        "database=mysql+pymysql://operator:secret@localhost:3306/industrialops "
        "Authorization: Bearer abc.def.ghi path=E:\\private\\manual.pdf"
    )

    redacted = redact_sensitive_text(value)

    assert "operator:secret" not in redacted
    assert "abc.def.ghi" not in redacted
    assert "E:\\private" not in redacted
    assert "[REDACTED_DATABASE_URL]" in redacted
    assert "[REDACTED_TOKEN]" in redacted
    assert "[REDACTED_PATH]" in redacted


def test_public_error_never_echoes_the_original_exception() -> None:
    payload = public_error(
        RuntimeError("mysql+pymysql://operator:secret@localhost:3306/industrialops"),
        request_id="request-123",
    )

    assert payload == {
        "error": {
            "code": "internal_error",
            "message": "Service could not process the request",
            "request_id": "request-123",
        }
    }
