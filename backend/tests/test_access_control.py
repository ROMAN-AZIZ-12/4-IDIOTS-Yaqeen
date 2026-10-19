"""Direct tests for role guards and bank/owner scoping helpers."""
from __future__ import annotations

import uuid

import pytest
from app.auth.dependencies import (
    CurrentUser,
    assert_application_access,
    borrower,
    officer,
)
from app.models import Application


def _application(borrower_id: uuid.UUID, bank_id: uuid.UUID) -> Application:
    return Application(
        id=uuid.uuid4(),
        borrower_id=borrower_id,
        bank_id=bank_id,
        amount_pkr=100000,
        purpose="working capital",
        business_type="retail",
    )


def _current_user(role: str, user_id: uuid.UUID | None = None, bank_id: uuid.UUID | None = None) -> CurrentUser:
    return CurrentUser(
        user_id=user_id or uuid.uuid4(),
        email="test@example.invalid",
        role=role,
        bank_id=bank_id,
        totp_enabled=True,
    )


def test_borrower_guard_allows_borrower() -> None:
    user = _current_user("borrower")
    assert borrower(user) is user


def test_borrower_guard_rejects_officer() -> None:
    user = _current_user("officer", bank_id=uuid.uuid4())
    with pytest.raises(Exception) as exc:
        borrower(user)
    assert exc.value.status_code == 403  # type: ignore[attr-defined]


def test_officer_guard_allows_officer() -> None:
    user = _current_user("officer", bank_id=uuid.uuid4())
    assert officer(user) is user


def test_officer_guard_rejects_borrower() -> None:
    user = _current_user("borrower")
    with pytest.raises(Exception) as exc:
        officer(user)
    assert exc.value.status_code == 403  # type: ignore[attr-defined]


def test_borrower_sees_own_application() -> None:
    user_id = uuid.uuid4()
    user = _current_user("borrower", user_id=user_id)
    app_record = _application(user_id, uuid.uuid4())
    assert assert_application_access(user, app_record) is None


def test_borrower_foreign_application_is_404() -> None:
    user = _current_user("borrower")
    app_record = _application(uuid.uuid4(), uuid.uuid4())
    with pytest.raises(Exception) as exc:
        assert_application_access(user, app_record)
    assert exc.value.status_code == 404  # type: ignore[attr-defined]


def test_officer_sees_own_bank_application() -> None:
    bank_id = uuid.uuid4()
    user = _current_user("officer", bank_id=bank_id)
    app_record = _application(uuid.uuid4(), bank_id)
    assert assert_application_access(user, app_record) is None


def test_officer_foreign_bank_application_is_404() -> None:
    user = _current_user("officer", bank_id=uuid.uuid4())
    app_record = _application(uuid.uuid4(), uuid.uuid4())
    with pytest.raises(Exception) as exc:
        assert_application_access(user, app_record)
    assert exc.value.status_code == 404  # type: ignore[attr-defined]


