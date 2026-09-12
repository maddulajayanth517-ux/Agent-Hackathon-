from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..agent import build_student_mentor_brief
from ..database import get_db
from ..models import (
    ActionItem,
    Allocation,
    MeetingRecord,
    Mentor,
    Student,
    User,
    Flag,
)
from ..rbac import can_access_student, get_current_user
from ..schemas import UserContext

router = APIRouter(prefix="/brief", tags=["Student Brief"])


@router.get("/student/{student_id}")
def get_student_brief(
    student_id: int,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    if not can_access_student(
        db=db,
        user=user,
        student_id=student_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "student_access_denied",
                "student_id": student_id,
            },
        )

    student = db.scalar(
        select(Student)
        .options(selectinload(Student.user))
        .where(
            Student.id == student_id,
            Student.is_active.is_(True),
        )
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    allocation = db.scalar(
        select(Allocation).where(
            Allocation.student_id == student_id,
            Allocation.is_active.is_(True),
        )
    )

    mentor = None

    if allocation:
        mentor = db.scalar(
            select(Mentor)
            .options(selectinload(Mentor.user))
            .where(Mentor.id == allocation.mentor_id)
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
        select(Flag).where(Flag.student_id == student_id, Flag.is_active.is_(True)).order_by(Flag.created_at.desc())
    ).all()

    now = datetime.utcnow()

    open_actions = [
        action
        for action in actions
        if action.status.value in {"open", "in_progress"}
    ]

    overdue_actions = [
    action
    for action in actions
    if action.due_date is not None
    and action.due_date < now
    and action.status.value not in {"completed", "cancelled"}
    ]

    completed_actions = [
        action
        for action in actions
        if action.status.value == "completed"
    ]

    latest_meeting = meetings[0] if meetings else None

    base_response = {
        "student": {
            "id": student.id,
            "user_id": student.user_id,
            "name": student.user.full_name if student.user else None,
            "email": student.user.email if student.user else None,
            "register_number": student.register_number,
            "department": student.department,
            "year": student.year,
            "section": student.section,
        },
        "mentor": (
            {
                "id": mentor.id,
                "user_id": mentor.user_id,
                "name": mentor.user.full_name if mentor.user else None,
                "email": mentor.user.email if mentor.user else None,
                "department": mentor.department,
                "specialization": mentor.specialization,
            }
            if mentor
            else None
        ),
        "summary": {
            "total_meetings": len(meetings),
            "total_actions": len(actions),
            "open_actions": len(open_actions),
            "overdue_actions": len(overdue_actions),
            "completed_actions": len(completed_actions),
            "completion_percentage": (
                round(len(completed_actions) / len(actions) * 100, 2)
                if actions
                else 0.0
            ),
        },
        "latest_meeting": (
            {
                "id": latest_meeting.id,
                "meeting_at": latest_meeting.meeting_at,
                "mode": latest_meeting.mode,
                "agenda": latest_meeting.agenda,
                "notes": latest_meeting.notes,
                "student_concerns": latest_meeting.student_concerns,
                "mentor_observations": latest_meeting.mentor_observations,
                "next_meeting_at": latest_meeting.next_meeting_at,
            }
            if latest_meeting
            else None
        ),
        "action_items": [
            {
                "id": action.id,
                "meeting_id": action.meeting_id,
                "title": action.title,
                "description": action.description,
                "owner_id": action.owner_id,
                "due_date": action.due_date,
                "status": action.status,
                "completed_at": action.completed_at,
            }
            for action in actions
        ],
        "key_changes": [
            f"New active flag: {flag.category} ({flag.severity.value}) — {flag.description}"
            for flag in flags[:5]
        ] + ([f"Last meeting was on {latest_meeting.meeting_at.date()}." ] if latest_meeting else ["No meeting has been recorded yet."]),
        "open_concerns": [flag.description for flag in flags[:5]],
        "pending_actions": [
            f"{action.title} (due {action.due_date.date() if action.due_date else 'no deadline'})"
            for action in open_actions
        ],
        "discussion_points": [
            "Review academic progress and attendance since the last meeting.",
            "Confirm progress on each pending action and remove blockers.",
            "Discuss career direction and any support the student has requested.",
        ],
        "generated_at": datetime.utcnow(),
    }

    risk_snapshot = build_student_mentor_brief(db, student_id)
    base_response["source"] = "agent"
    base_response["warning"] = "Institutional mentor brief generated from current records."
    base_response["risk"] = {
        "score": risk_snapshot["risk_score"],
        "level": risk_snapshot["risk_level"],
        "alerts": risk_snapshot["alerts"],
    }
    base_response["recommendations"] = risk_snapshot["recommendations"]
    base_response["next_steps"] = risk_snapshot["next_steps"]
    base_response["recommended_next_steps"] = risk_snapshot["next_steps"]
    if risk_snapshot.get("institutional_context"):
        base_response["institutional_context"] = risk_snapshot["institutional_context"]
    return base_response


@router.get("/{student_id}", include_in_schema=False)
def get_student_brief_compat(
    student_id: int,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    payload = get_student_brief(student_id, db, user)
    payload["source"] = "fallback"
    payload["warning"] = "AI brief unavailable; using institutional fallback mentoring summary."
    payload["risk"] = {
        "score": 0,
        "level": "low",
        "alerts": [],
    }
    payload["recommendations"] = [
        "Continue regular mentoring review.",
        "Track overdue actions and new flags promptly.",
    ]
    return payload
