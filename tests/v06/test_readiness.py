from __future__ import annotations

from pathlib import Path

from industrialops.readiness import _project_root


def test_readiness_uses_the_deployment_working_directory_when_packaged(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("INDUSTRIALOPS_PROJECT_ROOT", raising=False)
    monkeypatch.chdir(tmp_path)

    assert _project_root() == tmp_path
