"""Lazy availability checks for optional third-party evaluation frameworks."""

from __future__ import annotations

from dataclasses import dataclass
import importlib


@dataclass(frozen=True)
class FrameworkAvailability:
    framework: str
    status: str
    version: str | None
    error_code: str | None


def framework_availability(module_name: str) -> FrameworkAvailability:
    """Probe a framework lazily so default API imports never require it."""

    try:
        module = importlib.import_module(module_name)
    except Exception:
        return FrameworkAvailability(module_name, "framework_unavailable", None, "EVALUATION_FRAMEWORK_IMPORT_FAILED")
    return FrameworkAvailability(module_name, "available", str(getattr(module, "__version__", "unknown")), None)
