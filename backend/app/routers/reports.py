from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, case, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    ActionItem,
    ActionStatus,
    Allocation,
    AuditEvent,
    Escalation,
    EscalationStatus,
    Flag,
    MeetingRecord,
    Mentor,
    Student,
    User,
    UserRole,
)
from ..rbac import Permission, require_permission
from ..schemas import UserContext

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


@router.get("/compliance")
def compliance_report(
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission(Permission.VIEW_REPORTS)),
):
    total_students = db.scalar(
        select(func.count(Student.id)).where(Student.is_active.is_(True))
    ) or 0

    active_allocations = db.scalar(
        select(func.count(Allocation.id)).where(
            Allocation.is_active.is_(True)
        )
    ) or 0

    total_meetings = db.scalar(
        select(func.count(MeetingRecord.id))
    ) or 0

    open_actions = db.scalar(
        select(func.count(ActionItem.id)).where(
            ActionItem.status.in_([
                ActionStatus.OPEN,
                ActionStatus.IN_PROGRESS,
            ])
        )
    ) or 0

    overdue_actions = db.scalar(
        select(func.count(ActionItem.id)).where(
            ActionItem.due_date < datetime.utcnow().date(),
            ActionItem.status.in_([
                ActionStatus.OPEN,
                ActionStatus.IN_PROGRESS,
            ])
        )
    ) or 0

    completed_actions = db.scalar(
        select(func.count(ActionItem.id)).where(
            ActionItem.status == ActionStatus.COMPLETED
        )
    ) or 0

    active_flags = db.scalar(
        select(func.count(Flag.id)).where(
            Flag.is_active.is_(True)
        )
    ) or 0

    open_escalations = db.scalar(
        select(func.count(Escalation.id)).where(
            Escalation.status.in_([
                EscalationStatus.OPEN,
                EscalationStatus.ACKNOWLEDGED,
            ])
        )
    ) or 0

    students_with_meetings = db.scalar(
        select(func.count(func.distinct(MeetingRecord.student_id)))
    ) or 0

    meeting_coverage = (
        round((students_with_meetings / total_students) * 100, 2)
        if total_students
        else 0.0
    )

    action_completion_rate = (
        round(
            (completed_actions / (completed_actions + open_actions + overdue_actions))
            * 100,
            2,
        )
        if (completed_actions + open_actions + overdue_actions)
        else 0.0
    )

    return {
        "report": "compliance",
        "generated_at": datetime.utcnow(),
        "generated_for_user_id": user.id,
        "metrics": {
            "active_students": total_students,
            "active_allocations": active_allocations,
            "total_meetings": total_meetings,
            "students_with_meetings": students_with_meetings,
            "meeting_coverage_percent": meeting_coverage,
            "open_actions": open_actions,
            "overdue_actions": overdue_actions,
            "completed_actions": completed_actions,
            "action_completion_rate_percent": action_completion_rate,
            "active_flags": active_flags,
            "open_escalations": open_escalations,
        },
    }


@router.get("/mentor-load")
def mentor_load_report(
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission(Permission.VIEW_REPORTS)),
):
    rows = db.execute(
        select(
            Mentor.id,
            User.id.label("user_id"),
            User.full_name,
            User.email,
            Mentor.department,
            Mentor.specialization,
            Mentor.max_students,
            func.count(
                func.distinct(
                    case(
                        (Allocation.is_active.is_(True), Allocation.student_id),
                        else_=None,
                    )
                )
            ).label("active_students"),
        )
        .join(User, User.id == Mentor.user_id)
        .outerjoin(
            Allocation,
            Allocation.mentor_id == Mentor.id,
        )
        .where(Mentor.is_active.is_(True))
        .group_by(
            Mentor.id,
            User.id,
            User.full_name,
            User.email,
            Mentor.department,
            Mentor.specialization,
            Mentor.max_students,
        )
        .order_by(User.full_name)
    ).all()

    mentors = []

    for row in rows:
        active_students = int(row.active_students or 0)
        capacity = int(row.max_students or 0)

        utilization = (
            round((active_students / capacity) * 100, 2)
            if capacity > 0
            else 0.0
        )

        mentors.append({
            "mentor_id": row.id,
            "user_id": row.user_id,
            "full_name": row.full_name,
            "email": row.email,
            "department": row.department,
            "specialization": row.specialization,
            "max_students": capacity,
            "active_students": active_students,
            "available_slots": max(capacity - active_students, 0),
            "utilization_percent": utilization,
        })

    return {
        "report": "mentor_load",
        "generated_at": datetime.utcnow(),
        "generated_for_user_id": user.id,
        "mentors": mentors,
    }


@router.get("/audit-summary")
def audit_summary_report(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission(Permission.VIEW_REPORTS)),
):
    since = datetime.utcnow() - timedelta(days=days)

    total_events = db.scalar(
        select(func.count(AuditEvent.id)).where(
            AuditEvent.created_at >= since
        )
    ) or 0

    actor_count = db.scalar(
        select(func.count(func.distinct(AuditEvent.actor_id))).where(
            AuditEvent.created_at >= since,
            AuditEvent.actor_id.is_not(None),
        )
    ) or 0

    event_rows = db.execute(
        select(
            AuditEvent.action,
            func.count(AuditEvent.id).label("count"),
        )
        .where(AuditEvent.created_at >= since)
        .group_by(AuditEvent.action)
        .order_by(func.count(AuditEvent.id).desc())
    ).all()

    actions = [
        {
            "action": row.action,
            "count": int(row.count),
        }
        for row in event_rows
    ]

    return {
        "report": "audit_summary",
        "generated_at": datetime.utcnow(),
        "generated_for_user_id": user.id,
        "period_days": days,
        "since": since,
        "total_events": int(total_events),
        "unique_actors": int(actor_count),
        "actions": actions,
    }