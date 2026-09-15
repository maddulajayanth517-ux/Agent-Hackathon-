from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..audit import record_audit_event
from ..database import get_db
from ..models import Alert, Allocation, Escalation, EscalationStatus, Mentor, Message, Student, User
from ..notifications import send_email_alert
from ..rbac import can_access_student, get_current_user
from ..schemas import UserContext

router = APIRouter(prefix="/messages", tags=["Messaging"])


class MessageCreate(BaseModel):
    student_id: int
    body: str = Field(min_length=1, max_length=4000)


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    sender_id: int
    sender_name: str
    sender_role: str
    body: str
    created_at: datetime


def _active_participants(db: Session, student_id: int) -> list[tuple[int, str]]:
    """Every (user_id, role) currently authorized to see this student's thread."""
    participants: list[tuple[int, str]] = []

    student = db.scalar(select(Student).where(Student.id == student_id))
    if student:
        participants.append((student.user_id, "student"))

    allocation = db.scalar(
        select(Allocation).where(Allocation.student_id == student_id, Allocation.is_active.is_(True))
    )
    if allocation:
        mentor = db.scalar(select(Mentor).where(Mentor.id == allocation.mentor_id))
        if mentor:
            participants.append((mentor.user_id, "mentor"))

    assignees = db.scalars(
        select(Escalation.assigned_to).where(
            Escalation.student_id == student_id,
            Escalation.assigned_to.is_not(None),
            Escalation.status.in_([EscalationStatus.OPEN, EscalationStatus.ACKNOWLEDGED]),
        )
    ).all()
    for user_id in set(assignees):
        participants.append((user_id, "escalation_contact"))

    return participants


def _serialize(rows) -> list[MessageResponse]:
    return [
        MessageResponse(
            id=message.id,
            student_id=message.student_id,
            sender_id=message.sender_id,
            sender_name=name,
            sender_role=role.value if hasattr(role, "value") else str(role),
            body=message.body,
            created_at=message.created_at,
        )
        for message, name, role in rows
    ]


@router.get("/student/{student_id}", response_model=list[MessageResponse])
def list_messages(
    student_id: int,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    if not can_access_student(db=db, user=user, student_id=student_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student access denied")

    query = (
        select(Message, User.full_name, User.role)
        .join(User, User.id == Message.sender_id)
        .where(Message.student_id == student_id)
        .order_by(Message.created_at.asc())
    )
    return _serialize(db.execute(query).all())


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(
    payload: MessageCreate,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    if not can_access_student(db=db, user=user, student_id=payload.student_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student access denied")

    message = Message(student_id=payload.student_id, sender_id=user.id, body=payload.body.strip())
    db.add(message)
    db.flush()

    record_audit_event(
        db,
        actor_id=user.id,
        action="MESSAGE_SENT",
        resource_type="message",
        resource_id=message.id,
        details=f"student_id={payload.student_id}",
    )

    sender = db.scalar(select(User).where(User.id == user.id))
    sender_name = sender.full_name if sender else "a mentoring contact"
    recipients = {uid for uid, _ in _active_participants(db, payload.student_id) if uid != user.id}
    for recipient_id in recipients:
        db.add(
            Alert(
                student_id=payload.student_id,
                recipient_id=recipient_id,
                severity="INFO",
                title=f"New message from {sender_name}",
                body=payload.body.strip()[:280],
                channel="IN_APP",
            )
        )

    db.commit()
    db.refresh(message)

    for recipient_id in recipients:
        recipient_email = db.scalar(select(User.email).where(User.id == recipient_id))
        if recipient_email:
            send_email_alert(
                recipient=recipient_email,
                subject=f"New mentoring message from {sender_name}",
                body=payload.body.strip(),
            )

    return MessageResponse(
        id=message.id,
        student_id=message.student_id,
        sender_id=message.sender_id,
        sender_name=sender_name,
        sender_role=sender.role.value if sender else "unknown",
        body=message.body,
        created_at=message.created_at,
    )
