"""Explicit one-shot initialization for the containerized local demo stack."""

from __future__ import annotations

from collections.abc import Callable, Mapping
import hashlib
import json
import os
from pathlib import Path
import sys

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from industrialops.config import Settings
from industrialops.demo_seed import seed_demo_assets
from industrialops.knowledge.pack_loader import EquipmentPackLoader
from industrialops.readiness import _RuntimePaths
from industrialops.retrieval.index_store import IndexStore
from industrialops.retrieval.local_models import LocalBgeM3, model_fingerprint


class BootstrapError(RuntimeError):
    """A named startup phase failed, so dependent services must not start."""


_STEP_ERROR_CODES = {
    "preflight": "CONFIG_PREFLIGHT_FAILED",
    "migration": "DATABASE_MIGRATION_FAILED",
    "seed": "DATABASE_SEED_FAILED",
    "knowledge_packs": "PACK_VERIFICATION_FAILED",
    "indexes": "INDEX_BUILD_FAILED",
}


def run_bootstrap_steps(steps: Mapping[str, Callable[[], str]]) -> list[dict[str, str]]:
    """Execute ordered, explicit initialization phases and stop at first failure."""

    results: list[dict[str, str]] = []
    for name, step in steps.items():
        try:
            detail = step()
        except Exception as error:
            code = _STEP_ERROR_CODES.get(name, "BOOTSTRAP_STEP_FAILED")
            raise BootstrapError(f"{code}: {name} failed") from error
        results.append({"step": name, "status": "completed", "detail": detail})
    return results


def bootstrap(settings: Settings, *, project_root: Path | None = None) -> list[dict[str, str]]:
    """Run the production bootstrap sequence; it never mutates frozen packs."""

    root = project_root or Path(__file__).resolve().parents[2]
    paths = _RuntimePaths.from_settings(settings, root)
    return run_bootstrap_steps({
        "preflight": lambda: _preflight(settings, paths),
        "migration": lambda: _migrate(settings, root),
        "seed": lambda: _seed(settings),
        "knowledge_packs": lambda: _verify_packs(paths),
        "indexes": lambda: _prepare_indexes(paths),
    })


def _preflight(settings: Settings, paths: _RuntimePaths) -> str:
    if not settings.database_url.startswith("mysql+pymysql://"):
        raise ValueError("database URL must use mysql+pymysql")
    if not paths.packs_root.is_dir() or not paths.registry_path.is_file():
        raise FileNotFoundError("frozen pack directory or registry is missing")
    for model_path in (paths.bge_model_path, paths.reranker_model_path):
        if not model_path.is_absolute() or not (model_path / "config.json").is_file():
            raise FileNotFoundError("local model config is missing")
    paths.indexes_root.mkdir(parents=True, exist_ok=True)
    if not os.access(paths.indexes_root, os.W_OK):
        raise PermissionError("index root is not writable")
    return "Configuration and local delivery paths checked"


def _migrate(settings: Settings, root: Path) -> str:
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(config, "head")
    return "Database migrated to head"


def _seed(settings: Settings) -> str:
    factory = sessionmaker(bind=create_engine(settings.database_url, pool_pre_ping=True))
    with factory() as db:
        created = seed_demo_assets(db)
        db.commit()
    return f"Synthetic assets seeded (created={created})"


def _load_packs(paths: _RuntimePaths):
    registry = json.loads(paths.registry_path.read_text(encoding="utf-8"))
    pack_ids = tuple(registry.get("packs", {}))
    if set(pack_ids) != {"cnc_pack_v1.0.0", "dry_vacuum_pump_pack_v1.0.0"}:
        raise ValueError("unexpected frozen knowledge pack set")
    loader = EquipmentPackLoader(paths.packs_root, paths.registry_path)
    return registry, tuple(loader.load(pack_id) for pack_id in pack_ids)


def _verify_packs(paths: _RuntimePaths) -> str:
    _, packs = _load_packs(paths)
    return f"{len(packs)} frozen knowledge packs verified"


def _prepare_indexes(paths: _RuntimePaths) -> str:
    _, packs = _load_packs(paths)
    registry_sha256 = hashlib.sha256(paths.registry_path.read_bytes()).hexdigest()
    embedding = LocalBgeM3(paths.bge_model_path)
    store = IndexStore(paths.indexes_root)
    for pack in packs:
        store.prepare(
            pack,
            registry_sha256=registry_sha256,
            model_fingerprint=model_fingerprint(paths.bge_model_path),
            encode=lambda texts: embedding.embed(texts),
        )
    return f"{len(packs)} local retrieval indexes prepared"


def main() -> None:
    try:
        results = bootstrap(Settings.from_environment(os.environ))
    except BootstrapError as error:
        print(json.dumps({"status": "failed", "error": str(error).split(":", maxsplit=1)[0]}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1) from error
    print(json.dumps({"status": "completed", "steps": results}, ensure_ascii=False))


if __name__ == "__main__":
    main()
