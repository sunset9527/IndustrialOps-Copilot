"""Re-evaluate scope at the smaller, same-page segment granularity."""

from __future__ import annotations

from industrialops.phase0.applicability_filter import apply_exclusion_terms
from industrialops.phase0.source_scope_policy import apply_source_scope_policy


def classify_segment_scope(
    segments: list[dict[str, object]],
    exclusion_terms: list[str],
    broad_review_sources: set[str],
    catalog_sources: set[str],
) -> list[dict[str, object]]:
    """Classify chunks afresh rather than inheriting a parent page's risk flag."""
    baseline = []
    for segment in segments:
        updated = dict(segment)
        updated["applicability"] = "review_required"
        updated["applicability_reasons"] = []
        baseline.append(updated)
    term_screened = apply_exclusion_terms(baseline, exclusion_terms)
    return apply_source_scope_policy(
        term_screened,
        broad_review_sources=broad_review_sources,
        catalog_sources=catalog_sources,
    )
