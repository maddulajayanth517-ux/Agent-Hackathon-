import os

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_allocation_recommendation_prefers_available_mentor():
    response = client.get('/allocations/recommend/4')
    assert response.status_code == 200
    payload = response.json()
    assert payload['mentor_id'] in {1, 2, 3}
    assert 'reason' in payload
    assert payload['current_workload'] < payload['capacity']


def test_flag_creation_and_escalation():
    response = client.post('/flags/', json={
        'student_id': 1,
        'category': 'ACADEMIC',
        'severity': 'HIGH',
        'title': 'Final grade risk',
        'description': 'Needs support with finals.'
    })
    assert response.status_code == 200
    escalation = client.get(f"/escalations/{response.json()['id']}")
    assert escalation.status_code == 200
    assert escalation.json()['destination'] == 'HOD'
    assert escalation.json()['priority'] in {'HIGH', 'CRITICAL'}


def test_brief_fallback_generation_without_groq_key():
    os.environ.pop('GROQ_API_KEY', None)
    response = client.get('/brief/2')
    assert response.status_code == 200
    payload = response.json()
    assert payload['source'] == 'fallback'
    assert 'AI brief unavailable' in payload['warning']


def test_duplicate_allocation_rejected():
    response = client.post('/allocations/', json={
        'student_id': 1,
        'mentor_id': 2,
        'reason': 'reallocation',
        'active': True,
    })
    assert response.status_code == 400


def test_invalid_flag_category_rejected():
    response = client.post('/flags/', json={
        'student_id': 1,
        'category': 'INVALID',
        'severity': 'MEDIUM',
        'title': 'Bad flag',
        'description': 'should fail'
    })
    assert response.status_code == 422
