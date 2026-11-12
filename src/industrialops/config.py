"""Minimal, explicitly namespaced runtime configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


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

    @classmethod
    def from_environment(cls, environment: Mapping[str, str]) -> "Settings":
        return cls(
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
        )
