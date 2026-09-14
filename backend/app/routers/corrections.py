from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..audit import record_audit_event
from ..database import get_db
from ..models import Alert, Allocation, CorrectionRequest, CorrectionStatus, Mentor, Student, UserRole
from ..notifications import send_email_alert
from ..rbac import can_access_student, get_current_user
from ..schemas import UserContext

router = APIRouter(prefix="/corrections", tags=["Record Corrections"])


class CorrectionRequestCreate(BaseModel):
    field_reference: str = Field(min_length=2, max_length=150)
    description: str = Field(min_length=3, max_length=2000)
    meeting_id: int | None = None


class CorrectionRequestUpdate(BaseModel):
    status: CorrectionStatus
    resolution_notes: str | None = Field(default=None, max_length=2000)


class CorrectionRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    meeting_id: int | None
    field_reference: str
    description: str
    status: CorrectionStatus
    resolution_notes: str | None
    created_at: datetime
    resolved_by: int | None
    resolved_at: datetime | None


@router.post("", response_model=CorrectionRequestResponse, status_code=status.HTTP_201_CREATED)
def create_correction_request(
    payload: CorrectionRequestCreate,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    if user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can raise a correction request about their own record",
        )

    student = db.scalar(select(Student).where(Student.user_id == user.id, Student.is_active.is_(True)))
    if student is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active student profile not found")

    correction = CorrectionRequest(
        student_id=student.id,
        meeting_id=payload.meeting_id,
        field_reference=payload.field_reference.strip(),
        description=payload.description.strip(),
    )
    db.add(correction)

    record_audit_event(
        db,
        actor_id=user.id,
        action="CORRECTION_REQUESTED",
        resource_type="correction_request",
        resource_id=None,
        details=f"student_id={student.id}; field={payload.field_reference.strip()}",
    )

    db.commit()
    db.refresh(correction)

    allocation = db.scalar(
        select(Allocation).where(Allocation.student_id == student.id, Allocation.is_active.is_(True))
    )
    if allocation:
        mentor = db.scalar(select(Mentor).where(Mentor.id == allocation.mentor_id))
        if mentor:
            db.add(
                Alert(
                    student_id=student.id,
                    recipient_id=mentor.user_id,
                    severity="MEDIUM",
                    title="Student requested a record correction",
                    body=f"{payload.field_reference.strip()}: {payload.description.strip()}",
                    channel="IN_APP",
                )
            )
            db.commit()
            if mentor.user:
                send_email_alert(
                    recipient=mentor.user.email,
                    subject="Student requested a mentoring record correction",
                    body=f"{payload.field_reference.strip()}: {payload.description.strip()}",
                )

    return correction


@router.get("/student/{student_id}", response_model=list[CorrectionRequestResponse])
def list_student_corrections(
    student_id: int,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    if not can_access_student(db=db, user=user, student_id=student_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student access denied")

    return db.scalars(
        select(CorrectionRequest)
        .where(CorrectionRequest.student_id == student_id)
        .order_by(CorrectionRequest.created_at.desc())
    ).all()


@router.patch("/{correction_id}", response_model=CorrectionRequestResponse)
def resolve_correction_request(
    correction_id: int,
    payload: CorrectionRequestUpdate,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    if user.role not in {UserRole.ADMIN, UserRole.HOD, UserRole.MENTOR}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only mentors, HOD or administrators can act on a correction request",
        )

    correction = db.scalar(select(CorrectionRequest).where(CorrectionRequest.id == correction_id))
    if correction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Correction request not found")

    if not can_access_student(db=db, user=user, student_id=correction.student_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student access denied")

    correction.status = payload.status
    if payload.resolution_notes is not None:
        correction.resolution_notes = payload.resolution_notes.strip()
    if payload.status in {CorrectionStatus.RESOLVED, CorrectionStatus.DISMISSED}:
        correction.resolved_by = user.id
        correction.resolved_at = datetime.now(timezone.utc)

    record_audit_event(
        db,
        actor_id=user.id,
        action="CORRECTION_REQUEST_UPDATED",
        resource_type="correction_request",
        resource_id=correction.id,
        details=f"status={correction.status.value}",
    )

    db.commit()
    db.refresh(correction)
    return correction
