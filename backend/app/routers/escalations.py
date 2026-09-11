from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status

from backend.app.database import Escalation, get_db
from backend.app.models import EscalationDecision

router = APIRouter(prefix="/escalations", tags=["escalations"])


def determine_escalation(flag: Any) -> EscalationDecision:
    category = str(flag.category).upper()
    severity = str(flag.severity).upper()

    if category == "ACADEMIC":
        destination = "HOD"
        priority = "HIGH" if severity in {"HIGH", "CRITICAL"} else "MEDIUM"
        reason = "High-severity academic concerns require departmental intervention." if severity in {"HIGH", "CRITICAL"} else "Academic concerns are routed to the HOD for review and support."
    elif category == "PERSONAL":
        destination = "Counselling / Agent 66"
        priority = "HIGH" if severity in {"HIGH", "CRITICAL"} else "MEDIUM"
        reason = "Personal concerns are routed to counselling and a support agent for appropriate follow-up."
    elif category == "FINANCIAL":
        destination = "Finance / Scholarship"
        priority = "HIGH" if severity in {"HIGH", "CRITICAL"} else "MEDIUM"
        reason = "Financial hardship requires finance or scholarship support to resolve the risk."
    elif category == "CAREER":
        destination = "Career Guidance"
        priority = "HIGH" if severity in {"HIGH", "CRITICAL"} else "MEDIUM"
        reason = "Career concerns should be reviewed by the career guidance team."
    elif category == "ATTENDANCE":
        destination = "Mentor / HOD"
        priority = "HIGH" if severity in {"HIGH", "CRITICAL"} else "MEDIUM"
        reason = "Attendance issues are handled by the mentor first and escalated to HOD when risk increases."
    else:
        destination = "Mentor"
        priority = "MEDIUM"
        reason = "General concerns are managed by the mentor with monitoring."

    if severity == "LOW":
        destination = "Mentor"
        priority = "LOW"
        reason = "Low-severity issues are handled by the mentor and monitored."
    elif severity == "CRITICAL":
        destination = "Immediate institutional escalation"
        priority = "CRITICAL"
        reason = "Critical severity requires immediate escalation according to the institutional workflow."

    return EscalationDecision(destination=destination, priority=priority, reason=reason, route=destination)


@router.get("/{flag_id}")
async def get_escalation(flag_id: int) -> Dict[str, Any]:
    db = get_db()
    flag = db.flags.get(flag_id)
    if not flag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flag not found")

    decision = determine_escalation(flag)
    db.escalations[flag_id] = Escalation(
        id=flag_id,
        flag_id=flag_id,
        destination=decision.destination,
        priority=decision.priority,
        reason=decision.reason,
        status="PENDING",
    )

    return {
        "flag_id": flag_id,
        "category": flag.category,
        "severity": flag.severity,
        "destination": decision.destination,
        "priority": decision.priority,
        "reason": decision.reason,
    }
