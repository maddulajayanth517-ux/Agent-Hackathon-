import csv
import io
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import case, func, select, text
from sqlalchemy.exc import SQLAlchemyError
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
    ScheduledMeeting,
    ScheduledMeetingStatus,
    Student,
    User,
    UserRole,
)
from ..rbac import Permission, require_permission
from ..policy import frequency_days
from ..schemas import UserContext

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


def frequency_compliance_snapshot(db: Session) -> tuple[int, int, list[dict]]:
    """Return required cadence compliance for every active mentor allocation."""
    now = datetime.now(timezone.utc)
    required_days = frequency_days(db)
    compliant = 0
    exceptions: list[dict] = []
    allocations = db.scalars(select(Allocation).where(Allocation.is_active.is_(True))).all()
    for allocation in allocations:
        last_meeting = db.scalar(
            select(MeetingRecord.meeting_at)
            .where(MeetingRecord.student_id == allocation.student_id, MeetingRecord.mentor_id == allocation.mentor_id)
            .order_by(MeetingRecord.meeting_at.desc())
        )
        reference_date = last_meeting or allocation.allocated_at
        if reference_date.tzinfo is None:
            reference_date = reference_date.replace(tzinfo=timezone.utc)
        due_at = reference_date + timedelta(days=required_days)
        if due_at >= now:
            compliant += 1
        else:
            exceptions.append({
                "student_id": allocation.student_id,
                "mentor_id": allocation.mentor_id,
                "last_meeting_at": last_meeting,
                "due_at": due_at,
                "days_overdue": (now - due_at).days,
            })
    return required_days, compliant, exceptions


def _simple_pdf(lines: list[str]) -> bytes:
    """Generate a compact text-only PDF without a heavyweight runtime dependency."""
    safe_lines = [line.encode("ascii", "replace").decode().replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") for line in lines]
    content = "BT /F1 11 Tf 50 790 Td 14 TL " + " ".join(f"({line}) Tj T*" for line in safe_lines) + " ET"
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        f"<< /Length {len(content.encode())} >>\nstream\n{content}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    result = "%PDF-1.4\n"
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(result.encode()))
        result += f"{index} 0 obj\n{obj}\nendobj\n"
    xref = len(result.encode())
    result += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    result += "".join(f"{offset:010d} 00000 n \n" for offset in offsets[1:])
    result += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF"
    return result.encode()


@router.get("/agent-health")
def agent_health_report(
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission(Permission.VIEW_REPORTS)),
):
    try:
        result = db.execute(text("SELECT * FROM agentops.v_agent_health")).mappings().all()
    except SQLAlchemyError:
        db.rollback()
        return {"report": "agent_health", "agents": []}
    return {"report": "agent_health", "generated_for_user_id": user.id, "agents": [dict(row) for row in result]}


