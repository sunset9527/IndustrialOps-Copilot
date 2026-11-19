from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from industrialops.config import Settings
from industrialops.diagnosis.deepseek import DeepSeekAnswerGenerator
from industrialops.diagnosis.schemas import Citation


def _citation() -> Citation:
    return Citation(
        evidence_id="evidence-1",
        pack_id="cnc_pack_v1.0.0",
        source_id="HAAS-TEST",
        document_revision="2025",
        page_number=3,
        evidence_locator="HAAS-TEST:p.3",
    )


def test_settings_reads_explicit_offline_delivery_paths() -> None:
    settings = Settings.from_environment({
        "INDUSTRIALOPS_OFFLINE": "true",
        "INDUSTRIALOPS_PACKS_ROOT": "D:/private/packs",
        "INDUSTRIALOPS_PACK_REGISTRY_PATH": "D:/private/registry.json",
        "INDUSTRIALOPS_INDEXES_ROOT": "D:/runtime/indexes",
        "INDUSTRIALOPS_BGE_MODEL_PATH": "D:/models/bge-m3",
        "INDUSTRIALOPS_RERANKER_MODEL_PATH": "D:/models/reranker",
    })

    assert settings.offline_mode is True
    assert settings.packs_root == Path("D:/private/packs")
    assert settings.pack_registry_path == Path("D:/private/registry.json")
    assert settings.indexes_root == Path("D:/runtime/indexes")
    assert settings.bge_model_path == Path("D:/models/bge-m3")
    assert settings.reranker_model_path == Path("D:/models/reranker")


def test_settings_rejects_invalid_boolean_offline_mode() -> None:
    with pytest.raises(ValueError, match="CONFIG_OFFLINE_MODE_INVALID"):
        Settings.from_environment({"INDUSTRIALOPS_OFFLINE": "maybe"})


def test_offline_mode_never_calls_external_answer_provider_even_when_a_key_exists() -> None:
    calls: list[httpx.Request] = []
    generator = DeepSeekAnswerGenerator.from_settings(
        api_key="test-key",
        model="deepseek-flash",
        timeout_seconds=2,
        max_tokens=100,
        offline_mode=True,
        transport=httpx.MockTransport(lambda request: calls.append(request) or httpx.Response(200, json={})),
    )

    result = generator.generate(
        question="What does alarm mean?",
        approved_evidence={"evidence-1": "Alarm evidence"},
        citations={"evidence-1": _citation()},
        allowed_fields=("confirmed_facts",),
    )

    assert calls == []
    assert result.provider == "evidence_fallback"
    assert result.fallback_reason == "OFFLINE_MODE_ENABLED"
