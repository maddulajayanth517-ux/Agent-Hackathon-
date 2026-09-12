from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Allocation, AuditEvent, MeetingRecord, Mentor, Student, UserRole
from ..rbac import get_current_user
from ..schemas import AllocationCreate, AllocationResponse, UserContext

router = APIRouter(
    prefix="/allocations",
    tags=["Mentor Allocations"],
)


@router.post(
    "",
    response_model=AllocationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_allocation(
    payload: AllocationCreate,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    if user.role not in {
        UserRole.ADMIN,
        UserRole.HOD,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators or HOD users can create allocations",
        )

    student = db.scalar(
        select(Student).where(
            Student.id == payload.student_id,
            Student.is_active.is_(True),
        )
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active student not found",
        )

    mentor = db.scalar(
        select(Mentor).where(
            Mentor.id == payload.mentor_id,
            Mentor.is_active.is_(True),
        )
    )

    if mentor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active mentor not found",
        )

    existing = db.scalar(
        select(Allocation).where(
            Allocation.student_id == payload.student_id,
            Allocation.mentor_id == payload.mentor_id,
        )
    )

    if existing is not None:
        if existing.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Student is already allocated to this mentor",
            )

        existing.is_active = True
        existing.allocation_reason = payload.reason.strip()
        existing.ended_at = None
        db.commit()
        db.refresh(existing)
        return existing

    current_load = len(
        db.scalars(
            select(Allocation.id).where(
                Allocation.mentor_id == mentor.id,
                Allocation.is_active.is_(True),
            )
        ).all()
    )


    if mentor.max_students and current_load >= mentor.max_students:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Mentor has reached maximum student capacity",
        )

    prior_allocation = db.scalar(
        select(Allocation).where(
            Allocation.student_id == student.id,
            Allocation.is_active.is_(True),
        )
    )
    if prior_allocation is not None:
        prior_allocation.is_active = False
        from ..models import utc_now
        prior_allocation.ended_at = utc_now()

    allocation = Allocation(
        student_id=student.id,
        mentor_id=mentor.id,
        is_active=True,
        allocation_reason=payload.reason.strip(),
        reallocated_from_mentor_id=prior_allocation.mentor_id if prior_allocation else None,
    )

    db.add(allocation)
    db.add(AuditEvent(
        actor_id=user.id,
        action="MENTOR_REALLOCATED" if prior_allocation else "MENTOR_ALLOCATED",
        resource_type="allocation",
        resource_id=None,
        details=f"student_id={student.id}; mentor_id={mentor.id}; reason={payload.reason.strip()}",
    ))
    db.commit()
    db.refresh(allocation)

    return allocation


@router.get(
    "/recommend/{student_id}",
)
def recommend_allocation(student_id: int, db: Session = Depends(get_db), user: UserContext = Depends(get_current_user)):
    if user.role not in {UserRole.ADMIN, UserRole.HOD, UserRole.MENTOR}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to view allocation recommendations")

    mentors = db.scalars(
        select(Mentor).where(Mentor.is_active.is_(True)).order_by(Mentor.id)
    ).all()

    if not mentors:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active mentors available")

    student = db.scalar(select(Student).where(Student.id == student_id))
    prior_mentor_ids = {
        mentor_id
        for mentor_id in db.scalars(
            select(MeetingRecord.mentor_id).where(MeetingRecord.student_id == student_id)
        ).all()
    }

    scored_mentors = []
    for mentor in mentors:
        current_workload = len(db.scalars(
            select(Allocation.id).where(
                Allocation.mentor_id == mentor.id,
                Allocation.is_active.is_(True),
            )
        ).all())
        capacity = mentor.max_students or 999
        continuity_bonus = 2 if mentor.id in prior_mentor_ids else 0
        department_bonus = 1 if student and student.department == mentor.department else 0
        capacity_penalty = 100 if current_workload >= capacity else 0
        score = continuity_bonus + department_bonus - (current_workload / max(capacity, 1)) - capacity_penalty
        scored_mentors.append((score, mentor, current_workload, capacity, continuity_bonus, department_bonus))

    _, best_mentor, current_workload, capacity, continuity_bonus, department_bonus = max(
        scored_mentors,
        key=lambda item: item[0],
    )
    reasons = [f"workload {current_workload}/{capacity}"]
    if continuity_bonus:
        reasons.append("continuity with a previous mentor")
    if department_bonus:
        reasons.append("same department")
    best_reason = "Selected using " + ", ".join(reasons) + "."

    return {
        "student_id": student_id,
        "mentor_id": best_mentor.id,
        "mentor_name": best_mentor.user.full_name if best_mentor.user else "Mentor",
        "reason": best_reason,
        "current_workload": current_workload,
        "capacity": best_mentor.max_students or 999,
    }


@router.get(
    "",
    response_model=list[AllocationResponse],
)
def list_allocations(
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    if user.role not in {
        UserRole.ADMIN,
        UserRole.HOD,
        UserRole.COUNSELLOR,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view allocations",
        )

    return db.scalars(
        select(Allocation)
        .where(Allocation.is_active.is_(True))
        .order_by(Allocation.id)
    ).all()


@router.get(
    "/student/{student_id}",
    response_model=list[AllocationResponse],
)
def get_student_allocations(
    student_id: int,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    if user.role == UserRole.ADMIN:
        allowed = True

    elif user.role in {
        UserRole.HOD,
        UserRole.COUNSELLOR,
    }:
        allowed = True

    elif user.role == UserRole.STUDENT:
        student = db.scalar(
            select(Student).where(
                Student.id == student_id,
                Student.is_active.is_(True),
                Student.user_id == user.id,
            )
        )
        allowed = student is not None

    elif user.role == UserRole.MENTOR:
        mentor = db.scalar(
            select(Mentor).where(
                Mentor.user_id == user.id,
                Mentor.is_active.is_(True),
            )
        )

        allowed = (
            mentor is not None
            and db.scalar(
                select(Allocation.id).where(
                    Allocation.mentor_id == mentor.id,
                    Allocation.student_id == student_id,
                    Allocation.is_active.is_(True),
                )
            )
            is not None
        )

    else:
        allowed = False

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "student_access_denied",
                "student_id": student_id,
            },
        )

    return db.scalars(
        select(Allocation)
        .where(
            Allocation.student_id == student_id,
            Allocation.is_active.is_(True),
        )
        .order_by(Allocation.id)
    ).all()


@router.delete(
    "/{allocation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def deactivate_allocation(
    allocation_id: int,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    if user.role not in {
        UserRole.ADMIN,
        UserRole.HOD,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators or HOD users can deactivate allocations",
        )

    allocation = db.scalar(
        select(Allocation).where(
            Allocation.id == allocation_id,
            Allocation.is_active.is_(True),
        )
    )

    if allocation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active allocation not found",
        )

    allocation.is_active = False
    from ..models import utc_now
    allocation.ended_at = utc_now()
    db.commit()

    return None
