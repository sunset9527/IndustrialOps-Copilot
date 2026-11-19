"""Read-only dependency checks used by the API readiness endpoint."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

from industrialops.config import Settings
from industrialops.knowledge.pack_loader import EquipmentPackLoader
from industrialops.retrieval.index_store import IndexStore
from industrialops.retrieval.local_models import model_fingerprint
from industrialops.services.error_sanitizer import redact_sensitive_text


@dataclass(frozen=True)
class DependencyStatus:
    name: str
    status: str
    code: str | None
    detail: str


@dataclass(frozen=True)
class ReadinessReport:
    dependencies: tuple[DependencyStatus, ...]

    @property
    def ready(self) -> bool:
        return all(item.status == "ready" for item in self.dependencies)

    def as_dict(self) -> dict[str, object]:
        return {
            "status": "ready" if self.ready else "not_ready",
            "dependencies": [
                {"name": item.name, "status": item.status, "code": item.code, "detail": item.detail}
                for item in self.dependencies
            ],
        }


def inspect_readiness(checks: Mapping[str, Callable[[], str]]) -> ReadinessReport:
    """Run each named read-only check and retain safe detail for every result."""

    statuses: list[DependencyStatus] = []
    for name, check in checks.items():
        try:
            detail = check()
        except RuntimeError as error:
            code, _, message = str(error).partition(":")
            statuses.append(DependencyStatus(name, "not_ready", code or "READINESS_FAILED", redact_sensitive_text(message.strip())))
        except Exception:
            statuses.append(DependencyStatus(name, "not_ready", "READINESS_FAILED", "Dependency verification failed"))
        else:
            statuses.append(DependencyStatus(name, "ready", None, detail))
    return ReadinessReport(tuple(statuses))


def build_readiness_checker(settings: Settings) -> Callable[[], ReadinessReport]:
    """Build the production checker without doing I/O during app construction."""

    root = _project_root()
    paths = _RuntimePaths.from_settings(settings, root)

    def check() -> ReadinessReport:
        return inspect_readiness({
            "database": lambda: _check_database(settings.database_url),
            "migration": lambda: _check_migration(settings.database_url, root),
            "knowledge_packs": lambda: _check_packs(paths),
            "indexes": lambda: _check_indexes(paths),
            "local_models": lambda: _check_models(paths),
            "offline_policy": lambda: _check_offline_policy(settings),
        })

    return check


def _project_root() -> Path:
    """Find deployment files when the package is installed in site-packages."""

    configured_root = os.environ.get("INDUSTRIALOPS_PROJECT_ROOT")
    return Path(configured_root) if configured_root else Path.cwd()


@dataclass(frozen=True)
class _RuntimePaths:
    packs_root: Path
    registry_path: Path
    indexes_root: Path
    bge_model_path: Path
    reranker_model_path: Path

    @classmethod
    def from_settings(cls, settings: Settings, root: Path) -> "_RuntimePaths":
        return cls(
            packs_root=_absolute(root, settings.packs_root),
            registry_path=_absolute(root, settings.pack_registry_path),
            indexes_root=_absolute(root, settings.indexes_root),
            bge_model_path=settings.bge_model_path,
            reranker_model_path=settings.reranker_model_path,
        )


def _absolute(root: Path, value: Path) -> Path:
    return value if value.is_absolute() else root / value


def _check_database(database_url: str) -> str:
    try:
        with create_engine(database_url, pool_pre_ping=True).connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as error:
        raise RuntimeError("DATABASE_UNAVAILABLE: Database connection failed") from error
    return "Database connection verified"


def _check_migration(database_url: str, root: Path) -> str:
    try:
        config = Config(str(root / "alembic.ini"))
        config.set_main_option("sqlalchemy.url", database_url)
        script = ScriptDirectory.from_config(config)
        with create_engine(database_url, pool_pre_ping=True).connect() as connection:
            current = MigrationContext.configure(connection).get_current_heads()
        if tuple(script.get_heads()) != tuple(current):
            raise RuntimeError("DATABASE_MIGRATION_OUTDATED: Database migration is not at head")
    except RuntimeError:
        raise
    except Exception as error:
        raise RuntimeError("DATABASE_MIGRATION_UNAVAILABLE: Database migration could not be checked") from error
    return "Database migration is at head"


def _load_packs(paths: _RuntimePaths):
    try:
        registry = json.loads(paths.registry_path.read_text(encoding="utf-8"))
        pack_ids = tuple(registry["packs"])
        if set(pack_ids) != {"cnc_pack_v1.0.0", "dry_vacuum_pump_pack_v1.0.0"}:
            raise ValueError("unexpected frozen pack set")
        loader = EquipmentPackLoader(paths.packs_root, paths.registry_path)
        return registry, {pack_id: loader.load(pack_id) for pack_id in pack_ids}
    except Exception as error:
        raise RuntimeError("PACK_UNAVAILABLE: Frozen knowledge packs could not be verified") from error


def _check_packs(paths: _RuntimePaths) -> str:
    _, packs = _load_packs(paths)
    return f"{len(packs)} frozen knowledge packs verified"


def _check_models(paths: _RuntimePaths) -> str:
    try:
        model_fingerprint(paths.bge_model_path)
        model_fingerprint(paths.reranker_model_path)
    except Exception as error:
        raise RuntimeError("MODEL_UNAVAILABLE: Local model files could not be verified") from error
    return "Local retrieval models verified"


def _check_indexes(paths: _RuntimePaths) -> str:
    registry, packs = _load_packs(paths)
    try:
        registry_sha256 = hashlib.sha256(paths.registry_path.read_bytes()).hexdigest()
        embedding_fingerprint = model_fingerprint(paths.bge_model_path)
        store = IndexStore(paths.indexes_root)
        for pack in packs.values():
            store.load(store.expected_artifact(
                pack, registry_sha256=registry_sha256, model_fingerprint=embedding_fingerprint
            ))
    except Exception as error:
        raise RuntimeError("INDEX_UNAVAILABLE: Local retrieval indexes could not be verified") from error
    return f"{len(registry['packs'])} retrieval indexes verified"


def _check_offline_policy(settings: Settings) -> str:
    if settings.offline_mode:
        return "Offline mode enabled; external answer provider disabled"
    if not settings.deepseek_base_url.startswith("https://"):
        raise RuntimeError("CONFIG_EXTERNAL_MODEL_URL_INVALID: Online model URL must use HTTPS")
    return "Online model provider explicitly enabled"
