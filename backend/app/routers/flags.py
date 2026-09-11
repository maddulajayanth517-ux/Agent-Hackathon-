from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status

from backend.app.database import Flag, get_db
from backend.app.models import FlagCategory, FlagCreate, FlagOut, FlagStatus, Severity

router = APIRouter(prefix="/flags", tags=["flags"])


@router.get("/")
async def list_flags() -> List[Dict[str, Any]]:
    db = get_db()
    result: List[Dict[str, Any]] = []
    for flag in sorted(db.flags.values(), key=lambda item: item.id):
        student = db.students.get(flag.student_id)
        result.append({
            "id": flag.id,
            "student_id": flag.student_id,
            "student_name": student.name if student else None,
            "category": flag.category,
            "severity": flag.severity,
            "status": flag.status,
            "title": flag.title,
            "description": flag.description,
        })
    return result


@router.post("/")
async def create_flag(payload: FlagCreate) -> FlagOut:
    db = get_db()
    if not db.students.get(payload.student_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    if payload.category.value not in {item.value for item in FlagCategory}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid category")
    if payload.severity.value not in {item.value for item in Severity}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid severity")
    if payload.status.value not in {item.value for item in FlagStatus}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid status")
    if not payload.title or not payload.description:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title and description are required")

    flag_id = db.next_id()
    db.flags[flag_id] = Flag(
        id=flag_id,
        student_id=payload.student_id,
        category=payload.category.value,
        severity=payload.severity.value,
        status=payload.status.value,
        title=payload.title,
        description=payload.description,
    )
    return FlagOut(
        id=flag_id,
        student_id=payload.student_id,
        category=payload.category,
        severity=payload.severity,
        status=payload.status,
        title=payload.title,
        description=payload.description,
    )


@router.put("/{flag_id}")
async def update_flag(flag_id: int, payload: dict[str, Any]) -> Dict[str, Any]:
    db = get_db()
    flag = db.flags.get(flag_id)
    if not flag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flag not found")
    if "status" in payload and payload["status"] not in {item.value for item in FlagStatus}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid status")
    if "category" in payload and payload["category"] not in {item.value for item in FlagCategory}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid category")
    if "severity" in payload and payload["severity"] not in {item.value for item in Severity}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid severity")
    for key, value in payload.items():
        if hasattr(flag, key):
            setattr(flag, key, value)
    return {
        "id": flag.id,
        "student_id": flag.student_id,
        "category": flag.category,
        "severity": flag.severity,
        "status": flag.status,
        "title": flag.title,
        "description": flag.description,
    }
