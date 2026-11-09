"""Explicit offline-only adapters for the project's local retrieval models."""
from __future__ import annotations
import hashlib
from pathlib import Path
from collections.abc import Sequence
import math

class LocalModelUnavailableError(RuntimeError): pass

def model_fingerprint(path: Path) -> str:
    config = path / "config.json"
    if not config.is_file(): raise LocalModelUnavailableError("local model config is missing")
    return hashlib.sha256(config.read_bytes()).hexdigest()

class LocalBgeM3:
    def __init__(self, path: Path) -> None:
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(str(path), local_files_only=True)
        except Exception as error: raise LocalModelUnavailableError("local BGE-M3 is unavailable") from error
        self.loaded_from_local, self.fingerprint = True, model_fingerprint(path)
    def embed(self, texts: str | list[str]) -> Sequence[float] | list[Sequence[float]]:
        result = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        rows = result.tolist()
        vectors = rows if isinstance(texts, list) else rows
        sample = vectors[0] if isinstance(texts, list) else vectors
        if len(sample) != 1024 or not all(math.isfinite(value) for value in sample): raise LocalModelUnavailableError("BGE-M3 embedding is not a finite 1024-dimensional vector")
        return vectors

class LocalCrossEncoder:
    def __init__(self, path: Path) -> None:
        try:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(str(path), local_files_only=True, max_length=512)
        except Exception as error: raise LocalModelUnavailableError("local reranker is unavailable") from error
        self.loaded_from_local, self.fingerprint = True, model_fingerprint(path)
    def score(self, query: str, text: str) -> float:
        value = float(self._model.predict([(query, text)])[0])
        if not math.isfinite(value): raise LocalModelUnavailableError("local reranker emitted a non-finite score")
        return value
