"""Bag-of-words vectors and cosine similarity.

Each token is a dimension. The score is the cosine between the query vector
and a chunk vector. This is the VectorRetriever port: a later pgvector index
can replace the class without changing the caller. There is no embedding model
and no second database.
"""

import math

from app.rag.rank import top_k
from app.rag.text import tokenize
from app.rag.types import RetrievalQuery, RetrievedChunk


class VectorRetriever:
    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        self._chunks = list(chunks)
        vocabulary = sorted({token for chunk in self._chunks for token in _tokens(chunk)})
        self._index = {token: position for position, token in enumerate(vocabulary)}
        self._vectors = {chunk.chunk_id: self._embed(_tokens(chunk)) for chunk in self._chunks}

    def retrieve(self, query: RetrievalQuery) -> list[RetrievedChunk]:
        query_tokens = tokenize(query.text)
        query_vector = self._embed(query_tokens)

        def score_of(chunk: RetrievedChunk) -> float:
            if query_tokens.isdisjoint(_tokens(chunk)):
                return 0.0
            return _cosine(query_vector, self._vectors[chunk.chunk_id])

        return top_k(self._chunks, query, score_of)

    def _embed(self, tokens: set[str]) -> list[float]:
        vector = [0.0] * len(self._index)
        for token in tokens:
            position = self._index.get(token)
            if position is not None:
                vector[position] = 1.0
        return _normalize(vector)


def _tokens(chunk: RetrievedChunk) -> set[str]:
    return tokenize(f"{chunk.document_title} {chunk.content}")


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=True))
