"""Keep only citations that were actually retrieved, and copy excerpts from those chunks."""

from app.rag.text import excerpt
from app.rag.types import RetrievedChunk
from app.schemas.analysis import AnalysisDraft, SourceCitation


def ground_sources(draft: AnalysisDraft, retrieved: list[RetrievedChunk]) -> tuple[AnalysisDraft, list[str]]:
    by_id = {chunk.chunk_id: chunk for chunk in retrieved}
    kept: list[SourceCitation] = []
    dropped: list[str] = []
    seen: set[str] = set()
    for source in draft.sources:
        chunk = by_id.get(source.chunk_id)
        if chunk is None or chunk.document_id != source.document_id or source.chunk_id in seen:
            dropped.append(source.chunk_id)
            continue
        seen.add(source.chunk_id)
        kept.append(
            SourceCitation(
                document_id=chunk.document_id,
                chunk_id=chunk.chunk_id,
                title=chunk.document_title,
                excerpt=excerpt(chunk.content),
            )
        )
    confidence = min(draft.confidence, 0.4) if dropped else draft.confidence
    return draft.model_copy(update={"sources": kept, "confidence": confidence}), dropped


_TRUSTED_KEYS = (
    "company_name",
    "industry",
    "annual_revenue_eur",
    "employee_count",
    "countries",
    "product",
    "limit_eur",
    "claim_count",
    "max_claim_eur",
)


def apply_trusted_facts(extracted: dict, facts: dict) -> dict:
    """Database fields win when the model rewrites them."""
    if not facts.get("company_name"):
        return dict(extracted)
    merged = dict(extracted)
    for key in _TRUSTED_KEYS:
        if key in facts:
            merged[key] = facts[key]
    return merged
