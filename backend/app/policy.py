from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import MentoringPolicy

DEFAULT_FREQUENCY_DAYS = 30
DEFAULT_REMINDER_DAYS = 2


def get_mentoring_policy(db: Session) -> MentoringPolicy | None:
    return db.scalar(select(MentoringPolicy).where(MentoringPolicy.id == 1))


def frequency_days(db: Session) -> int:
    policy = get_mentoring_policy(db)
    return policy.required_frequency_days if policy else DEFAULT_FREQUENCY_DAYS


def reminder_days(db: Session) -> int:
    policy = get_mentoring_policy(db)
    return policy.reminder_days_before if policy else DEFAULT_REMINDER_DAYS
