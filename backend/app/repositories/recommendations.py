"""Draft analyses and the human review attached to them."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tables import AIRecommendation, Review


class RecommendationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def latest(self, submission_id: str) -> AIRecommendation | None:
        stmt = (
            select(AIRecommendation)
            .where(AIRecommendation.submission_id == submission_id)
            .order_by(AIRecommendation.created_at.desc())
            .limit(1)
        )
        return self._session.scalars(stmt).one_or_none()

    def add(self, recommendation: AIRecommendation) -> AIRecommendation:
        self._session.add(recommendation)
        self._session.flush()
        return recommendation


class ReviewRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def for_recommendation(self, recommendation_id: str) -> Review | None:
        stmt = select(Review).where(Review.recommendation_id == recommendation_id)
        return self._session.scalars(stmt).one_or_none()

    def add(self, review: Review) -> Review:
        self._session.add(review)
        self._session.flush()
        return review
