from __future__ import annotations

import json
from pathlib import Path

from industrialops.evaluation.v08.preflight import run_preflight


def test_preflight_accepts_complete_isolated_offline_inputs_without_exposing_paths(tmp_path: Path) -> None:
    environment, documents = _complete_environment(tmp_path)

    result = run_preflight(environment=environment, required_documents=documents, port_available=lambda _: True)

    assert result.ready is True
    assert {check.name for check in result.checks} == {
        "offline_policy",
        "knowledge_packs",
        "bge_model",
        "reranker_model",
        "api_port",
        "frontend_port",
        "required_documents",
    }
    assert all(check.code is None for check in result.checks)
    assert str(tmp_path) not in json.dumps(result.as_dict())


def test_preflight_reports_missing_model_with_stable_code_and_no_private_path(tmp_path: Path) -> None:
    environment, documents = _complete_environment(tmp_path)
    missing_model = tmp_path / "private" / "missing-bge"
    environment["INDUSTRIALOPS_BGE_MODEL_PATH"] = str(missing_model)

    result = run_preflight(environment=environment, required_documents=documents, port_available=lambda _: True)

    check = result.by_name("bge_model")
    assert result.ready is False
    assert check.code == "RC_PREFLIGHT_BGE_MODEL_MISSING"
    assert str(missing_model) not in check.detail


def test_preflight_rejects_online_mode_missing_pack_and_occupied_port(tmp_path: Path) -> None:
    environment, documents = _complete_environment(tmp_path)
    environment["INDUSTRIALOPS_OFFLINE"] = "false"
    (Path(environment["INDUSTRIALOPS_PACKS_PATH"]) / "dry_vacuum_pump_pack_v1.0.0").rmdir()

    result = run_preflight(
        environment=environment,
        required_documents=documents,
        port_available=lambda port: port != 9100,
    )

    assert result.ready is False
    assert result.by_name("offline_policy").code == "RC_PREFLIGHT_OFFLINE_REQUIRED"
    assert result.by_name("knowledge_packs").code == "RC_PREFLIGHT_PACK_MISSING"
    assert result.by_name("api_port").code == "RC_PREFLIGHT_PORT_UNAVAILABLE"
    assert result.by_name("frontend_port").code is None


def test_preflight_requires_all_release_documents(tmp_path: Path) -> None:
    environment, documents = _complete_environment(tmp_path)
    documents[-1].unlink()

    result = run_preflight(environment=environment, required_documents=documents, port_available=lambda _: True)

    check = result.by_name("required_documents")
    assert check.code == "RC_PREFLIGHT_DOCUMENT_MISSING"
    assert "architecture.md" in check.detail
    assert str(tmp_path) not in check.detail


def _complete_environment(tmp_path: Path) -> tuple[dict[str, str], list[Path]]:
    packs_root = tmp_path / "private" / "packs"
    (packs_root / "cnc_pack_v1.0.0").mkdir(parents=True)
    (packs_root / "dry_vacuum_pump_pack_v1.0.0").mkdir()
    bge_model = tmp_path / "private" / "bge"
    reranker_model = tmp_path / "private" / "reranker"
    bge_model.mkdir(parents=True)
    reranker_model.mkdir()
    (bge_model / "config.json").write_text("{}", encoding="utf-8")
    (reranker_model / "config.json").write_text("{}", encoding="utf-8")
    documents = [tmp_path / "README.md", tmp_path / "THIRD_PARTY_NOTICES.md", tmp_path / "architecture.md"]
    for document in documents:
        document.write_text("placeholder", encoding="utf-8")
    return (
        {
            "INDUSTRIALOPS_OFFLINE": "true",
            "INDUSTRIALOPS_PACKS_PATH": str(packs_root),
            "INDUSTRIALOPS_BGE_MODEL_PATH": str(bge_model),
            "INDUSTRIALOPS_RERANKER_MODEL_PATH": str(reranker_model),
            "INDUSTRIALOPS_API_PORT": "9100",
            "INDUSTRIALOPS_FRONTEND_PORT": "9174",
        },
        documents,
    )
