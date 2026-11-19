from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def test_compose_defines_the_complete_local_delivery_stack_with_bootstrap_gate() -> None:
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))

    assert set(compose["services"]) == {"db", "bootstrap", "api", "web"}
    assert "ports" not in compose["services"]["db"]
    assert compose["services"]["api"]["depends_on"]["bootstrap"]["condition"] == "service_completed_successfully"
    assert compose["services"]["web"]["depends_on"]["api"]["condition"] == "service_healthy"
    assert compose["services"]["api"]["ports"] == ["127.0.0.1:8100:8100"]
    assert compose["services"]["web"]["ports"] == ["127.0.0.1:5174:80"]
    assert compose["services"]["bootstrap"]["command"] == ["python", "-m", "industrialops.bootstrap"]
    assert all(volume.endswith(":ro") for volume in compose["services"]["bootstrap"]["volumes"][:3])
    environment = compose["services"]["bootstrap"]["environment"]
    assert environment["USER"] == "industrialops"
    assert environment["HOME"] == "/tmp"
    assert environment["TORCHINDUCTOR_CACHE_DIR"] == "/tmp/torchinductor"


def test_container_builds_exclude_private_evidence_and_use_a_runtime_only_web_image() -> None:
    backend = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    frontend = (ROOT / "frontend" / "Dockerfile").read_text(encoding="utf-8")
    ignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    cpu_constraints = (ROOT / "constraints-docker-cpu.txt").read_text(encoding="utf-8")

    assert "COPY alembic/ alembic/" in backend
    assert "COPY config/ config/" in backend
    assert "'.[local-models]'" in backend
    assert "constraints-docker-cpu.txt" in backend
    assert "https://download.pytorch.org/whl/cpu" in backend
    assert "torch==2.10.0+cpu" in cpu_constraints
    assert "!constraints-docker-cpu.txt" in ignore
    assert "mkdir -p /app/data/indexes" in backend
    assert "chown -R 10001:10001 /app" in backend
    assert "USER 10001:10001" in backend
    assert "FROM node:22" in frontend
    assert "FROM nginx:" in frontend
    assert "COPY nginx.conf" in frontend
    assert "data/packs" not in backend
    assert "!data/" not in ignore
