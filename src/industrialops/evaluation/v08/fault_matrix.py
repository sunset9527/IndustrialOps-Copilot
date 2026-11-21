"""Fail-closed accounting for the v0.8 controlled dependency-failure matrix."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from industrialops.evaluation.v08.core import assess_fault_scenario


_SCENARIOS = {
    "missing_models": "MODEL_UNAVAILABLE",
    "missing_pack": "PACK_UNAVAILABLE",
    "corrupt_index": "INDEX_UNAVAILABLE",
    "database_unavailable": "DATABASE_UNAVAILABLE",
    "llm_timeout": "DEEPSEEK_UNAVAILABLE",
    "llm_error": "DEEPSEEK_REQUEST_REJECTED",
    "offline_egress_decoy": "RC_OFFLINE_ZERO_EGRESS",
}


@dataclass(frozen=True)
class FaultMatrixResult:
    """Per-scenario evidence with a suite-level pass state."""

    rows: tuple[dict[str, str], ...]

    @property
    def passed(self) -> bool:
        return all(row["status"] == "passed" for row in self.rows)

    def by_scenario(self, scenario_id: str) -> dict[str, str]:
        for row in self.rows:
            if row["scenario_id"] == scenario_id:
                return row
        raise KeyError(scenario_id)


def evaluate_fault_matrix(observations: Mapping[str, Mapping[str, object]]) -> FaultMatrixResult:
    """Evaluate all required fault scenarios; missing evidence is always a failure."""

    rows: list[dict[str, str]] = []
    for scenario_id, expected_code in _SCENARIOS.items():
        observation = observations.get(scenario_id)
        if observation is None:
            rows.append(
                {
                    "scenario_id": scenario_id,
                    "status": "failed",
                    "reason_code": "RC_FAULT_SCENARIO_NOT_EXECUTED",
                }
            )
            continue
        outcome = assess_fault_scenario(
            expected_code=expected_code,
            observed_code=str(observation.get("observed_code", "")),
            recovered=observation.get("recovered") is True,
            safety_violation_ids=tuple(str(item) for item in observation.get("safety_violation_ids", ())),
        )
        rows.append({"scenario_id": scenario_id, **outcome})
    return FaultMatrixResult(tuple(rows))
