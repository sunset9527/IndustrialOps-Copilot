"""Small in-memory BM25 retriever for deterministic baseline tests."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math
import re


_TOKEN_PATTERN = re.compile(r"[\w.-]+")


@dataclass(frozen=True)
class RetrievalDocument:
    document_id: str
    text: str


@dataclass(frozen=True)
class RetrievalResult:
    document_id: str
    score: float


class Bm25Index:
    def __init__(self, documents: list[RetrievalDocument]):
        self._documents = documents
        self._tokens = [_tokenize(document.text) for document in documents]
        self._document_frequency = Counter(token for tokens in self._tokens for token in set(tokens))
        self._average_length = sum(map(len, self._tokens)) / len(documents) if documents else 0.0

    @classmethod
    def from_documents(cls, documents: list[RetrievalDocument]) -> "Bm25Index":
        return cls(documents)

    def search(self, query: str, *, limit: int) -> list[RetrievalResult]:
        query_tokens = _tokenize(query)
        scored: list[RetrievalResult] = []
        for document, tokens in zip(self._documents, self._tokens, strict=True):
            score = sum(self._term_score(token, tokens) for token in query_tokens)
            if score > 0:
                scored.append(RetrievalResult(document.document_id, score))
        return sorted(scored, key=lambda result: (-result.score, result.document_id))[:limit]

    def _term_score(self, token: str, tokens: list[str]) -> float:
        frequency = tokens.count(token)
        if not frequency or not self._documents:
            return 0.0
        document_frequency = self._document_frequency[token]
        inverse_frequency = math.log(1 + (len(self._documents) - document_frequency + 0.5) / (document_frequency + 0.5))
        k1, b = 1.5, 0.75
        normalization = frequency + k1 * (1 - b + b * len(tokens) / self._average_length)
        return inverse_frequency * frequency * (k1 + 1) / normalization


def _tokenize(value: str) -> list[str]:
    return _TOKEN_PATTERN.findall(value.casefold())
