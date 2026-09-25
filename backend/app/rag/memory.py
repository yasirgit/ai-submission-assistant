"""Lexical overlap ranker. Deterministic and easy to read in a test."""

from app.rag.rank import top_k
from app.rag.text import tokenize
from app.rag.types import RetrievalQuery, RetrievedChunk


class InMemoryRetriever:
    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        self._chunks = list(chunks)

    def retrieve(self, query: RetrievalQuery) -> list[RetrievedChunk]:
        query_tokens = tokenize(query.text)

        def score_of(chunk: RetrievedChunk) -> float:
            chunk_tokens = tokenize(f"{chunk.document_title} {chunk.content}")
            if not query_tokens or not chunk_tokens:
                return 0.0
            return len(query_tokens & chunk_tokens) / len(query_tokens)

        return top_k(self._chunks, query, score_of)
