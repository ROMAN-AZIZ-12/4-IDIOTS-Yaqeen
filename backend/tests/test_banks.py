"""Tests for GET /banks (authenticated)."""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.auth import jwt as jwt_helpers
from app.auth.password import hash_password
from app.config import get_settings
from app.db import get_db
from app.main import app
from app.models import Bank, User

from tests.test_auth import (
    FakeSession,
    _REQUIRED_ENV,
    _add_borrower,
    _make_fernet_key,
)


@pytest.fixture(autouse=True)
def _env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in _REQUIRED_ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("FERNET_KEY", _make_fernet_key())
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client() -> TestClient:
    session = FakeSession()
    app.dependency_overrides[get_db] = lambda: session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_banks_requires_authentication(client: TestClient) -> None:
    response = client.get("/banks")
    assert response.status_code == 401


def test_banks_returns_all_banks(client: TestClient) -> None:
    session = app.dependency_overrides[get_db]()
    bank_a = Bank(id=uuid.uuid4(), name="Bank A")
    bank_b = Bank(id=uuid.uuid4(), name="Bank B")
    session.tables["banks"].extend([bank_b, bank_a])
    borrower = _add_borrower(session, "b@example.invalid", "password123")
    token = jwt_helpers.create_access_token(
        borrower.id, borrower.role, borrower.bank_id, get_settings(),
    )
    response = client.get("/banks", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    names = {b["name"] for b in body}
    assert names == {"Bank A", "Bank B"}
    for b in body:
        assert "id" in b and "name" in b
        assert "secret" not in b


def test_officer_can_list_banks(client: TestClient) -> None:
    session = app.dependency_overrides[get_db]()
    bank_id = uuid.uuid4()
    session.tables["banks"].append(Bank(id=bank_id, name="Officer Bank"))
    officer = User(
        id=uuid.uuid4(),
        email="officer@example.invalid",
        password_hash=hash_password("password123"),
        full_name="Officer",
        role="officer",
        bank_id=bank_id,
        totp_enabled=True,
        failed_2fa_count=0,
    )
    session.tables["users"].append(officer)
    token = jwt_helpers.create_access_token(
        officer.id, officer.role, officer.bank_id, get_settings(),
    )
    response = client.get("/banks", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json()) == 1
