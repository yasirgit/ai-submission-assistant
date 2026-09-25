"""Create, duplicate detection, audit contents, and the not-yet-implemented analysis route."""

from app.domain.enums import SubmissionStatus
from app.models.tables import Submission

from tests.helpers import ALEX, ALICE, BOB, BOB_SUBMISSION, MIA, NOAH


def _payload(narrative: str = "A new synthetic submission for Harbor.") -> dict:
    return {
        "company_id": "company-harbor",
        "requested_coverage": {"product": "Cyber Product X", "limit_eur": 750000},
        "narrative": narrative,
    }


def test_underwriter_creates_a_submission_assigned_to_herself(api) -> None:
    response = api.post("/api/submissions", headers=ALICE, json=_payload())
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "NEW"
    assert body["assigned_underwriter_id"] == "user-alice"
    assert body["team_id"] == "team-north"
    assert body["company"]["name"] == "Harbor Logistics"

    audit = api.get(f"/api/submissions/{body['id']}/audit", headers=ALICE)
    event = audit.json()["events"][0]
    assert event["action"] == "submission.created"
    assert event["user_id"] == "user-alice"
    assert "narrative" not in event["metadata"]
    assert "Hamburg" not in audit.text


def test_duplicate_narrative_returns_the_existing_id(api) -> None:
    narrative = "Unique warehouse wording for the duplicate check."
    first = api.post("/api/submissions", headers=ALICE, json=_payload(narrative))
    second = api.post(
        "/api/submissions",
        headers=ALICE,
        json=_payload("Unique   warehouse wording for the duplicate check."),
    )
    assert second.status_code == 409
    assert second.json()["existing_id"] == first.json()["id"]


def test_unknown_company_is_a_catalog_miss(api) -> None:
    body = _payload()
    body["company_id"] = "company-missing"
    response = api.post("/api/submissions", headers=ALICE, json=body)
    assert response.status_code == 404
    assert response.json()["detail"] == "Company not found"


def test_alice_cannot_assign_work_to_bob(api) -> None:
    body = _payload("Assignment attempt.")
    body["assigned_underwriter_id"] = "user-bob"
    response = api.post("/api/submissions", headers=ALICE, json=body)
    assert response.status_code == 403
    assert api.get(f"/api/submissions/{BOB_SUBMISSION}", headers=BOB).status_code == 200


def test_manager_assigns_only_inside_the_team(api) -> None:
    outside = _payload("Mia tries to assign Bob.")
    outside["assigned_underwriter_id"] = "user-bob"
    assert api.post("/api/submissions", headers=MIA, json=outside).status_code == 403

    inside = _payload("Mia assigns Noah.")
    inside["company_id"] = "company-nordic"
    inside["assigned_underwriter_id"] = "user-noah"
    created = api.post("/api/submissions", headers=MIA, json=inside)
    assert created.status_code == 201
    assert created.json()["assigned_underwriter_id"] == "user-noah"
    assert api.get(f"/api/submissions/{created.json()['id']}", headers=ALICE).status_code == 404
    assert api.get(f"/api/submissions/{created.json()['id']}", headers=NOAH).status_code == 200


def test_admin_assignment_keeps_the_underwriters_team(api) -> None:
    body = _payload("Alex assigns Bob.")
    body["company_id"] = "company-brightgrid"
    body["assigned_underwriter_id"] = "user-bob"
    created = api.post("/api/submissions", headers=ALEX, json=body)
    assert created.status_code == 201
    assert created.json()["team_id"] == "team-south"
    assert api.get(f"/api/submissions/{created.json()['id']}", headers=MIA).status_code == 404


def test_analyze_checks_access_and_does_not_decide(api) -> None:
    missing = api.post(f"/api/submissions/{BOB_SUBMISSION}/analyze", headers=ALICE)
    assert missing.status_code == 404

    draft = api.post("/api/submissions/sub-alice-harbor-cyber/analyze", headers=ALICE)
    assert draft.status_code == 200
    assert draft.json()["status"] == "DRAFT"
    assert "approved" not in draft.json()["summary"].lower()
    ready = api.get("/api/submissions/sub-alice-harbor-cyber", headers=ALICE)
    assert ready.json()["status"] == "READY_FOR_REVIEW"

    accepted = api.post(
        "/api/submissions/sub-alice-harbor-cyber/review",
        headers=ALICE,
        json={"action": "ACCEPT", "comment": "Looks complete."},
    )
    assert accepted.status_code == 200
    again = api.post("/api/submissions/sub-alice-harbor-cyber/analyze", headers=ALICE)
    assert again.status_code == 409


def test_processing_submission_is_not_started_twice(api) -> None:
    factory = api.app.state.session_factory
    with factory() as session:
        submission = session.get(Submission, "sub-alice-cobolt-cyber")
        submission.status = SubmissionStatus.PROCESSING
        session.commit()
    response = api.post("/api/submissions/sub-alice-cobolt-cyber/analyze", headers=ALICE)
    assert response.status_code == 409
