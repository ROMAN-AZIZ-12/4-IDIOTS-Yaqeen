"""Tests for the X-Yaqeen-Token Authorization fallback.

The DevMarketplace preview proxy strips the standard Authorization header, so the
backend accepts the token via a custom X-Yaqeen-Token header. Authorization is
always preferred; the fallback is used only when Authorization is absent; malformed
Authorization is never bypassed; and conflicting tokens are rejected.
"""
from __future__ import annotations

import uuid

import pytest
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app.auth import jwt as jwt_helpers
from app.auth.dependencies import CurrentUser, get_current_user
from app.config import get_settings
from app.db import get_db
from app.models import User


_REQUIRED_ENV = {
    "ENV": "local",
    "DATABASE_URL": "postgresql+psycopg://postgres.test:pass12345@db.example.invalid:5432/yaqeen",
    "SUPABASE_URL": "https://test.supabase.co",
    "SUPABASE_SERVICE_ROLE_KEY": "test-service-role-key",
    "STORAGE_BUCKET": "documents",
    "GEMINI_API_KEY": "test-gemini-key",
    "GEMINI_MODEL": "gemini-2.5-flash",
    "JWT_SECRET": "test-jwt-secret-test-jwt-secret-test",
    "ACCESS_TOKEN_MINUTES": "30",
    "PENDING_TOKEN_MINUTES": "5",
    "FRONTEND_ORIGIN": "http://localhost:5173",
}


def _make_fernet_key() -> str:
    from cryptography.fernet import Fernet

    return Fernet.generate_key().decode("ascii")


class _StubSession:
    def __init__(self, user: User) -> None:
        self._user = user

    def get(self, model: type, ident: object) -> object:
        return self._user if ident == self._user.id else None


@pytest.fixture(autouse=True)
def _env(monkeypatch: pytest.MonkeyPatch):
    for name, value in _REQUIRED_ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("FERNET_KEY", _make_fernet_key())
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def context():
    user = User(
        id=uuid.uuid4(),
        email="borrower@example.com",
        password_hash="x",
        full_name="Borrower",
        role="borrower",
        bank_id=None,
        totp_enabled=False,
        failed_2fa_count=0,
    )
    token = jwt_helpers.create_access_token(user.id, user.role, user.bank_id, get_settings())

    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[get_settings().FRONTEND_ORIGIN],
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-Yaqeen-Token"],
        allow_credentials=False,
    )

    @app.get("/protected")
    def protected(current: CurrentUser = Depends(get_current_user)) -> dict:
        return {"email": current.email}

    app.dependency_overrides[get_db] = lambda: _StubSession(user)
    with TestClient(app) as client:
        yield client, token, user


def test_authorization_bearer_works(context) -> None:
    client, token, user = context
    response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == user.email


def test_fallback_header_works_when_authorization_absent(context) -> None:
    client, token, user = context
    response = client.get("/protected", headers={"X-Yaqeen-Token": token})
    assert response.status_code == 200
    assert response.json()["email"] == user.email


def test_missing_both_headers_is_401(context) -> None:
    client, _, _ = context
    response = client.get("/protected")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing authentication"


def test_matching_tokens_in_both_headers_succeed(context) -> None:
    client, token, user = context
    response = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {token}", "X-Yaqeen-Token": token},
    )
    assert response.status_code == 200
    assert response.json()["email"] == user.email


def test_conflicting_tokens_are_rejected(context) -> None:
    client, token, _ = context
    other = jwt_helpers.create_access_token(uuid.uuid4(), "borrower", None, get_settings())
    response = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {token}", "X-Yaqeen-Token": other},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Conflicting authentication tokens"


def test_malformed_authorization_not_bypassed_by_fallback(context) -> None:
    client, token, _ = context
    # A malformed Authorization header must be rejected, even if a valid fallback
    # token is present, so an attacker cannot downgrade the auth path.
    response = client.get(
        "/protected",
        headers={"Authorization": "Basic abc123", "X-Yaqeen-Token": token},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authorization header"


def test_invalid_fallback_token_is_rejected(context) -> None:
    client, _, _ = context
    response = client.get("/protected", headers={"X-Yaqeen-Token": "not-a-jwt"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


def test_cors_preflight_allows_fallback_header(context) -> None:
    client, _, _ = context
    response = client.options(
        "/protected",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "x-yaqeen-token",
        },
    )
    assert response.status_code == 200
    allowed = response.headers.get("access-control-allow-headers", "").lower()
    assert "x-yaqeen-token" in allowed
