"""Analysis result and the no-guideline draft.

The HTTP path asks the bounded agent to choose tools. This module still
holds the product those tools return, including the case where search
finds nothing and the model is not asked to invent a guideline.
"""

from dataclasses import dataclass, field


@dataclass
class AnalysisProduct:
    outcome: str
    error: Exception | None
    summary: str
    extracted_data: dict
    risk_flags: list[dict]
    missing_information: list[str]
    follow_up_questions: list[str]
    confidence: float
    sources: list[dict]
    model: str
    retrieved_document_ids: list[str]
    dropped_source_ids: list[str] = field(default_factory=list)
    token_usage: dict = field(default_factory=dict)
    tool_calls: list[str] = field(default_factory=list)


def _insufficient(facts: dict, document_ids: list[str]) -> AnalysisProduct:
    return AnalysisProduct(
        outcome="INSUFFICIENT_CONTEXT",
        error=None,
        summary=("No underwriting guideline matched this submission. The draft does not invent guidance."),
        extracted_data=facts,
        risk_flags=[],
        missing_information=["No matching underwriting guideline was retrieved."],
        follow_up_questions=["Which guideline should apply to this submission?"],
        confidence=0.15,
        sources=[],
        model="none",
        retrieved_document_ids=document_ids,
        token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "repair_attempts": 0},
    )


def _document_ids(chunks) -> list[str]:
    seen: list[str] = []
    for chunk in chunks:
        if chunk.document_id not in seen:
            seen.append(chunk.document_id)
    return seen
