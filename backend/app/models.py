from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserRole(str, Enum):
    ADMIN = "admin"
    HOD = "hod"
    MENTOR = "mentor"
    STUDENT = "student"
    COUNSELLOR = "counsellor"


class MeetingMode(str, Enum):
    IN_PERSON = "in_person"
    ONLINE = "online"
    PHONE = "phone"


class ScheduledMeetingStatus(str, Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    MISSED = "missed"


class MentoringPolicy(Base):
    """Singleton institutional policy; row id=1 is the active policy."""
    __tablename__ = "mentoring_policy"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    required_frequency_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    reminder_days_before: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class ActionStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class FlagSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EscalationStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ServiceQueue(Base):
    __tablename__ = "service_queues"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    recipient_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    recipient_email: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, native_enum=False),
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    student_profile: Mapped["Student | None"] = relationship(
        back_populates="user",
        uselist=False,
    )
    mentor_profile: Mapped["Mentor | None"] = relationship(
        back_populates="user",
        uselist=False,
    )


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    register_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    section: Mapped[str | None] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped["User"] = relationship(back_populates="student_profile")

    meetings: Mapped[list["MeetingRecord"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
    )

    actions: Mapped[list["ActionItem"]] = relationship(
        back_populates="student",
    )


class Mentor(Base):
    __tablename__ = "mentors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    specialization: Mapped[str | None] = mapped_column(String(255))
    max_students: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped["User"] = relationship(back_populates="mentor_profile")

    meetings: Mapped[list["MeetingRecord"]] = relationship(
        back_populates="mentor",
    )


class Allocation(Base):
    __tablename__ = "allocations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    )
    mentor_id: Mapped[int] = mapped_column(
        ForeignKey("mentors.id", ondelete="CASCADE"),
        nullable=False,
    )
    allocated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allocation_reason: Mapped[str] = mapped_column(String(500), default="INITIAL", nullable=False)
    reallocated_from_mentor_id: Mapped[int | None] = mapped_column(
        ForeignKey("mentors.id", ondelete="SET NULL")
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "mentor_id",
            name="uq_student_mentor_allocation",
        ),
        Index(
            "ix_allocation_active_mentor",
            "mentor_id",
            "is_active",
        ),
    )


class MeetingRecord(Base):
    __tablename__ = "meeting_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    mentor_id: Mapped[int] = mapped_column(
        ForeignKey("mentors.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    meeting_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    mode: Mapped[MeetingMode] = mapped_column(
        SAEnum(MeetingMode, native_enum=False),
        nullable=False,
    )

    agenda: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    student_concerns: Mapped[str | None] = mapped_column(Text)
    mentor_observations: Mapped[str | None] = mapped_column(Text)
    academic_progress: Mapped[str | None] = mapped_column(Text)
    attendance_review: Mapped[str | None] = mapped_column(Text)
    personal_circumstances: Mapped[str | None] = mapped_column(Text)
    career_direction: Mapped[str | None] = mapped_column(Text)
    recording_boundary_acknowledged: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )


    next_meeting_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    student: Mapped["Student"] = relationship(
        back_populates="meetings",
    )

    mentor: Mapped["Mentor"] = relationship(
        back_populates="meetings",
    )

    action_items: Mapped[list["ActionItem"]] = relationship(
        back_populates="meeting",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index(
            "ix_meeting_student_date",
            "student_id",
            "meeting_at",
        ),
        Index(
            "ix_meeting_mentor_date",
            "mentor_id",
            "meeting_at",
        ),
    )


class ActionItem(Base):
    __tablename__ = "action_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    meeting_id: Mapped[int] = mapped_column(
        ForeignKey("meeting_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(Text)

    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        index=True,
    )

    status: Mapped[ActionStatus] = mapped_column(
        SAEnum(ActionStatus, native_enum=False),
        default=ActionStatus.OPEN,
        nullable=False,
        index=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    meeting: Mapped["MeetingRecord"] = relationship(
        back_populates="action_items",
    )

    student: Mapped["Student"] = relationship(
        back_populates="actions",
    )


class Flag(Base):
    __tablename__ = "flags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    severity: Mapped[FlagSeverity] = mapped_column(
        SAEnum(FlagSeverity, native_enum=False),
        nullable=False,
        index=True,
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )


class Escalation(Base):
    __tablename__ = "escalations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    raised_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    assigned_to: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
    )

    severity: Mapped[FlagSeverity] = mapped_column(
        SAEnum(FlagSeverity, native_enum=False),
        nullable=False,
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[EscalationStatus] = mapped_column(
        SAEnum(EscalationStatus, native_enum=False),
        default=EscalationStatus.OPEN,
        nullable=False,
        index=True,
    )

    resolution_notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    resource_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    resource_id: Mapped[int | None] = mapped_column(Integer)

    details: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    flag_id: Mapped[int | None] = mapped_column(
        ForeignKey("flags.id", ondelete="SET NULL"),
        index=True,
    )
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(String(20), default="IN_APP", nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actioned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )
    destination: Mapped[str] = mapped_column(String(150), default="Mentor", nullable=False)
    queue_id: Mapped[int | None] = mapped_column(ForeignKey("service_queues.id", ondelete="SET NULL"))


class ScheduledMeeting(Base):
    __tablename__ = "scheduled_meetings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    mentor_id: Mapped[int] = mapped_column(ForeignKey("mentors.id", ondelete="RESTRICT"), nullable=False, index=True)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    mode: Mapped[MeetingMode] = mapped_column(SAEnum(MeetingMode, native_enum=False), nullable=False)
    agenda: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ScheduledMeetingStatus] = mapped_column(SAEnum(ScheduledMeetingStatus, native_enum=False), default=ScheduledMeetingStatus.SCHEDULED, nullable=False, index=True)
    completed_meeting_id: Mapped[int | None] = mapped_column(ForeignKey("meeting_records.id", ondelete="SET NULL"))
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
