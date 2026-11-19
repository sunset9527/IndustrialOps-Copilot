"""Central stdout logging with output-stage secret redaction."""

from __future__ import annotations

import logging
import sys

from industrialops.services.error_sanitizer import redact_sensitive_text


class RedactingFormatter(logging.Formatter):
    """Format a copy so handlers never receive an unredacted message string."""

    def format(self, record: logging.LogRecord) -> str:
        safe_record = logging.makeLogRecord(record.__dict__.copy())
        safe_record.msg = redact_sensitive_text(record.getMessage())
        safe_record.args = ()
        return super().format(safe_record)


def configure_logging() -> None:
    """Install one idempotent stdout handler for application-owned loggers."""

    logger = logging.getLogger("industrialops")
    if any(getattr(handler, "_industrialops_redacting", False) for handler in logger.handlers):
        return
    handler = logging.StreamHandler(sys.stdout)
    handler._industrialops_redacting = True  # type: ignore[attr-defined]
    handler.setFormatter(RedactingFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
