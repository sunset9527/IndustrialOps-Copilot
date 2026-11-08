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
        )
