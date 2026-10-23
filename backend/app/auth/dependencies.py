"""FastAPI dependencies for authentication, roles and bank scoping."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth import jwt
from app.db import get_db
from app.models import Application, User

bearer_scheme = HTTPBearer(auto_error=False)

# Compatibility header for proxies (e.g. the DevMarketplace preview) that strip
# the standard Authorization header before the request reaches FastAPI.
FALLBACK_TOKEN_HEADER = "X-Yaqeen-Token"


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
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_yaqeen_token: Annotated[str | None, Header(alias=FALLBACK_TOKEN_HEADER)] = None,
) -> str:
    """Resolve the bearer token, preferring Authorization over the fallback header.

    Security rules:
      * Authorization (a valid ``Bearer <token>``) is always preferred.
      * A malformed Authorization header is rejected and never bypassed by the
        fallback, so an attacker cannot downgrade to the custom header.
      * The fallback ``X-Yaqeen-Token`` is used only when Authorization is absent.
      * If both carry a token and they disagree, the request is rejected rather
        than silently picking one.
    """
    header_token = credentials.credentials if credentials is not None else None
    fallback_token = x_yaqeen_token.strip() if x_yaqeen_token else None

    # A present-but-unparseable Authorization header must never be bypassed by
    # the fallback: HTTPBearer returns None for malformed values, so detect the
    # raw header separately and reject it outright.
    if header_token is None and authorization is not None and authorization.strip():
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    if header_token:
        # Both present: they must match exactly; otherwise reject the ambiguity.
        if fallback_token and fallback_token != header_token:
            raise HTTPException(
                status_code=401, detail="Conflicting authentication tokens"
            )
        return header_token

    if fallback_token:
        return fallback_token

    raise HTTPException(status_code=401, detail="Missing authentication")


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
