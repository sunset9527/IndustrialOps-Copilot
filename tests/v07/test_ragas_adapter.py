from __future__ import annotations

from industrialops.evaluation.v07.ragas_adapter import to_ragas_row


def test_ragas_row_keeps_only_reviewed_reference_and_explicit_metadata() -> None:
    row = to_ragas_row(
        scenario_id="v07-case-1",
        question="查询冷却液故障资料",
        response="请参照已引用的资料。",
        retrieved_contexts=("approved excerpt",),
        reference_contexts=("reviewed excerpt",),
        reference="经人工审核的参考要点",
        pack_id="cnc_pack_v1.0.0",
        evidence_ids=("e-1",),
    )

    assert row["user_input"] == "查询冷却液故障资料"
    assert row["reference"] == "经人工审核的参考要点"
    assert row["metadata"] == {"scenario_id": "v07-case-1", "pack_id": "cnc_pack_v1.0.0", "evidence_ids": ["e-1"]}
