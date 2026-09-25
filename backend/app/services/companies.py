"""Company and claims access. Tools in a later phase must call this, not the tables."""

from sqlalchemy.orm import Session

from app.domain.entitlements import Principal
from app.domain.errors import NotFoundError
from app.models.tables import Claim, Company
from app.repositories.companies import CompanyRepository
from app.repositories.scope import has_visible_submission


class CompanyService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._companies = CompanyRepository(session)

    def get_company(self, principal: Principal, company_id: str) -> Company:
        if not has_visible_submission(self._session, principal, company_id):
            raise NotFoundError()
        company = self._companies.get(company_id)
        if company is None:
            raise NotFoundError()
        return company

    def get_claims(self, principal: Principal, company_id: str) -> list[Claim]:
        self.get_company(principal, company_id)
        return self._companies.list_claims(company_id)
