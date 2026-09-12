from datetime import date,datetime

from pydantic import BaseModel, ConfigDict, Field

from .models import (
    ActionStatus,
    MeetingMode,
    UserRole,
    ScheduledMeetingStatus,
)


class UserContext(BaseModel):
    id: int
    role: UserRole
    email: str | None = None


class ActionItemCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str | None = None
    owner_id: int
    due_date: date

class OverdueRefreshResponse(BaseModel):
    updated_count: int
    message: str

class ActionItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = None
    owner_id: int | None = None
    due_date: date | None = None
    status: ActionStatus | None = None


class ActionItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    meeting_id: int
    student_id: int
    owner_id: int
    title: str
    description: str | None
    due_date: datetime | None
    status: ActionStatus
    completed_at: datetime | None


class MeetingCreate(BaseModel):
    student_id: int
    meeting_at: datetime
    mode: MeetingMode
    agenda: str | None = None
    notes: str = Field(min_length=1)
    student_concerns: str | None = None
    mentor_observations: str | None = None
    academic_progress: str | None = Field(default=None, max_length=4000)
    attendance_review: str | None = Field(default=None, max_length=4000)
    personal_circumstances: str | None = Field(default=None, max_length=4000)
    career_direction: str | None = Field(default=None, max_length=4000)
    recording_boundary_acknowledged: bool = False
    next_meeting_at: datetime | None = None
    scheduled_meeting_id: int | None = None
    action_items: list[ActionItemCreate] = Field(default_factory=list)


class MeetingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    mentor_id: int
    meeting_at: datetime
    mode: MeetingMode
    agenda: str | None
    notes: str
    student_concerns: str | None
    mentor_observations: str | None
    academic_progress: str | None
    attendance_review: str | None
    personal_circumstances: str | None
    career_direction: str | None
    recording_boundary_acknowledged: bool
    next_meeting_at: datetime | None
    created_by: int
    created_at: datetime
    action_items: list[ActionItemResponse]


class ActionClosureResponse(BaseModel):
    action_item_id: int
    previous_status: ActionStatus
    new_status: ActionStatus
    completed_at: datetime | None


class ComplianceReport(BaseModel):
    total_students: int
    students_with_meeting: int
    meeting_compliance_percentage: float
    total_action_items: int
    completed_action_items: int
    overdue_action_items: int
    action_closure_percentage: float
    active_flags: int
    open_escalations: int


class MentorLoad(BaseModel):
    mentor_id: int
    mentor_name: str
    active_students: int
    meetings_last_30_days: int
    open_actions: int
    overdue_actions: int

class AllocationCreate(BaseModel):
    student_id: int
    mentor_id: int
    reason: str = Field(min_length=3, max_length=500)


class AllocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    mentor_id: int
    allocated_at: datetime
    is_active: bool
    allocation_reason: str
    reallocated_from_mentor_id: int | None
    ended_at: datetime | None


class ScheduledMeetingCreate(BaseModel):
    student_id: int
    scheduled_for: datetime
    mode: MeetingMode
    agenda: str | None = Field(default=None, max_length=2000)


class ScheduledMeetingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    mentor_id: int
    scheduled_for: datetime
    mode: MeetingMode
    agenda: str | None
    status: ScheduledMeetingStatus
    completed_meeting_id: int | None
    created_by: int
    created_at: datetime
