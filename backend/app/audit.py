from sqlalchemy.orm import Session

from .models import AuditEvent


def record_audit_event(
    db: Session,
    *,
    actor_id: int | None,
    action: str,
    resource_type: str,
    resource_id: int | None,
    details: str,
) -> None:
    """Append an audit trail entry. Caller is responsible for the commit."""
    db.add(
        AuditEvent(
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
        )
    )
