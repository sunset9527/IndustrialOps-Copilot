"""Frozen-scenario evaluation and auditable v0.2 report generation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path


@dataclass(frozen=True)
class RetrievalMetrics:
    hit_at_1: float
    hit_at_3: float
    hit_at_5: float
    mrr: float
    ndcg_at_5: float
    source_hit: float
    page_hit: float


def calculate_metrics(cases: list[tuple[list[dict[str, object]], dict[str, object]]]) -> RetrievalMetrics:
    if not cases:
        return RetrievalMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    hits = {1: 0, 3: 0, 5: 0}
    reciprocal = ndcg = source = page = 0.0
    for ranked, case in cases:
        sources, pages = set(map(str, case["allowed_source_ids"])), set(case["allowed_pages"])
        relevant = [str(item.get("source_id")) in sources and item.get("page_number") in pages for item in ranked]
        for k in hits:
            hits[k] += bool(any(relevant[:k]))
        if True in relevant:
            rank = relevant.index(True) + 1
            reciprocal += 1 / rank
            ndcg += 1 / math.log2(rank + 1)
        source += bool(any(str(item.get("source_id")) in sources for item in ranked[:5]))
        page += bool(any(item.get("page_number") in pages for item in ranked[:5]))
    count = len(cases)
    return RetrievalMetrics(hits[1] / count, hits[3] / count, hits[5] / count, reciprocal / count, ndcg / count, source / count, page / count)


def load_frozen_scenarios(path: Path) -> list[dict[str, object]]:
    return [item for line in path.read_text(encoding="utf-8").splitlines() if line.strip() for item in [json.loads(line)] if item.get("expected_outcome") == "retrieve"]


def write_report(output: Path, payload: dict[str, object]) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"generated_at_utc": datetime.now(timezone.utc).isoformat(), **payload}, ensure_ascii=False, indent=2), encoding="utf-8")
    return output
