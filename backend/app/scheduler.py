"""In-process daily reminder scheduler. Use one application worker in production."""
import asyncio
import logging
import os

from .database import SessionLocal
from .models import UserRole
from .routers.alerts import run_meeting_reminders
from .schemas import UserContext

logger = logging.getLogger(__name__)


async def reminder_scheduler() -> None:
    interval_seconds = max(3600, int(os.getenv("REMINDER_SCHEDULER_INTERVAL_HOURS", "24")) * 3600)
    lock_db = SessionLocal()
    acquired = False
    try:
        # This session remains open, so exactly one worker owns the scheduler.
        acquired = lock_db.execute(__import__("sqlalchemy").text("SELECT pg_try_advisory_lock(450045)")).scalar()
        if not acquired:
            logger.info("Reminder scheduler not started: another worker owns the lock")
            return
        while True:
            db = SessionLocal()
            try:
                await asyncio.to_thread(run_meeting_reminders, days=None, db=db, user=UserContext(id=0, role=UserRole.ADMIN))
            except Exception:
                logger.exception("Automatic mentoring reminder run failed")
            finally:
                db.close()
            await asyncio.sleep(interval_seconds)
    finally:
        try:
            if acquired:
                lock_db.execute(__import__("sqlalchemy").text("SELECT pg_advisory_unlock(450045)"))
        finally:
            lock_db.close()
