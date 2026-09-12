from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Alert, Allocation, Flag, FlagSeverity, Mentor, User, UserRole
from ..notifications import send_email_alert
from ..rbac import can_access_student, get_current_user
from ..schemas import UserContext

router = APIRouter(prefix="/flags", tags=["Student Flags"])


class FlagCreate(BaseModel):
    student_id: int
    severity: FlagSeverity
    category: str = Field(min_length=2, max_length=100)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str = Field(min_length=3, max_length=2000)

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        normalized = value.strip().upper()
        allowed = {"ACADEMIC", "ATTENDANCE", "PERSONAL", "EMOTIONAL", "FINANCIAL", "CAREER", "CONDUCT", "OTHER"}
        if normalized not in allowed:
            raise ValueError("Category must be one of: " + ", ".join(sorted(allowed)))
        return normalized


class FlagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    created_by: int
    severity: FlagSeverity
    category: str
    description: str
    is_active: bool
    created_at: datetime


MANAGE_ROLES = {
    UserRole.ADMIN,
    UserRole.MENTOR,
    UserRole.HOD,
    UserRole.COUNSELLOR,
}


@router.post(
    "",
    response_model=FlagResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_flag(
    payload: FlagCreate,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    if user.role not in MANAGE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students cannot create flags",
        )

    if not can_access_student(
        db=db,
        user=user,
        student_id=payload.student_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "student_access_denied",
                "student_id": payload.student_id,
            },
        )

    flag = Flag(
        student_id=payload.student_id,
        created_by=user.id,
        severity=payload.severity,
        category=payload.category.strip(),
        description=(payload.title + ": " if payload.title else "") + payload.description.strip(),
        is_active=True,
    )

    db.add(flag)
    db.commit()
    db.refresh(flag)

    allocation = db.scalar(select(Allocation).where(
        Allocation.student_id == flag.student_id,
        Allocation.is_active.is_(True),
    ))
    recipient_id = user.id
    if allocation:
        recipient_id = db.scalar(
            select(Mentor.user_id).where(Mentor.id == allocation.mentor_id)
        ) or user.id
    title = "Urgent student risk flag" if flag.severity in {FlagSeverity.HIGH, FlagSeverity.CRITICAL} else "New student mentoring flag"
    alert = Alert(
        student_id=flag.student_id,
        recipient_id=recipient_id,
        flag_id=flag.id,
        severity=flag.severity.value.upper(),
        title=title,
        body=flag.description,
        channel="IN_APP",
    )
    db.add(alert)
    db.commit()
    recipient_email = db.scalar(select(User.email).where(User.id == recipient_id))
    send_email_alert(recipient=recipient_email, subject=alert.title, body=f"Student {flag.student_id}\n\n{alert.body}")

    return flag


@router.get(
    "/student/{student_id}",
    response_model=list[FlagResponse],
)
def get_student_flags(
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

    return db.scalars(
        select(Flag)
        .where(
            Flag.student_id == student_id,
            Flag.is_active.is_(True),
        )
        .order_by(Flag.created_at.desc())
    ).all()


@router.patch(
    "/{flag_id}/resolve",
    response_model=FlagResponse,
)
def resolve_flag(
    flag_id: int,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    if user.role not in MANAGE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to resolve flags",
        )

    flag = db.scalar(
        select(Flag).where(Flag.id == flag_id)
    )

    if flag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flag not found",
        )

    if not can_access_student(
        db=db,
        user=user,
        student_id=flag.student_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access denied",
        )

    flag.is_active = False

    db.commit()
    db.refresh(flag)

    return flag
