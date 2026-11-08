from __future__ import annotations

import json
from pathlib import Path

from industrialops.migration_audit import (
    HERITAGEMIND_BASELINE,
    HERITAGEMIND_REPOSITORY,
    find_forbidden_runtime_references,
    load_migration_inventory,
)


def test_inventory_records_the_fixed_heritagemind_source_baseline() -> None:
    project_root = Path(__file__).parents[2]

    inventory = load_migration_inventory(project_root)

    assert inventory["source_repository"] == HERITAGEMIND_REPOSITORY
    assert inventory["source_commit"] == HERITAGEMIND_BASELINE
    assert inventory["source_commit"] == "1edc5c4"
    assert inventory["strategy"] == "selective_migration"
    assert inventory["excluded_runtime_capabilities"] == [
        "knowledge_graph",
        "graph_agent",
        "heritage_domain_features",
    ]


def test_runtime_scan_reports_only_forbidden_references_in_runtime_paths(tmp_path: Path) -> None:
    runtime_file = tmp_path / "src" / "industrialops" / "service.py"
    runtime_file.parent.mkdir(parents=True)
    runtime_file.write_text(
        "SOURCE_ROOT = 'E:/python/LLM/IntangibleCulturalHeritage_MultiAgent'\n",
        encoding="utf-8",
    )
    documentation = tmp_path / "docs" / "migration.md"
    documentation.parent.mkdir()
    documentation.write_text(
        "HeritageMind is the source project.\n",
        encoding="utf-8",
    )

    findings = find_forbidden_runtime_references(
        tmp_path,
        forbidden_references=("IntangibleCulturalHeritage_MultiAgent", "heritagemind"),
    )

    assert findings == [
        {
            "path": "src/industrialops/service.py",
            "line": 1,
            "reference": "IntangibleCulturalHeritage_MultiAgent",
        }
    ]


def test_project_runtime_has_no_heritagemind_directory_reference() -> None:
    project_root = Path(__file__).parents[2]

    findings = find_forbidden_runtime_references(
        project_root,
        forbidden_references=("IntangibleCulturalHeritage_MultiAgent",),
    )

    assert findings == []


def test_inventory_is_valid_json_with_no_undocumented_fields() -> None:
    project_root = Path(__file__).parents[2]
    inventory_path = project_root / "docs" / "migration" / "heritagemind-v01-migration-inventory.json"

    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))

    assert set(inventory) == {
        "source_repository",
        "source_commit",
        "strategy",
        "migrated_capabilities",
        "excluded_runtime_capabilities",
        "notes",
    }
