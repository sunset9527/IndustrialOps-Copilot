"""Validate that public release claims retain explicit, inspectable evidence anchors."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


_EVIDENCE_KINDS = {"code", "test", "command", "report", "compose", "configuration"}


@dataclass(frozen=True)
class TruthCheck:
    """One public claim and the result of verifying its declared evidence."""

    claim_id: str
    status: str
    code: str | None
    detail: str


@dataclass(frozen=True)
class TruthAuditResult:
    """An audit result that can fail closed before release status is updated."""

    checks: tuple[TruthCheck, ...]

    @property
    def ready(self) -> bool:
        return all(check.status == "passed" for check in self.checks)

    def by_claim(self, claim_id: str) -> TruthCheck:
        for check in self.checks:
            if check.claim_id == claim_id:
                return check
        raise KeyError(claim_id)


def audit_claim_manifest(*, project_root: Path, manifest_path: Path) -> TruthAuditResult:
    """Check each release claim against its public document and concrete evidence files."""

    manifest = _load_manifest(manifest_path)
    claims = manifest.get("claims")
    if manifest.get("format_version") != 1 or not isinstance(claims, list):
        return TruthAuditResult((TruthCheck("manifest", "failed", "RC_TRUTH_MANIFEST_INVALID", "Manifest format is invalid"),))
    return TruthAuditResult(tuple(_audit_claim(project_root, claim) for claim in claims))


def _load_manifest(manifest_path: Path) -> dict[str, Any]:
    try:
        loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _audit_claim(project_root: Path, raw_claim: object) -> TruthCheck:
    if not isinstance(raw_claim, dict):
        return TruthCheck("unknown", "failed", "RC_TRUTH_CLAIM_INVALID", "Claim entry is invalid")
    claim_id = raw_claim.get("claim_id")
    document = raw_claim.get("public_document")
    public_marker = raw_claim.get("public_marker")
    evidence = raw_claim.get("evidence")
    if not all(isinstance(value, str) and value for value in (claim_id, document, public_marker)):
        return TruthCheck("unknown", "failed", "RC_TRUTH_CLAIM_INVALID", "Claim identity or public marker is invalid")
    if not isinstance(evidence, list) or not evidence:
        return TruthCheck(claim_id, "failed", "RC_TRUTH_EVIDENCE_REQUIRED", "Claim has no evidence mapping")
    document_path = _resolve_project_path(project_root, document)
    if document_path is None or not document_path.is_file():
        return TruthCheck(claim_id, "failed", "RC_TRUTH_DOCUMENT_MISSING", f"Public document is missing: {Path(document).name}")
    if public_marker not in document_path.read_text(encoding="utf-8"):
        return TruthCheck(claim_id, "failed", "RC_TRUTH_PUBLIC_MARKER_MISSING", "Public claim marker is missing")
    for entry in evidence:
        issue = _validate_evidence(project_root, entry)
        if issue is not None:
            code, detail = issue
            return TruthCheck(claim_id, "failed", code, detail)
    return TruthCheck(claim_id, "passed", None, "Public claim has matching evidence anchors")


def _validate_evidence(project_root: Path, entry: object) -> tuple[str, str] | None:
    if not isinstance(entry, dict):
        return "RC_TRUTH_EVIDENCE_INVALID", "Evidence entry is invalid"
    kind = entry.get("kind")
    relative_path = entry.get("path")
    markers = entry.get("required_markers")
    if kind not in _EVIDENCE_KINDS or not isinstance(relative_path, str):
        return "RC_TRUTH_EVIDENCE_INVALID", "Evidence kind or path is invalid"
    if not isinstance(markers, list) or not markers or not all(isinstance(marker, str) and marker for marker in markers):
        return "RC_TRUTH_EVIDENCE_MARKERS_REQUIRED", "Evidence requires one or more exact markers"
    evidence_path = _resolve_project_path(project_root, relative_path)
    if evidence_path is None or not evidence_path.is_file():
        return "RC_TRUTH_EVIDENCE_MISSING", f"Evidence file is missing: {Path(relative_path).name}"
    source = evidence_path.read_text(encoding="utf-8")
    if not all(marker in source for marker in markers):
        return "RC_TRUTH_EVIDENCE_MARKER_MISSING", "Evidence markers do not match the declared source"
    return None


def _resolve_project_path(project_root: Path, relative_path: str) -> Path | None:
    candidate = (project_root / relative_path).resolve()
    try:
        candidate.relative_to(project_root.resolve())
    except ValueError:
        return None
    return candidate
