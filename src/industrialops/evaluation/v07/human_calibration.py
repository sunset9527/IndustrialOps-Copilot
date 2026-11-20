"""Local, auditable two-reviewer agreement calculations.

This module only calculates agreement from supplied human labels.  It never
substitutes model output, duplicate sampling, or a single review for a second
independent reviewer.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from collections.abc import Iterable


@dataclass(frozen=True)
class ReviewLabel:
    case_id: str
    reviewer_id: str
    label: str


@dataclass(frozen=True)
class AgreementResult:
    status: str
    compared_case_ids: tuple[str, ...]
    missing_second_review_case_ids: tuple[str, ...]
    raw_agreement: float | None
    cohens_kappa: float | None
    disagreement_case_ids: tuple[str, ...]
    reason: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "compared_case_ids": list(self.compared_case_ids),
            "missing_second_review_case_ids": list(self.missing_second_review_case_ids),
            "raw_agreement": self.raw_agreement,
            "cohens_kappa": self.cohens_kappa,
            "disagreement_case_ids": list(self.disagreement_case_ids),
            "reason": self.reason,
        }


def calculate_two_reviewer_agreement(
    labels: Iterable[ReviewLabel], *, reviewer_a: str, reviewer_b: str
) -> AgreementResult:
    """Calculate raw agreement and Cohen's Kappa for two named reviewers."""

    if reviewer_a == reviewer_b:
        raise ValueError("EVALUATION_REVIEWERS_MUST_BE_DISTINCT")
    by_case: dict[str, dict[str, str]] = {}
    for item in labels:
        if item.reviewer_id not in {reviewer_a, reviewer_b}:
            continue
        reviewer_labels = by_case.setdefault(item.case_id, {})
        if item.reviewer_id in reviewer_labels:
            raise ValueError("EVALUATION_DUPLICATE_REVIEW_LABEL")
        reviewer_labels[item.reviewer_id] = item.label

    compared = tuple(sorted(case_id for case_id, values in by_case.items() if set(values) == {reviewer_a, reviewer_b}))
    incomplete = tuple(sorted(case_id for case_id, values in by_case.items() if set(values) != {reviewer_a, reviewer_b}))
    if not compared:
        return AgreementResult("not_run", (), incomplete, None, None, (), "TWO_INDEPENDENT_REVIEWS_REQUIRED")

    first = [by_case[case_id][reviewer_a] for case_id in compared]
    second = [by_case[case_id][reviewer_b] for case_id in compared]
    agreement_count = sum(left == right for left, right in zip(first, second, strict=True))
    raw_agreement = agreement_count / len(compared)
    first_counts, second_counts = Counter(first), Counter(second)
    expected_agreement = sum(
        (first_counts[label] / len(compared)) * (second_counts[label] / len(compared))
        for label in set(first_counts) | set(second_counts)
    )
    kappa = None if expected_agreement == 1 else (raw_agreement - expected_agreement) / (1 - expected_agreement)
    disagreement = tuple(case_id for case_id, left, right in zip(compared, first, second, strict=True) if left != right)
    return AgreementResult("completed", compared, incomplete, raw_agreement, kappa, disagreement)
