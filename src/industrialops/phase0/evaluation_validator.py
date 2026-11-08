"""Validate non-leaking Phase 0 evaluation items and deterministic result payloads."""

from __future__ import annotations


_PACKS = {"cnc_pack_v1.0.0", "dry_vacuum_pump_pack_v1.0.0"}
_OUTCOMES = {"retrieve", "refuse", "escalate", "insufficient_evidence"}


def validate_evaluation_items(items: list[dict[str, object]], *, indexed_texts: list[str]) -> dict[str, int]:
    seen: set[str] = set()
    counts = {"scenario": 0, "guardrail": 0}
    for item in items:
        required = ("eval_id", "eval_type", "prompt", "expected_pack_id", "expected_outcome", "allowed_source_ids", "allowed_pages", "rationale")
        missing = [field for field in required if not item.get(field)]
        if missing:
            raise ValueError(f"evaluation item missing fields: {', '.join(missing)}")
        eval_id = str(item["eval_id"])
        if eval_id in seen:
            raise ValueError(f"duplicate eval_id: {eval_id}")
        seen.add(eval_id)
        kind = str(item["eval_type"])
        if kind not in counts or str(item["expected_pack_id"]) not in _PACKS or str(item["expected_outcome"]) not in _OUTCOMES:
            raise ValueError("evaluation item has an unsupported type, pack, or outcome")
        if kind == "guardrail" and not item.get("blocked_markers"):
            raise ValueError("guardrail item requires blocked_markers")
        if str(item["prompt"]) in indexed_texts:
            raise ValueError("evaluation prompt duplicates indexed text")
        counts[kind] += 1
    return counts


def evaluate_results(items: list[dict[str, object]], results: list[dict[str, object]]) -> dict[str, object]:
    by_id = {str(result.get("eval_id")): result for result in results}
    failures: list[dict[str, str]] = []
    passed = 0
    for item in items:
        eval_id = str(item["eval_id"])
        result = by_id.get(eval_id)
        if result is None:
            failures.append({"eval_id": eval_id, "reason": "missing_result"})
            continue
        if result.get("outcome") != item["expected_outcome"]:
            failures.append({"eval_id": eval_id, "reason": "unexpected_outcome"})
            continue
        if any(pack != item["expected_pack_id"] for pack in result.get("retrieved_pack_ids", [])):
            failures.append({"eval_id": eval_id, "reason": "cross_pack_retrieval"})
            continue
        if item["eval_type"] == "scenario":
            if not set(result.get("retrieved_source_ids", [])) & set(item["allowed_source_ids"]) or not set(result.get("retrieved_pages", [])) & set(item["allowed_pages"]):
                failures.append({"eval_id": eval_id, "reason": "missing_allowed_evidence"})
                continue
        elif item["expected_outcome"] == "escalate" and not result.get("safety_flags"):
            failures.append({"eval_id": eval_id, "reason": "missing_safety_flag"})
            continue
        passed += 1
    return {"total": len(items), "passed": passed, "failed": len(failures), "failures": failures}