@router.get("/intervention-effectiveness")
def intervention_effectiveness_report(
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission(Permission.VIEW_REPORTS)),
):
    try:
        result = db.execute(text("SELECT * FROM agentops.v_intervention_effectiveness")).mappings().all()
    except SQLAlchemyError:
        db.rollback()
        result = []
    return {"report": "intervention_effectiveness", "generated_for_user_id": user.id, "interventions": [dict(row) for row in result]}


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

    scheduled_meetings = db.scalar(select(func.count(ScheduledMeeting.id))) or 0
    completed_scheduled_meetings = db.scalar(
        select(func.count(ScheduledMeeting.id)).where(ScheduledMeeting.status == ScheduledMeetingStatus.COMPLETED)
    ) or 0
    missed_scheduled_meetings = db.scalar(
        select(func.count(ScheduledMeeting.id)).where(
            ScheduledMeeting.status == ScheduledMeetingStatus.SCHEDULED,
            ScheduledMeeting.scheduled_for < datetime.utcnow(),
        )
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
    required_frequency_days, frequency_compliant, frequency_exceptions = frequency_compliance_snapshot(db)
    active_allocations_count = int(active_allocations)
    frequency_compliance = round(frequency_compliant / active_allocations_count * 100, 2) if active_allocations_count else 100.0

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
            "scheduled_meetings": scheduled_meetings,
            "completed_scheduled_meetings": completed_scheduled_meetings,
            "missed_scheduled_meetings": missed_scheduled_meetings,
            "students_with_meetings": students_with_meetings,
            "meeting_coverage_percent": meeting_coverage,
            "required_frequency_days": required_frequency_days,
            "frequency_compliant_allocations": frequency_compliant,
            "frequency_overdue_allocations": len(frequency_exceptions),
            "frequency_compliance_percent": frequency_compliance,
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


@router.get("/accreditation-evidence.csv")
def accreditation_evidence_csv(
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission(Permission.VIEW_REPORTS)),
):
    """Download audit-ready mentoring evidence without exposing note contents."""
    required_days, compliant, exceptions = frequency_compliance_snapshot(db)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Agent 45 Student Mentoring — Accreditation Evidence"])
    writer.writerow(["Generated at (UTC)", datetime.now(timezone.utc).isoformat()])
    writer.writerow(["Required mentoring frequency (days)", required_days])
    writer.writerow(["Frequency-compliant allocations", compliant])
    writer.writerow([])
    writer.writerow(["Frequency exceptions"])
    writer.writerow(["student_id", "mentor_id", "last_meeting_at", "due_at", "days_overdue"])
    for row in exceptions:
        writer.writerow([row["student_id"], row["mentor_id"], row["last_meeting_at"], row["due_at"], row["days_overdue"]])
    writer.writerow([])
    writer.writerow(["Mentor load register"])
    writer.writerow(["mentor_id", "mentor_name", "capacity", "active_students", "utilization_percent"])
    load_rows = db.execute(
        select(Mentor.id, User.full_name, Mentor.max_students, func.count(Allocation.id).label("active_students"))
        .join(User, User.id == Mentor.user_id)
        .outerjoin(Allocation, (Allocation.mentor_id == Mentor.id) & Allocation.is_active.is_(True))
        .where(Mentor.is_active.is_(True)).group_by(Mentor.id, User.full_name, Mentor.max_students).order_by(User.full_name)
    ).all()
    for row in load_rows:
        capacity = int(row.max_students or 0)
        active = int(row.active_students or 0)
        writer.writerow([row.id, row.full_name, capacity, active, round(active / capacity * 100, 2) if capacity else 0])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=agent45_accreditation_evidence.csv"},
    )


@router.get("/accreditation-evidence.pdf")
def accreditation_evidence_pdf(
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission(Permission.VIEW_REPORTS)),
):
    """Download a concise, shareable accreditation evidence summary."""
    required_days, compliant, exceptions = frequency_compliance_snapshot(db)
    active_allocations = db.scalar(select(func.count(Allocation.id)).where(Allocation.is_active.is_(True))) or 0
    completed_actions = db.scalar(select(func.count(ActionItem.id)).where(ActionItem.status == ActionStatus.COMPLETED)) or 0
    total_actions = db.scalar(select(func.count(ActionItem.id))) or 0
    pdf = _simple_pdf([
        "Agent 45 - Student Mentoring Accreditation Evidence",
        f"Generated (UTC): {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
        f"Institutional mentoring frequency: every {required_days} days",
        f"Active mentor allocations: {active_allocations}",
        f"Cadence-compliant allocations: {compliant}",
        f"Cadence exceptions: {len(exceptions)}",
        f"Action items closed: {completed_actions} of {total_actions}",
        "Detailed allocation and exception evidence is included in the companion CSV export.",
    ])
    return StreamingResponse(iter([pdf]), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=agent45_accreditation_evidence.pdf"})


@router.post("/accreditation-evidence/register")
def register_accreditation_evidence(
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_permission(Permission.VIEW_REPORTS)),
):
    """Register the Agent 45 evidence pack in the supplied quality schema."""
    try:
        row = db.execute(text("""
            INSERT INTO quality.evidence_item
                (title, evidence_type, period_start, period_end, source_schema,
                 source_table, generated_by_agent, content_hash)
            VALUES
                ('Agent 45 Student Mentoring accreditation evidence', 'DATA_EXPORT',
                 CURRENT_DATE, CURRENT_DATE, 'public', 'meeting_records',
                 'Agent 45', md5(CURRENT_TIMESTAMP::text || :actor))
            RETURNING evidence_item_id, created_at
        """), {"actor": str(user.id)}).mappings().one()
        db.commit()
        return {"registered": True, "evidence_item_id": str(row["evidence_item_id"]), "created_at": row["created_at"]}
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Quality evidence schema is unavailable") from exc
