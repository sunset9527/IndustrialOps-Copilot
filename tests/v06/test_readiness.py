from __future__ import annotations

from pathlib import Path

from industrialops.readiness import _project_root


def test_readiness_uses_the_deployment_working_directory_when_packaged(monkeypatch) -> None:
    monkeypatch.delenv("INDUSTRIALOPS_PROJECT_ROOT", raising=False)
    monkeypatch.chdir(Path("E:/python/LLM/IndustrialOps_Copilot"))

    assert _project_root() == Path.cwd()
