from __future__ import annotations

import hashlib

from industrialops.phase0.candidate_builder import build_candidates


def test_build_candidates_keeps_extracted_page_with_traceability() -> None:
    page = {
        "pack_id": "cnc_pack_v1.0.0",
        "source_id": "HAAS-TEST",
        "source_file": "cnc_haas_vf2_ngc/01_operator/manual.pdf",
        "source_sha256": "a" * 64,
        "language": "zh-CN",
        "page_number": 7,
        "text": "主轴报警诊断步骤。",
        "text_extraction_status": "extracted",
        "evidence_locator": "HAAS-TEST:p.7",
    }

    candidates = build_candidates([page])

    assert candidates == [
        {
            "candidate_id": hashlib.sha256(b"HAAS-TEST:p.7:" + b"a" * 64).hexdigest()[:24],
            "pack_id": "cnc_pack_v1.0.0",
            "source_id": "HAAS-TEST",
            "source_file": "cnc_haas_vf2_ngc/01_operator/manual.pdf",
            "source_sha256": "a" * 64,
            "language": "zh-CN",
            "page_number": 7,
            "text": "主轴报警诊断步骤。",
            "evidence_locator": "HAAS-TEST:p.7",
            "applicability": "review_required",
        }
    ]


def test_build_candidates_excludes_empty_and_reference_only_pages() -> None:
    candidates = build_candidates(
        [
            {
                "pack_id": "cnc_pack_v1.0.0",
                "source_id": "EMPTY",
                "source_file": "cnc_haas_vf2_ngc/01_operator/empty.pdf",
                "source_sha256": "b" * 64,
                "language": "zh-CN",
                "page_number": 1,
                "text": "",
                "text_extraction_status": "empty",
                "evidence_locator": "EMPTY:p.1",
            },
            {
                "pack_id": "cnc_pack_v1.0.0",
                "source_id": "LEGACY",
                "source_file": "cnc_haas_vf2_ngc/90_reference_only/legacy.pdf",
                "source_sha256": "c" * 64,
                "language": "en",
                "page_number": 1,
                "text": "Legacy text",
                "text_extraction_status": "extracted",
                "evidence_locator": "LEGACY:p.1",
            },
        ]
    )

    assert candidates == []
