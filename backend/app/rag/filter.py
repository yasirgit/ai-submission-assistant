"""Metadata filter applied before any scoring.

A chunk with no industry, product, or country constraint is general guidance
and can match. A chunk that names one of those and disagrees with the
submission is dropped before rank, so it never reaches the model.
"""

from app.rag.types import RetrievalQuery


def metadata_matches(metadata: dict, query: RetrievalQuery) -> bool:
    industry = metadata.get("industry")
    if isinstance(industry, str) and query.industry and industry.casefold() != query.industry.casefold():
        return False
    product = metadata.get("product")
    if isinstance(product, str) and query.product and product.casefold() != query.product.casefold():
        return False
    countries = metadata.get("countries") or []
    if countries and query.countries:
        wanted = {country.upper() for country in query.countries}
        named = {str(country).upper() for country in countries}
        if wanted.isdisjoint(named):
            return False
    return True
