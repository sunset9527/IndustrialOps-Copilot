from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_ci_runs_backend_frontend_and_container_configuration_checks_without_private_artifacts() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "pytest" in workflow
    assert "npm ci" in workflow
    assert "npm run test" in workflow
    assert "npm run build" in workflow
    assert "docker compose config" in workflow
    assert "data/packs" not in workflow
    assert "E:\\huggingface" not in workflow
