from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..models import (
    ActionItem,
    ActionStatus,
    AuditEvent,
    MeetingRecord,
    User,
    UserRole,
)
from ..rbac import (
    Permission,
    can_access_student,
    get_current_user,
    get_mentor_by_user_id,
    mentor_can_access_student,
)
from ..schemas import (
    ActionClosureResponse,
    ActionItemCreate,
    ActionItemResponse,
    ActionItemUpdate,
    MeetingCreate,
    MeetingResponse,
    OverdueRefreshResponse,
    UserContext,
)

router = APIRouter(
    prefix="/meetings",
    tags=["Meetings & Action Items"],
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_audit_event(
    db: Session,
    actor_id: int,
    action: str,
    resource_type: str,
    resource_id: int | None,
    details: str,
) -> None:
    db.add(
        AuditEvent(
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
        )
    )


def serialize_action(action: ActionItem) -> ActionItemResponse:
    return ActionItemResponse.model_validate(action)


def serialize_meeting(meeting: MeetingRecord) -> MeetingResponse:
    return MeetingResponse.model_validate(meeting)


@router.post(
    "",
    response_model=MeetingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_meeting(
    payload: MeetingCreate,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    if user.role not in {
        UserRole.ADMIN,
        UserRole.MENTOR,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only mentors or administrators can create meeting records",
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

    mentor = get_mentor_by_user_id(
        db,
        user.id,
    )

    if mentor is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authenticated user does not have an active mentor profile",
        )

    meeting = MeetingRecord(
        student_id=payload.student_id,
        mentor_id=mentor.id,
        meeting_at=payload.meeting_at,
        mode=payload.mode,
        agenda=payload.agenda,
        notes=payload.notes,
        student_concerns=payload.student_concerns,
        mentor_observations=payload.mentor_observations,
        next_meeting_at=payload.next_meeting_at,
        created_by=user.id,
    )

    db.add(meeting)
    db.flush()

    for action_payload in payload.action_items:
        if action_payload.due_date < date.today():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "invalid_due_date",
                    "title": action_payload.title,
                    "message": "Action-item due date cannot be in the past",
                },
            )

        action = ActionItem(
            meeting_id=meeting.id,
            student_id=payload.student_id,
            owner_id=action_payload.owner_id,
            title=action_payload.title,
            description=action_payload.description,
            due_date=action_payload.due_date,
            status=ActionStatus.OPEN,
        )

        db.add(action)

    create_audit_event(
        db=db,
        actor_id=user.id,
        action="MEETING_CREATED",
        resource_type="meeting",
        resource_id=meeting.id,
        details=f"Meeting created for student_id={payload.student_id}",
    )

    db.commit()

    result = db.scalar(
        select(MeetingRecord)
        .options(
            selectinload(MeetingRecord.action_items),
        )
        .where(MeetingRecord.id == meeting.id)
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Meeting was created but could not be reloaded",
        )

    return serialize_meeting(result)


@router.get(
    "/student/{student_id}",
    response_model=list[MeetingResponse],
)
def get_student_meetings(
    student_id: int,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
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

    meetings = db.scalars(
        select(MeetingRecord)
        .options(
            selectinload(MeetingRecord.action_items),
        )
        .where(MeetingRecord.student_id == student_id)
        .order_by(MeetingRecord.meeting_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    return [
        serialize_meeting(meeting)
        for meeting in meetings
    ]


@router.patch(
    "/actions/{action_id}",
    response_model=ActionItemResponse,
)
def update_action_item(
    action_id: int,
    payload: ActionItemUpdate,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    action = db.scalar(
        select(ActionItem)
        .where(ActionItem.id == action_id)
    )

    if action is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action item not found",
        )

    if not can_access_student(
        db=db,
        user=user,
        student_id=action.student_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to modify this action item",
        )

    if (
        user.role == UserRole.STUDENT
        and action.owner_id != user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students can modify only action items assigned to themselves",
        )

    if payload.due_date is not None:
        if payload.due_date < date.today():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Due date cannot be in the past",
            )

        action.due_date = payload.due_date

    if payload.title is not None:
        action.title = payload.title

    if payload.description is not None:
        action.description = payload.description

    if payload.status is not None:
        action.status = payload.status

        if payload.status == ActionStatus.COMPLETED:
            action.completed_at = utc_now()
        elif payload.status != ActionStatus.COMPLETED:
            action.completed_at = None

    action.updated_at = utc_now()

    create_audit_event(
        db=db,
        actor_id=user.id,
        action="ACTION_ITEM_UPDATED",
        resource_type="action_item",
        resource_id=action.id,
        details=f"Action item updated; status={action.status.value}",
    )

    db.commit()
    db.refresh(action)

    return serialize_action(action)


@router.post(
    "/actions/refresh-overdue",
    response_model=OverdueRefreshResponse,
)
def refresh_overdue_actions(
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    if user.role not in {
        UserRole.ADMIN,
        UserRole.HOD,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators or HOD users can refresh overdue actions",
        )

    today = date.today()

    overdue_actions = db.scalars(
        select(ActionItem)
        .where(
            ActionItem.due_date < today,
            ActionItem.status.in_([
                ActionStatus.OPEN,
                ActionStatus.IN_PROGRESS,
            ]),
        )
    ).all()

    updated_count = 0

    for action in overdue_actions:
        action.status = ActionStatus.OVERDUE
        action.updated_at = utc_now()
        updated_count += 1

    create_audit_event(
        db=db,
        actor_id=user.id,
        action="OVERDUE_ACTIONS_REFRESHED",
        resource_type="action_item",
        resource_id=None,
        details=f"Marked {updated_count} action items as overdue",
    )

    db.commit()

    return OverdueRefreshResponse(
    updated_count=updated_count,
    message=f"{updated_count} action items marked as overdue",
)