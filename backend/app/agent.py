from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .institutional import get_institutional_context
from .models import ActionItem, ActionStatus, Flag, MeetingRecord, Student


RISK_SCORE_MAP = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


def _score_flag(flag: Flag) -> int:
    severity = getattr(flag.severity, "value", flag.severity)
    return RISK_SCORE_MAP.get(str(severity).lower(), 0)


def _is_overdue(item: ActionItem, now: datetime) -> bool:
    due_date = item.due_date
    current_date = now.date()
    if isinstance(due_date, datetime):
        return (
            due_date < now
            and item.status not in {ActionStatus.COMPLETED, ActionStatus.CANCELLED}
        )
    return (
        due_date is not None
        and due_date < current_date
        and item.status not in {ActionStatus.COMPLETED, ActionStatus.CANCELLED}
    )


def _score_student_context(
    *,
    flags: Iterable[Flag],
    actions: Iterable[ActionItem],
    meetings: Iterable[MeetingRecord],
    now: datetime,
) -> tuple[int, str, list[str], list[str], list[str]]:
    risk_score = 0
    reasons: list[str] = []
    alerts: list[str] = []

    for flag in flags:
        risk_score += _score_flag(flag)
        severity = getattr(flag.severity, "value", flag.severity)
        reasons.append(f"{flag.category}: {flag.description} ({severity})")

    overdue_count = 0
    open_count = 0
    for action in actions:
        if action.status in {ActionStatus.OPEN, ActionStatus.IN_PROGRESS}:
            open_count += 1
        if _is_overdue(action, now):
            overdue_count += 1
            alerts.append(f"Overdue action: {action.title}")

    if open_count >= 3:
        risk_score += 1
        reasons.append("Multiple open actions outstanding")

    if overdue_count >= 1:
        risk_score += 1
        reasons.append("Action backlog is overdue")

    if meetings:
        latest_meeting = max(meetings, key=lambda m: m.meeting_at)
        days_since = (now - latest_meeting.meeting_at).days
        if days_since > 30:
            risk_score += 2
            alerts.append("No recent mentoring meeting recorded")
            reasons.append("Mentoring cadence is below expected frequency")
        elif days_since > 14:
            risk_score += 1
            alerts.append("Meeting gap is growing")

    if risk_score >= 7:
        level = "critical"
    elif risk_score >= 4:
        level = "high"
    elif risk_score >= 2:
        level = "medium"
    else:
        level = "low"

    if level == "critical":
        recommended = [
            "Arrange immediate mentor follow-up and review support needs.",
            "Escalate to HoD or counselling based on issue category.",
            "Reassess action plan within 48 hours.",
        ]
    elif level == "high":
        recommended = [
            "Review recent notes and unresolved actions with the mentee.",
            "Check for new academic or personal risk signals.",
            "Escalate if concerns continue after the next review.",
        ]
    elif level == "medium":
        recommended = [
            "Continue close monitoring and follow-up in the next meeting.",
            "Confirm progress on open actions.",
            "Keep the student brief updated before the next session.",
        ]
    else:
        recommended = [
            "Maintain regular review cadence.",
            "Confirm all routine follow-ups are on track.",
            "Keep mentoring notes current and actionable.",
        ]

    return risk_score, level, alerts, recommended, reasons


def build_student_mentor_brief(db: Session, student_id: int) -> dict[str, Any]:
    now = datetime.utcnow()
    student = db.get(Student, student_id)
    institutional_context = (
        get_institutional_context(db, student.register_number) if student else None
    )

    meetings = db.scalars(
        select(MeetingRecord)
        .where(MeetingRecord.student_id == student_id)
        .order_by(MeetingRecord.meeting_at.desc())
    ).all()

    actions = db.scalars(
        select(ActionItem)
        .where(ActionItem.student_id == student_id)
        .order_by(ActionItem.due_date.asc())
    ).all()

    flags = db.scalars(
        select(Flag)
        .where(Flag.student_id == student_id, Flag.is_active.is_(True))
        .order_by(Flag.created_at.desc())
    ).all()

    score, level, alerts, recommendations, evidence = _score_student_context(
        flags=flags,
        actions=actions,
        meetings=meetings,
        now=now,
    )

    latest_meeting = meetings[0] if meetings else None
    latest_notes = latest_meeting.notes if latest_meeting else "No recent mentoring meeting recorded."

    if latest_meeting and latest_meeting.student_concerns:
        concern_text = latest_meeting.student_concerns
    elif flags:
        concern_text = "; ".join(f.description for f in flags[:3])
    else:
        concern_text = "No active concerns recorded."

    open_actions = [
        a for a in actions if a.status in {ActionStatus.OPEN, ActionStatus.IN_PROGRESS}
    ]
    overdue_actions = [a for a in actions if _is_overdue(a, now)]

    result = {
        "risk_score": score,
        "risk_level": level,
        "alert_count": len(alerts),
        "alerts": alerts,
        "evidence": evidence,
        "recommendations": recommendations,
        "summary": (
            "Student is currently in a "
            f"{level} risk state with {len(open_actions)} active actions and "
            f"{len(overdue_actions)} overdue items."
        ),
        "latest_meeting_summary": latest_notes,
        "concerns": concern_text,
        "next_steps": recommendations,
        "generated_at": now.isoformat(),
    }

    if institutional_context:
        result["institutional_context"] = institutional_context

    return result


def route_escalation_by_risk(student_id: int, risk_level: str, category: str | None = None) -> dict[str, Any]:
    normalized = (risk_level or "low").lower()
    if category:
        category_key = category.lower()
    else:
        category_key = "general"

    if normalized in {"critical", "high"}:
        if "academic" in category_key:
            destination = "HOD"
        elif "financial" in category_key:
            destination = "Scholarship / Fee Section"
        elif "personal" in category_key or "emotional" in category_key:
            destination = "Counselling Cell"
        else:
            destination = "HOD"
        priority = "HIGH" if normalized == "high" else "CRITICAL"
    else:
        destination = "Mentor"
        priority = "MEDIUM"

    return {
        "student_id": student_id,
        "destination": destination,
        "priority": priority,
        "risk_level": normalized,
        "reason": (
            "Automated mentoring risk routing based on student risk score and issue category."
        ),
    }
