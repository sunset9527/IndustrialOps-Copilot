"""Safe command construction for isolated, operator-controlled RC Compose runs."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from industrialops.evaluation.v08.core import RcRun


class RcComposeError(ValueError):
    """An RC Compose operation would be ambiguous or unsafe."""


def build_rc_environment(
    run: RcRun,
    base_environment: Mapping[str, str],
    *,
    api_port: int,
    frontend_port: int,
) -> dict[str, str]:
    """Copy runtime settings while scoping only project identity and published ports."""

    if not 1 <= api_port <= 65535 or not 1 <= frontend_port <= 65535:
        raise RcComposeError("RC_COMPOSE_PORT_INVALID")
    environment = dict(base_environment)
    environment.update(
        {
            "COMPOSE_PROJECT_NAME": run.compose_project,
            "INDUSTRIALOPS_API_PORT": str(api_port),
            "INDUSTRIALOPS_FRONTEND_PORT": str(frontend_port),
        }
    )
    return environment


def build_compose_command(run: RcRun, compose_file: Path, action: str) -> tuple[str, ...]:
    """Construct a non-destructive Compose command scoped to exactly one RC run."""

    base = _command_prefix(run, compose_file)
    if action == "build":
        return (*base, "build", "--no-cache")
    if action == "up":
        return (*base, "up", "--detach")
    if action == "ps":
        return (*base, "ps", "--format", "json")
    if action == "logs":
        return (*base, "logs", "--no-color")
    raise RcComposeError("RC_COMPOSE_ACTION_INVALID")


def build_cleanup_command(run: RcRun, compose_file: Path, *, confirmed: bool) -> tuple[str, ...]:
    """Require an explicit operator decision before generating a volume-removal command."""

    if not confirmed:
        raise RcComposeError("RC_CLEANUP_CONFIRMATION_REQUIRED")
    return (*_command_prefix(run, compose_file), "down", "--volumes", "--remove-orphans")


def _command_prefix(run: RcRun, compose_file: Path) -> tuple[str, ...]:
    if run.compose_project == "industrialops" or not compose_file.is_file():
        raise RcComposeError("RC_COMPOSE_SCOPE_INVALID")
    return ("docker", "compose", "--project-name", run.compose_project, "--file", str(compose_file))
