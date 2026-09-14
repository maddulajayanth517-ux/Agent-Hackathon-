from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..audit import record_audit_event
from ..database import get_db
from ..models import Alert, Escalation, EscalationStatus, Flag, FlagSeverity, ServiceQueue, User, UserRole
from ..notifications import send_email_alert
from ..rbac import can_access_student, get_current_user
from ..routing import route_escalation
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


class QueueUpsert(BaseModel):
    code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=150)
    recipient_user_id: int | None = None
    recipient_email: str | None = None


class EscalationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    raised_by: int
    assigned_to: int | None
    destination: str
    queue_id: int | None
    severity: FlagSeverity
    reason: str
    status: EscalationStatus
    resolution_notes: str | None
    created_at: datetime
    resolved_at: datetime | None
    priority: str
    routing_explanation: str


MANAGE_ROLES = {
    UserRole.ADMIN,
    UserRole.MENTOR,
    UserRole.HOD,
    UserRole.COUNSELLOR,
}


@router.get("/queues")
def list_queues(db: Session = Depends(get_db), user: UserContext = Depends(get_current_user)):
    if user.role not in {UserRole.ADMIN, UserRole.HOD}:
        raise HTTPException(status_code=403, detail="Only administrators or HOD users can view escalation queues")
    return db.scalars(select(ServiceQueue).order_by(ServiceQueue.code)).all()


@router.put("/queues/{code}")
def upsert_queue(code: str, payload: QueueUpsert, db: Session = Depends(get_db), user: UserContext = Depends(get_current_user)):
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only administrators can configure escalation queues")
    normalized = code.strip().upper()
    if normalized != payload.code.strip().upper():
        raise HTTPException(status_code=422, detail="Queue code must match path")
    queue = db.scalar(select(ServiceQueue).where(ServiceQueue.code == normalized))
    if queue is None:
        queue = ServiceQueue(code=normalized, name=payload.name.strip())
        db.add(queue)
    queue.name, queue.recipient_user_id, queue.recipient_email, queue.is_active = payload.name.strip(), payload.recipient_user_id, payload.recipient_email, True
    db.commit(); db.refresh(queue)
    return queue


@router.get("/mine", response_model=list[EscalationResponse])
def list_my_escalations(
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    """Escalations relevant to the current user's role: assigned to them
    (HOD/Counsellor queue owners) or raised by them (mentors)."""
    if user.role in {UserRole.HOD, UserRole.COUNSELLOR}:
        query = select(Escalation).where(Escalation.assigned_to == user.id)
    elif user.role == UserRole.MENTOR:
        query = select(Escalation).where(Escalation.raised_by == user.id)
    elif user.role == UserRole.ADMIN:
        query = select(Escalation).where(
            Escalation.status.in_([EscalationStatus.OPEN, EscalationStatus.ACKNOWLEDGED])
        )
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Students cannot view escalation queues")

    return db.scalars(query.order_by(Escalation.created_at.desc()).limit(100)).all()


@router.get(
    "/{escalation_id}",
    response_model=dict,
)
def get_escalation_by_id(
    escalation_id: int,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    escalation = db.scalar(
        select(Escalation).where(Escalation.id == escalation_id)
    )

    if escalation is not None:
        if not can_access_student(db, user, escalation.student_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student access denied")
        _, priority, explanation = route_escalation(escalation.severity, escalation.reason)
        return {
            "id": escalation.id,
            "student_id": escalation.student_id,
            "raised_by": escalation.raised_by,
            "assigned_to": escalation.assigned_to,
            "severity": escalation.severity,
            "reason": escalation.reason,
            "status": escalation.status,
            "resolution_notes": escalation.resolution_notes,
            "created_at": escalation.created_at,
            "resolved_at": escalation.resolved_at,
            "destination": escalation.destination,
            "priority": priority,
            "routing_explanation": explanation,
        }

    flag = db.scalar(
        select(Flag).where(
            Flag.id == escalation_id,
            Flag.is_active.is_(True),
        )
    )
    if flag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Escalation not found")
    if not can_access_student(db, user, flag.student_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student access denied")

    destination, priority, explanation = route_escalation(flag.severity, flag.description)
    return {
        "id": flag.id,
        "student_id": flag.student_id,
        "raised_by": flag.created_by,
        "assigned_to": None,
        "severity": flag.severity,
        "reason": flag.description,
        "status": "open",
        "resolution_notes": None,
        "created_at": flag.created_at,
        "resolved_at": None,
        "destination": destination,
        "priority": priority,
        "routing_explanation": explanation,
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

    destination, _, _ = route_escalation(payload.severity, payload.reason)
    queue_code = {"HOD": "HOD", "Counselling Cell": "COUNSELLING", "Scholarship / Fee Section": "SCHOLARSHIP_FEE"}.get(destination)
    queue = db.scalar(select(ServiceQueue).where(ServiceQueue.code == queue_code, ServiceQueue.is_active.is_(True))) if queue_code else None
    escalation = Escalation(
        student_id=payload.student_id,
        raised_by=user.id,
        assigned_to=payload.assigned_to or None,
        destination=destination,
        queue_id=queue.id if queue else None,
        severity=payload.severity,
        reason=payload.reason.strip(),
        status=EscalationStatus.OPEN,
    )

    if payload.assigned_to is not None:
        assignee = db.scalar(select(User).where(User.id == payload.assigned_to, User.is_active.is_(True)))
        if assignee is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Escalation assignee must be an active user")
    elif queue and queue.recipient_user_id:
        escalation.assigned_to = queue.recipient_user_id

    db.add(escalation)
    db.flush()
    record_audit_event(
        db,
        actor_id=user.id,
        action="ESCALATION_CREATED",
        resource_type="escalation",
        resource_id=escalation.id,
        details=f"student_id={escalation.student_id}; destination={destination}",
    )
    db.commit()
    db.refresh(escalation)
    if queue and queue.recipient_user_id:
        db.add(Alert(student_id=escalation.student_id, recipient_id=queue.recipient_user_id, severity=escalation.severity.value.upper(), title=f"Escalation routed: {destination}", body=escalation.reason, channel="IN_APP"))
        db.commit()
    if queue and queue.recipient_email:
        send_email_alert(recipient=queue.recipient_email, subject=f"Mentoring escalation: {destination}", body=escalation.reason)

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

    record_audit_event(
        db,
        actor_id=user.id,
        action="ESCALATION_UPDATED",
        resource_type="escalation",
        resource_id=escalation.id,
        details=f"status={escalation.status.value}",
    )

    db.commit()
    db.refresh(escalation)

    return escalation
