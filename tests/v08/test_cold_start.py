from __future__ import annotations

import json
from pathlib import Path

from industrialops.evaluation.v08.cold_start import CommandResult, execute_cold_start
from industrialops.evaluation.v08.core import create_rc_run


def test_cold_start_records_no_cache_build_and_detached_start_as_append_only_events(tmp_path: Path) -> None:
    run = create_rc_run(tmp_path, "20261121-cold-start")
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text("services: {}\n", encoding="utf-8")
    calls: list[tuple[str, ...]] = []
    clock_values = iter((0.0, 0.25, 0.25, 0.75))

    result = execute_cold_start(
        run=run,
        compose_file=compose_file,
        environment={"INDUSTRIALOPS_DB_PASSWORD": "private"},
        invoke=lambda command, _: calls.append(command) or CommandResult(0, "completed", ""),
        monotonic=lambda: next(clock_values),
    )

    assert result.status == "passed"
    assert [command[-2:] for command in calls] == [("build", "--no-cache"), ("up", "--detach")]
    assert result.steps == (
        {"stage": "cold_start.build", "status": "passed", "duration_ms": 250.0},
        {"stage": "cold_start.up", "status": "passed", "duration_ms": 500.0},
    )
    events = [json.loads(line) for line in (run.report_directory / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert events == list(result.steps)


def test_cold_start_stops_after_failed_build_and_redacts_partial_diagnostics(tmp_path: Path) -> None:
    run = create_rc_run(tmp_path, "20261121-cold-failure")
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text("services: {}\n", encoding="utf-8")
    calls: list[tuple[str, ...]] = []
    clock_values = iter((0.0, 0.5))

    result = execute_cold_start(
        run=run,
        compose_file=compose_file,
        environment={},
        invoke=lambda command, _: calls.append(command) or CommandResult(1, "", "Bearer private-build-token"),
        monotonic=lambda: next(clock_values),
    )

    assert result.status == "failed"
    assert result.steps == (
        {
            "stage": "cold_start.build",
            "status": "failed",
            "reason_code": "RC_COLD_START_BUILD_FAILED",
            "duration_ms": 500.0,
            "diagnostic": "[REDACTED_TOKEN]",
        },
    )
    assert len(calls) == 1
