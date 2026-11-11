"""Run the offline, frozen v0.2 retrieval baseline; never silently downgrade models."""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
from pathlib import Path

from industrialops.evaluation.industrial_retrieval import calculate_metrics, load_frozen_scenarios, write_report
from industrialops.knowledge.pack_loader import EquipmentPackLoader
from industrialops.retrieval.bm25 import Bm25Index, RetrievalDocument
from industrialops.retrieval.fusion import reciprocal_rank_fusion
from industrialops.retrieval.local_models import LocalBgeM3, LocalCrossEncoder
from industrialops.retrieval.vector import VectorIndex


def _progress(stage: str, **details: object) -> None:
    """Emit a flushed, machine-readable checkpoint for long local model runs."""
    try:
        import psutil

        details["available_memory_bytes"] = psutil.virtual_memory().available
    except Exception:
        details["available_memory_bytes"] = None
    print(json.dumps({"stage": stage, **details}, ensure_ascii=False), flush=True)


def _results(pack, ids):
    documents = {item.document_id: item for item in pack.documents}
    return [{"document_id": item, "source_id": documents[item].source_id, "page_number": documents[item].page_number} for item in ids]


def _embed_with_progress(embedding: LocalBgeM3, texts: list[str], pack_id: str) -> list[object]:
    """Embed in LexRAG-sized batches and make long CPU work observable."""
    vectors: list[object] = []
    batch_size = 8
    total_batches = (len(texts) + batch_size - 1) // batch_size
    for batch_number, offset in enumerate(range(0, len(texts), batch_size), start=1):
        batch = texts[offset : offset + batch_size]
        vectors.extend(embedding.embed(batch))
        if batch_number == total_batches or batch_number % 10 == 0:
            _progress(
                "bge_encode_progress",
                pack_id=pack_id,
                batch_number=batch_number,
                total_batches=total_batches,
                documents_completed=min(offset + len(batch), len(texts)),
            )
    return vectors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--embedding-model", type=Path, default=Path(r"E:\huggingface\model"))
    parser.add_argument("--reranker-model", type=Path, default=Path(r"E:\huggingface\bge-reranker-base"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.project_root
    loader = EquipmentPackLoader(root / "data/packs", root / "config/equipment_pack_registry_v1.json")
    scenarios = load_frozen_scenarios(root / "data/evaluation/scenario_eval_v1.jsonl")
    # Do not hold BGE-M3 and the CrossEncoder in memory together.  Both models
    # must be real local models, but their work is independent: first persist
    # the BGE/BM25/RRF candidates in process memory, then release BGE before
    # loading the reranker for the same RRF candidates.
    _progress("before_bge_load", model_path=str(args.embedding_model))
    embedding = LocalBgeM3(args.embedding_model)
    _progress("after_bge_load", model_fingerprint=embedding.fingerprint)
    intermediate = {}
    for pack_id in sorted({str(item["expected_pack_id"]) for item in scenarios}):
        pack = loader.load(pack_id)
        texts = [item.text + " " + item.text_zh for item in pack.documents]
        _progress("before_bge_encode", pack_id=pack_id, document_count=len(texts))
        vectors = _embed_with_progress(embedding, texts, pack_id)
        _progress("after_bge_encode", pack_id=pack_id, vector_count=len(vectors))
        vector = VectorIndex(dict(zip((item.document_id for item in pack.documents), vectors, strict=True)), embedder=lambda query: embedding.embed(query))
        bm25 = Bm25Index.from_documents([RetrievalDocument(item.document_id, text) for item, text in zip(pack.documents, texts, strict=True)])
        by_id = {item.document_id: item for item in pack.documents}
        cases = [item for item in scenarios if item["expected_pack_id"] == pack_id]
        methods = {name: [] for name in ("bm25", "vector", "rrf")}
        rrf_candidates = []
        for case in cases:
            question = str(case["prompt"])
            bm25_ids = [item.document_id for item in bm25.search(question, limit=20)]
            vector_ids = vector.search(question, limit=20)
            rrf_ids = reciprocal_rank_fusion([bm25_ids, vector_ids], limit=20)
            rrf_candidates.append((question, rrf_ids, by_id))
            for name, ids in (("bm25", bm25_ids), ("vector", vector_ids), ("rrf", rrf_ids)):
                methods[name].append(_results(pack, ids[:5]))
        intermediate[pack_id] = (pack, cases, methods, rrf_candidates)
    embedding_fingerprint = embedding.fingerprint
    _progress("before_bge_release")
    del embedding
    gc.collect()
    _progress("after_bge_release")

    _progress("before_reranker_load", model_path=str(args.reranker_model))
    reranker = LocalCrossEncoder(args.reranker_model)
    _progress("after_reranker_load", model_fingerprint=reranker.fingerprint)
    all_results = {}
    for pack_id, (pack, cases, methods, rrf_candidates) in intermediate.items():
        rerank_rows = []
        for question, rrf_ids, by_id in rrf_candidates:
            rerank_ids = sorted(rrf_ids, key=lambda item: (-reranker.score(question, by_id[item].text + " " + by_id[item].text_zh), item))
            rerank_rows.append(_results(pack, rerank_ids[:5]))
        methods["rerank"] = rerank_rows
        all_results[pack_id] = {name: {"metrics": calculate_metrics(list(zip(rows, cases, strict=True))).__dict__, "cases": [{"eval_id": case["eval_id"], "results": rows[index]} for index, case in enumerate(cases)]} for name, rows in methods.items()}
    payload = {"scenario_sha256": hashlib.sha256((root / "data/evaluation/scenario_eval_v1.jsonl").read_bytes()).hexdigest(), "pack_hashes": {pack: loader.load(pack).content_sha256 for pack in all_results}, "registry_sha256": hashlib.sha256((root / "config/equipment_pack_registry_v1.json").read_bytes()).hexdigest(), "model_fingerprints": {"bge_m3": embedding_fingerprint, "bge_reranker_base": reranker.fingerprint}, "loaded_from_local": True, "results": all_results}
    write_report(args.output, payload)
    _progress("report_written", output=str(args.output))


if __name__ == "__main__":
    main()
