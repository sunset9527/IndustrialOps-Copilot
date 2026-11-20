"""Auditable deterministic metrics for IndustrialOps v0.7.

The functions deliberately represent absent applicability as ``not_run``
rather than as a zero score.  They never call an LLM or infer relevance from
unreviewed text.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class MetricResult:
    name: str
    status: str
    numerator: int
    denominator: int
    rate: float | None
    passed_case_ids: tuple[str, ...]
    failed_case_ids: tuple[str, ...]
    not_run_case_ids: tuple[str, ...]
    not_run_reasons: dict[str, str]

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "status": self.status,
            "numerator": self.numerator,
            "denominator": self.denominator,
            "rate": self.rate,
            "passed_case_ids": list(self.passed_case_ids),
            "failed_case_ids": list(self.failed_case_ids),
            "not_run_case_ids": list(self.not_run_case_ids),
            "not_run_reasons": self.not_run_reasons,
        }


def binary_metric(name: str, outcomes: Iterable[tuple[str, bool | None]]) -> MetricResult:
    """Calculate a bounded rate while excluding inapplicable cases."""

    passed: list[str] = []
    failed: list[str] = []
    not_run: list[str] = []
    for case_id, outcome in outcomes:
        if outcome is None:
            not_run.append(case_id)
        elif outcome:
            passed.append(case_id)
        else:
            failed.append(case_id)
    denominator = len(passed) + len(failed)
    return MetricResult(
        name=name,
        status="completed" if denominator else "not_run",
        numerator=len(passed),
        denominator=denominator,
        rate=len(passed) / denominator if denominator else None,
        passed_case_ids=tuple(passed),
        failed_case_ids=tuple(failed),
        not_run_case_ids=tuple(not_run),
        not_run_reasons={},
    )


def inspection_evidence_coverage(
    case_id: str, *, inspection_steps: Iterable[str], supported_steps: Iterable[str]
) -> MetricResult:
    """Measure unique published inspection steps with approved evidence."""

    unique_steps = tuple(dict.fromkeys(inspection_steps))
    supported = set(supported_steps)
    if not unique_steps:
        return MetricResult(
            name="inspection_evidence_coverage",
            status="not_run",
            numerator=0,
            denominator=0,
            rate=None,
            passed_case_ids=(),
            failed_case_ids=(),
            not_run_case_ids=(case_id,),
            not_run_reasons={case_id: "NO_INSPECTION_STEPS"},
        )
    return binary_metric(
        "inspection_evidence_coverage",
        ((f"{case_id}:{index}", step in supported) for index, step in enumerate(unique_steps, start=1)),
    )


def retrieval_metrics(
    cases: Iterable[tuple[str, Iterable[Mapping[str, object]], set[str], set[int]]]
) -> dict[str, MetricResult]:
    """Calculate ranked source/page hit rates plus joint-relevance MRR/nDCG."""

    materialized = [(case_id, tuple(ranked), sources, pages) for case_id, ranked, sources, pages in cases]
    return {
        **{
            f"source_hit_at_{k}": binary_metric(
                f"source_hit_at_{k}",
                ((case_id, _has_source(ranked[:k], sources)) for case_id, ranked, sources, _ in materialized),
            )
            for k in (1, 3, 5)
        },
        **{
            f"page_hit_at_{k}": binary_metric(
                f"page_hit_at_{k}",
                ((case_id, _has_page(ranked[:k], pages)) for case_id, ranked, _, pages in materialized),
            )
            for k in (1, 3, 5)
        },
        "mrr": _rank_metric("mrr", materialized, reciprocal=True),
        "ndcg_at_5": _rank_metric("ndcg_at_5", materialized, reciprocal=False),
    }


def _has_source(ranked: Iterable[Mapping[str, object]], allowed_sources: set[str]) -> bool:
    return any(str(item.get("source_id")) in allowed_sources for item in ranked)


def _has_page(ranked: Iterable[Mapping[str, object]], allowed_pages: set[int]) -> bool:
    return any(item.get("page_number") in allowed_pages for item in ranked)


def _rank_metric(
    name: str,
    cases: Iterable[tuple[str, tuple[Mapping[str, object], ...], set[str], set[int]]],
    *,
    reciprocal: bool,
) -> MetricResult:
    scored: list[tuple[str, float]] = []
    for case_id, ranked, sources, pages in cases:
        rank = next(
            (
                index
                for index, item in enumerate(ranked[:5], start=1)
                if str(item.get("source_id")) in sources and item.get("page_number") in pages
            ),
            None,
        )
        scored.append((case_id, 0.0 if rank is None else 1 / rank if reciprocal else 1 / math.log2(rank + 1)))
    applicable = len(scored)
    passed = tuple(case_id for case_id, score in scored if score > 0)
    failed = tuple(case_id for case_id, score in scored if score == 0)
    return MetricResult(
        name=name,
        status="completed" if applicable else "not_run",
        numerator=sum(1 for _, score in scored if score > 0),
        denominator=applicable,
        rate=sum(score for _, score in scored) / applicable if applicable else None,
        passed_case_ids=passed,
        failed_case_ids=failed,
        not_run_case_ids=(),
        not_run_reasons={},
    )
