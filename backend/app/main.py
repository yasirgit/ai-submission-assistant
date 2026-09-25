"""FastAPI application.

Demo only. Not a production Insurance system.
AI-generated assistance — final decision remains with the underwriter.
"""

import json
import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_exception_handlers
from app.api.routes import guidelines, health, runs, submissions
from app.config.settings import Settings
from app.db import make_engine, make_session_factory
from app.llm.factory import build_llm_client
from app.models import Base
from app.rag.factory import make_retriever_builder
from app.seed import seed_if_empty

logger = logging.getLogger("insurance.access")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    if settings.retriever not in {"memory", "vector"}:
        raise ValueError("retriever must be 'memory' or 'vector'")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = make_engine(settings.database_url)
        Base.metadata.create_all(engine)
        factory = make_session_factory(engine)
        app.state.engine = engine
        app.state.session_factory = factory
        with factory() as session:
            seed_if_empty(session)
            session.commit()
        yield
        engine.dispose()

    app = FastAPI(
        title="Insurance AI Submission Assistant",
        description=(
            "Demo only, using synthetic data. Not a production Insurance system. "
            "AI-generated assistance — final decision remains with the underwriter."
        ),
        lifespan=lifespan,
    )
    app.state.llm = build_llm_client(settings)
    app.state.build_retriever = make_retriever_builder(settings.retriever)
    app.state.retrieval_k = settings.retrieval_k
    app.state.tool_timeout_seconds = settings.tool_timeout_seconds
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(health.router, prefix="/api")
    app.include_router(submissions.router, prefix="/api")
    app.include_router(guidelines.router, prefix="/api")
    app.include_router(runs.router, prefix="/api")

    @app.middleware("http")
    async def access_log(request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        logger.info(
            json.dumps(
                {
                    "event": "http_request",
                    "request_id": request_id,
                    "user_id": getattr(request.state, "user_id", None),
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "latency_ms": round((time.perf_counter() - started) * 1000, 1),
                }
            )
        )
        return response

    return app


app = create_app()
