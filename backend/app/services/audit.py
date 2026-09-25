"""Write an audit event without putting narrative text in the metadata."""

from app.models.tables import AuditEvent
from app.repositories.audit import AuditRepository
from app.services.clock import new_id, utc_now


def record(
    audit: AuditRepository,
    *,
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    request_id: str | None,
    details: dict,
) -> None:
    audit.add(
        AuditEvent(
            id=new_id(),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            occurred_at=utc_now(),
            details=details,
            request_id=request_id,
        )
    )
