from __future__ import annotations

from pathlib import Path

import pytest

from industrialops.evaluation.v07.input_integrity import FrozenInputChanged, FrozenInputVerifier


def test_frozen_input_verifier_rejects_byte_changes_after_baseline_capture(tmp_path: Path) -> None:
    frozen = tmp_path / "scenario_eval_v1.jsonl"
    frozen.write_text('{"eval_id":"case-1"}\n', encoding="utf-8")
    verifier = FrozenInputVerifier.capture((frozen,))

    frozen.write_text('{"eval_id":"case-1","changed":true}\n', encoding="utf-8")

    with pytest.raises(FrozenInputChanged, match="FROZEN_INPUT_SHA256_MISMATCH"):
        verifier.verify()


def test_frozen_input_verifier_returns_named_hashes_when_inputs_are_unchanged(tmp_path: Path) -> None:
    frozen = tmp_path / "guardrail_eval_v1.jsonl"
    frozen.write_text('{"eval_id":"case-2"}\n', encoding="utf-8")
    verifier = FrozenInputVerifier.capture((frozen,))

    hashes = verifier.verify()

    assert hashes == {str(frozen): verifier.expected_hashes[str(frozen)]}
