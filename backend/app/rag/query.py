"""Build a retrieval query from structured submission fields, not from raw narrative."""

from app.rag.types import RetrievalQuery


def build_query(submission, company, k: int) -> RetrievalQuery:
    product = submission.requested_coverage["product"]
    text = " ".join(
        [
            company.industry,
            " ".join(company.countries),
            product,
            "revenue employees claims coverage underwriting review",
        ]
    )
    return RetrievalQuery(
        text=text,
        industry=company.industry,
        countries=tuple(company.countries),
        product=product,
        k=k,
    )
