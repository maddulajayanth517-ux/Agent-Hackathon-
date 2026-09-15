from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..agent import build_student_mentor_brief
from ..database import get_db
from ..institutional import get_institutional_context
from ..models import (
    ActionItem,
    ActionStatus,
    Alert,
    Allocation,
    Escalation,
    EscalationStatus,
    Flag,
    MeetingRecord,
    Mentor,
    ScheduledMeeting,
    ScheduledMeetingStatus,
    Student,
    User,
    UserRole,
)
from ..rbac import (
    Permission,
    can_access_student,
    get_current_user,
    get_mentor_by_user_id,
    require_permission,
)
from ..schemas import UserContext

router = APIRouter(tags=["Dashboards"])


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@router.get("/mentor/dashboard")
def mentor_dashboard(db: Session = Depends(get_db), user: UserContext = Depends(get_current_user)):
    mentor = get_mentor_by_user_id(db, user.id)
    if mentor is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Active mentor profile not found")

    now = _utc_now()
    today_start = datetime.combine(now.date(), datetime.min.time(), tzinfo=timezone.utc)
    today_end = today_start + timedelta(days=1)

    allocations = db.scalars(
        select(Allocation).where(Allocation.mentor_id == mentor.id, Allocation.is_active.is_(True))
    ).all()
    student_ids = [a.student_id for a in allocations]

    meetings_today_count = len(db.scalars(
        select(ScheduledMeeting.id).where(
            ScheduledMeeting.mentor_id == mentor.id,
            ScheduledMeeting.status == ScheduledMeetingStatus.SCHEDULED,
            ScheduledMeeting.scheduled_for >= today_start,
            ScheduledMeeting.scheduled_for < today_end,
        )
    ).all())

    open_actions_count = 0
    if student_ids:
        open_actions_count = len(db.scalars(
            select(ActionItem.id).where(
                ActionItem.student_id.in_(student_ids),
                ActionItem.status.in_([ActionStatus.OPEN, ActionStatus.IN_PROGRESS]),
            )
        ).all())

    new_alerts_count = len(db.scalars(
        select(Alert.id).where(Alert.recipient_id == user.id, Alert.read_at.is_(None))
    ).all())

    priority_queue = []
    for allocation in allocations:
        student = db.scalar(select(Student).where(Student.id == allocation.student_id))
        if student is None or student.user is None:
            continue
        brief = build_student_mentor_brief(db, student.id)
        last_meeting_at = db.scalar(
            select(MeetingRecord.meeting_at)
            .where(MeetingRecord.student_id == student.id, MeetingRecord.mentor_id == mentor.id)
            .order_by(MeetingRecord.meeting_at.desc())
        )
        last_contact_days = None
        if last_meeting_at is not None:
            reference = last_meeting_at if last_meeting_at.tzinfo else last_meeting_at.replace(tzinfo=timezone.utc)
            last_contact_days = (now - reference).days
        priority_queue.append({
            "student_id": student.id,
            "name": student.user.full_name,
            "register_number": student.register_number,
            "risk_level": brief["risk_level"],
            "risk_score": brief["risk_score"],
            "top_issue": brief["evidence"][0] if brief["evidence"] else "No active concerns recorded.",
            "last_contact_days": last_contact_days,
            "recommended_action": brief["recommendations"][0] if brief["recommendations"] else "Continue regular mentoring review.",
        })

    priority_queue.sort(key=lambda item: item["risk_score"], reverse=True)

    upcoming_meetings = []
    for meeting in db.scalars(
        select(ScheduledMeeting)
        .where(
            ScheduledMeeting.mentor_id == mentor.id,
            ScheduledMeeting.status == ScheduledMeetingStatus.SCHEDULED,
            ScheduledMeeting.scheduled_for >= now,
        )
        .order_by(ScheduledMeeting.scheduled_for)
        .limit(6)
    ).all():
        student = db.scalar(select(Student).where(Student.id == meeting.student_id))
        upcoming_meetings.append({
            "id": meeting.id,
            "student_id": meeting.student_id,
            "student_name": student.user.full_name if student and student.user else "Unknown student",
            "scheduled_for": meeting.scheduled_for,
            "mode": meeting.mode,
            "agenda": meeting.agenda,
        })

    recent_alerts = [
        {
            "id": alert.id,
            "student_id": alert.student_id,
            "title": alert.title,
            "body": alert.body,
            "severity": alert.severity,
            "created_at": alert.created_at,
            "read_at": alert.read_at,
        }
        for alert in db.scalars(
            select(Alert).where(Alert.recipient_id == user.id).order_by(Alert.created_at.desc()).limit(8)
        ).all()
    ]

    return {
        "mentor": {"id": mentor.id, "user_id": mentor.user_id, "department": mentor.department},
        "counts": {
            "total_mentees": len(student_ids),
            "meetings_today": meetings_today_count,
            "open_actions": open_actions_count,
            "new_alerts": new_alerts_count,
        },
        "priority_queue": priority_queue[:8],
        "upcoming_meetings": upcoming_meetings,
        "recent_alerts": recent_alerts,
        "generated_at": now,
    }


