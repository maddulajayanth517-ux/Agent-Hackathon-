from __future__ import annotations

import json
import os
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status

from backend.app.database import get_db
from backend.app.models import BriefSummary

router = APIRouter(prefix="/brief", tags=["brief"])


def _build_fallback_brief(student_id: int) -> BriefSummary:
    db = get_db()
    student = db.students.get(student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    latest_meeting = next(
        (m for m in sorted(db.meetings.values(), key=lambda item: item.created_at, reverse=True) if m.student_id == student_id),
        None,
    )
    flags = [flag for flag in db.flags.values() if flag.student_id == student_id]
    actions = [item for item in db.action_items.values() if item.student_id == student_id]

    return BriefSummary(
        summary=f"Student {student.name} has {len(flags)} active flag(s) and {len(actions)} action item(s).",
        key_changes=[f"Latest meeting: {latest_meeting.summary}"] if latest_meeting else ["No recent meeting notes available."],
        open_concerns=[flag.title for flag in flags if flag.status in {"OPEN", "IN_PROGRESS"}] or ["No open concerns recorded."],
        pending_actions=[item.title for item in actions if item.status in {"OPEN", "PENDING"}] or ["No pending actions."],
        discussion_points=[
            "Review the latest mentoring notes and unresolved concerns.",
            "Confirm whether any pending actions are overdue.",
            "Assess whether the student needs a support escalation.",
        ],
        recommended_next_steps=[
            "Align the student with the next key priority.",
            "Address overdue or high-risk actions first.",
            "Monitor the student and update the mentor plan.",
        ],
        source="fallback",
        warning="AI brief unavailable — showing fallback briefing.",
    )


async def _generate_ai_brief(student_id: int) -> BriefSummary:
    db = get_db()
    student = db.students.get(student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    latest_meeting = next(
        (m for m in sorted(db.meetings.values(), key=lambda item: item.created_at, reverse=True) if m.student_id == student_id),
        None,
    )
    flags = [flag for flag in db.flags.values() if flag.student_id == student_id]
    actions = [item for item in db.action_items.values() if item.student_id == student_id]

    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("GROQ_API_KEY is not configured")

    context = {
        "student": {"name": student.name, "cohort": student.cohort, "mentor_id": student.mentor_id},
        "latest_meeting": {
            "summary": latest_meeting.summary if latest_meeting else None,
            "notes": latest_meeting.notes if latest_meeting else None,
            "created_at": latest_meeting.created_at if latest_meeting else None,
        },
        "flags": [{"category": flag.category, "severity": flag.severity, "status": flag.status, "title": flag.title} for flag in flags],
        "actions": [{"title": item.title, "status": item.status, "due_date": item.due_date} for item in actions],
    }

    try:
        from groq import Groq

        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Use only the supplied context. Do not invent facts. Prioritize recent changes and unresolved issues. Highlight overdue actions. Clearly separate facts from suggestions. Return valid JSON only with summary, key_changes, open_concerns, pending_actions, discussion_points, recommended_next_steps."},
                {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
            ],
            temperature=0.2,
            max_tokens=500,
        )
        content = completion.choices[0].message.content
        data = json.loads(content)
        validated = BriefSummary(**data)
        return validated
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(str(exc)) from exc


@router.get("/{student_id}")
async def generate_brief(student_id: int) -> BriefSummary:
    try:
        return await _generate_ai_brief(student_id)
    except HTTPException:
        raise
    except Exception:
        return _build_fallback_brief(student_id)
