"""Integration smoke tests against the mentoring API.

These tests assume a Postgres database reachable via DATABASE_URL that has
already been migrated (``alembic upgrade head``) and seeded with:
  - an admin user with id 1
  - mentors with ids 1, 2, 3 (capacity remaining for at least one)
  - students with ids 1, 2, 4 (student 1 already allocated to a mentor)

They authenticate using the ``x-user-id`` dev header, so
``AUTH_ALLOW_DEV_HEADER=true`` must be set in the test environment.
"""
import os

os.environ.setdefault("AUTH_ALLOW_DEV_HEADER", "true")

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)
ADMIN_HEADERS = {"x-user-id": "1"}


def test_allocation_recommendation_prefers_available_mentor():
    response = client.get("/allocations/recommend/4", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    payload = response.json()
    assert payload["mentor_id"] in {1, 2, 3}
    assert "reason" in payload
    assert payload["current_workload"] < payload["capacity"]


def test_flag_creation_and_escalation():
    response = client.post(
        "/flags",
        json={
            "student_id": 1,
            "category": "ACADEMIC",
            "severity": "high",
            "title": "Final grade risk",
            "description": "Needs support with finals.",
        },
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 201
    escalation = client.get(f"/escalations/{response.json()['id']}", headers=ADMIN_HEADERS)
    assert escalation.status_code == 200
    assert escalation.json()["destination"] == "HOD"
    assert escalation.json()["priority"] in {"HIGH", "CRITICAL"}


def test_brief_generation_returns_risk_and_evidence():
    response = client.get("/brief/student/2", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "agent"
    assert "evidence" in payload["risk"]


def test_duplicate_allocation_rejected():
    response = client.post(
        "/allocations",
        json={"student_id": 1, "mentor_id": 2, "reason": "reallocation"},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 409


def test_invalid_flag_category_rejected():
    response = client.post(
        "/flags",
        json={
            "student_id": 1,
            "category": "INVALID",
            "severity": "medium",
            "title": "Bad flag",
            "description": "should fail",
        },
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 422
