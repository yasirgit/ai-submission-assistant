"""Choose a retriever implementation from configuration."""

from collections.abc import Callable

from sqlalchemy.orm import Session

from app.rag.load import load_guideline_chunks
from app.rag.memory import InMemoryRetriever
from app.rag.vector import VectorRetriever


def make_retriever_builder(kind: str) -> Callable[[Session], InMemoryRetriever | VectorRetriever]:
    if kind not in {"memory", "vector"}:
        raise ValueError("retriever must be 'memory' or 'vector'")

    def build(session: Session) -> InMemoryRetriever | VectorRetriever:
        chunks = load_guideline_chunks(session)
        if kind == "vector":
            return VectorRetriever(chunks)
        return InMemoryRetriever(chunks)

    return build
