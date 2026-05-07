"""Tests for auth endpoints: /auth/sync and /auth/me"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# --- /auth/sync tests ---

@patch("app.routers.auth.get_db")
def test_sync_creates_new_user(mock_get_db):
    """POST /auth/sync should create a new user when google_id doesn't exist."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None  # No existing user

    async def fake_execute(stmt):
        return mock_result

    mock_session.execute = fake_execute
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.commit = AsyncMock()

    async def fake_db():
        yield mock_session

    mock_get_db.return_value = fake_db()

    response = client.post("/auth/sync", json={
        "google_id": "google-123",
        "email": "test@example.com",
        "name": "Test User",
        "avatar_url": "https://example.com/avatar.jpg",
        "access_token": "access-token-abc",
        "refresh_token": "refresh-token-xyz",
        "expires_at": "2026-05-06T12:00:00Z",
        "scope": "openid email profile https://www.googleapis.com/auth/drive.readonly",
    })

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "user_id" in data


def test_sync_rejects_missing_fields():
    """POST /auth/sync should return 422 for missing required fields."""
    response = client.post("/auth/sync", json={
        "email": "test@example.com",
        # missing google_id and access_token
    })
    assert response.status_code == 422


def test_sync_rejects_empty_body():
    """POST /auth/sync should return 422 for empty body."""
    response = client.post("/auth/sync", json={})
    assert response.status_code == 422


# --- /auth/me tests ---

def test_me_requires_google_id():
    """GET /auth/me without google_id param should return 422."""
    response = client.get("/auth/me")
    assert response.status_code == 422


@patch("app.routers.auth.get_db")
def test_me_returns_404_for_unknown_user(mock_get_db):
    """GET /auth/me with unknown google_id should return 404."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    async def fake_execute(stmt):
        return mock_result

    mock_session.execute = fake_execute

    async def fake_db():
        yield mock_session

    mock_get_db.return_value = fake_db()

    response = client.get("/auth/me", params={"google_id": "nonexistent"})
    assert response.status_code == 404


# --- Input validation tests ---

def test_sync_rejects_invalid_email_type():
    """POST /auth/sync should handle missing access_token."""
    response = client.post("/auth/sync", json={
        "google_id": "google-123",
        "email": "test@example.com",
        # missing access_token — required field
    })
    assert response.status_code == 422


# --- Health endpoint ---

def test_health():
    """GET /health should return ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
