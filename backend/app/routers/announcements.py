from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..audit import record_audit_event
from ..database import get_db
from ..models import Allocation, Announcement, AnnouncementScope, Mentor, Student, User, UserRole
from ..rbac import get_current_user
from ..schemas import UserContext

router = APIRouter(prefix="/announcements", tags=["Announcements"])


class AnnouncementCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    body: str = Field(min_length=3, max_length=4000)
    scope: AnnouncementScope | None = None


class AnnouncementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    author_id: int
    author_name: str
    author_role: str
    scope: AnnouncementScope
    title: str
    body: str
    created_at: datetime


def _serialize(rows) -> list[AnnouncementResponse]:
    return [
        AnnouncementResponse(
            id=a.id,
            author_id=a.author_id,
            author_name=name,
            author_role=role.value if hasattr(role, "value") else str(role),
            scope=a.scope,
            title=a.title,
            body=a.body,
            created_at=a.created_at,
        )
        for a, name, role in rows
    ]


@router.post("", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
def create_announcement(
    payload: AnnouncementCreate,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    if user.role == UserRole.MENTOR:
        scope = AnnouncementScope.MY_MENTEES
    elif user.role in {UserRole.HOD, UserRole.ADMIN}:
        scope = payload.scope or AnnouncementScope.ALL
        if scope == AnnouncementScope.MY_MENTEES:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Only mentors post to 'my mentees'")
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only mentors, HOD or administrators can post announcements")

    announcement = Announcement(author_id=user.id, scope=scope, title=payload.title.strip(), body=payload.body.strip())
    db.add(announcement)
    db.flush()

    record_audit_event(
        db,
        actor_id=user.id,
        action="ANNOUNCEMENT_POSTED",
        resource_type="announcement",
        resource_id=announcement.id,
        details=f"scope={scope.value}",
    )

    db.commit()
    db.refresh(announcement)

    author = db.scalar(select(User).where(User.id == user.id))
    return AnnouncementResponse(
        id=announcement.id,
        author_id=announcement.author_id,
        author_name=author.full_name if author else "Unknown",
        author_role=author.role.value if author else "unknown",
        scope=announcement.scope,
        title=announcement.title,
        body=announcement.body,
        created_at=announcement.created_at,
    )


@router.get("/mine", response_model=list[AnnouncementResponse])
def list_my_announcements(
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    if user.role in {UserRole.ADMIN, UserRole.HOD}:
        query = select(Announcement, User.full_name, User.role).join(User, User.id == Announcement.author_id)
    elif user.role == UserRole.MENTOR:
        query = (
            select(Announcement, User.full_name, User.role)
            .join(User, User.id == Announcement.author_id)
            .where(
                Announcement.scope.in_([AnnouncementScope.ALL, AnnouncementScope.MENTORS])
                | ((Announcement.scope == AnnouncementScope.MY_MENTEES) & (Announcement.author_id == user.id))
            )
        )
    elif user.role == UserRole.STUDENT:
        mentor_user_id = None
        student = db.scalar(select(Student).where(Student.user_id == user.id, Student.is_active.is_(True)))
        if student:
            allocation = db.scalar(
                select(Allocation).where(Allocation.student_id == student.id, Allocation.is_active.is_(True))
            )
            if allocation:
                mentor = db.scalar(select(Mentor).where(Mentor.id == allocation.mentor_id))
                mentor_user_id = mentor.user_id if mentor else None

        visible_scopes = Announcement.scope.in_([AnnouncementScope.ALL, AnnouncementScope.STUDENTS])
        if mentor_user_id is not None:
            visible_scopes = visible_scopes | (
                (Announcement.scope == AnnouncementScope.MY_MENTEES) & (Announcement.author_id == mentor_user_id)
            )

        query = (
            select(Announcement, User.full_name, User.role)
            .join(User, User.id == Announcement.author_id)
            .where(visible_scopes)
        )
    else:
        query = (
            select(Announcement, User.full_name, User.role)
            .join(User, User.id == Announcement.author_id)
            .where(Announcement.scope == AnnouncementScope.ALL)
        )

    query = query.order_by(Announcement.created_at.desc()).limit(100)
    return _serialize(db.execute(query).all())
