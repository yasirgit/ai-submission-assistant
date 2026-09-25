"""A person accepts, edits, or rejects a draft. The draft text stays intact."""

from app.schemas.contracts import ASSISTANCE_DISCLAIMER

from tests.helpers import ALICE, BOB, MIA, add_draft


def test_accept_approves_and_keeps_the_disclaimer(api) -> None:
    add_draft(api, "sub-alice-harbor-property", "rec-accept")
    response = api.post(
        "/api/submissions/sub-alice-harbor-property/review",
        headers=ALICE,
        json={"action": "ACCEPT", "comment": "Agreed."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ACCEPTED"
    assert body["summary"] == "Draft summary for human review."
    assert body["human_review"]["action"] == "ACCEPT"
    assert body["disclaimer"] == ASSISTANCE_DISCLAIMER
    submission = api.get("/api/submissions/sub-alice-harbor-property", headers=ALICE)
    assert submission.json()["status"] == "APPROVED"


def test_edit_stores_the_human_version_beside_the_draft(api) -> None:
    add_draft(api, "sub-alice-cobolt-property", "rec-edit")
    response = api.post(
        "/api/submissions/sub-alice-cobolt-property/review",
        headers=ALICE,
        json={
            "action": "EDIT",
            "comment": "Narrowed the summary.",
            "edited": {"summary": "Human summary replaces nothing in the draft row."},
        },
    )
    body = response.json()
    assert body["status"] == "EDITED"
    assert body["summary"] == "Draft summary for human review."
    assert body["human_review"]["edited_payload"]["summary"].startswith("Human summary")
    submission = api.get("/api/submissions/sub-alice-cobolt-property", headers=ALICE)
    assert submission.json()["status"] == "APPROVED"


def test_reject_requires_a_comment_and_records_the_decision(api) -> None:
    add_draft(api, "sub-alice-cobolt-cyber", "rec-reject")
    empty = api.post(
        "/api/submissions/sub-alice-cobolt-cyber/review",
        headers=ALICE,
        json={"action": "REJECT", "comment": "   "},
    )
    assert empty.status_code == 422

    response = api.post(
        "/api/submissions/sub-alice-cobolt-cyber/review",
        headers=ALICE,
        json={"action": "REJECT", "comment": "Missing audited accounts."},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "REJECTED"
    submission = api.get("/api/submissions/sub-alice-cobolt-cyber", headers=ALICE)
    assert submission.json()["status"] == "REJECTED"
    audit = api.get("/api/submissions/sub-alice-cobolt-cyber/audit", headers=ALICE)
    assert audit.json()["events"][-1]["action"] == "submission.reviewed"
    assert audit.json()["events"][-1]["metadata"]["review_action"] == "REJECT"


def test_bob_cannot_review_alices_draft(api) -> None:
    add_draft(api, "sub-noah-nordic-property", "rec-noah")
    response = api.post(
        "/api/submissions/sub-noah-nordic-property/review",
        headers=BOB,
        json={"action": "ACCEPT", "comment": "Trying someone else's file."},
    )
    assert response.status_code == 404
    still_ready = api.get("/api/submissions/sub-noah-nordic-property", headers=MIA)
    assert still_ready.json()["status"] == "READY_FOR_REVIEW"


def test_a_draft_can_be_reviewed_once(api) -> None:
    add_draft(api, "sub-alice-harbor-cyber", "rec-once")
    first = api.post(
        "/api/submissions/sub-alice-harbor-cyber/review",
        headers=ALICE,
        json={"action": "ACCEPT", "comment": "Once."},
    )
    second = api.post(
        "/api/submissions/sub-alice-harbor-cyber/review",
        headers=ALICE,
        json={"action": "REJECT", "comment": "Changed my mind."},
    )
    assert first.status_code == 200
    assert second.status_code == 409
