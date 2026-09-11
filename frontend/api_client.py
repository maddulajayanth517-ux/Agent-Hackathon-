from __future__ import annotations

import json
from typing import Any, Dict, List

import requests

API_BASE_URL = "http://localhost:8000"


def _request(method: str, path: str, payload: Dict[str, Any] | None = None) -> Any:
    url = f"{API_BASE_URL}{path}"
    response = requests.request(method, url, json=payload, timeout=20)
    if response.status_code >= 400:
        detail = response.json().get("detail", response.text) if response.content else response.text
        raise RuntimeError(detail)
    if not response.content:
        return {}
    try:
        return response.json()
    except ValueError:
        return response.text


def get_allocations() -> List[Dict[str, Any]]:
    return _request("GET", "/allocations/")


def create_allocation(student_id: int, mentor_id: int, reason: str = "INITIAL") -> Dict[str, Any]:
    return _request("POST", "/allocations/", {"student_id": student_id, "mentor_id": mentor_id, "reason": reason, "active": True})


def update_allocation(allocation_id: int, student_id: int, mentor_id: int, reason: str = "REALLOCATION") -> Dict[str, Any]:
    return _request("PUT", f"/allocations/{allocation_id}", {"student_id": student_id, "mentor_id": mentor_id, "reason": reason, "active": True})


def get_workloads() -> List[Dict[str, Any]]:
    return _request("GET", "/allocations/workloads")


def get_allocation_recommendation(student_id: int) -> Dict[str, Any]:
    return _request("GET", f"/allocations/recommend/{student_id}")


def generate_brief(student_id: int) -> Dict[str, Any]:
    return _request("GET", f"/brief/{student_id}")


def create_flag(student_id: int, category: str, severity: str, title: str, description: str) -> Dict[str, Any]:
    return _request("POST", "/flags/", {"student_id": student_id, "category": category, "severity": severity, "title": title, "description": description, "status": "OPEN"})


def get_flags() -> List[Dict[str, Any]]:
    return _request("GET", "/flags/")


def get_escalation(flag_id: int) -> Dict[str, Any]:
    return _request("GET", f"/escalations/{flag_id}")
