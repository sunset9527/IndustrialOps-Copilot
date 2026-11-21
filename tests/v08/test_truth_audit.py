from __future__ import annotations

import json
from pathlib import Path

from industrialops.evaluation.v08.truth_audit import audit_claim_manifest


def test_truth_audit_requires_a_public_marker_and_precise_evidence_markers(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("The offline workflow is evidence bound.", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "runtime.py").write_text("if offline_mode:\n    return fallback()\n", encoding="utf-8")
    manifest = tmp_path / "claims.json"
    manifest.write_text(
        json.dumps(
            {
                "format_version": 1,
                "claims": [
                    {
                        "claim_id": "offline-policy",
                        "public_document": "README.md",
                        "public_marker": "offline workflow",
                        "evidence": [
                            {
                                "kind": "code",
                                "path": "src/runtime.py",
                                "required_markers": ["if offline_mode:", "return fallback()"],
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = audit_claim_manifest(project_root=tmp_path, manifest_path=manifest)

    assert result.ready is True
    assert result.by_claim("offline-policy").status == "passed"


def test_truth_audit_rejects_a_claim_that_has_no_evidence_mapping(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("A documented capability.", encoding="utf-8")
    manifest = tmp_path / "claims.json"
    manifest.write_text(
        json.dumps(
            {
                "format_version": 1,
                "claims": [
                    {
                        "claim_id": "unmapped",
                        "public_document": "README.md",
                        "public_marker": "documented capability",
                        "evidence": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = audit_claim_manifest(project_root=tmp_path, manifest_path=manifest)

    check = result.by_claim("unmapped")
    assert result.ready is False
    assert check.code == "RC_TRUTH_EVIDENCE_REQUIRED"


def test_repository_truth_manifest_covers_compose_offline_approval_architecture_and_data_boundary() -> None:
    project_root = Path(__file__).resolve().parents[2]

    result = audit_claim_manifest(
        project_root=project_root,
        manifest_path=project_root / "config" / "release_truth_audit_v08.json",
    )

    assert result.ready is True
    assert {check.claim_id for check in result.checks} == {
        "compose-topology",
        "offline-answer-policy",
        "human-approval-recovery",
        "architecture-topology",
        "private-evidence-boundary",
    }
