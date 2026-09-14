from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AuditEvent, User, UserRole
from ..rbac import get_current_user
from ..schemas import UserContext

router = APIRouter(prefix="/audit", tags=["Audit Trail"])


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_id: int | None
    actor_name: str
    action: str
    resource_type: str
    resource_id: int | None
    details: str | None
    created_at: datetime


def _require_oversight(user: UserContext) -> None:
    if user.role not in {UserRole.ADMIN, UserRole.HOD}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators or HOD users can view the audit trail",
        )


def _serialize(rows) -> list[AuditEventResponse]:
    return [
        AuditEventResponse(
            id=event.id,
            actor_id=event.actor_id,
            actor_name=name or "System",
            action=event.action,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            details=event.details,
            created_at=event.created_at,
        )
        for event, name in rows
    ]


@router.get("", response_model=list[AuditEventResponse])
def list_audit_events(
    resource_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    """Recent audit trail entries — who did what, to which record, and when."""
    _require_oversight(user)
    query = select(AuditEvent, User.full_name).outerjoin(User, User.id == AuditEvent.actor_id)
    if resource_type:
        query = query.where(AuditEvent.resource_type == resource_type)
    query = query.order_by(AuditEvent.created_at.desc()).limit(limit)
    return _serialize(db.execute(query).all())


@router.get("/{resource_type}/{resource_id}", response_model=list[AuditEventResponse])
def get_resource_audit_trail(
    resource_type: str,
    resource_id: int,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    """Full audit history for one specific record (e.g. a meeting or escalation)."""
    _require_oversight(user)
    query = (
        select(AuditEvent, User.full_name)
        .outerjoin(User, User.id == AuditEvent.actor_id)
        .where(AuditEvent.resource_type == resource_type, AuditEvent.resource_id == resource_id)
        .order_by(AuditEvent.created_at.desc())
    )
    return _serialize(db.execute(query).all())
