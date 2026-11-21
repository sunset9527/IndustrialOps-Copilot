"""Non-destructive RC input checks that avoid exposing private deployment paths."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path


_REQUIRED_PACK_IDS = ("cnc_pack_v1.0.0", "dry_vacuum_pump_pack_v1.0.0")


@dataclass(frozen=True)
class PreflightCheck:
    """One safe-to-persist preflight observation."""

    name: str
    status: str
    code: str | None
    detail: str


@dataclass(frozen=True)
class PreflightResult:
    """The complete preflight result used to decide whether RC startup may begin."""

    checks: tuple[PreflightCheck, ...]

    @property
    def ready(self) -> bool:
        return all(check.status == "ready" for check in self.checks)

    def by_name(self, name: str) -> PreflightCheck:
        for check in self.checks:
            if check.name == name:
                return check
        raise KeyError(name)

    def as_dict(self) -> dict[str, object]:
        return {
            "status": "ready" if self.ready else "not_ready",
            "checks": [
                {"name": check.name, "status": check.status, "code": check.code, "detail": check.detail}
                for check in self.checks
            ],
        }


def run_preflight(
    *,
    environment: Mapping[str, str],
    required_documents: Sequence[Path],
    port_available: Callable[[int], bool],
) -> PreflightResult:
    """Validate the minimum local inputs without starting containers or reading private data."""

    checks = (
        _check_offline_policy(environment),
        _check_packs(environment),
        _check_model(environment, "INDUSTRIALOPS_BGE_MODEL_PATH", "bge_model", "RC_PREFLIGHT_BGE_MODEL_MISSING"),
        _check_model(
            environment,
            "INDUSTRIALOPS_RERANKER_MODEL_PATH",
            "reranker_model",
            "RC_PREFLIGHT_RERANKER_MODEL_MISSING",
        ),
        _check_port(environment, "INDUSTRIALOPS_API_PORT", "api_port", port_available),
        _check_port(environment, "INDUSTRIALOPS_FRONTEND_PORT", "frontend_port", port_available),
        _check_documents(required_documents),
    )
    return PreflightResult(checks)


def _check_offline_policy(environment: Mapping[str, str]) -> PreflightCheck:
    if environment.get("INDUSTRIALOPS_OFFLINE", "").strip().casefold() == "true":
        return PreflightCheck("offline_policy", "ready", None, "Offline policy enabled")
    return PreflightCheck(
        "offline_policy",
        "not_ready",
        "RC_PREFLIGHT_OFFLINE_REQUIRED",
        "Release-candidate validation requires INDUSTRIALOPS_OFFLINE=true",
    )


def _check_packs(environment: Mapping[str, str]) -> PreflightCheck:
    raw_path = environment.get("INDUSTRIALOPS_PACKS_PATH", "")
    packs_root = Path(raw_path)
    if not raw_path or not packs_root.is_dir():
        return PreflightCheck(
            "knowledge_packs", "not_ready", "RC_PREFLIGHT_PACK_MISSING", "Frozen knowledge-pack root is unavailable"
        )
    missing_pack_ids = [pack_id for pack_id in _REQUIRED_PACK_IDS if not (packs_root / pack_id).is_dir()]
    if missing_pack_ids:
        return PreflightCheck(
            "knowledge_packs",
            "not_ready",
            "RC_PREFLIGHT_PACK_MISSING",
            f"Required frozen knowledge pack is unavailable: {missing_pack_ids[0]}",
        )
    return PreflightCheck("knowledge_packs", "ready", None, "Both frozen knowledge-pack directories are present")


def _check_model(
    environment: Mapping[str, str], environment_name: str, check_name: str, missing_code: str
) -> PreflightCheck:
    raw_path = environment.get(environment_name, "")
    config_path = Path(raw_path) / "config.json"
    if not raw_path or not config_path.is_file():
        return PreflightCheck(check_name, "not_ready", missing_code, "Required local model configuration is unavailable")
    return PreflightCheck(check_name, "ready", None, "Local model configuration is present")


def _check_port(
    environment: Mapping[str, str],
    environment_name: str,
    check_name: str,
    port_available: Callable[[int], bool],
) -> PreflightCheck:
    try:
        port = int(environment.get(environment_name, ""))
    except ValueError:
        return PreflightCheck(check_name, "not_ready", "RC_PREFLIGHT_PORT_INVALID", "Configured host port is invalid")
    if not 1 <= port <= 65535:
        return PreflightCheck(check_name, "not_ready", "RC_PREFLIGHT_PORT_INVALID", "Configured host port is invalid")
    if not port_available(port):
        return PreflightCheck(check_name, "not_ready", "RC_PREFLIGHT_PORT_UNAVAILABLE", "Configured host port is unavailable")
    return PreflightCheck(check_name, "ready", None, "Configured host port is available")


def _check_documents(required_documents: Sequence[Path]) -> PreflightCheck:
    missing_documents = [document.name for document in required_documents if not document.is_file()]
    if missing_documents:
        return PreflightCheck(
            "required_documents",
            "not_ready",
            "RC_PREFLIGHT_DOCUMENT_MISSING",
            f"Required document is missing: {missing_documents[0]}",
        )
    return PreflightCheck("required_documents", "ready", None, "Required release documents are present")
