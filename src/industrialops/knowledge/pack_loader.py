"""Load verified, frozen equipment knowledge packs."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from industrialops.phase0.pack_freezer import _canonical_hash


class PackLoadError(ValueError):
    """A frozen knowledge pack failed deterministic verification."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True)
class EquipmentDocument:
    """Frozen evidence enriched with versioned industrial applicability metadata."""

    document_id: str
    pack_id: str
    equipment_type: str
    manufacturer: str
    applicable_models: tuple[str, ...]
    controller: str
    source_id: str
    source_file: str
    source_sha256: str
    document_revision: str
    page_number: int
    evidence_locator: str
    text: str
    text_zh: str
    language: str
    translation_status: str
    source_record_id: str
    registry_version: str


@dataclass(frozen=True)
class AlarmRecord:
    """An approved structured alarm candidate from a loaded frozen pack."""

    candidate_id: str
    pack_id: str
    label: str
    source_id: str
    source_file: str
    source_sha256: str
    page_number: int
    evidence_locator: str
    evidence_text: str


@dataclass(frozen=True)
class StructuredEvidence:
    """An approved structured candidate that remains traceable to frozen evidence."""

    evidence_id: str
    candidate_id: str
    candidate_type: str
    pack_id: str
    label: str
    source_id: str
    source_file: str
    source_sha256: str
    page_number: int
    evidence_locator: str
    evidence_text: str


@dataclass(frozen=True)
class EquipmentPack:
    """A fully verified equipment knowledge pack with no partial-load state."""

    pack_id: str
    content_sha256: str
    registry_version: str
    documents: tuple[EquipmentDocument, ...]
    alarm_records: tuple[AlarmRecord, ...]
    structured_evidence: tuple[StructuredEvidence, ...]


