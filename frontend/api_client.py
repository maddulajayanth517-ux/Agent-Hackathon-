import os
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

REQUEST_TIMEOUT = 15


class APIError(Exception):
    def __init__(self, status_code: int, detail: Any):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API request failed with status {status_code}: {detail}")


def _request(
    method: str,
    path: str,
    user_id: int,
    *,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
) -> Any:
    headers = {
        "x-user-id": str(user_id),
        "Accept": "application/json",
    }

    try:
        response = requests.request(
            method=method,
            url=f"{API_BASE_URL}{path}",
            headers=headers,
            params=params,
            json=json,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise APIError(
            503,
            f"Backend unavailable: {exc}",
        ) from exc

    if not response.ok:
        try:
            detail = response.json()
        except ValueError:
            detail = response.text

        raise APIError(response.status_code, detail)

    if not response.content:
        return None

    return response.json()


def health_check() -> Any:
    return _request(
        "GET",
        "/health",
        user_id=1,
    )


def get_allocations(user_id: int) -> Any:
    return _request(
        "GET",
        "/allocations",
        user_id,
    )


def get_student_allocations(
    user_id: int,
    student_id: int,
) -> Any:
    return _request(
        "GET",
        f"/allocations/student/{student_id}",
        user_id,
    )


def get_student_brief(
    user_id: int,
    student_id: int,
) -> Any:
    return _request(
        "GET",
        f"/brief/student/{student_id}",
        user_id,
    )


def get_student_meetings(
    user_id: int,
    student_id: int,
    limit: int = 50,
    offset: int = 0,
) -> Any:
    return _request(
        "GET",
        f"/meetings/student/{student_id}",
        user_id,
        params={
            "limit": limit,
            "offset": offset,
        },
    )


def create_meeting(
    user_id: int,
    payload: dict[str, Any],
) -> Any:
    return _request(
        "POST",
        "/meetings",
        user_id,
        json=payload,
    )


def update_action(
    user_id: int,
    action_id: int,
    payload: dict[str, Any],
) -> Any:
    return _request(
        "PATCH",
        f"/meetings/actions/{action_id}",
        user_id,
        json=payload,
    )


def get_student_flags(
    user_id: int,
    student_id: int,
) -> Any:
    return _request(
        "GET",
        f"/flags/student/{student_id}",
        user_id,
    )


def create_flag(
    user_id: int,
    payload: dict[str, Any],
) -> Any:
    return _request(
        "POST",
        "/flags",
        user_id,
        json=payload,
    )


def resolve_flag(
    user_id: int,
    flag_id: int,
) -> Any:
    return _request(
        "PATCH",
        f"/flags/{flag_id}/resolve",
        user_id,
    )


def get_student_escalations(
    user_id: int,
    student_id: int,
) -> Any:
    return _request(
        "GET",
        f"/escalations/student/{student_id}",
        user_id,
    )


def create_escalation(
    user_id: int,
    payload: dict[str, Any],
) -> Any:
    return _request(
        "POST",
        "/escalations",
        user_id,
        json=payload,
    )


def update_escalation(
    user_id: int,
    escalation_id: int,
    payload: dict[str, Any],
) -> Any:
    return _request(
        "PATCH",
        f"/escalations/{escalation_id}",
        user_id,
        json=payload,
    )


def get_compliance_report(user_id: int) -> Any:
    return _request(
        "GET",
        "/reports/compliance",
        user_id,
    )


def get_mentor_load_report(user_id: int) -> Any:
    return _request(
        "GET",
        "/reports/mentor-load",
        user_id,
    )


def get_audit_summary(
    user_id: int,
    days: int = 30,
) -> Any:
    return _request(
        "GET",
        "/reports/audit-summary",
        user_id,
        params={"days": days},
    )