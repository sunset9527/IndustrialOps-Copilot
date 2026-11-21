"""Observable, fail-closed execution of the isolated RC Compose cold-start steps."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
import subprocess
import time

from industrialops.evaluation.v08.compose import build_compose_command
from industrialops.evaluation.v08.core import RcRun, append_event
from industrialops.services.error_sanitizer import redact_sensitive_text


@dataclass(frozen=True)
class CommandResult:
    """The bounded, text-only outcome of one external command."""

    return_code: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class ColdStartResult:
    """Cold-start stage evidence, including partial evidence after a failed build."""

    status: str
    steps: tuple[dict[str, object], ...]


def execute_cold_start(
    *,
    run: RcRun,
    compose_file: Path,
    environment: Mapping[str, str],
    invoke: Callable[[tuple[str, ...], Mapping[str, str]], CommandResult],
    monotonic: Callable[[], float] = time.monotonic,
) -> ColdStartResult:
    """Build without cache, start detached, and stop immediately after any failed command."""

    steps: list[dict[str, object]] = []
    for action, reason_code in (("build", "RC_COLD_START_BUILD_FAILED"), ("up", "RC_COLD_START_UP_FAILED")):
        started = monotonic()
        command = build_compose_command(run, compose_file, action)
        result = invoke(command, environment)
        duration_ms = (monotonic() - started) * 1000
        if result.return_code:
            step = {
                "stage": f"cold_start.{action}",
                "status": "failed",
                "reason_code": reason_code,
                "duration_ms": duration_ms,
                "diagnostic": redact_sensitive_text(result.stderr or result.stdout, max_length=10_000),
            }
            append_event(run, step)
            return ColdStartResult("failed", tuple((*steps, step)))
        step = {"stage": f"cold_start.{action}", "status": "passed", "duration_ms": duration_ms}
        append_event(run, step)
        steps.append(step)
    return ColdStartResult("passed", tuple(steps))


def invoke_subprocess(command: tuple[str, ...], environment: Mapping[str, str]) -> CommandResult:
    """Run one pre-built command without shell interpolation or inherited output streams."""

    completed = subprocess.run(command, capture_output=True, check=False, text=True, env=dict(environment))
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)
