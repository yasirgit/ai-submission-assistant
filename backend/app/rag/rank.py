"""Shared top-k selection so the two retrievers stay comparable."""

from collections.abc import Callable
from dataclasses import replace

from app.rag.filter import metadata_matches
from app.rag.types import RetrievalQuery, RetrievedChunk


def top_k(
    chunks: list[RetrievedChunk],
    query: RetrievalQuery,
    score_of: Callable[[RetrievedChunk], float],
) -> list[RetrievedChunk]:
    scored: list[tuple[float, str, RetrievedChunk]] = []
    for chunk in chunks:
        if not metadata_matches(chunk.metadata, query):
            continue
        score = score_of(chunk)
        if score <= 0:
            continue
        scored.append((score, chunk.chunk_id, chunk))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [replace(chunk, score=score) for score, _chunk_id, chunk in scored[: query.k]]
