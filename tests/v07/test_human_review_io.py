from __future__ import annotations

import json
from pathlib import Path

import pytest

from industrialops.evaluation.v07.human_calibration import load_review_labels, write_agreement_report


def test_review_label_loader_requires_a_complete_independent_label(tmp_path: Path) -> None:
    source = tmp_path / "reviews.jsonl"
    source.write_text(
        '{"case_id":"case-1","reviewer_id":"reviewer-a","label":"supported"}\n'
        '{"case_id":"case-1","reviewer_id":"reviewer-b","label":"supported"}\n',
        encoding="utf-8",
    )

    labels = load_review_labels(source)

    assert tuple((item.case_id, item.reviewer_id, item.label) for item in labels) == (
        ("case-1", "reviewer-a", "supported"), ("case-1", "reviewer-b", "supported"),
    )


def test_review_label_loader_rejects_missing_or_blank_values(tmp_path: Path) -> None:
    source = tmp_path / "invalid.jsonl"
    source.write_text('{"case_id":"case-1","reviewer_id":"reviewer-a"}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="EVALUATION_REVIEW_LABEL_INVALID"):
        load_review_labels(source)


def test_agreement_report_is_append_only(tmp_path: Path) -> None:
    destination = tmp_path / "agreement.json"
    write_agreement_report(destination, {"status": "completed"})

    assert json.loads(destination.read_text(encoding="utf-8")) == {"status": "completed"}
    with pytest.raises(FileExistsError, match="EVALUATION_REVIEW_REPORT_EXISTS"):
        write_agreement_report(destination, {"status": "completed"})
