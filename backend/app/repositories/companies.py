"""Company and claims reads. Callers must already have checked entitlement."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tables import Claim, Company, User


class CompanyRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, company_id: str) -> Company | None:
        return self._session.get(Company, company_id)

    def list_claims(self, company_id: str) -> list[Claim]:
        stmt = select(Claim).where(Claim.company_id == company_id).order_by(Claim.year.desc())
        return list(self._session.scalars(stmt).all())


class UserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, user_id: str) -> User | None:
        return self._session.get(User, user_id)
