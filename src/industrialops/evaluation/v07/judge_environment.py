"""Strict, non-logging loader for a private v0.7 Judge environment file."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from industrialops.config import Settings


class JudgeEnvironmentError(ValueError):
    """The private Judge configuration is invalid without exposing its values."""


_ALLOWED_KEYS = frozenset(
    {
        "INDUSTRIALOPS_EVALUATION_PROFILE",
        "INDUSTRIALOPS_EVALUATION_JUDGE_ENABLED",
        "INDUSTRIALOPS_EVALUATION_JUDGE_PROVIDER",
        "INDUSTRIALOPS_EVALUATION_JUDGE_BASE_URL",
        "INDUSTRIALOPS_EVALUATION_JUDGE_MODEL",
        "INDUSTRIALOPS_EVALUATION_JUDGE_API_KEY",
    }
)


def load_judge_environment(path: Path) -> Mapping[str, str]:
    """Load only explicit Judge keys; errors identify a line, never a secret."""

    if not path.is_file():
        raise JudgeEnvironmentError("EVALUATION_JUDGE_ENV_FILE_NOT_FOUND")

    environment: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise JudgeEnvironmentError(f"EVALUATION_JUDGE_ENV_INVALID_LINE:{line_number}")
        key, value = (part.strip() for part in line.split("=", maxsplit=1))
        key = key.removeprefix("$env:")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"\"", "'"}:
            value = value[1:-1]
        if key not in _ALLOWED_KEYS:
            raise JudgeEnvironmentError(f"EVALUATION_JUDGE_ENV_UNSUPPORTED_KEY:{line_number}")
        if key in environment:
            raise JudgeEnvironmentError(f"EVALUATION_JUDGE_ENV_DUPLICATE_KEY:{line_number}")
        environment[key] = value
    return environment


def load_judge_settings(path: Path) -> Settings:
    """Validate a private Judge file through the ordinary Settings contract."""

    return Settings.from_environment(load_judge_environment(path))
