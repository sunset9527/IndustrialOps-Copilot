"""Checks that IndustrialOps remains independent from its source project at runtime."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


HERITAGEMIND_REPOSITORY = "https://github.com/sunset9527/HeritageMind"
HERITAGEMIND_BASELINE = "1edc5c4"
_INVENTORY_PATH = Path("docs/migration/heritagemind-v01-migration-inventory.json")
_RUNTIME_DIRECTORIES = (Path("src"), Path("api"))


def load_migration_inventory(project_root: Path) -> dict[str, Any]:
    """Load the versioned record that identifies the source-project baseline."""

    with (project_root / _INVENTORY_PATH).open(encoding="utf-8") as stream:
        return json.load(stream)


def find_forbidden_runtime_references(
    project_root: Path,
    *,
    forbidden_references: tuple[str, ...],
) -> list[dict[str, object]]:
    """Return forbidden textual references from executable source directories only."""

    findings: list[dict[str, object]] = []
    for runtime_directory in _RUNTIME_DIRECTORIES:
        directory = project_root / runtime_directory
        if not directory.exists():
            continue
        for path in sorted(candidate for candidate in directory.rglob("*") if candidate.is_file()):
            if path.suffix in {".pyc", ".pyo"} or "__pycache__" in path.parts:
                continue
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                for reference in forbidden_references:
                    if reference.casefold() in line.casefold():
                        findings.append(
                            {
                                "path": path.relative_to(project_root).as_posix(),
                                "line": line_number,
                                "reference": reference,
                            }
                        )
    return findings
