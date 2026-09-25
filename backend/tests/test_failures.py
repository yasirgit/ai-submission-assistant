"""Retrieval and tool deadlines fail closed. The response stays generic."""

import time

from app.llm.types import LLMCompletion
from app.rag.types import RetrievalQuery, RetrievedChunk

from tests.helpers import ALICE


def test_retrieval_outage_hides_the_cause(api) -> None:
    _Quiet.users = []
    api.app.state.llm = _Quiet()
    api.app.state.build_retriever = lambda _session: _DownRetriever()
    response = api.post("/api/submissions/sub-alice-harbor-cyber/analyze", headers=ALICE)
    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"]
    assert "vector-password" not in response.text
    stored = api.get("/api/submissions/sub-alice-harbor-cyber", headers=ALICE)
    assert stored.json()["status"] == "NEW"
    run = api.get("/api/ai-runs", headers=ALICE).json()["runs"][0]
    assert run["outcome"] == "RETRIEVAL_UNAVAILABLE"
    assert run["success"] is False
    audit = api.get("/api/submissions/sub-alice-harbor-cyber/audit", headers=ALICE).json()
    denied = [event for event in audit["events"] if event["metadata"].get("error") == "retrieval_unavailable"]
    assert denied
    assert "vector-password" not in response.text
    assert all("<submission_facts>" not in user for user in _Quiet.users)


def test_slow_tool_does_not_produce_a_draft(api) -> None:
    api.app.state.tool_timeout_seconds = 0.05
    api.app.state.build_retriever = lambda _session: _SlowRetriever()
    response = api.post("/api/submissions/sub-alice-harbor-cyber/analyze", headers=ALICE)
    assert response.status_code == 504
    assert "did not finish" in response.json()["detail"]
    assert "approved" not in response.json()["detail"].lower()
    stored = api.get("/api/submissions/sub-alice-harbor-cyber", headers=ALICE)
    assert stored.json()["status"] == "NEW"
    run = api.get("/api/ai-runs", headers=ALICE).json()["runs"][0]
    assert run["outcome"] == "TOOL_TIMEOUT"
    assert run["success"] is False
    audit = api.get("/api/submissions/sub-alice-harbor-cyber/audit", headers=ALICE).json()
    assert any(event["metadata"].get("error") == "timeout" for event in audit["events"])


class _Quiet:
    model_name = "quiet"
    users: list[str] = []

    def complete(self, system: str, user: str) -> LLMCompletion:
        _Quiet.users.append(user)
        if "<submission_facts>" in user:
            raise AssertionError("the draft prompt must not be sent when retrieval fails")
        from app.llm.mock import MockLLMClient

        return MockLLMClient().complete(system, user)


class _DownRetriever:
    def retrieve(self, query: RetrievalQuery) -> list[RetrievedChunk]:
        raise RuntimeError("vector store password=vector-password")


class _SlowRetriever:
    def retrieve(self, query: RetrievalQuery) -> list[RetrievedChunk]:
        time.sleep(0.2)
        return []
