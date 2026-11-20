"""Append-only filesystem storage for v0.7 evaluation runs."""

from __future__ import annotations

from pathlib import Path


class RunStoreError(ValueError):
    """A requested run operation would break evaluation history."""


def create_run_directory(output_root: Path, run_id: str) -> Path:
    """Create a fresh run directory and reject accidental report replacement."""

    destination = output_root / run_id
    if destination.exists():
        raise RunStoreError(f"EVALUATION_RUN_ALREADY_EXISTS: {run_id}")
    destination.mkdir(parents=True)
    return destination
