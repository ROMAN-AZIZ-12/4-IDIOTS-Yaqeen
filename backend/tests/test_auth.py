"""Deterministic auth tests with an in-memory session double; no external DB."""
from __future__ import annotations

import operator
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import BinaryExpression, BooleanClauseList, Select

from app.auth import jwt as jwt_helpers
from app.auth import totp as totp_helpers
from app.auth.password import hash_password, verify_password
from app.auth.totp import decrypt_secret, generate_demo_code
from app.config import get_settings
from app.db import get_db
from app.main import app
from app.models import User


# Real environment values are never stored here; these are synthetic test fixtures.
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


class FakeScalars:
    def __init__(self, items: list[Any]) -> None:
        self._items = items

    def first(self) -> Any:
        return self._items[0] if self._items else None

    def all(self) -> list[Any]:
        return list(self._items)


class FakeResult:
    def __init__(self, items: list[Any]) -> None:
        self._items = items

    def scalar_one_or_none(self) -> Any:
        return self._items[0] if self._items else None

    def scalars(self) -> FakeScalars:
        return FakeScalars(self._items)

    def all(self) -> list[Any]:
        return list(self._items)


class FakeSession:
    """Minimal SQLAlchemy session double supporting the queries auth routes issue."""

    def __init__(self) -> None:
        self.tables: dict[str, list[Any]] = {"users": [], "banks": []}

    def add(self, obj: Any) -> None:
        table = obj.__tablename__
        self.tables[table].append(obj)

    def commit(self) -> None:
        pass

    def refresh(self, obj: Any) -> None:
        pass

    def get(self, model: type[Any], ident: Any) -> Any:
        table = model.__tablename__
        return next((r for r in self.tables[table] if r.id == ident), None)

    def execute(self, statement: Any) -> FakeResult:
        if isinstance(statement, Select):
            table = statement.get_final_froms()[0]
            rows = list(self.tables[table.name])
            if statement.whereclause is not None:
                rows = [r for r in rows if self._match(statement.whereclause, r)]
            return FakeResult(rows)
        raise NotImplementedError(type(statement))

    def _match(self, clause: Any, row: Any) -> bool:
        if isinstance(clause, BooleanClauseList):
            parts = [self._match(c, row) for c in clause.clauses]
            if clause.operator is operator.and_:
                return all(parts)
            return any(parts)
        if isinstance(clause, BinaryExpression):
            col = clause.left.name
            val = clause.right.value
            op = clause.operator
            actual = getattr(row, col)
            if op is operator.eq:
                return actual == val
            if op is operator.ne:
                return actual != val
            if op is operator.lt:
                return actual < val
            if op is operator.le:
                return actual <= val
            if op is operator.gt:
                return actual > val
            if op is operator.ge:
                return actual >= val
        return True


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


def _add_borrower(session: FakeSession, email: str, password: str) -> User:
    user = User(
        id=uuid.uuid4(),
        email=email.lower(),
        password_hash=hash_password(password),
        full_name="Test Borrower",
        role="borrower",
        bank_id=None,
        totp_enabled=False,
        failed_2fa_count=0,
    )
    session.tables["users"].append(user)
    return user


def _add_officer(session: FakeSession, email: str, password: str, bank_id: uuid.UUID) -> User:
    user = User(
        id=uuid.uuid4(),
        email=email.lower(),
        password_hash=hash_password(password),
        full_name="Test Officer",
        role="officer",
        bank_id=bank_id,
        totp_enabled=False,
        failed_2fa_count=0,
    )
    session.tables["users"].append(user)
    return user


def _encrypted_totp_secret(secret: str | None = None) -> str:
    secret = secret or totp_helpers.generate_secret()
    return totp_helpers.encrypt_secret(secret, get_settings())


