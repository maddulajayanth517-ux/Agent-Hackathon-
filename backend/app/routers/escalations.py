from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Escalation, EscalationStatus, FlagSeverity, UserRole
from ..rbac import can_access_student, get_current_user
from ..schemas import UserContext

router = APIRouter(prefix="/escalations", tags=["Escalations"])


class EscalationCreate(BaseModel):
    student_id: int
    severity: FlagSeverity
    reason: str = Field(min_length=3, max_length=2000)
    assigned_to: int | None = None


class EscalationUpdate(BaseModel):
    status: EscalationStatus | None = None
    assigned_to: int | None = None
    resolution_notes: str | None = Field(default=None, max_length=2000)


class EscalationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    raised_by: int
    assigned_to: int | None
    severity: FlagSeverity
    reason: str
    status: EscalationStatus
    resolution_notes: str | None
    created_at: datetime
    resolved_at: datetime | None


MANAGE_ROLES = {
    UserRole.ADMIN,
    UserRole.MENTOR,
    UserRole.HOD,
    UserRole.COUNSELLOR,
}


@router.post(
    "",
    response_model=EscalationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_escalation(
    payload: EscalationCreate,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    if user.role not in MANAGE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create escalations",
        )

    if not can_access_student(
        db=db,
        user=user,
        student_id=payload.student_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "student_access_denied",
                "student_id": payload.student_id,
            },
        )

    escalation = Escalation(
        student_id=payload.student_id,
        raised_by=user.id,
        assigned_to=payload.assigned_to,
        severity=payload.severity,
        reason=payload.reason.strip(),
        status=EscalationStatus.OPEN,
    )

    db.add(escalation)
    db.commit()
    db.refresh(escalation)

    return escalation


@router.get(
    "/student/{student_id}",
    response_model=list[EscalationResponse],
)
def get_student_escalations(
    student_id: int,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    if user.role not in {
        UserRole.ADMIN,
        UserRole.HOD,
        UserRole.COUNSELLOR,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view escalations",
        )

    if not can_access_student(
        db=db,
        user=user,
        student_id=student_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access denied",
        )

    return db.scalars(
        select(Escalation)
        .where(Escalation.student_id == student_id)
        .order_by(Escalation.created_at.desc())
    ).all()


@router.patch(
    "/{escalation_id}",
    response_model=EscalationResponse,
)
def update_escalation(
    escalation_id: int,
    payload: EscalationUpdate,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    if user.role not in {
        UserRole.ADMIN,
        UserRole.HOD,
        UserRole.COUNSELLOR,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update escalations",
        )

    escalation = db.scalar(
        select(Escalation).where(Escalation.id == escalation_id)
    )

    if escalation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Escalation not found",
        )

    if not can_access_student(
        db=db,
        user=user,
        student_id=escalation.student_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access denied",
        )

    if payload.status is not None:
        escalation.status = payload.status

        if payload.status in {
            EscalationStatus.RESOLVED,
            EscalationStatus.CLOSED,
        }:
            escalation.resolved_at = datetime.utcnow()

    if payload.assigned_to is not None:
        escalation.assigned_to = payload.assigned_to

    if payload.resolution_notes is not None:
        escalation.resolution_notes = payload.resolution_notes.strip()

    db.commit()
    db.refresh(escalation)

    return escalation