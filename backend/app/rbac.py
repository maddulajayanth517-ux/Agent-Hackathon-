from enum import Enum
from typing import Callable

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .models import (
    Allocation,
    Mentor,
    Student,
    User,
    UserRole,
)
from .schemas import UserContext


class Permission(str, Enum):
    VIEW_OWN_MEETINGS = "view_own_meetings"
    CREATE_MEETING = "create_meeting"
    UPDATE_ACTION = "update_action"
    VIEW_REPORTS = "view_reports"
    VIEW_FLAGS = "view_flags"
    VIEW_ESCALATIONS = "view_escalations"


ROLE_PERMISSIONS: dict[UserRole, frozenset[Permission]] = {
    UserRole.ADMIN: frozenset(Permission),

    UserRole.HOD: frozenset({
        Permission.VIEW_REPORTS,
        Permission.VIEW_FLAGS,
        Permission.VIEW_ESCALATIONS,
    }),

    UserRole.MENTOR: frozenset({
        Permission.VIEW_OWN_MEETINGS,
        Permission.CREATE_MEETING,
        Permission.UPDATE_ACTION,
    }),

    UserRole.STUDENT: frozenset({
        Permission.VIEW_OWN_MEETINGS,
    }),

    UserRole.COUNSELLOR: frozenset({
        Permission.VIEW_REPORTS,
        Permission.VIEW_FLAGS,
        Permission.VIEW_ESCALATIONS,
    }),
}


def get_current_user(
    x_user_id: int | None = Header(default=None),
    db: Session = Depends(get_db),
) -> UserContext:

    if x_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user context is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.scalar(
        select(User).where(
            User.id == x_user_id,
            User.is_active.is_(True),
        )
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserContext(
        id=user.id,
        role=user.role,
        email=user.email,
    )


def require_permission(permission: Permission) -> Callable:

    def dependency(
        user: UserContext = Depends(get_current_user),
    ) -> UserContext:

        permissions = ROLE_PERMISSIONS.get(user.role, frozenset())

        if permission not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "permission_denied",
                    "required_permission": permission.value,
                    "user_role": user.role.value,
                },
            )

        return user

    return dependency


def require_roles(*roles: UserRole) -> Callable:

    def dependency(
        user: UserContext = Depends(get_current_user),
    ) -> UserContext:

        if user.role not in roles:
            allowed_roles = [role.value for role in roles]

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "role_not_allowed",
                    "allowed_roles": allowed_roles,
                    "user_role": user.role.value,
                },
            )

        return user

    return dependency


def get_mentor_by_user_id(
    db: Session,
    user_id: int,
) -> Mentor | None:

    return db.scalar(
        select(Mentor).where(
            Mentor.user_id == user_id,
            Mentor.is_active.is_(True),
        )
    )


def get_student_by_id(
    db: Session,
    student_id: int,
) -> Student | None:

    return db.scalar(
        select(Student).where(
            Student.id == student_id,
            Student.is_active.is_(True),
        )
    )


def mentor_can_access_student(
    db: Session,
    mentor_user_id: int,
    student_id: int,
) -> bool:

    mentor = get_mentor_by_user_id(
        db,
        mentor_user_id,
    )

    if mentor is None:
        return False

    student = get_student_by_id(
        db,
        student_id,
    )

    if student is None:
        return False

    allocation = db.scalar(
        select(Allocation).where(
            Allocation.mentor_id == mentor.id,
            Allocation.student_id == student.id,
            Allocation.is_active.is_(True),
        )
    )

    return allocation is not None


def student_can_access_self(
    db: Session,
    student_user_id: int,
    student_id: int,
) -> bool:

    student = get_student_by_id(
        db,
        student_id,
    )

    if student is None:
        return False

    return student.user_id == student_user_id


def can_access_student(
    db: Session,
    user: UserContext,
    student_id: int,
) -> bool:

    if user.role == UserRole.ADMIN:
        return True

    if user.role == UserRole.HOD:
        return get_student_by_id(db, student_id) is not None

    if user.role == UserRole.COUNSELLOR:
        return get_student_by_id(db, student_id) is not None

    if user.role == UserRole.MENTOR:
        return mentor_can_access_student(
            db=db,
            mentor_user_id=user.id,
            student_id=student_id,
        )

    if user.role == UserRole.STUDENT:
        return student_can_access_self(
            db=db,
            student_user_id=user.id,
            student_id=student_id,
        )

    return False


def require_student_access(
    student_id: int,
    db: Session,
    user: UserContext,
) -> None:

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


def require_mentor_access_to_student(
    db: Session,
    user: UserContext,
    student_id: int,
) -> Mentor:

    if user.role == UserRole.ADMIN:
        mentor = get_mentor_by_user_id(db, user.id)

        if mentor is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin is not associated with a mentor profile",
            )

        return mentor

    if user.role != UserRole.MENTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only mentors can perform this operation",
        )

    mentor = get_mentor_by_user_id(
        db,
        user.id,
    )

    if mentor is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active mentor profile not found",
        )

    if not mentor_can_access_student(
        db=db,
        mentor_user_id=user.id,
        student_id=student_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "student_not_allocated",
                "student_id": student_id,
            },
        )

    return mentor