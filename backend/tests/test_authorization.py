"""User A cannot read User B's submission. This is an application check, not a prompt."""

from datetime import UTC, datetime

from app.domain.errors import NotFoundError
from app.models.tables import AIRun, Document
from app.services.companies import CompanyService
from sqlalchemy import select

from tests.helpers import (
    ALEX,
    ALICE,
    ALICE_SUBMISSION,
    BOB,
    BOB_SUBMISSION,
    MIA,
    NOAH_SUBMISSION,
    add_run,
)


def test_alice_cannot_read_bobs_submission(api) -> None:
    response = api.get(f"/api/submissions/{BOB_SUBMISSION}", headers=ALICE)
    assert response.status_code == 404
    assert response.json()["detail"] == "Not found"
    assert "Brightgrid" not in response.text


def test_alice_cannot_read_noahs_submission_on_the_same_team(api) -> None:
    response = api.get(f"/api/submissions/{NOAH_SUBMISSION}", headers=ALICE)
    assert response.status_code == 404


def test_mia_reads_her_team_and_not_bobs(api) -> None:
    assert api.get(f"/api/submissions/{ALICE_SUBMISSION}", headers=MIA).status_code == 200
    assert api.get(f"/api/submissions/{NOAH_SUBMISSION}", headers=MIA).status_code == 200
    denied = api.get(f"/api/submissions/{BOB_SUBMISSION}", headers=MIA)
    assert denied.status_code == 404


def test_alex_reads_bobs_submission(api) -> None:
    response = api.get(f"/api/submissions/{BOB_SUBMISSION}", headers=ALEX)
    assert response.status_code == 200
    assert response.json()["company"]["name"] == "Brightgrid Energy"


def test_missing_and_unknown_users_are_unauthenticated(api) -> None:
    assert api.get(f"/api/submissions/{ALICE_SUBMISSION}").status_code == 401
    unknown = api.get(f"/api/submissions/{ALICE_SUBMISSION}", headers={"X-User-Id": "user-nobody"})
    assert unknown.status_code == 401
    assert unknown.json()["detail"] == "Authentication required"


def test_lists_are_scoped(api) -> None:
    alice_ids = {row["id"] for row in api.get("/api/submissions", headers=ALICE).json()["submissions"]}
    mia_ids = {row["id"] for row in api.get("/api/submissions", headers=MIA).json()["submissions"]}
    alex_ids = {row["id"] for row in api.get("/api/submissions", headers=ALEX).json()["submissions"]}

    assert alice_ids == {
        "sub-alice-harbor-cyber",
        "sub-alice-harbor-property",
        "sub-alice-cobolt-cyber",
        "sub-alice-cobolt-property",
    }
    assert NOAH_SUBMISSION in mia_ids
    assert BOB_SUBMISSION not in mia_ids
    assert BOB_SUBMISSION not in alice_ids
    assert len(alex_ids) == 10
    assert "narrative" not in api.get("/api/submissions", headers=ALICE).json()["submissions"][0]


def test_alice_cannot_read_brightgrid_claims(api) -> None:
    factory = api.app.state.session_factory
    with factory() as session:
        service = CompanyService(session)
        try:
            service.get_claims(_principal_alice(), "company-brightgrid")
        except NotFoundError:
            return
        raise AssertionError("claims for another underwriter's company were returned")


def test_mia_can_read_nordic_claims_and_alice_cannot(api) -> None:
    factory = api.app.state.session_factory
    with factory() as session:
        service = CompanyService(session)
        claims = service.get_claims(_principal_mia(), "company-nordic")
        assert [claim.id for claim in claims] == ["claim-nordic-2020"]
        try:
            service.get_claims(_principal_alice(), "company-nordic")
        except NotFoundError:
            return
        raise AssertionError("alice saw nordic claims")


def test_detail_includes_only_that_companys_claims(api) -> None:
    body = api.get(f"/api/submissions/{ALICE_SUBMISSION}", headers=ALICE).json()
    assert [claim["id"] for claim in body["claims"]] == ["claim-harbor-2023"]
    brightgrid = api.get(f"/api/submissions/{BOB_SUBMISSION}", headers=BOB).json()
    assert {claim["id"] for claim in brightgrid["claims"]} == {
        "claim-brightgrid-2022",
        "claim-brightgrid-2024",
    }


def test_ai_runs_follow_the_same_scope(api) -> None:
    add_run(
        api,
        AIRun(
            id="run-alice",
            request_id="req-alice",
            user_id="user-alice",
            submission_id=ALICE_SUBMISSION,
            model="mock",
            latency_ms=10,
            retrieved_document_ids=["doc-revenue-threshold"],
            tool_calls=["get_submission"],
            success=True,
            token_usage=None,
            outcome="COMPLETE",
            created_at=datetime(2026, 4, 1, tzinfo=UTC),
        ),
    )
    assert api.get("/api/ai-runs", headers=BOB).json()["runs"] == []
    assert api.get("/api/ai-runs", headers=ALICE).json()["runs"][0]["id"] == "run-alice"
    assert api.get("/api/ai-runs", headers=MIA).json()["runs"][0]["id"] == "run-alice"
    assert api.get("/api/ai-runs", headers=ALEX).json()["runs"][0]["id"] == "run-alice"


def test_seeded_document_text_is_untrusted(api) -> None:
    factory = api.app.state.session_factory
    with factory() as session:
        levels = set(session.scalars(select(Document.trust_level)))
    assert levels == {"UNTRUSTED"}


def _principal_alice():
    from types import SimpleNamespace

    from app.domain.enums import Role

    return SimpleNamespace(id="user-alice", role=Role.UNDERWRITER, team_id="team-north")


def _principal_mia():
    from types import SimpleNamespace

    from app.domain.enums import Role

    return SimpleNamespace(id="user-mia", role=Role.MANAGER, team_id="team-north")
