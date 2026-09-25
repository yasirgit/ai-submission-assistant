"""Tool calls are authorized for the HTTP caller and stop after six steps."""

import json

from app.agents.loop import run_agent
from app.api.deps import RequestPrincipal
from app.llm.errors import ToolLoopError
from app.llm.types import LLMCompletion, ToolCall
from app.models.tables import User
from app.repositories.audit import AuditRepository
from app.tools.gateway import ToolGateway, ToolOutcome

from tests.helpers import ALICE

HARBOR = "sub-alice-harbor-cyber"
BRIGHTGRID_SUBMISSION = "sub-bob-brightgrid-cyber"
BRIGHTGRID = "company-brightgrid"


def test_alice_cannot_read_bob_through_the_gateway(api) -> None:
    session, gateway = _gateway(api)
    submission = gateway.execute("get_submission", {"submission_id": BRIGHTGRID_SUBMISSION})
    company = gateway.execute("get_company", {"company_id": BRIGHTGRID})
    claims = gateway.execute("get_company_claims", {"company_id": BRIGHTGRID})
    session.commit()
    session.close()

    for outcome in (submission, company, claims):
        assert outcome.ok is False
        assert outcome.payload == {"error": "not_found"}
        dumped = json.dumps(outcome.payload)
        assert "Brightgrid" not in dumped
        assert "United States" not in dumped

    audit = api.get(f"/api/submissions/{HARBOR}/audit", headers=ALICE).json()
    denied = [event for event in audit["events"] if event["action"] == "tool.denied"]
    assert [event["metadata"]["tool"] for event in denied] == [
        "get_submission",
        "get_company",
        "get_company_claims",
    ]
    assert "Brightgrid" not in json.dumps(audit)


def test_extra_user_id_and_unknown_tools_are_rejected(api) -> None:
    session, gateway = _gateway(api)
    extra = gateway.execute("get_submission", {"submission_id": HARBOR, "user_id": "user-alex"})
    missing = gateway.execute("get_company", {})
    approve = gateway.execute("approve_submission", {"submission_id": HARBOR})
    session.commit()
    session.close()

    assert extra.payload == {"error": "invalid_arguments"}
    assert missing.payload == {"error": "invalid_arguments"}
    assert approve.payload == {"error": "unknown_tool"}
    assert "Harbor" not in json.dumps(extra.payload)

    audit = api.get(f"/api/submissions/{HARBOR}/audit", headers=ALICE).json()
    denied = [event["metadata"]["error"] for event in audit["events"] if event["action"] == "tool.denied"]
    assert denied == ["invalid_arguments", "invalid_arguments", "unknown_tool"]


def test_step_cap_returns_no_draft() -> None:
    product = run_agent(_AlwaysTool(), _RepeatingGateway(), HARBOR)
    assert product.outcome == "STEP_LIMIT"
    assert isinstance(product.error, ToolLoopError)
    assert product.tool_calls == ["get_submission"] * 6
    assert product.summary == ""
    assert product.confidence == 0.0


def test_step_cap_keeps_the_submission_new(api) -> None:
    api.app.state.llm = _AlwaysTool()
    response = api.post(f"/api/submissions/{HARBOR}/analyze", headers=ALICE)
    assert response.status_code == 502
    assert "stopped" in response.json()["detail"]
    assert "approved" not in response.json()["detail"].lower()
    stored = api.get(f"/api/submissions/{HARBOR}", headers=ALICE)
    assert stored.json()["status"] == "NEW"
    assert api.get(f"/api/submissions/{HARBOR}/recommendation", headers=ALICE).status_code == 404
    run = api.get("/api/ai-runs", headers=ALICE).json()["runs"][0]
    assert run["outcome"] == "STEP_LIMIT"
    assert run["success"] is False
    assert len(run["tool_calls"]) == 6


def _gateway(api) -> tuple:
    session = api.app.state.session_factory()
    user = session.get(User, "user-alice")
    gateway = ToolGateway(
        session,
        RequestPrincipal(user),
        AuditRepository(session),
        _EmptyRetriever(),
        submission_id=HARBOR,
        request_id="req-tools",
        retrieval_k=5,
    )
    return session, gateway


class _EmptyRetriever:
    def retrieve(self, query) -> list:
        return []


class _AlwaysTool:
    model_name = "always"

    def complete(self, system: str, user: str) -> LLMCompletion:
        return LLMCompletion(
            content="",
            model=self.model_name,
            tool_call=ToolCall("get_submission", {"submission_id": HARBOR}),
        )


class _RepeatingGateway:
    def execute(self, name: str, arguments: dict) -> ToolOutcome:
        return ToolOutcome(name=name, ok=True, payload={"id": HARBOR, "company_id": "company-harbor"})
