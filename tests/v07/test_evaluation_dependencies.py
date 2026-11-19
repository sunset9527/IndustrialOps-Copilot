from __future__ import annotations

from pathlib import Path
import tomllib


def test_ragas_and_deepeval_are_pinned_to_the_optional_evaluation_extra() -> None:
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    extras = project["project"]["optional-dependencies"]

    assert "eval" in extras
    assert any(requirement.startswith("ragas>=0.4.4,<0.5") for requirement in extras["eval"])
    assert any(requirement.startswith("deepeval>=4.3.4,<4.4") for requirement in extras["eval"])
    assert not any(
        requirement.startswith(("ragas", "deepeval")) for requirement in project["project"]["dependencies"]
    )
