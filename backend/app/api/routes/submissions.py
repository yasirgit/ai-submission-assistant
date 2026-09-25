"""Submission routes. Handlers call services and return schemas."""

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_principal, get_session
from app.api.errors import json_error
from app.domain.entitlements import Principal
from app.domain.errors import RetrievalUnavailableError, ToolTimeoutError
from app.llm.errors import InvalidModelOutputError, ModelUnavailableError, ToolLoopError
from app.schemas.contracts import (
    AuditList,
    RecommendationRead,
    ReviewCreate,
    SubmissionCreate,
    SubmissionDetail,
    SubmissionList,
)
from app.schemas.mapping import (
    audit_event_read,
    recommendation_read,
    submission_detail,
    submission_summary,
)
from app.services.submissions import SubmissionService

router = APIRouter(prefix="/submissions", tags=["submissions"])


def _service(request: Request, session: Session = Depends(get_session)) -> SubmissionService:
    return SubmissionService(
        session,
        llm=request.app.state.llm,
        build_retriever=request.app.state.build_retriever,
        retrieval_k=request.app.state.retrieval_k,
        tool_timeout_seconds=request.app.state.tool_timeout_seconds,
    )


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


@router.get("", response_model=SubmissionList)
def list_submissions(
    limit: int = Query(default=50, ge=1, le=100),
    principal: Principal = Depends(get_principal),
    service: SubmissionService = Depends(_service),
) -> SubmissionList:
    rows = service.list_submissions(principal, limit)
    return SubmissionList(
        submissions=[submission_summary(submission, company) for submission, company in rows]
    )


@router.post("", response_model=SubmissionDetail, status_code=201)
def create_submission(
    body: SubmissionCreate,
    request: Request,
    principal: Principal = Depends(get_principal),
    service: SubmissionService = Depends(_service),
) -> SubmissionDetail:
    created = service.create(principal, body, _request_id(request))
    return submission_detail(created.submission, created.company, created.claims)


@router.get("/{submission_id}", response_model=SubmissionDetail)
def get_submission(
    submission_id: str,
    principal: Principal = Depends(get_principal),
    service: SubmissionService = Depends(_service),
) -> SubmissionDetail:
    found = service.get_submission(principal, submission_id)
    return submission_detail(found.submission, found.company, found.claims)


@router.post("/{submission_id}/analyze", response_model=RecommendationRead)
def analyze_submission(
    submission_id: str,
    request: Request,
    principal: Principal = Depends(get_principal),
    service: SubmissionService = Depends(_service),
) -> RecommendationRead | JSONResponse:
    try:
        analyzed = service.analyze(principal, submission_id, _request_id(request))
    except ModelUnavailableError:
        return json_error(
            request,
            503,
            "The analysis model is unavailable. No underwriting decision was made.",
        )
    except InvalidModelOutputError:
        return json_error(
            request,
            502,
            "The analysis model returned an unusable result. No underwriting decision was made.",
        )
    except ToolLoopError:
        return json_error(
            request,
            502,
            "The analysis stopped before a draft was ready. No underwriting decision was made.",
        )
    except RetrievalUnavailableError:
        return json_error(
            request,
            503,
            "Guideline search is unavailable. No underwriting decision was made.",
        )
    except ToolTimeoutError:
        return json_error(
            request,
            504,
            "A tool did not finish in time. No underwriting decision was made.",
        )
    return recommendation_read(analyzed.recommendation, analyzed.review)


@router.get("/{submission_id}/recommendation", response_model=RecommendationRead)
def get_recommendation(
    submission_id: str,
    principal: Principal = Depends(get_principal),
    service: SubmissionService = Depends(_service),
) -> RecommendationRead:
    found = service.get_recommendation(principal, submission_id)
    return recommendation_read(found.recommendation, found.review)


@router.post("/{submission_id}/review", response_model=RecommendationRead)
def review_submission(
    submission_id: str,
    body: ReviewCreate,
    request: Request,
    principal: Principal = Depends(get_principal),
    service: SubmissionService = Depends(_service),
) -> RecommendationRead:
    reviewed = service.review(principal, submission_id, body, _request_id(request))
    return recommendation_read(reviewed.recommendation, reviewed.review)


@router.get("/{submission_id}/audit", response_model=AuditList)
def list_audit(
    submission_id: str,
    principal: Principal = Depends(get_principal),
    service: SubmissionService = Depends(_service),
) -> AuditList:
    events = service.list_audit(principal, submission_id)
    return AuditList(events=[audit_event_read(event) for event in events])