class EquipmentPackLoader:
    """Public entry point for loading verified equipment knowledge packs."""

    def __init__(self, packs_root: Path, registry_path: Path) -> None:
        self._packs_root = packs_root
        self._registry_path = registry_path

    def load(self, pack_id: str) -> EquipmentPack:
        """Return one validated pack or fail without exposing a partial result."""

        pack_directory = self._packs_root / pack_id
        manifest = self._read_json(pack_directory / "manifest.json", "PACK_MANIFEST_MISSING")
        registry = self._read_json(self._registry_path, "PACK_REGISTRY_MISSING")
        registry_version = self._required_string(registry, "registry_version", "REGISTRY_VERSION_MISSING")
        pack_registry = self._required_mapping(
            self._required_mapping(registry, "packs", "REGISTRY_PACKS_MISSING"),
            pack_id,
            "REGISTRY_PACK_MISSING",
        )

        if manifest.get("pack_id") != pack_id:
            raise PackLoadError("PACK_ID_MISMATCH", f"manifest does not declare {pack_id!r}")
        corpus = self._read_jsonl(pack_directory / "corpus.jsonl", "PACK_CORPUS_MISSING")
        structured = self._read_jsonl(
            pack_directory / "structured_candidates_auto_reviewed.jsonl",
            "PACK_STRUCTURED_MISSING",
        )
        self._verify_manifest_counts(manifest, corpus, structured)
        content_sha256 = self._required_string(manifest, "content_sha256", "PACK_CONTENT_HASH_MISSING")
        if _canonical_hash(corpus) != content_sha256:
            raise PackLoadError("PACK_CONTENT_HASH_MISMATCH", f"pack {pack_id!r} corpus hash differs from its manifest")

        manifest_sources = self._sources_by_id(manifest)
        registry_sources = self._required_mapping(pack_registry, "sources", "REGISTRY_SOURCES_MISSING")
        documents = tuple(
            self._to_document(record, pack_id, pack_registry, registry_sources, manifest_sources, registry_version)
            for record in corpus
        )
        alarm_records = tuple(
            self._to_alarm_record(record, pack_id, manifest_sources)
            for record in structured
            if record.get("candidate_status") == "auto_reviewed_include" and record.get("candidate_type") == "alarms"
        )
        structured_evidence = tuple(
            self._to_structured_evidence(record, pack_id, manifest_sources)
            for record in structured
            if record.get("candidate_status") == "auto_reviewed_include"
        )
        return EquipmentPack(
            pack_id=pack_id,
            content_sha256=content_sha256,
            registry_version=registry_version,
            documents=documents,
            alarm_records=alarm_records,
            structured_evidence=structured_evidence,
        )

    @staticmethod
    def _read_json(path: Path, missing_code: str) -> dict[str, Any]:
        if not path.is_file():
            raise PackLoadError(missing_code, f"required file is missing: {path.name}")
        try:
            parsed = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise PackLoadError("PACK_JSON_INVALID", f"invalid JSON in {path.name}") from error
        if not isinstance(parsed, dict):
            raise PackLoadError("PACK_JSON_INVALID", f"{path.name} must contain an object")
        return parsed

    @staticmethod
    def _read_jsonl(path: Path, missing_code: str) -> list[dict[str, Any]]:
        if not path.is_file():
            raise PackLoadError(missing_code, f"required file is missing: {path.name}")
        records: list[dict[str, Any]] = []
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise PackLoadError("PACK_JSONL_INVALID", f"invalid JSONL at {path.name}:{line_number}") from error
            if not isinstance(record, dict):
                raise PackLoadError("PACK_JSONL_INVALID", f"{path.name}:{line_number} must contain an object")
            records.append(record)
        return records

    @staticmethod
    def _required_mapping(mapping: dict[str, Any], key: str, code: str) -> dict[str, Any]:
        value = mapping.get(key)
        if not isinstance(value, dict):
            raise PackLoadError(code, f"required object {key!r} is absent")
        return value

    @staticmethod
    def _required_string(mapping: dict[str, Any], key: str, code: str) -> str:
        value = mapping.get(key)
        if not isinstance(value, str) or not value:
            raise PackLoadError(code, f"required string {key!r} is absent")
        return value

    def _verify_manifest_counts(
        self,
        manifest: dict[str, Any],
        corpus: list[dict[str, Any]],
        structured: list[dict[str, Any]],
    ) -> None:
        if manifest.get("corpus_record_count") != len(corpus):
            raise PackLoadError("PACK_CORPUS_COUNT_MISMATCH", "corpus record count differs from manifest")
        if manifest.get("structured_candidate_count") != len(structured):
            raise PackLoadError("PACK_STRUCTURED_COUNT_MISMATCH", "structured record count differs from manifest")

    def _sources_by_id(self, manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
        sources = manifest.get("sources")
        if not isinstance(sources, list):
            raise PackLoadError("PACK_SOURCES_INVALID", "manifest sources must be a list")
        if manifest.get("source_count") != len(sources):
            raise PackLoadError("PACK_SOURCE_COUNT_MISMATCH", "source count differs from manifest")
        source_by_id: dict[str, dict[str, Any]] = {}
        for source in sources:
            if not isinstance(source, dict):
                raise PackLoadError("PACK_SOURCES_INVALID", "manifest source must be an object")
            source_id = self._required_string(source, "source_id", "PACK_SOURCE_ID_MISSING")
            if source_id in source_by_id:
                raise PackLoadError("PACK_SOURCE_DUPLICATE", f"duplicate source ID {source_id!r}")
            source_by_id[source_id] = source
        return source_by_id

    def _to_document(
        self,
        record: dict[str, Any],
        pack_id: str,
        pack_registry: dict[str, Any],
        registry_sources: dict[str, Any],
        manifest_sources: dict[str, dict[str, Any]],
        registry_version: str,
    ) -> EquipmentDocument:
        self._verify_record_provenance(record, pack_id, manifest_sources)
        if record.get("applicability") != "approved_in_scope":
            raise PackLoadError("PACK_CORPUS_APPLICABILITY_INVALID", "corpus record is not approved_in_scope")
        source_id = self._required_string(record, "source_id", "PACK_RECORD_SOURCE_MISSING")
        source_registry = self._required_mapping(registry_sources, source_id, "REGISTRY_SOURCE_MISSING")
        models = source_registry.get("applicable_models")
        if not isinstance(models, list) or not models or not all(isinstance(model, str) and model for model in models):
            raise PackLoadError("REGISTRY_SOURCE_MODELS_INVALID", f"source {source_id!r} has no applicable models")
        return EquipmentDocument(
            document_id=self._document_id(record),
            pack_id=pack_id,
            equipment_type=self._required_string(pack_registry, "equipment_type", "REGISTRY_EQUIPMENT_TYPE_MISSING"),
            manufacturer=self._required_string(pack_registry, "manufacturer", "REGISTRY_MANUFACTURER_MISSING"),
            applicable_models=tuple(models),
            controller=self._required_string(source_registry, "controller", "REGISTRY_SOURCE_CONTROLLER_MISSING"),
            source_id=source_id,
            source_file=self._required_string(record, "source_file", "PACK_RECORD_SOURCE_FILE_MISSING"),
            source_sha256=self._required_string(record, "source_sha256", "PACK_RECORD_SOURCE_HASH_MISSING"),
            document_revision=self._required_string(source_registry, "document_revision", "REGISTRY_SOURCE_REVISION_MISSING"),
            page_number=record["page_number"] if isinstance(record.get("page_number"), int) else self._invalid_page_number(),
            evidence_locator=self._required_string(record, "evidence_locator", "PACK_EVIDENCE_LOCATOR_MISSING"),
            text=self._required_string(record, "text", "PACK_TEXT_MISSING"),
            text_zh=self._required_string(record, "text_zh", "PACK_TEXT_ZH_MISSING"),
            language=self._required_string(record, "language", "PACK_LANGUAGE_MISSING"),
            translation_status=self._required_string(record, "translation_status", "PACK_TRANSLATION_STATUS_MISSING"),
            source_record_id=self._source_record_id(record),
            registry_version=registry_version,
        )

    def _to_alarm_record(
        self,
        record: dict[str, Any],
        pack_id: str,
        manifest_sources: dict[str, dict[str, Any]],
    ) -> AlarmRecord:
        self._verify_record_provenance(record, pack_id, manifest_sources)
        return AlarmRecord(
            candidate_id=self._required_string(record, "candidate_id", "PACK_ALARM_ID_MISSING"),
            pack_id=pack_id,
            label=self._required_string(record, "label", "PACK_ALARM_LABEL_MISSING"),
            source_id=self._required_string(record, "source_id", "PACK_RECORD_SOURCE_MISSING"),
            source_file=self._required_string(record, "source_file", "PACK_RECORD_SOURCE_FILE_MISSING"),
            source_sha256=self._required_string(record, "source_sha256", "PACK_RECORD_SOURCE_HASH_MISSING"),
            page_number=record["page_number"] if isinstance(record.get("page_number"), int) else self._invalid_page_number(),
            evidence_locator=self._required_string(record, "evidence_locator", "PACK_EVIDENCE_LOCATOR_MISSING"),
            evidence_text=self._required_string(record, "evidence_text", "PACK_ALARM_EVIDENCE_MISSING"),
        )

    def _to_structured_evidence(
        self,
        record: dict[str, Any],
        pack_id: str,
        manifest_sources: dict[str, dict[str, Any]],
    ) -> StructuredEvidence:
        self._verify_record_provenance(record, pack_id, manifest_sources)
        candidate_id = self._required_string(record, "candidate_id", "PACK_STRUCTURED_ID_MISSING")
        return StructuredEvidence(
            evidence_id=candidate_id,
            candidate_id=candidate_id,
            candidate_type=self._required_string(record, "candidate_type", "PACK_STRUCTURED_TYPE_MISSING"),
            pack_id=pack_id,
            label=self._required_string(record, "label", "PACK_STRUCTURED_LABEL_MISSING"),
            source_id=self._required_string(record, "source_id", "PACK_RECORD_SOURCE_MISSING"),
            source_file=self._required_string(record, "source_file", "PACK_RECORD_SOURCE_FILE_MISSING"),
            source_sha256=self._required_string(record, "source_sha256", "PACK_RECORD_SOURCE_HASH_MISSING"),
            page_number=record["page_number"] if isinstance(record.get("page_number"), int) else self._invalid_page_number(),
            evidence_locator=self._required_string(record, "evidence_locator", "PACK_EVIDENCE_LOCATOR_MISSING"),
            evidence_text=self._required_string(record, "evidence_text", "PACK_STRUCTURED_EVIDENCE_MISSING"),
        )

    @staticmethod
    def _invalid_page_number() -> int:
        raise PackLoadError("PACK_PAGE_NUMBER_INVALID", "page number must be an integer")

    def _document_id(self, record: dict[str, Any]) -> str:
        chunk_id = record.get("chunk_id")
        if isinstance(chunk_id, str) and chunk_id:
            return chunk_id
        candidate_id = record.get("candidate_id")
        if isinstance(candidate_id, str) and candidate_id:
            return candidate_id
        return self._required_string(record, "unit_id", "PACK_DOCUMENT_ID_MISSING")

    def _source_record_id(self, record: dict[str, Any]) -> str:
        candidate_id = record.get("candidate_id")
        if isinstance(candidate_id, str) and candidate_id:
            return candidate_id
        parent_candidate_id = record.get("parent_candidate_id")
        if isinstance(parent_candidate_id, str) and parent_candidate_id:
            return parent_candidate_id
        unit_id = record.get("unit_id")
        if isinstance(unit_id, str) and unit_id:
            return unit_id
        return self._required_string(record, "chunk_id", "PACK_SOURCE_RECORD_ID_MISSING")

    def _verify_record_provenance(
        self,
        record: dict[str, Any],
        pack_id: str,
        manifest_sources: dict[str, dict[str, Any]],
    ) -> None:
        if record.get("pack_id") != pack_id:
            raise PackLoadError("PACK_RECORD_ID_MISMATCH", f"record does not belong to {pack_id!r}")
        source_id = self._required_string(record, "source_id", "PACK_RECORD_SOURCE_MISSING")
        source = manifest_sources.get(source_id)
        if source is None:
            raise PackLoadError("PACK_RECORD_SOURCE_UNKNOWN", f"record references unknown source {source_id!r}")
        if record.get("source_file") != source.get("relative_path"):
            raise PackLoadError("PACK_RECORD_SOURCE_FILE_MISMATCH", f"source file differs for {source_id!r}")
        if record.get("source_sha256") != source.get("sha256"):
            raise PackLoadError("PACK_RECORD_SOURCE_HASH_MISMATCH", f"source hash differs for {source_id!r}")