@router.get("/mentor/actions")
def mentor_actions(
    status_filter: ActionStatus | None = None,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    mentor = get_mentor_by_user_id(db, user.id)
    if mentor is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Active mentor profile not found")

    student_ids = [
        a.student_id
        for a in db.scalars(
            select(Allocation).where(Allocation.mentor_id == mentor.id, Allocation.is_active.is_(True))
        ).all()
    ]
    if not student_ids:
        return []

    query = select(ActionItem).where(ActionItem.student_id.in_(student_ids))
    if status_filter is not None:
        query = query.where(ActionItem.status == status_filter)

    items = db.scalars(query.order_by(ActionItem.due_date.asc().nulls_last())).all()
    students_by_id = {
        s.id: s for s in db.scalars(select(Student).where(Student.id.in_(student_ids))).all()
    }

    return [
        {
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "student_id": item.student_id,
            "student_name": students_by_id[item.student_id].user.full_name if item.student_id in students_by_id and students_by_id[item.student_id].user else "Unknown",
            "owner_id": item.owner_id,
            "due_date": item.due_date,
            "status": item.status,
            "completed_at": item.completed_at,
        }
        for item in items
    ]


@router.get("/student/dashboard")
def student_dashboard(db: Session = Depends(get_db), user: UserContext = Depends(get_current_user)):
    student = db.scalar(select(Student).where(Student.user_id == user.id, Student.is_active.is_(True)))
    if student is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Active student profile not found")

    now = _utc_now()

    allocation = db.scalar(select(Allocation).where(Allocation.student_id == student.id, Allocation.is_active.is_(True)))
    mentor = db.scalar(select(Mentor).where(Mentor.id == allocation.mentor_id)) if allocation else None

    next_meeting = db.scalar(
        select(ScheduledMeeting)
        .where(
            ScheduledMeeting.student_id == student.id,
            ScheduledMeeting.status == ScheduledMeetingStatus.SCHEDULED,
            ScheduledMeeting.scheduled_for >= now,
        )
        .order_by(ScheduledMeeting.scheduled_for)
    )

    actions = db.scalars(select(ActionItem).where(ActionItem.student_id == student.id)).all()
    open_actions = [a for a in actions if a.status in {ActionStatus.OPEN, ActionStatus.IN_PROGRESS}]
    completed_actions = [a for a in actions if a.status == ActionStatus.COMPLETED]

    brief = build_student_mentor_brief(db, student.id)
    institutional_context = get_institutional_context(db, student.register_number)
    profile = (institutional_context or {}).get("profile") or {}

    return {
        "student": {
            "id": student.id,
            "name": student.user.full_name if student.user else None,
            "register_number": student.register_number,
            "department": student.department,
            "year": student.year,
        },
        "mentor": (
            {"id": mentor.id, "name": mentor.user.full_name if mentor.user else None, "email": mentor.user.email if mentor.user else None}
            if mentor
            else None
        ),
        "next_meeting": (
            {
                "id": next_meeting.id,
                "scheduled_for": next_meeting.scheduled_for,
                "mode": next_meeting.mode,
                "agenda": next_meeting.agenda,
            }
            if next_meeting
            else None
        ),
        "counts": {
            "pending_actions": len(open_actions),
            "completed_actions": len(completed_actions),
        },
        "profile_snapshot": {
            "attendance_pct": profile.get("attendance_pct"),
            "cgpa": profile.get("cgpa"),
            "backlog_count": profile.get("backlog_count"),
        },
        "risk_level": brief["risk_level"],
        "open_actions": [
            {"id": a.id, "title": a.title, "due_date": a.due_date, "status": a.status}
            for a in sorted(open_actions, key=lambda a: (a.due_date is None, a.due_date))
        ],
        "generated_at": now,
    }


@router.get("/hod/analytics")
def hod_analytics(
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission(Permission.VIEW_REPORTS)),
):
    total_mentors = len(db.scalars(select(Mentor.id).where(Mentor.is_active.is_(True))).all())
    total_mentees = len(db.scalars(select(Student.id).where(Student.is_active.is_(True))).all())

    open_escalations = db.scalars(
        select(Escalation).where(Escalation.status.in_([EscalationStatus.OPEN, EscalationStatus.ACKNOWLEDGED]))
    ).all()
    escalations_by_destination: dict[str, int] = {}
    for escalation in open_escalations:
        escalations_by_destination[escalation.destination] = escalations_by_destination.get(escalation.destination, 0) + 1

    overdue_actions = len(db.scalars(
        select(ActionItem.id).where(
            ActionItem.due_date < date.today(),
            ActionItem.status.in_([ActionStatus.OPEN, ActionStatus.IN_PROGRESS]),
        )
    ).all())

    mentor_rows = db.scalars(select(Mentor).where(Mentor.is_active.is_(True))).all()
    mentor_workload = []
    for mentor in mentor_rows:
        active_students = len(db.scalars(
            select(Allocation.id).where(Allocation.mentor_id == mentor.id, Allocation.is_active.is_(True))
        ).all())
        capacity = mentor.max_students or 0
        mentor_workload.append({
            "mentor_id": mentor.id,
            "name": mentor.user.full_name if mentor.user else "Mentor",
            "active_students": active_students,
            "capacity": capacity,
            "utilization_percent": round((active_students / capacity) * 100, 2) if capacity else 0.0,
        })

    status_distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for student in db.scalars(select(Student).where(Student.is_active.is_(True))).all():
        brief = build_student_mentor_brief(db, student.id)
        status_distribution[brief["risk_level"]] = status_distribution.get(brief["risk_level"], 0) + 1

    return {
        "totals": {
            "total_mentors": total_mentors,
            "total_mentees": total_mentees,
            "open_escalations": len(open_escalations),
            "overdue_actions": overdue_actions,
        },
        "mentor_workload": mentor_workload,
        "student_status_distribution": status_distribution,
        "escalations_by_destination": escalations_by_destination,
        "generated_for_user_id": user.id,
        "generated_at": _utc_now(),
    }


