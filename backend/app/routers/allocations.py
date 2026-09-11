from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Allocation, Mentor, Student, UserRole
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

    allocation = Allocation(
        student_id=student.id,
        mentor_id=mentor.id,
        is_active=True,
    )

    db.add(allocation)
    db.commit()
    db.refresh(allocation)

    return allocation


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
    db.commit()

    return None