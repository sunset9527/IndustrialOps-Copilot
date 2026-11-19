from __future__ import annotations

import pytest

from industrialops.bootstrap import BootstrapError, run_bootstrap_steps


def test_bootstrap_runs_every_explicit_step_once_in_delivery_order() -> None:
    calls: list[str] = []
    results = run_bootstrap_steps({
        "preflight": lambda: calls.append("preflight") or "configuration checked",
        "migration": lambda: calls.append("migration") or "database migrated",
        "seed": lambda: calls.append("seed") or "synthetic assets seeded",
        "knowledge_packs": lambda: calls.append("knowledge_packs") or "packs verified",
        "indexes": lambda: calls.append("indexes") or "indexes prepared",
    })

    assert calls == ["preflight", "migration", "seed", "knowledge_packs", "indexes"]
    assert results == [
        {"step": "preflight", "status": "completed", "detail": "configuration checked"},
        {"step": "migration", "status": "completed", "detail": "database migrated"},
        {"step": "seed", "status": "completed", "detail": "synthetic assets seeded"},
        {"step": "knowledge_packs", "status": "completed", "detail": "packs verified"},
        {"step": "indexes", "status": "completed", "detail": "indexes prepared"},
    ]


def test_bootstrap_stops_at_the_first_failure_without_running_later_steps() -> None:
    calls: list[str] = []

    with pytest.raises(BootstrapError, match="DATABASE_MIGRATION_FAILED"):
        run_bootstrap_steps({
            "preflight": lambda: calls.append("preflight") or "configuration checked",
            "migration": lambda: calls.append("migration") or (_ for _ in ()).throw(RuntimeError("migration failed")),
            "seed": lambda: calls.append("seed") or "must not run",
        })

    assert calls == ["preflight", "migration"]
