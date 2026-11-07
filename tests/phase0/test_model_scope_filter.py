from __future__ import annotations

from industrialops.phase0.model_scope_filter import exclude_exclusive_out_of_scope_nxds_models


def test_excludes_page_that_names_only_excluded_nxds_variants() -> None:
    records = [
        {
            "candidate_id": "tip-seal-r-only",
            "text": "Fit the tip seal to an nXDS15iR or nXDS20iR pump.",
            "applicability": "mixed_scope_review",
        }
    ]

    result = exclude_exclusive_out_of_scope_nxds_models(records)

    assert result == [
        {
            "candidate_id": "tip-seal-r-only",
            "text": "Fit the tip seal to an nXDS15iR or nXDS20iR pump.",
            "applicability": "excluded",
            "applicability_reasons": [
                "exclusive_out_of_scope_models:nXDS15iR,nXDS20iR"
            ],
        }
    ]


def test_keeps_page_that_names_a_standard_nxds_model_alongside_excluded_variant() -> None:
    records = [
        {
            "candidate_id": "mixed-models",
            "text": "The nXDS20i, nXDS20iC and nXDS20iR share this illustration.",
            "applicability": "mixed_scope_review",
        }
    ]

    result = exclude_exclusive_out_of_scope_nxds_models(records)

    assert result == records
