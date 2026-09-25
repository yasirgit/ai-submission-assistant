"""Map use-case errors to HTTP responses without leaking internals."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.domain.errors import (
    AppError,
    CompanyNotFoundError,
    DuplicateSubmissionError,
    ForbiddenError,
    InvalidTransitionError,
    NotFoundError,
)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception(_request: Request, exc: HTTPException) -> JSONResponse:
        return _error(_request, exc.status_code, str(exc.detail))

    @app.exception_handler(NotFoundError)
    async def not_found(request: Request, _exc: NotFoundError) -> JSONResponse:
        return _error(request, 404, "Not found")

    @app.exception_handler(CompanyNotFoundError)
    async def company_missing(request: Request, _exc: CompanyNotFoundError) -> JSONResponse:
        return _error(request, 404, "Company not found")

    @app.exception_handler(DuplicateSubmissionError)
    async def duplicate(request: Request, exc: DuplicateSubmissionError) -> JSONResponse:
        return _error(request, 409, "Duplicate submission", existing_id=exc.existing_id)

    @app.exception_handler(ForbiddenError)
    async def forbidden(request: Request, exc: ForbiddenError) -> JSONResponse:
        return _error(request, 403, str(exc))

    @app.exception_handler(InvalidTransitionError)
    async def invalid_transition(request: Request, exc: InvalidTransitionError) -> JSONResponse:
        return _error(request, 409, str(exc))

    @app.exception_handler(AppError)
    async def app_error(request: Request, _exc: AppError) -> JSONResponse:
        return _error(request, 400, "Request could not be completed")


def json_error(request: Request, status_code: int, detail: str, **extra: object) -> JSONResponse:
    return _error(request, status_code, detail, **extra)


def _error(request: Request, status_code: int, detail: str, **extra: object) -> JSONResponse:
    body = {
        "detail": detail,
        "request_id": getattr(request.state, "request_id", None),
        **extra,
    }
    return JSONResponse(status_code=status_code, content=body)
