"""Run a tool only after the caller's entitlement is checked.

The principal is the one on the HTTP request. Tool arguments cannot replace it.
"""

import time
from dataclasses import dataclass, field, replace

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.domain.entitlements import Principal
from app.domain.errors import RetrievalUnavailableError, ToolTimeoutError
from app.rag.query import build_query
from app.rag.text import excerpt
from app.rag.types import DocumentRetriever, RetrievedChunk
from app.repositories.audit import AuditRepository
from app.repositories.companies import CompanyRepository
from app.repositories.scope import has_visible_submission
from app.repositories.submissions import SubmissionRepository
from app.services.audit import record
from app.tools.schemas import ARG_MODELS


@dataclass
class ToolOutcome:
    name: str
    ok: bool
    payload: dict
    chunks: list[RetrievedChunk] = field(default_factory=list)


class ToolGateway:
    def __init__(
        self,
        session: Session,
        principal: Principal,
        audit: AuditRepository,
        retriever: DocumentRetriever,
        *,
        submission_id: str,
        request_id: str | None,
        retrieval_k: int,
        tool_timeout_seconds: float = 2.0,
    ) -> None:
        self._session = session
        self._principal = principal
        self._audit = audit
        self._retriever = retriever
        self._submission_id = submission_id
        self._request_id = request_id
        self._retrieval_k = retrieval_k
        self._tool_timeout_seconds = tool_timeout_seconds
        self._submissions = SubmissionRepository(session)
        self._companies = CompanyRepository(session)

    def execute(self, name: str, arguments: dict) -> ToolOutcome:
        started = time.perf_counter()
        try:
            outcome = self._execute(name, arguments)
        except RetrievalUnavailableError:
            self._check_deadline(name, started)
            raise
        self._check_deadline(name, started)
        return outcome

    def _check_deadline(self, name: str, started: float) -> None:
        if time.perf_counter() - started <= self._tool_timeout_seconds:
            return
        self._write(name, False, {"error": "timeout"})
        raise ToolTimeoutError("A tool exceeded its deadline")

    def _execute(self, name: str, arguments: dict) -> ToolOutcome:
        if name not in ARG_MODELS:
            self._write(name, False, {"error": "unknown_tool"})
            return ToolOutcome(name=name, ok=False, payload={"error": "unknown_tool"})
        try:
            args = ARG_MODELS[name].model_validate(arguments)
        except ValidationError:
            self._write(name, False, {"error": "invalid_arguments"})
            return ToolOutcome(name=name, ok=False, payload={"error": "invalid_arguments"})
        outcome = self._dispatch(name, args)
        return outcome

    def _dispatch(self, name: str, args) -> ToolOutcome:
        if name == "get_submission":
            return self._submission(args.submission_id)
        if name == "get_company":
            return self._company(args.company_id)
        if name == "get_company_claims":
            return self._claims(args.company_id)
        return self._search(args.query)

    def _submission(self, submission_id: str) -> ToolOutcome:
        row = self._submissions.get_visible(self._principal, submission_id)
        if row is None:
            self._write("get_submission", False, {"submission_id": submission_id})
            return ToolOutcome("get_submission", False, {"error": "not_found"})
        payload = {
            "id": row.id,
            "company_id": row.company_id,
            "status": row.status.value,
            "requested_coverage": row.requested_coverage,
            "narrative": row.narrative,
        }
        self._write("get_submission", True, {"submission_id": row.id})
        return ToolOutcome("get_submission", True, payload)

    def _company(self, company_id: str) -> ToolOutcome:
        if not has_visible_submission(self._session, self._principal, company_id):
            self._write("get_company", False, {"company_id": company_id})
            return ToolOutcome("get_company", False, {"error": "not_found"})
        company = self._companies.get(company_id)
        if company is None:
            self._write("get_company", False, {"company_id": company_id})
            return ToolOutcome("get_company", False, {"error": "not_found"})
        payload = {
            "id": company.id,
            "name": company.name,
            "industry": company.industry,
            "annual_revenue_eur": company.annual_revenue_eur,
            "employee_count": company.employee_count,
            "countries": list(company.countries),
        }
        self._write("get_company", True, {"company_id": company.id})
        return ToolOutcome("get_company", True, payload)

    def _claims(self, company_id: str) -> ToolOutcome:
        if not has_visible_submission(self._session, self._principal, company_id):
            self._write("get_company_claims", False, {"company_id": company_id})
            return ToolOutcome("get_company_claims", False, {"error": "not_found"})
        claims = [
            {
                "id": claim.id,
                "year": claim.year,
                "claim_type": claim.claim_type,
                "amount_eur": claim.amount_eur,
            }
            for claim in self._companies.list_claims(company_id)
        ]
        self._write("get_company_claims", True, {"company_id": company_id, "claim_count": len(claims)})
        return ToolOutcome("get_company_claims", True, {"claims": claims})

    def _search(self, query: str) -> ToolOutcome:
        submission = self._submissions.get_visible(self._principal, self._submission_id)
        if submission is None:
            self._write("search_underwriting_guidelines", False, {"error": "not_found"})
            return ToolOutcome("search_underwriting_guidelines", False, {"error": "not_found"})
        company = self._companies.get(submission.company_id)
        if company is None:
            self._write("search_underwriting_guidelines", False, {"error": "not_found"})
            return ToolOutcome("search_underwriting_guidelines", False, {"error": "not_found"})
        # The model supplies the words. Industry, country, and product filters
        # come from the submission this request is already allowed to read.
        scoped = build_query(submission, company, self._retrieval_k)
        try:
            chunks = self._retriever.retrieve(replace(scoped, text=query))
        except Exception:
            self._write("search_underwriting_guidelines", False, {"error": "retrieval_unavailable"})
            raise RetrievalUnavailableError("Guideline search is unavailable") from None
        payload = {
            "results": [
                {
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "title": chunk.document_title,
                    "excerpt": excerpt(chunk.content),
                }
                for chunk in chunks
            ]
        }
        self._write(
            "search_underwriting_guidelines",
            True,
            {"chunk_ids": [chunk.chunk_id for chunk in chunks], "query_chars": len(query)},
        )
        return ToolOutcome("search_underwriting_guidelines", True, payload, chunks)

    def _write(self, tool: str, ok: bool, details: dict) -> None:
        record(
            self._audit,
            user_id=self._principal.id,
            action="tool.invoked" if ok else "tool.denied",
            resource_type="submission",
            resource_id=self._submission_id,
            request_id=self._request_id,
            details={"tool": tool, "success": ok, **details},
        )
