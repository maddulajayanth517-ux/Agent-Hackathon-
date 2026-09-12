from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Allocation, MeetingRecord, Mentor, ScheduledMeeting, ScheduledMeetingStatus, UserRole
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


@router.get("/student/{student_id}", response_model=list[ScheduledMeetingResponse])
def list_scheduled_meetings(student_id: int, include_closed: bool = Query(False), db: Session = Depends(get_db), user: UserContext = Depends(get_current_user)):
    if not can_access_student(db, user, student_id):
        raise HTTPException(status_code=403, detail="Student access denied")
    query = select(ScheduledMeeting).where(ScheduledMeeting.student_id == student_id)
    if not include_closed:
        query = query.where(ScheduledMeeting.status == ScheduledMeetingStatus.SCHEDULED)
    return db.scalars(query.order_by(ScheduledMeeting.scheduled_for)).all()


@router.patch("/{schedule_id}/status", response_model=ScheduledMeetingResponse)
def update_schedule_status(schedule_id: int, state: ScheduledMeetingStatus, db: Session = Depends(get_db), user: UserContext = Depends(get_current_user)):
    item = db.scalar(select(ScheduledMeeting).where(ScheduledMeeting.id == schedule_id))
    if item is None or not can_access_student(db, user, item.student_id):
        raise HTTPException(status_code=404, detail="Scheduled meeting not found")
    if user.role != UserRole.MENTOR:
        raise HTTPException(status_code=403, detail="Only the allocated mentor can update a scheduled meeting")
    item.status = state
    db.commit(); db.refresh(item)
    return item
