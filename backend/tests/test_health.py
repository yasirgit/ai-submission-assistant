"""Health stays quiet when the database fails."""

from app.api.deps import get_session
from fastapi.testclient import TestClient


def test_health_ok(api: TestClient) -> None:
    response = api.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
    assert response.headers["x-request-id"]


def test_health_hides_database_errors(api: TestClient) -> None:
    def broken_session():
        class _Session:
            def execute(self, *_args, **_kwargs):
                raise RuntimeError("password=supersecret host=db.internal")

            def commit(self) -> None:
                return None

            def rollback(self) -> None:
                return None

            def close(self) -> None:
                return None

        yield _Session()

    api.app.dependency_overrides[get_session] = broken_session
    try:
        response = api.get("/api/health")
    finally:
        api.app.dependency_overrides.clear()
    assert response.status_code == 503
    assert response.json()["database"] == "unavailable"
    assert "supersecret" not in response.text
    assert "db.internal" not in response.text
