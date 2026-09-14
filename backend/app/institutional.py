from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


def get_institutional_context(
    db: Session,
    register_number: str,
) -> dict[str, Any] | None:
    """Read the institutional views without changing the existing public schema.

    The shared institutional schema keys students by ``roll_no``, which
    corresponds to this application's ``Student.register_number`` — not the
    mentoring app's internal integer primary key.
    """
    try:
        profile = db.execute(
            text(
                """
                SELECT student_id, roll_no, full_name, status, programme_code,
                       department_code, batch_label, section_code,
                       current_year_of_study, cgpa, backlog_count, attendance_pct,
                       verified_achievements, certifications, internships,
                       offers_accepted, fee_outstanding
                FROM people.v_student_profile
                WHERE roll_no = :roll_no
                """
            ),
            {"roll_no": register_number},
        ).mappings().first()

        if profile is None:
            return None

        flags = db.execute(
            text(
                """
                SELECT flag_type, severity, deviation_summary,
                       suggested_first_action, status
                FROM agentops.v_open_flags
                WHERE student_id = :student_id
                ORDER BY raised_at DESC
                """
            ),
            {"student_id": profile["student_id"]},
        ).mappings().all()

        return {
            "profile": dict(profile),
            "open_flags": [dict(flag) for flag in flags],
            "source": "institutional_views",
        }
    except SQLAlchemyError:
        # The public mentoring workflow remains available if optional views are unavailable.
        db.rollback()
        return None