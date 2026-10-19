"""FastAPI dependencies for authentication, roles and bank scoping."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth import jwt
from app.db import get_db
from app.models import Application, User

bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser:
    """Typed container for the authenticated caller."""

    def __init__(
        self,
        user_id: uuid.UUID,
        email: str,
        role: str,
        bank_id: uuid.UUID | None,
        totp_enabled: bool,
    ) -> None:
        self.user_id = user_id
        self.email = email
        self.role = role
        self.bank_id = bank_id
        self.totp_enabled = totp_enabled


def _token_from_header(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing authentication")
    return credentials.credentials


def get_current_user(
    token: Annotated[str, Depends(_token_from_header)],
    db: Annotated[Session, Depends(get_db)],
) -> CurrentUser:
    try:
        payload = jwt.decode_access_token(token)
    except jwt.TokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return _user_from_payload(db, payload)


def get_pending_user(
    token: Annotated[str, Depends(_token_from_header)],
    db: Annotated[Session, Depends(get_db)],
) -> CurrentUser:
    try:
        payload = jwt.decode_pending_token(token)
    except jwt.TokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired pending token")
    return _user_from_payload(db, payload)


def _user_from_payload(db: Session, payload: dict) -> CurrentUser:
    user_id = uuid.UUID(payload["sub"])
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    bank_id = uuid.UUID(payload["bank_id"]) if payload.get("bank_id") else None
    return CurrentUser(
        user_id=user.id,
        email=user.email,
        role=user.role,
        bank_id=bank_id,
        totp_enabled=user.totp_enabled,
    )


def require_role(required_role: str):
    """Return a dependency that accepts only the given role (403 otherwise)."""

    def checker(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        if user.role != required_role:
            raise HTTPException(
                status_code=403,
                detail=f"This action requires the {required_role} role",
            )
        return user

    return checker


borrower = require_role("borrower")
officer = require_role("officer")


def assert_application_access(user: CurrentUser, application: Application) -> None:
    """Raise 404 if the caller may not see or act on this application.

    Borrowers may access only their own applications. Officers may access only
    applications sent to their own bank. Cross-bank and cross-owner requests
    are indistinguishable from non-existent records.
    """
    if user.role == "borrower":
        if application.borrower_id != user.user_id:
            raise HTTPException(status_code=404, detail="Not found")
        return
    if user.role == "officer":
        if application.bank_id != user.bank_id:
            raise HTTPException(status_code=404, detail="Not found")
        return
    raise HTTPException(status_code=403, detail="Forbidden")