@router.get("/students/{student_id}/what-changed")
def what_changed(student_id: int, db: Session = Depends(get_db), user: UserContext = Depends(get_current_user)):
    if not can_access_student(db=db, user=user, student_id=student_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student access denied")

    student = db.scalar(select(Student).where(Student.id == student_id, Student.is_active.is_(True)))
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    meetings = db.scalars(
        select(MeetingRecord).where(MeetingRecord.student_id == student_id).order_by(MeetingRecord.meeting_at.desc())
    ).all()
    latest_meeting = meetings[0] if meetings else None

    since = latest_meeting.meeting_at if latest_meeting else None
    since_reference = since if (since is None or since.tzinfo) else since.replace(tzinfo=timezone.utc)

    flags = db.scalars(
        select(Flag).where(Flag.student_id == student_id, Flag.is_active.is_(True)).order_by(Flag.created_at.desc())
    ).all()
    new_signals = [
        f"{flag.category}: {flag.description}"
        for flag in flags
        if since_reference is None or flag.created_at.replace(tzinfo=flag.created_at.tzinfo or timezone.utc) > since_reference
    ]

    actions = db.scalars(select(ActionItem).where(ActionItem.student_id == student_id)).all()
    completed_since_last = [
        a.title for a in actions
        if a.status == ActionStatus.COMPLETED and a.completed_at is not None
        and (since_reference is None or a.completed_at.replace(tzinfo=a.completed_at.tzinfo or timezone.utc) > since_reference)
    ]
    still_open = [
        {"title": a.title, "due_date": a.due_date, "status": a.status}
        for a in actions if a.status in {ActionStatus.OPEN, ActionStatus.IN_PROGRESS}
    ]

    institutional_context = get_institutional_context(db, student.register_number)
    current_profile = (institutional_context or {}).get("profile") or {}

    def _delta(label: str, before, after, unit: str = ""):
        if before is None or after is None:
            return None
        before_f, after_f = float(before), float(after)
        direction = "up" if after_f > before_f else "down" if after_f < before_f else "flat"
        return {"label": label, "from": before_f, "to": after_f, "unit": unit, "direction": direction}

    metric_changes = [
        change for change in [
            _delta("Attendance", latest_meeting.attendance_pct_snapshot if latest_meeting else None, current_profile.get("attendance_pct"), "%"),
            _delta("CGPA", latest_meeting.cgpa_snapshot if latest_meeting else None, current_profile.get("cgpa")),
            _delta("Backlogs", latest_meeting.backlog_count_snapshot if latest_meeting else None, current_profile.get("backlog_count")),
        ]
        if change is not None
    ]

    return {
        "student_id": student_id,
        "since_last_meeting_at": latest_meeting.meeting_at if latest_meeting else None,
        "metric_changes": metric_changes,
        "new_signals": new_signals,
        "actions_completed_since_last_meeting": completed_since_last,
        "still_open_actions": still_open,
        "has_baseline": latest_meeting is not None,
    }