class TestSignup:
    def test_borrower_signup_creates_user(self, client: TestClient) -> None:
        response = client.post("/auth/signup", json={
            "email": "Borrower@Example.invalid",
            "password": "password123",
            "full_name": "Ali Khan",
        })
        assert response.status_code == 201
        body = response.json()
        assert body["email"] == "borrower@example.invalid"
        assert body["full_name"] == "Ali Khan"
        assert body["role"] == "borrower"

    def test_password_is_bcrypt_hashed(self, client: TestClient) -> None:
        client.post("/auth/signup", json={
            "email": "b@example.invalid",
            "password": "password123",
            "full_name": "Borrower",
        })
        session = app.dependency_overrides[get_db]()
        user = session.tables["users"][0]
        assert user.password_hash.startswith("$2b$")
        assert verify_password("password123", user.password_hash)

    def test_duplicate_email_rejected(self, client: TestClient) -> None:
        payload = {"email": "dup@example.invalid", "password": "password123", "full_name": "A"}
        assert client.post("/auth/signup", json=payload).status_code == 201
        assert client.post("/auth/signup", json=payload).status_code == 409

    def test_short_password_rejected(self, client: TestClient) -> None:
        response = client.post("/auth/signup", json={
            "email": "short@example.invalid", "password": "short", "full_name": "A",
        })
        assert response.status_code == 422


class TestBorrowerLogin:
    def test_valid_login_returns_access_token(self, client: TestClient) -> None:
        session = app.dependency_overrides[get_db]()
        _add_borrower(session, "borrower@example.invalid", "password123")
        response = client.post("/auth/login", json={
            "email": "borrower@example.invalid", "password": "password123",
        })
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert "access_token" in body
        payload = jwt_helpers.decode_access_token(body["access_token"])
        assert payload["scope"] == "access"
        assert payload["role"] == "borrower"

    def test_invalid_credentials_generic(self, client: TestClient) -> None:
        session = app.dependency_overrides[get_db]()
        _add_borrower(session, "b@example.invalid", "password123")
        response = client.post("/auth/login", json={
            "email": "b@example.invalid", "password": "wrongpassword",
        })
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_unknown_email_generic(self, client: TestClient) -> None:
        response = client.post("/auth/login", json={
            "email": "nobody@example.invalid", "password": "password123",
        })
        assert response.status_code == 401


