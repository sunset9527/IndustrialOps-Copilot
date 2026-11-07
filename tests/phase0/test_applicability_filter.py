from __future__ import annotations

from industrialops.phase0.applicability_filter import apply_exclusion_terms


def test_apply_exclusion_terms_marks_explicit_out_of_scope_option_for_mixed_scope_review() -> None:
    candidates = [
        {
            "candidate_id": "c1",
            "text": "TSC coolant option installation procedure",
            "applicability": "review_required",
        }
    ]

    filtered = apply_exclusion_terms(candidates, ["TSC", "robot"])

    assert filtered == [
        {
            "candidate_id": "c1",
            "text": "TSC coolant option installation procedure",
            "applicability": "mixed_scope_review",
            "applicability_reasons": ["explicit_out_of_scope_term:TSC"],
        }
    ]


def test_apply_exclusion_terms_keeps_unmatched_candidate_for_review() -> None:
    candidates = [
        {
            "candidate_id": "c2",
            "text": "Check the standard flood coolant pump.",
            "applicability": "review_required",
        }
    ]

    filtered = apply_exclusion_terms(candidates, ["TSC", "robot"])

    assert filtered == [
        {
            "candidate_id": "c2",
            "text": "Check the standard flood coolant pump.",
            "applicability": "review_required",
            "applicability_reasons": [],
        }
    ]
