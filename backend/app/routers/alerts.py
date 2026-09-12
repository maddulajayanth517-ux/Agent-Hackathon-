from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Alert, Allocation, MeetingRecord, Mentor, ScheduledMeeting, ScheduledMeetingStatus, User, UserRole
from ..notifications import send_email_alert
from ..policy import frequency_days, reminder_days
from ..rbac import get_current_user
from ..schemas import UserContext

router = APIRouter(prefix="/alerts", tags=["Alerts & Reminders"])


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    recipient_id: int
    flag_id: int | None
    severity: str
    title: str
    body: str
    channel: str
    read_at: datetime | None
    actioned_at: datetime | None
    created_at: datetime


@router.get("/student/{student_id}", response_model=list[AlertResponse])
def list_student_alerts(
    student_id: int,
    unread_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    query = select(Alert).where(Alert.student_id == student_id)
    if user.role not in {UserRole.ADMIN, UserRole.HOD, UserRole.COUNSELLOR}:
        query = query.where(Alert.recipient_id == user.id)
    if unread_only:
        query = query.where(Alert.read_at.is_(None))
    return db.scalars(query.order_by(Alert.created_at.desc())).all()


@router.patch("/{alert_id}/read", response_model=AlertResponse)
def mark_alert_read(
    alert_id: int,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    alert = db.scalar(select(Alert).where(Alert.id == alert_id))
    if alert is None or (alert.recipient_id != user.id and user.role not in {UserRole.ADMIN, UserRole.HOD}):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    alert.read_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return alert


@router.post("/reminders/run")
def run_meeting_reminders(
    days: int | None = Query(default=None, ge=1, le=30),
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    if user.role not in {UserRole.ADMIN, UserRole.HOD}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administrators or HOD users can run reminders")

    days = days or reminder_days(db)
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=days)
    meetings = db.scalars(
        select(MeetingRecord).where(
            MeetingRecord.next_meeting_at >= now,
            MeetingRecord.next_meeting_at <= cutoff,
        )
    ).all()
    created = 0
    for meeting in meetings:
        allocation = db.scalar(select(Allocation).where(
            Allocation.student_id == meeting.student_id,
            Allocation.mentor_id == meeting.mentor_id,
            Allocation.is_active.is_(True),
        ))
        if allocation is None:
            continue
        mentor_user_id = db.scalar(
            select(Mentor.user_id).where(Mentor.id == allocation.mentor_id)
        ) or meeting.created_by
        duplicate = db.scalar(select(Alert.id).where(
            Alert.student_id == meeting.student_id,
            Alert.recipient_id == mentor_user_id,
            Alert.title == "Upcoming mentoring meeting",
            Alert.created_at >= now - timedelta(days=1),
        ))
        if duplicate is None:
            alert = Alert(
                student_id=meeting.student_id,
                recipient_id=mentor_user_id,
                severity="INFO",
                title="Upcoming mentoring meeting",
                body=f"Meeting {meeting.next_meeting_at.isoformat()} is scheduled for student {meeting.student_id}.",
                channel="IN_APP",
            )
            db.add(alert)
            created += 1
    scheduled_meetings = db.scalars(
        select(ScheduledMeeting).where(
            ScheduledMeeting.status == ScheduledMeetingStatus.SCHEDULED,
            ScheduledMeeting.scheduled_for >= now,
            ScheduledMeeting.scheduled_for <= cutoff,
        )
    ).all()
    for meeting in scheduled_meetings:
        mentor_user_id = db.scalar(select(Mentor.user_id).where(Mentor.id == meeting.mentor_id))
        if mentor_user_id is None:
            continue
        duplicate = db.scalar(select(Alert.id).where(
            Alert.student_id == meeting.student_id,
            Alert.recipient_id == mentor_user_id,
            Alert.title == "Upcoming mentoring meeting",
            Alert.created_at >= now - timedelta(days=1),
        ))
        if duplicate is None:
            db.add(Alert(
                student_id=meeting.student_id,
                recipient_id=mentor_user_id,
                severity="INFO",
                title="Upcoming mentoring meeting",
                body=f"Scheduled mentoring meeting {meeting.scheduled_for.isoformat()} requires preparation.",
                channel="IN_APP",
            ))
            created += 1
    # Frequency enforcement: alert the mentor whenever a mentee has passed
    # the institutional cadence without a completed mentoring record.
    cadence = frequency_days(db)
    allocations = db.scalars(select(Allocation).where(Allocation.is_active.is_(True))).all()
    for allocation in allocations:
        last_meeting = db.scalar(
            select(MeetingRecord.meeting_at)
            .where(MeetingRecord.student_id == allocation.student_id, MeetingRecord.mentor_id == allocation.mentor_id)
            .order_by(MeetingRecord.meeting_at.desc())
        )
        reference = last_meeting or allocation.allocated_at
        if reference.tzinfo is None:
            reference = reference.replace(tzinfo=timezone.utc)
        due_at = reference + timedelta(days=cadence)
        if due_at >= now:
            continue
        mentor_user_id = db.scalar(select(Mentor.user_id).where(Mentor.id == allocation.mentor_id))
        duplicate = db.scalar(select(Alert.id).where(
            Alert.student_id == allocation.student_id,
            Alert.recipient_id == mentor_user_id,
            Alert.title == "Mentoring frequency overdue",
            Alert.read_at.is_(None),
        ))
        if mentor_user_id is not None and duplicate is None:
            db.add(Alert(
                student_id=allocation.student_id, recipient_id=mentor_user_id,
                severity="HIGH", title="Mentoring frequency overdue",
                body=f"A mentoring meeting is overdue by {(now - due_at).days} day(s) under the {cadence}-day institutional policy.",
                channel="IN_APP",
            ))
            created += 1
    db.commit()
    for alert in db.scalars(select(Alert).where(
        Alert.title == "Upcoming mentoring meeting",
        Alert.created_at >= now,
    )).all():
        recipient_email = db.scalar(select(User.email).where(User.id == alert.recipient_id))
        send_email_alert(
            recipient=recipient_email,
            subject=alert.title,
            body=alert.body,
        )
    return {"created": created, "window_days": days}
