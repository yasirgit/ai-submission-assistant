"""Insert the demo catalog once per empty database."""

from sqlalchemy.orm import Session

from app.models.tables import User
from app.seed.catalog import chunks, claims, companies, documents, submissions, users


def seed_if_empty(session: Session) -> None:
    if session.get(User, "user-alice") is not None:
        return
    session.add_all(users())
    session.add_all(companies())
    session.flush()
    session.add_all(claims())
    session.add_all(documents())
    session.flush()
    session.add_all(chunks())
    session.add_all(submissions())
