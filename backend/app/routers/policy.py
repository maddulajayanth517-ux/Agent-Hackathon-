from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import MentoringPolicy, UserRole
from ..policy import DEFAULT_FREQUENCY_DAYS, DEFAULT_REMINDER_DAYS, get_mentoring_policy
from ..rbac import get_current_user
from ..schemas import UserContext

router = APIRouter(prefix="/policy", tags=["Institutional Mentoring Policy"])


class MentoringPolicyUpdate(BaseModel):
    required_frequency_days: int = Field(ge=7, le=365)
    reminder_days_before: int = Field(default=2, ge=1, le=30)


class MentoringPolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    required_frequency_days: int
    reminder_days_before: int
    updated_at: datetime | None = None


@router.get("", response_model=MentoringPolicyResponse)
def read_policy(db: Session = Depends(get_db), user: UserContext = Depends(get_current_user)):
    policy = get_mentoring_policy(db)
    if policy is None:
        return MentoringPolicyResponse(required_frequency_days=DEFAULT_FREQUENCY_DAYS, reminder_days_before=DEFAULT_REMINDER_DAYS)
    return policy


@router.put("", response_model=MentoringPolicyResponse)
def update_policy(payload: MentoringPolicyUpdate, db: Session = Depends(get_db), user: UserContext = Depends(get_current_user)):
    if user.role not in {UserRole.ADMIN, UserRole.HOD}:
        raise HTTPException(status_code=403, detail="Only administrators or HOD users can update mentoring policy")
    policy = get_mentoring_policy(db)
    if policy is None:
        policy = MentoringPolicy(id=1, **payload.model_dump(), updated_by=user.id)
        db.add(policy)
    else:
        policy.required_frequency_days = payload.required_frequency_days
        policy.reminder_days_before = payload.reminder_days_before
        policy.updated_by = user.id
    db.commit(); db.refresh(policy)
    return policy
