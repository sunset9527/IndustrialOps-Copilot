from __future__ import annotations

import logging

from industrialops.logging_config import RedactingFormatter


def test_log_formatter_redacts_credentials_tokens_and_windows_paths() -> None:
    formatter = RedactingFormatter("%(levelname)s %(message)s")
    record = logging.LogRecord(
        "industrialops", logging.ERROR, __file__, 1,
        "database=mysql+pymysql://operator:secret@localhost/ops Authorization: Bearer abc.def path=E:\\private\\pack", (), None,
    )

    rendered = formatter.format(record)

    assert "secret" not in rendered
    assert "abc.def" not in rendered
    assert "E:\\private" not in rendered
    assert "[REDACTED_DATABASE_URL]" in rendered
    assert "[REDACTED_TOKEN]" in rendered
    assert "[REDACTED_PATH]" in rendered
