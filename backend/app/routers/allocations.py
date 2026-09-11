from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status

from backend.app.database import Allocation, get_db
from backend.app.models import AllocationCreate, AllocationRecommendation

router = APIRouter(prefix="/allocations", tags=["allocations"])


def _workload_for_mentor(db: Any, mentor_id: int) -> int:
    return sum(1 for allocation in db.allocations.values() if allocation.active and allocation.mentor_id == mentor_id)


def _recommendation_reason(db: Any, mentor_id: int) -> str:
    mentor = db.mentors.get(mentor_id)
    workload = _workload_for_mentor(db, mentor_id)
    if not mentor:
        return "Mentor not found."
    if workload >= mentor.capacity:
        return "Current mentor is above capacity, so the system recommends a mentor with available capacity and the lowest current workload."
    if workload == 0:
        return "Mentor has available capacity and the lowest current workload."
    return "Mentor has available capacity and the lightest workload, preserving continuity where possible."


@router.get("/")
async def list_allocations() -> List[Dict[str, Any]]:
    db = get_db()
    result: List[Dict[str, Any]] = []
    for allocation in sorted(db.allocations.values(), key=lambda item: item.id):
        student = db.students.get(allocation.student_id)
        mentor = db.mentors.get(allocation.mentor_id)
        result.append({
            "id": allocation.id,
            "student_id": allocation.student_id,
            "student_name": student.name if student else None,
            "mentor_id": allocation.mentor_id,
            "mentor_name": mentor.name if mentor else None,
            "reason": allocation.reason,
            "active": allocation.active,
        })
    return result


@router.get("/workloads")
async def get_workloads() -> List[Dict[str, Any]]:
    db = get_db()
    result: List[Dict[str, Any]] = []
    for mentor in sorted(db.mentors.values(), key=lambda item: item.id):
        workload = _workload_for_mentor(db, mentor.id)
        result.append({
            "mentor_id": mentor.id,
            "mentor_name": mentor.name,
            "capacity": mentor.capacity,
            "current_workload": workload,
            "overloaded": workload >= mentor.capacity,
        })
    return result


@router.get("/recommend/{student_id}")
async def get_allocation_recommendation(student_id: int) -> AllocationRecommendation:
    db = get_db()
    student = db.students.get(student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    candidates = []
    for mentor in db.mentors.values():
        if not mentor.active:
            continue
        workload = _workload_for_mentor(db, mentor.id)
        if workload < mentor.capacity:
            candidates.append({
                "mentor_id": mentor.id,
                "mentor_name": mentor.name,
                "current_workload": workload,
                "capacity": mentor.capacity,
                "reason": _recommendation_reason(db, mentor.id),
            })

    if not candidates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No available mentor can take this student right now.")

    candidates.sort(key=lambda item: (item["current_workload"], item["mentor_id"]))
    best = candidates[0]
    return AllocationRecommendation(
        mentor_id=best["mentor_id"],
        mentor_name=best["mentor_name"],
        reason=best["reason"],
        current_workload=best["current_workload"],
        capacity=best["capacity"],
        available=True,
        priority="MEDIUM",
    )


@router.post("/")
async def create_allocation(payload: AllocationCreate) -> Dict[str, Any]:
    db = get_db()
    student = db.students.get(payload.student_id)
    mentor = db.mentors.get(payload.mentor_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    if not mentor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentor not found")
    if any(a.student_id == payload.student_id and a.active for a in db.allocations.values()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student already has an active allocation")
    if _workload_for_mentor(db, mentor.id) >= mentor.capacity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mentor is at or above capacity and cannot accept a new student")

    allocation_id = db.next_id()
    db.allocations[allocation_id] = Allocation(
        id=allocation_id,
        student_id=payload.student_id,
        mentor_id=payload.mentor_id,
        reason=payload.reason,
        active=payload.active,
    )
    student.mentor_id = payload.mentor_id
    return {"id": allocation_id, "student_id": payload.student_id, "mentor_id": payload.mentor_id, "reason": payload.reason, "active": payload.active}


@router.put("/{allocation_id}")
async def update_allocation(allocation_id: int, payload: AllocationCreate) -> Dict[str, Any]:
    db = get_db()
    allocation = db.allocations.get(allocation_id)
    if not allocation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allocation not found")
    if not db.students.get(payload.student_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    if not db.mentors.get(payload.mentor_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentor not found")

    new_mentor = db.mentors[payload.mentor_id]
    if payload.mentor_id != allocation.mentor_id and _workload_for_mentor(db, new_mentor.id) >= new_mentor.capacity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reallocation target mentor would exceed capacity")

    allocation.student_id = payload.student_id
    allocation.mentor_id = payload.mentor_id
    allocation.reason = payload.reason or "REALLOCATION"
    allocation.active = payload.active
    student = db.students.get(payload.student_id)
    if student:
        student.mentor_id = payload.mentor_id
    return {"id": allocation_id, "student_id": payload.student_id, "mentor_id": payload.mentor_id, "reason": allocation.reason, "active": allocation.active}


@router.delete("/{allocation_id}")
async def delete_allocation(allocation_id: int) -> Dict[str, str]:
    db = get_db()
    allocation = db.allocations.get(allocation_id)
    if not allocation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allocation not found")
    allocation.active = False
    student = db.students.get(allocation.student_id)
    if student:
        student.mentor_id = None
    return {"status": "deleted"}
