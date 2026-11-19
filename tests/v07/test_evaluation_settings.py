from __future__ import annotations

import pytest

from industrialops.config import ConfigurationError, Settings


def test_settings_default_to_deterministic_evaluation_without_a_network_judge() -> None:
    settings = Settings.from_environment({})

    assert settings.evaluation_profile == "deterministic"
    assert settings.evaluation_judge_enabled is False
    assert settings.evaluation_judge_api_key is None


def test_judge_profile_requires_explicit_opt_in_and_complete_judge_configuration() -> None:
    with pytest.raises(ConfigurationError, match="CONFIG_EVALUATION_JUDGE_OPT_IN_REQUIRED"):
        Settings.from_environment({"INDUSTRIALOPS_EVALUATION_PROFILE": "judge"})

    with pytest.raises(ConfigurationError, match="CONFIG_EVALUATION_JUDGE_CONFIGURATION_INCOMPLETE"):
        Settings.from_environment(
            {
                "INDUSTRIALOPS_EVALUATION_PROFILE": "judge",
                "INDUSTRIALOPS_EVALUATION_JUDGE_ENABLED": "true",
                "INDUSTRIALOPS_EVALUATION_JUDGE_PROVIDER": "deepseek",
                "INDUSTRIALOPS_EVALUATION_JUDGE_BASE_URL": "https://judge.example.test",
            }
        )


def test_judge_profile_uses_an_explicit_separate_configuration() -> None:
    settings = Settings.from_environment(
        {
            "INDUSTRIALOPS_EVALUATION_PROFILE": "judge",
            "INDUSTRIALOPS_EVALUATION_JUDGE_ENABLED": "true",
            "INDUSTRIALOPS_EVALUATION_JUDGE_PROVIDER": "deepseek",
            "INDUSTRIALOPS_EVALUATION_JUDGE_BASE_URL": "https://judge.example.test/v1",
            "INDUSTRIALOPS_EVALUATION_JUDGE_MODEL": "judge-model",
            "INDUSTRIALOPS_EVALUATION_JUDGE_API_KEY": "judge-key",
        }
    )

    assert settings.evaluation_profile == "judge"
    assert settings.evaluation_judge_enabled is True
    assert settings.evaluation_judge_provider == "deepseek"
    assert settings.evaluation_judge_base_url == "https://judge.example.test/v1"
    assert settings.evaluation_judge_model == "judge-model"
    assert settings.evaluation_judge_api_key == "judge-key"
