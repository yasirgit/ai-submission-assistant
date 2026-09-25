"""Rankers return the conflicting revenue rules and skip unrelated chunks."""

from app.domain.enums import DocumentType
from app.rag.load import load_guideline_chunks
from app.rag.memory import InMemoryRetriever
from app.rag.query import build_query
from app.rag.types import RetrievedChunk
from app.rag.vector import VectorRetriever
from app.seed.catalog import chunks, companies, documents, submissions


def test_memory_and_vector_return_both_revenue_rules() -> None:
    query = _harbor_cyber_query()
    corpus = _guideline_corpus()
    for retriever in (InMemoryRetriever(corpus), VectorRetriever(corpus)):
        found = {chunk.chunk_id for chunk in retriever.retrieve(query)}
        assert "chunk-revenue-10m" in found
        assert "chunk-cyber-25m" in found
        assert "chunk-injection" not in found
        assert "chunk-geo-us" not in found
        assert "chunk-industry-energy" not in found
        assert "chunk-private-harbor" not in found
        assert len(found) <= query.k


def test_loader_skips_submission_notes(api) -> None:
    with api.app.state.session_factory() as session:
        loaded = load_guideline_chunks(session)
    ids = {chunk.chunk_id for chunk in loaded}
    assert "chunk-private-harbor" not in ids
    assert "chunk-revenue-10m" in ids
    assert len(ids) >= 10


def _harbor_cyber_query():
    company = next(row for row in companies() if row.id == "company-harbor")
    submission = next(row for row in submissions() if row.id == "sub-alice-harbor-cyber")
    return build_query(submission, company, k=5)


def _guideline_corpus() -> list[RetrievedChunk]:
    titles = {document.id: document for document in documents()}
    corpus = []
    for chunk in chunks():
        document = titles[chunk.document_id]
        if document.doc_type != DocumentType.GUIDELINE:
            continue
        corpus.append(
            RetrievedChunk(
                document_id=document.id,
                document_title=document.title,
                chunk_id=chunk.id,
                content=chunk.content,
                metadata=dict(chunk.chunk_metadata),
            )
        )
    return corpus
