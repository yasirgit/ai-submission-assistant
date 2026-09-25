"""Request-scoped database session and the authenticated principal."""

from collections.abc import Iterator

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.domain.entitlements import Principal
from app.domain.enums import Role
from app.models.tables import User


class RequestPrincipal:
    """Concrete principal. The domain rule only needs id, role, and team."""

    def __init__(self, user: User) -> None:
        self.id = user.id
        self.role = user.role if isinstance(user.role, Role) else Role(user.role)
        self.team_id = user.team_id


def get_session(request: Request) -> Iterator[Session]:
    factory = request.app.state.session_factory
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_principal(
    request: Request,
    session: Session = Depends(get_session),
) -> Principal:
    user_id = request.headers.get("x-user-id")
    user = session.get(User, user_id) if user_id else None
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    request.state.user_id = user.id
    return RequestPrincipal(user)
