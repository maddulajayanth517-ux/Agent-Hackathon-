from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..audit import record_audit_event
from ..database import get_db
from ..models import Alert, Allocation, MeetingRecord, Mentor, ScheduledMeeting, ScheduledMeetingStatus, Student, UserRole
from ..policy import frequency_days
from ..rbac import can_access_student, get_current_user, get_mentor_by_user_id
from ..schemas import ScheduledMeetingCreate, ScheduledMeetingResponse, UserContext

router = APIRouter(prefix="/schedules", tags=["Meeting Scheduling"])


@router.post("", response_model=ScheduledMeetingResponse, status_code=status.HTTP_201_CREATED)
def schedule_meeting(payload: ScheduledMeetingCreate, db: Session = Depends(get_db), user: UserContext = Depends(get_current_user)):
    if user.role != UserRole.MENTOR or not can_access_student(db, user, payload.student_id):
        raise HTTPException(status_code=403, detail="Only the allocated mentor can schedule this meeting")
    if payload.scheduled_for <= datetime.now(timezone.utc):
        raise HTTPException(status_code=422, detail="Scheduled meeting must be in the future")
    mentor = get_mentor_by_user_id(db, user.id)
    if mentor is None:
        raise HTTPException(status_code=400, detail="Active mentor profile not found")
    last_meeting = db.scalar(
        select(MeetingRecord.meeting_at)
        .where(MeetingRecord.student_id == payload.student_id, MeetingRecord.mentor_id == mentor.id)
        .order_by(MeetingRecord.meeting_at.desc())
    )
    allocation = db.scalar(select(Allocation).where(
        Allocation.student_id == payload.student_id, Allocation.mentor_id == mentor.id, Allocation.is_active.is_(True)
    ))
    reference = last_meeting or allocation.allocated_at
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    due_at = reference + timedelta(days=frequency_days(db))
    if due_at >= datetime.now(timezone.utc) and payload.scheduled_for > due_at:
        raise HTTPException(status_code=422, detail=f"Meeting must be scheduled by {due_at.isoformat()} to meet institutional cadence")
    item = ScheduledMeeting(student_id=payload.student_id, mentor_id=mentor.id, scheduled_for=payload.scheduled_for,
                            mode=payload.mode, agenda=payload.agenda, created_by=user.id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.post("/request", response_model=ScheduledMeetingResponse, status_code=status.HTTP_201_CREATED)
def request_meeting(payload: ScheduledMeetingCreate, db: Session = Depends(get_db), user: UserContext = Depends(get_current_user)):
    """Let a student ask their mentor for a meeting, instead of only the mentor being able to schedule one."""
    if user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can request a meeting through this endpoint")

    student = db.scalar(select(Student).where(Student.user_id == user.id, Student.is_active.is_(True)))
    if student is None or student.id != payload.student_id:
        raise HTTPException(status_code=403, detail="Students can only request meetings for themselves")

    if payload.scheduled_for <= datetime.now(timezone.utc):
        raise HTTPException(status_code=422, detail="Requested meeting time must be in the future")

    allocation = db.scalar(
        select(Allocation).where(Allocation.student_id == student.id, Allocation.is_active.is_(True))
    )
    if allocation is None:
        raise HTTPException(status_code=400, detail="No active mentor allocation found")

    item = ScheduledMeeting(
        student_id=student.id,
        mentor_id=allocation.mentor_id,
        scheduled_for=payload.scheduled_for,
        mode=payload.mode,
        agenda=payload.agenda,
        status=ScheduledMeetingStatus.REQUESTED,
        created_by=user.id,
    )
    db.add(item)
    db.flush()
    record_audit_event(
        db,
        actor_id=user.id,
        action="MEETING_REQUESTED",
        resource_type="scheduled_meeting",
        resource_id=item.id,
        details=f"student_id={student.id}; scheduled_for={payload.scheduled_for.isoformat()}",
    )
    db.commit()
    db.refresh(item)

    mentor = db.scalar(select(Mentor).where(Mentor.id == allocation.mentor_id))
    if mentor:
        db.add(Alert(
            student_id=student.id,
            recipient_id=mentor.user_id,
            severity="INFO",
            title="Meeting requested by student",
            body=f"Requested for {payload.scheduled_for.isoformat()}" + (f" — {payload.agenda}" if payload.agenda else ""),
            channel="IN_APP",
        ))
        db.commit()

    return item


@router.get("/student/{student_id}", response_model=list[ScheduledMeetingResponse])
def list_scheduled_meetings(student_id: int, include_closed: bool = Query(False), db: Session = Depends(get_db), user: UserContext = Depends(get_current_user)):
    if not can_access_student(db, user, student_id):
        raise HTTPException(status_code=403, detail="Student access denied")
    query = select(ScheduledMeeting).where(ScheduledMeeting.student_id == student_id)
    if not include_closed:
        query = query.where(ScheduledMeeting.status.in_([ScheduledMeetingStatus.SCHEDULED, ScheduledMeetingStatus.REQUESTED]))
    return db.scalars(query.order_by(ScheduledMeeting.scheduled_for)).all()


@router.patch("/{schedule_id}/status", response_model=ScheduledMeetingResponse)
def update_schedule_status(schedule_id: int, state: ScheduledMeetingStatus, db: Session = Depends(get_db), user: UserContext = Depends(get_current_user)):
    item = db.scalar(select(ScheduledMeeting).where(ScheduledMeeting.id == schedule_id))
    if item is None or not can_access_student(db, user, item.student_id):
        raise HTTPException(status_code=404, detail="Scheduled meeting not found")
    if user.role != UserRole.MENTOR:
        raise HTTPException(status_code=403, detail="Only the allocated mentor can update a scheduled meeting")
    item.status = state
    record_audit_event(
        db,
        actor_id=user.id,
        action="SCHEDULED_MEETING_STATUS_UPDATED",
        resource_type="scheduled_meeting",
        resource_id=item.id,
        details=f"status={state.value}",
    )
    db.commit(); db.refresh(item)
    return item
