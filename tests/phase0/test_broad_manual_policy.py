from __future__ import annotations

from industrialops.phase0.broad_manual_policy import apply_broad_manual_scope_policy


def test_broad_manual_policy_approves_generic_mill_content_and_flags_other_model_content() -> None:
    records = [
        {
            "unit_id": "generic",
            "source_id": "HAAS-OP-EN-2025",
            "text": "Use the emergency stop before servicing the vertical mill.",
            "applicability": "review_required",
        },
        {
            "unit_id": "other-model",
            "source_id": "HAAS-OP-EN-2025",
            "text": "UMC rotary-axis operation requires this setting.",
            "applicability": "review_required",
        },
    ]

    result = apply_broad_manual_scope_policy(
        records,
        markers_by_source={"HAAS-OP-EN-2025": ["UMC"]},
    )

    assert result == [
        {
            "unit_id": "generic",
            "source_id": "HAAS-OP-EN-2025",
            "text": "Use the emergency stop before servicing the vertical mill.",
            "applicability": "approved_in_scope",
            "applicability_reasons": ["broad_manual_generic_mill_content"],
        },
        {
            "unit_id": "other-model",
            "source_id": "HAAS-OP-EN-2025",
            "text": "UMC rotary-axis operation requires this setting.",
            "applicability": "mixed_scope_review",
            "applicability_reasons": ["broad_manual_out_of_scope_model:UMC"],
        },
    ]
