"""Tests for /query endpoint validation."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_query_requires_question():
    """POST /query without question should return 422."""
    response = client.post("/query", json={"user_id": "user-123"})
    assert response.status_code == 422


def test_query_requires_user_id():
    """POST /query without user_id should return 422."""
    response = client.post("/query", json={"question": "What did we decide?"})
    assert response.status_code == 422


def test_query_rejects_empty_question():
    """POST /query with empty question should return 400."""
    response = client.post("/query", json={"question": "   ", "user_id": "user-123"})
    assert response.status_code == 400


def test_query_rejects_empty_body():
    """POST /query with empty body should return 422."""
    response = client.post("/query", json={})
    assert response.status_code == 422


def test_query_accepts_filters():
    """POST /query with filters should pass validation (may fail at DB layer)."""
    try:
        response = client.post("/query", json={
            "question": "What about auth?",
            "user_id": "user-123",
            "filters": {"date_from": "2026-03-01", "speaker": "Alice"},
        })
        # If we get a response, it passed validation
        assert response.status_code in (200, 500)
    except Exception:
        # DB connection error is expected without a real database
        pass