class TestOfficer2fa:
    def test_first_login_requires_enrolment(self, client: TestClient) -> None:
        session = app.dependency_overrides[get_db]()
        bank_id = uuid.uuid4()
        _add_officer(session, "officer@example.invalid", "password123", bank_id)
        response = client.post("/auth/login", json={
            "email": "officer@example.invalid", "password": "password123",
        })
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "2fa_enroll_required"
        assert "pending_token" in body
        payload = jwt_helpers.decode_pending_token(body["pending_token"])
        assert payload["scope"] == "pending_2fa"
        assert payload["role"] == "officer"

    def test_setup_returns_uri_and_secret(self, client: TestClient) -> None:
        session = app.dependency_overrides[get_db]()
        bank_id = uuid.uuid4()
        officer = _add_officer(session, "officer@example.invalid", "password123", bank_id)
        pending = jwt_helpers.create_pending_token(
            officer.id, officer.role, officer.bank_id, get_settings(),
        )
        response = client.post(
            "/auth/2fa/setup",
            headers={"Authorization": f"Bearer {pending}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["otpauth_uri"].startswith("otpauth://totp/")
        assert len(body["secret"]) > 0
        # Secret is stored encrypted, not plaintext.
        stored = session.tables["users"][0].totp_secret_enc
        assert stored is not None
        assert stored != body["secret"]
        assert decrypt_secret(stored, get_settings()) == body["secret"]
        assert session.tables["users"][0].totp_enabled is False

    def test_verify_correct_code_enables_totp(self, client: TestClient) -> None:
        session = app.dependency_overrides[get_db]()
        bank_id = uuid.uuid4()
        officer = _add_officer(session, "officer@example.invalid", "password123", bank_id)
        pending = jwt_helpers.create_pending_token(
            officer.id, officer.role, officer.bank_id, get_settings(),
        )
        setup = client.post(
            "/auth/2fa/setup",
            headers={"Authorization": f"Bearer {pending}"},
        ).json()
        code = generate_demo_code(setup["secret"])
        response = client.post("/auth/2fa/verify", json={
            "pending_token": pending, "code": code,
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert session.tables["users"][0].totp_enabled is True
        assert session.tables["users"][0].totp_last_step is not None

    def test_subsequent_login_requires_2fa(self, client: TestClient) -> None:
        session = app.dependency_overrides[get_db]()
        bank_id = uuid.uuid4()
        officer = _add_officer(session, "officer@example.invalid", "password123", bank_id)
        officer.totp_enabled = True
        officer.totp_secret_enc = "enc"
        response = client.post("/auth/login", json={
            "email": "officer@example.invalid", "password": "password123",
        })
        assert response.status_code == 200
        assert response.json()["status"] == "2fa_required"

    def test_wrong_code_increments_failures(self, client: TestClient) -> None:
        session = app.dependency_overrides[get_db]()
        bank_id = uuid.uuid4()
        officer = _add_officer(session, "officer@example.invalid", "password123", bank_id)
        officer.totp_enabled = True
        officer.totp_secret_enc = _encrypted_totp_secret()
        pending = jwt_helpers.create_pending_token(
            officer.id, officer.role, officer.bank_id, get_settings(),
        )
        response = client.post("/auth/2fa/verify", json={
            "pending_token": pending, "code": "000000",
        })
        assert response.status_code == 401
        assert session.tables["users"][0].failed_2fa_count == 1

    def test_five_wrong_codes_lock_account(self, client: TestClient) -> None:
        session = app.dependency_overrides[get_db]()
        bank_id = uuid.uuid4()
        officer = _add_officer(session, "officer@example.invalid", "password123", bank_id)
        officer.totp_enabled = True
        officer.totp_secret_enc = _encrypted_totp_secret()
        pending = jwt_helpers.create_pending_token(
            officer.id, officer.role, officer.bank_id, get_settings(),
        )
        for i in range(5):
            response = client.post("/auth/2fa/verify", json={
                "pending_token": pending, "code": "000000",
            })
            if i < 4:
                assert response.status_code == 401
        assert session.tables["users"][0].failed_2fa_count == 0
        assert session.tables["users"][0].locked_until is not None
        locked_response = client.post("/auth/2fa/verify", json={
            "pending_token": pending, "code": "000000",
        })
        assert locked_response.status_code == 429

    def test_used_code_cannot_be_reused(self, client: TestClient) -> None:
        session = app.dependency_overrides[get_db]()
        bank_id = uuid.uuid4()
        officer = _add_officer(session, "officer@example.invalid", "password123", bank_id)
        pending = jwt_helpers.create_pending_token(
            officer.id, officer.role, officer.bank_id, get_settings(),
        )
        setup = client.post(
            "/auth/2fa/setup",
            headers={"Authorization": f"Bearer {pending}"},
        ).json()
        code = generate_demo_code(setup["secret"])
        assert client.post("/auth/2fa/verify", json={
            "pending_token": pending, "code": code,
        }).status_code == 200
        replay = client.post("/auth/2fa/verify", json={
            "pending_token": pending, "code": code,
        })
        assert replay.status_code == 401

    def test_expired_pending_token_rejected(self, client: TestClient) -> None:
        settings = get_settings()
        expired = jwt.encode(
            {
                "sub": str(uuid.uuid4()),
                "role": "officer",
                "bank_id": None,
                "scope": "pending_2fa",
                "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
            },
            settings.JWT_SECRET.get_secret_value(),
            algorithm="HS256",
        )
        response = client.post("/auth/2fa/verify", json={
            "pending_token": expired, "code": "000000",
        })
        assert response.status_code == 401

    def test_access_token_rejected_by_2fa_routes(self, client: TestClient) -> None:
        session = app.dependency_overrides[get_db]()
        bank_id = uuid.uuid4()
        officer = _add_officer(session, "officer@example.invalid", "password123", bank_id)
        access = jwt_helpers.create_access_token(
            officer.id, officer.role, officer.bank_id, get_settings(),
        )
        response = client.post(
            "/auth/2fa/setup",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert response.status_code == 401
