"""Minimal, explicitly namespaced runtime configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


class ConfigurationError(ValueError):
    """A namespaced runtime configuration value is unsafe or invalid."""


@dataclass(frozen=True)
class Settings:
    """Settings that keep IndustrialOps isolated from its source project."""

    api_port: int
    frontend_port: int
    database_url: str
    redis_key_prefix: str
    request_max_bytes: int
    auth_session_ttl_seconds: int = 3600
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-flash"
    deepseek_timeout_seconds: float = 20.0
    deepseek_max_tokens: int = 1600
    offline_mode: bool = True
    packs_root: Path = Path("data/packs")
    pack_registry_path: Path = Path("config/equipment_pack_registry_v1.json")
    indexes_root: Path = Path("data/indexes")
    bge_model_path: Path = Path(r"E:\huggingface\model")
    reranker_model_path: Path = Path(r"E:\huggingface\bge-reranker-base")
    evaluation_profile: str = "deterministic"
    evaluation_judge_enabled: bool = False
    evaluation_judge_provider: str | None = None
    evaluation_judge_base_url: str | None = None
    evaluation_judge_model: str | None = None
    evaluation_judge_api_key: str | None = None

    @classmethod
    def from_environment(cls, environment: Mapping[str, str]) -> "Settings":
        evaluation_profile = _read_evaluation_profile(environment)
        evaluation_judge_enabled = _read_boolean(
            environment, "INDUSTRIALOPS_EVALUATION_JUDGE_ENABLED", default=False
        )
        settings = cls(
            api_port=int(environment.get("INDUSTRIALOPS_API_PORT", "8100")),
            frontend_port=int(environment.get("INDUSTRIALOPS_FRONTEND_PORT", "5174")),
            database_url=environment.get(
                "INDUSTRIALOPS_DATABASE_URL",
                "mysql+pymysql://root:change-me@localhost:3306/industrialops",
            ),
            redis_key_prefix=environment.get("INDUSTRIALOPS_REDIS_KEY_PREFIX", "industrialops:"),
            request_max_bytes=int(environment.get("INDUSTRIALOPS_REQUEST_MAX_BYTES", "26214400")),
            auth_session_ttl_seconds=int(environment.get("INDUSTRIALOPS_AUTH_SESSION_TTL_SECONDS", "3600")),
            deepseek_api_key=environment.get("INDUSTRIALOPS_DEEPSEEK_API_KEY") or None,
            deepseek_base_url=environment.get("INDUSTRIALOPS_DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            deepseek_model=environment.get("INDUSTRIALOPS_DEEPSEEK_MODEL", "deepseek-flash"),
            deepseek_timeout_seconds=float(environment.get("INDUSTRIALOPS_DEEPSEEK_TIMEOUT", "20")),
            deepseek_max_tokens=int(environment.get("INDUSTRIALOPS_DEEPSEEK_MAX_TOKENS", "1600")),
            offline_mode=_read_boolean(environment, "INDUSTRIALOPS_OFFLINE", default=True),
            packs_root=Path(environment.get("INDUSTRIALOPS_PACKS_ROOT", "data/packs")),
            pack_registry_path=Path(
                environment.get("INDUSTRIALOPS_PACK_REGISTRY_PATH", "config/equipment_pack_registry_v1.json")
            ),
            indexes_root=Path(environment.get("INDUSTRIALOPS_INDEXES_ROOT", "data/indexes")),
            bge_model_path=Path(environment.get("INDUSTRIALOPS_BGE_MODEL_PATH", r"E:\huggingface\model")),
            reranker_model_path=Path(
                environment.get("INDUSTRIALOPS_RERANKER_MODEL_PATH", r"E:\huggingface\bge-reranker-base")
            ),
            evaluation_profile=evaluation_profile,
            evaluation_judge_enabled=evaluation_judge_enabled,
            evaluation_judge_provider=environment.get("INDUSTRIALOPS_EVALUATION_JUDGE_PROVIDER") or None,
            evaluation_judge_base_url=environment.get("INDUSTRIALOPS_EVALUATION_JUDGE_BASE_URL") or None,
            evaluation_judge_model=environment.get("INDUSTRIALOPS_EVALUATION_JUDGE_MODEL") or None,
            evaluation_judge_api_key=environment.get("INDUSTRIALOPS_EVALUATION_JUDGE_API_KEY") or None,
        )
        _validate_evaluation_settings(settings)
        return settings


def _read_boolean(environment: Mapping[str, str], name: str, *, default: bool) -> bool:
    raw = environment.get(name)
    if raw is None:
        return default
    normalized = raw.strip().casefold()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ConfigurationError(f"CONFIG_OFFLINE_MODE_INVALID: {name} must be a boolean")


def _read_evaluation_profile(environment: Mapping[str, str]) -> str:
    profile = environment.get("INDUSTRIALOPS_EVALUATION_PROFILE", "deterministic").strip().casefold()
    if profile not in {"deterministic", "framework-smoke", "judge"}:
        raise ConfigurationError(
            "CONFIG_EVALUATION_PROFILE_INVALID: INDUSTRIALOPS_EVALUATION_PROFILE must be deterministic, framework-smoke, or judge"
        )
    return profile


def _validate_evaluation_settings(settings: Settings) -> None:
    if settings.evaluation_profile != "judge":
        if settings.evaluation_judge_enabled:
            raise ConfigurationError("CONFIG_EVALUATION_JUDGE_PROFILE_REQUIRED")
        return
    if not settings.evaluation_judge_enabled:
        raise ConfigurationError("CONFIG_EVALUATION_JUDGE_OPT_IN_REQUIRED")
    if not all(
        (
            settings.evaluation_judge_provider,
            settings.evaluation_judge_base_url,
            settings.evaluation_judge_model,
            settings.evaluation_judge_api_key,
        )
    ):
        raise ConfigurationError("CONFIG_EVALUATION_JUDGE_CONFIGURATION_INCOMPLETE")
