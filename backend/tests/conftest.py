"""In-memory database for API tests. No Postgres and no model API."""

from collections.abc import Iterator

import pytest
from app.config.settings import Settings
from app.main import create_app
from fastapi.testclient import TestClient


@pytest.fixture
def api() -> Iterator[TestClient]:
    app = create_app(Settings(database_url="sqlite://", llm_provider="mock", retriever="memory"))
    with TestClient(app) as client:
        yield client
