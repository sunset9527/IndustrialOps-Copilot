from __future__ import annotations

import pytest

from industrialops.evaluation.v07.human_calibration import ReviewLabel, calculate_two_reviewer_agreement


def test_two_reviewer_agreement_reports_raw_kappa_and_disagreements() -> None:
    result = calculate_two_reviewer_agreement(
        (
            ReviewLabel("c1", "reviewer-a", "supported"), ReviewLabel("c1", "reviewer-b", "supported"),
            ReviewLabel("c2", "reviewer-a", "risk-high"), ReviewLabel("c2", "reviewer-b", "risk-high"),
            ReviewLabel("c3", "reviewer-a", "supported"), ReviewLabel("c3", "reviewer-b", "risk-high"),
            ReviewLabel("c4", "reviewer-a", "unsupported"), ReviewLabel("c4", "reviewer-b", "unsupported"),
        ),
        reviewer_a="reviewer-a",
        reviewer_b="reviewer-b",
    )

    assert result.status == "completed"
    assert result.compared_case_ids == ("c1", "c2", "c3", "c4")
    assert result.raw_agreement == 0.75
    assert result.cohens_kappa == pytest.approx(0.6363636363636364)
    assert result.disagreement_case_ids == ("c3",)


def test_single_reviewer_data_is_not_mislabeled_as_kappa() -> None:
    result = calculate_two_reviewer_agreement(
        (ReviewLabel("c1", "reviewer-a", "supported"),),
        reviewer_a="reviewer-a",
        reviewer_b="reviewer-b",
    )

    assert result.status == "not_run"
    assert result.cohens_kappa is None
    assert result.missing_second_review_case_ids == ("c1",)


def test_duplicate_label_from_one_reviewer_is_rejected() -> None:
    with pytest.raises(ValueError, match="EVALUATION_DUPLICATE_REVIEW_LABEL"):
        calculate_two_reviewer_agreement(
            (ReviewLabel("c1", "reviewer-a", "supported"), ReviewLabel("c1", "reviewer-a", "risk-high")),
            reviewer_a="reviewer-a",
            reviewer_b="reviewer-b",
        )
