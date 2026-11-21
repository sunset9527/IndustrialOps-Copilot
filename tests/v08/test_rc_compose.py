from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from industrialops.evaluation.v08.compose import (
    RcComposeError,
    build_cleanup_command,
    build_compose_command,
    build_rc_environment,
)
from industrialops.evaluation.v08.core import create_rc_run


ROOT = Path(__file__).resolve().parents[2]


def test_rc_compose_commands_are_scoped_to_the_unique_run_and_use_no_cache_build(tmp_path: Path) -> None:
    run = create_rc_run(tmp_path, "20261121-compose")

    command = build_compose_command(run, ROOT / "docker-compose.yml", "build")

    assert command == (
        "docker",
        "compose",
        "--project-name",
        "industrialops_rc_20261121_compose",
        "--file",
        str(ROOT / "docker-compose.yml"),
        "build",
        "--no-cache",
    )
    assert command[3] != "industrialops"
    assert command[3].startswith("industrialops_rc_")


def test_rc_environment_overrides_only_rc_project_and_host_ports(tmp_path: Path) -> None:
    run = create_rc_run(tmp_path, "20261121-env")

    environment = build_rc_environment(
        run,
        {"INDUSTRIALOPS_DB_PASSWORD": "private", "INDUSTRIALOPS_API_PORT": "8100"},
        api_port=18100,
        frontend_port=15174,
    )

    assert environment["INDUSTRIALOPS_DB_PASSWORD"] == "private"
    assert environment["COMPOSE_PROJECT_NAME"] == "industrialops_rc_20261121_env"
    assert environment["INDUSTRIALOPS_API_PORT"] == "18100"
    assert environment["INDUSTRIALOPS_FRONTEND_PORT"] == "15174"


def test_rc_cleanup_requires_explicit_confirmation_and_targets_only_its_project(tmp_path: Path) -> None:
    run = create_rc_run(tmp_path, "20261121-cleanup")

    with pytest.raises(RcComposeError, match="RC_CLEANUP_CONFIRMATION_REQUIRED"):
        build_cleanup_command(run, ROOT / "docker-compose.yml", confirmed=False)

    command = build_cleanup_command(run, ROOT / "docker-compose.yml", confirmed=True)
    assert command[-3:] == ("down", "--volumes", "--remove-orphans")
    assert command[3] == run.compose_project


def test_base_compose_allows_isolated_host_port_overrides_while_preserving_defaults() -> None:
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))

    assert compose["services"]["api"]["ports"] == ["127.0.0.1:${INDUSTRIALOPS_API_PORT:-8100}:8100"]
    assert compose["services"]["web"]["ports"] == ["127.0.0.1:${INDUSTRIALOPS_FRONTEND_PORT:-5174}:80"]
