"""Run the golden cases through the mock model and the configured retriever."""

import time
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import RequestPrincipal
from app.config.settings import Settings
from app.domain.enums import SubmissionStatus
from app.domain.fingerprint import content_fingerprint
from app.evaluation.cases import CASES, EvalCase
from app.evaluation.score import CaseResult, judge_analysis, judge_retrieval
from app.main import create_app
from app.models.tables import AIRun, Claim, Company, Submission, User
from app.rag.query import build_query
from app.rag.types import RetrievalQuery
from app.services.submissions import SubmissionService

_SEEDED = datetime(2026, 4, 1, tzinfo=UTC)


def run_dataset() -> list[CaseResult]:
    settings = Settings(database_url="sqlite://", llm_provider="mock", retriever="memory")
    app = create_app(settings)
    from fastapi.testclient import TestClient

    with TestClient(app):
        session = app.state.session_factory()
        try:
            for case in CASES:
                _insert(session, case)
            session.flush()
            results = []
            for case in CASES:
                if case.kind == "analysis":
                    results.append(_analyze(app, session, case))
                else:
                    results.append(_retrieve(app, session, case))
            return results
        finally:
            session.close()


def _insert(session: Session, case: EvalCase) -> None:
    if case.kind != "analysis" or not case.narrative:
        return
    if case.company_name:
        session.add(
            Company(
                id=case.company_id,
                name=case.company_name,
                industry=case.industry,
                annual_revenue_eur=case.revenue,
                employee_count=case.employees,
                countries=list(case.countries),
                created_at=_SEEDED,
            )
        )
        session.flush()
        for index, (year, claim_type, amount) in enumerate(case.claims):
            session.add(
                Claim(
                    id=f"{case.company_id}-claim-{index}",
                    company_id=case.company_id,
                    year=year,
                    claim_type=claim_type,
                    amount_eur=amount,
                    description="Synthetic evaluation claim.",
                )
            )
    coverage = {"product": case.product, "limit_eur": case.limit_eur}
    session.add(
        Submission(
            id=case.submission_id,
            company_id=case.company_id,
            status=SubmissionStatus.NEW,
            created_by=case.user_id,
            assigned_underwriter_id=case.user_id,
            team_id="team-north",
            requested_coverage=coverage,
            existing_policy=None,
            narrative=case.narrative,
            content_fingerprint=content_fingerprint(case.company_id, coverage, case.narrative),
            created_at=_SEEDED,
            updated_at=_SEEDED,
        )
    )


def _analyze(app, session: Session, case: EvalCase) -> CaseResult:
    user = session.get(User, case.user_id)
    service = SubmissionService(
        session,
        llm=app.state.llm,
        build_retriever=app.state.build_retriever,
        retrieval_k=app.state.retrieval_k,
        tool_timeout_seconds=app.state.tool_timeout_seconds,
    )
    started = time.perf_counter()
    try:
        analyzed = service.analyze(RequestPrincipal(user), case.submission_id, "eval")
    except Exception:
        latency_ms = int((time.perf_counter() - started) * 1000)
        return judge_analysis(
            case,
            chunk_ids=[],
            flags=[],
            missing=[],
            summary="",
            tools=[],
            outcome="ERROR",
            latency_ms=latency_ms,
            prompt_tokens=0,
        )
    latency_ms = int((time.perf_counter() - started) * 1000)
    recommendation = analyzed.recommendation
    run = session.scalars(
        select(AIRun).where(AIRun.submission_id == case.submission_id).order_by(AIRun.created_at.desc())
    ).first()
    usage = (run.token_usage or {}) if run is not None else {}
    tools = list(run.tool_calls) if run is not None else []
    return judge_analysis(
        case,
        chunk_ids=[source["chunk_id"] for source in recommendation.source_references],
        flags=[flag["type"] for flag in recommendation.risk_flags],
        missing=list(recommendation.missing_information),
        summary=recommendation.summary,
        tools=tools,
        outcome=run.outcome if run is not None else "",
        latency_ms=latency_ms,
        prompt_tokens=int(usage.get("prompt_tokens") or 0),
    )


def _retrieve(app, session: Session, case: EvalCase) -> CaseResult:
    retriever = app.state.build_retriever(session)
    if case.query_text:
        query = RetrievalQuery(
            text=case.query_text,
            industry=case.query_industry,
            countries=case.query_countries,
            product=case.query_product,
            k=app.state.retrieval_k,
        )
    else:
        submission = session.get(Submission, case.submission_id)
        company = session.get(Company, submission.company_id)
        query = build_query(submission, company, app.state.retrieval_k)
    found = [chunk.chunk_id for chunk in retriever.retrieve(query)]
    return judge_retrieval(case, found)
