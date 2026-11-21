"""CLI entry point for the safe, staged v0.8 release-candidate acceptance run."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
import os
from pathlib import Path
import socket

from industrialops.evaluation.v08.cold_start import execute_cold_start, invoke_subprocess
from industrialops.evaluation.v08.compose import build_rc_environment
from industrialops.evaluation.v08.core import append_event, create_rc_run, write_report_atomically
from industrialops.evaluation.v08.preflight import run_preflight


def load_effective_environment(environment_file: Path, process_environment: Mapping[str, str]) -> dict[str, str]:
    """Read simple dotenv assignments while giving explicit process settings precedence."""

    environment: dict[str, str] = {}
    if environment_file.is_file():
        for raw_line in environment_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key:
                environment[key] = value
    environment.update(process_environment)
    return environment


def port_available(port: int) -> bool:
    """Return whether the local loopback port can be bound without starting a service."""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def main(arguments: list[str] | None = None) -> int:
    """Execute the selected safe RC phase and persist a final sanitized report."""

    parser = argparse.ArgumentParser(description="IndustrialOps v0.8 release-candidate acceptance")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--phase", choices=("preflight", "cold-start"), default="preflight")
    parser.add_argument("--api-port", type=int)
    parser.add_argument("--frontend-port", type=int)
    parsed = parser.parse_args(arguments)

    root = parsed.project_root.resolve()
    environment = load_effective_environment(parsed.env_file or root / ".env", os.environ)
    if parsed.api_port is not None:
        environment["INDUSTRIALOPS_API_PORT"] = str(parsed.api_port)
    if parsed.frontend_port is not None:
        environment["INDUSTRIALOPS_FRONTEND_PORT"] = str(parsed.frontend_port)
    run = create_rc_run(root / "data" / "evaluation" / "reports" / "v08", parsed.run_id)
    preflight = run_preflight(
        environment=environment,
        required_documents=(root / "README.md", root / "THIRD_PARTY_NOTICES.md", root / "docs" / "architecture.md"),
        port_available=port_available,
    )
    append_event(run, {"stage": "preflight", **preflight.as_dict()})
    report: dict[str, object] = {
        "format_version": 1,
        "run_id": run.run_id,
        "compose_project": run.compose_project,
        "phase": parsed.phase,
        "preflight": preflight.as_dict(),
    }
    if not preflight.ready:
        report["overall_status"] = "failed"
        write_report_atomically(run, report)
        return 1
    if parsed.phase == "preflight":
        report["overall_status"] = "passed"
        write_report_atomically(run, report)
        return 0

    api_port = parsed.api_port or int(environment.get("INDUSTRIALOPS_API_PORT", "8100"))
    frontend_port = parsed.frontend_port or int(environment.get("INDUSTRIALOPS_FRONTEND_PORT", "5174"))
    rc_environment = build_rc_environment(run, environment, api_port=api_port, frontend_port=frontend_port)
    cold_start = execute_cold_start(
        run=run,
        compose_file=root / "docker-compose.yml",
        environment=rc_environment,
        invoke=invoke_subprocess,
    )
    report["cold_start"] = {"status": cold_start.status, "steps": list(cold_start.steps)}
    report["overall_status"] = cold_start.status
    write_report_atomically(run, report)
    return 0 if cold_start.status == "passed" else 1


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
