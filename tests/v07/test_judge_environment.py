from __future__ import annotations

import pytest

from industrialops.evaluation.v07.judge_environment import JudgeEnvironmentError, load_judge_environment, load_judge_settings
from industrialops.evaluation.v07.run import load_explicit_judge_configuration


def test_load_judge_environment_accepts_only_required_namespaced_values(tmp_path) -> None:
    environment_file = tmp_path / "judge.env"
    environment_file.write_text(
        "\n".join(
            (
                "# private, ignored configuration",
                "INDUSTRIALOPS_EVALUATION_PROFILE=judge",
                "INDUSTRIALOPS_EVALUATION_JUDGE_ENABLED=true",
                "INDUSTRIALOPS_EVALUATION_JUDGE_PROVIDER=deepseek",
                "INDUSTRIALOPS_EVALUATION_JUDGE_BASE_URL=https://judge.example.test/v1",
                "INDUSTRIALOPS_EVALUATION_JUDGE_MODEL=judge-model",
                "INDUSTRIALOPS_EVALUATION_JUDGE_API_KEY=private-test-key",
            )
        )
        + "\n",
            encoding="utf-8",
        )

    environment = load_judge_environment(environment_file)

    assert environment["INDUSTRIALOPS_EVALUATION_PROFILE"] == "judge"
    assert environment["INDUSTRIALOPS_EVALUATION_JUDGE_API_KEY"] == "private-test-key"


def test_load_judge_environment_accepts_powershell_assignment_prefix(tmp_path) -> None:
    environment_file = tmp_path / "judge.env"
    environment_file.write_text(
        "\n".join(
            (
                '$env:INDUSTRIALOPS_EVALUATION_PROFILE="judge"',
                "$env:INDUSTRIALOPS_EVALUATION_JUDGE_ENABLED=true",
                '$env:INDUSTRIALOPS_EVALUATION_JUDGE_PROVIDER="deepseek"',
                "$env:INDUSTRIALOPS_EVALUATION_JUDGE_BASE_URL=https://judge.example.test/v1",
                "$env:INDUSTRIALOPS_EVALUATION_JUDGE_MODEL=judge-model",
                "$env:INDUSTRIALOPS_EVALUATION_JUDGE_API_KEY=private-test-key",
            )
        ),
        encoding="utf-8",
    )

    environment = load_judge_environment(environment_file)

    assert environment["INDUSTRIALOPS_EVALUATION_JUDGE_PROVIDER"] == "deepseek"


def test_load_judge_settings_validates_the_private_file_without_returning_the_key(tmp_path) -> None:
    environment_file = tmp_path / "judge.env"
    environment_file.write_text(
        "\n".join(
            (
                "INDUSTRIALOPS_EVALUATION_PROFILE=judge",
                "INDUSTRIALOPS_EVALUATION_JUDGE_ENABLED=true",
                "INDUSTRIALOPS_EVALUATION_JUDGE_PROVIDER=deepseek",
                "INDUSTRIALOPS_EVALUATION_JUDGE_BASE_URL=https://judge.example.test/v1",
                "INDUSTRIALOPS_EVALUATION_JUDGE_MODEL=judge-model",
                "INDUSTRIALOPS_EVALUATION_JUDGE_API_KEY=private-test-key",
            )
        ),
        encoding="utf-8",
    )

    settings = load_judge_settings(environment_file)

    assert settings.evaluation_profile == "judge"
    assert settings.evaluation_judge_enabled is True
    assert settings.evaluation_judge_provider == "deepseek"
    assert settings.evaluation_judge_model == "judge-model"


def test_judge_cli_configuration_requires_an_explicit_private_file(tmp_path) -> None:
    with pytest.raises(ValueError, match="EVALUATION_JUDGE_ENV_FILE_REQUIRED"):
        load_explicit_judge_configuration(None)

    environment_file = tmp_path / "judge.env"
    environment_file.write_text(
        "\n".join(
            (
                "INDUSTRIALOPS_EVALUATION_PROFILE=judge",
                "INDUSTRIALOPS_EVALUATION_JUDGE_ENABLED=true",
                "INDUSTRIALOPS_EVALUATION_JUDGE_PROVIDER=deepseek",
                "INDUSTRIALOPS_EVALUATION_JUDGE_BASE_URL=https://judge.example.test/v1",
                "INDUSTRIALOPS_EVALUATION_JUDGE_MODEL=judge-model",
                "INDUSTRIALOPS_EVALUATION_JUDGE_API_KEY=private-test-key",
            )
        ),
        encoding="utf-8",
    )

    assert load_explicit_judge_configuration(environment_file).evaluation_profile == "judge"


def test_load_judge_environment_rejects_unknown_or_duplicate_keys_without_echoing_values(tmp_path) -> None:
    environment_file = tmp_path / "judge.env"
    environment_file.write_text(
        "\n".join(
            (
                "INDUSTRIALOPS_EVALUATION_PROFILE=judge",
                "INDUSTRIALOPS_EVALUATION_PROFILE=private-secret-that-must-not-appear",
            )
        ),
        encoding="utf-8",
    )

    with pytest.raises(JudgeEnvironmentError, match="EVALUATION_JUDGE_ENV_DUPLICATE_KEY") as error:
        load_judge_environment(environment_file)

    assert "private-secret-that-must-not-appear" not in str(error.value)
