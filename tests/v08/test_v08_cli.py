from __future__ import annotations

import json
from pathlib import Path

from industrialops.evaluation.v08 import run


def test_cli_preflight_writes_a_sanitized_final_report_without_calling_docker(tmp_path: Path, monkeypatch) -> None:
    environment_file = _complete_project(tmp_path)
    monkeypatch.setattr(run, "port_available", lambda _: True)

    exit_code = run.main(
        [
            "--project-root",
            str(tmp_path),
            "--env-file",
            str(environment_file),
            "--run-id",
            "20261121-cli",
            "--phase",
            "preflight",
        ]
    )

    report_path = tmp_path / "data" / "evaluation" / "reports" / "v08" / "20261121-cli" / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert report["overall_status"] == "passed"
    assert report["phase"] == "preflight"
    assert "private" not in json.dumps(report)


def test_env_file_values_do_not_override_explicit_process_environment(tmp_path: Path) -> None:
    environment_file = tmp_path / ".env"
    environment_file.write_text("VISIBLE=file-value\nPRIVATE_TOKEN=file-secret\n", encoding="utf-8")

    environment = run.load_effective_environment(environment_file, {"VISIBLE": "process-value"})

    assert environment["VISIBLE"] == "process-value"
    assert environment["PRIVATE_TOKEN"] == "file-secret"


def test_cli_preflight_failure_writes_partial_report_and_returns_nonzero(tmp_path: Path, monkeypatch) -> None:
    environment_file = _complete_project(tmp_path)
    environment_file.write_text("INDUSTRIALOPS_OFFLINE=false\n", encoding="utf-8")
    monkeypatch.setattr(run, "port_available", lambda _: True)
    monkeypatch.setenv("INDUSTRIALOPS_OFFLINE", "false")

    exit_code = run.main(
        [
            "--project-root",
            str(tmp_path),
            "--env-file",
            str(environment_file),
            "--run-id",
            "20261121-cli-failure",
            "--phase",
            "preflight",
        ]
    )

    report_path = tmp_path / "data" / "evaluation" / "reports" / "v08" / "20261121-cli-failure" / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert exit_code == 1
    assert report["overall_status"] == "failed"
    assert report["preflight"]["status"] == "not_ready"


def test_cli_preflight_uses_rc_port_flags_instead_of_occupied_default_ports(tmp_path: Path, monkeypatch) -> None:
    environment_file = _complete_project(tmp_path)
    monkeypatch.setattr(run, "port_available", lambda port: port not in {19100, 19174})
    monkeypatch.setenv("INDUSTRIALOPS_API_PORT", "19100")
    monkeypatch.setenv("INDUSTRIALOPS_FRONTEND_PORT", "19174")

    exit_code = run.main(
        [
            "--project-root",
            str(tmp_path),
            "--env-file",
            str(environment_file),
            "--run-id",
            "20261121-cli-ports",
            "--api-port",
            "18100",
            "--frontend-port",
            "15174",
            "--phase",
            "preflight",
        ]
    )

    assert exit_code == 0


def _complete_project(root: Path) -> Path:
    packs_root = root / "private" / "packs"
    (packs_root / "cnc_pack_v1.0.0").mkdir(parents=True)
    (packs_root / "dry_vacuum_pump_pack_v1.0.0").mkdir()
    bge_model = root / "private" / "bge"
    reranker_model = root / "private" / "reranker"
    bge_model.mkdir(parents=True)
    reranker_model.mkdir()
    (bge_model / "config.json").write_text("{}", encoding="utf-8")
    (reranker_model / "config.json").write_text("{}", encoding="utf-8")
    (root / "docs").mkdir()
    for path in (root / "README.md", root / "THIRD_PARTY_NOTICES.md", root / "docs" / "architecture.md"):
        path.write_text("release document", encoding="utf-8")
    environment_file = root / ".env"
    environment_file.write_text(
        "\n".join(
            (
                "INDUSTRIALOPS_OFFLINE=true",
                f"INDUSTRIALOPS_PACKS_PATH={packs_root}",
                f"INDUSTRIALOPS_BGE_MODEL_PATH={bge_model}",
                f"INDUSTRIALOPS_RERANKER_MODEL_PATH={reranker_model}",
                "INDUSTRIALOPS_API_PORT=19100",
                "INDUSTRIALOPS_FRONTEND_PORT=19174",
                "PRIVATE_TOKEN=private",
            )
        ),
        encoding="utf-8",
    )
    return environment_file
