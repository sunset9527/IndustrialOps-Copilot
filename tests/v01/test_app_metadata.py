from __future__ import annotations

from industrialops.app_metadata import PRODUCT_NAME, PRODUCT_SLUG
from industrialops.config import Settings


def test_product_metadata_uses_the_industrialops_identity() -> None:
    assert PRODUCT_NAME == "IndustrialOps Copilot"
    assert PRODUCT_SLUG == "industrialops"


def test_default_settings_keep_industrialops_separate_from_heritagemind() -> None:
    settings = Settings.from_environment({})

    assert settings.api_port == 8100
    assert settings.frontend_port == 5174
    assert settings.database_url.endswith("/industrialops")
    assert settings.redis_key_prefix == "industrialops:"


def test_settings_use_only_industrialops_environment_variable_names() -> None:
    settings = Settings.from_environment(
        {
            "INDUSTRIALOPS_API_PORT": "8111",
            "INDUSTRIALOPS_DATABASE_URL": "sqlite:///./isolated-industrialops.db",
            "INDUSTRIALOPS_REDIS_KEY_PREFIX": "demo:",
            "HERITAGEMIND_API_PORT": "9999",
        }
    )

    assert settings.api_port == 8111
    assert settings.database_url == "sqlite:///./isolated-industrialops.db"
    assert settings.redis_key_prefix == "demo:"
