"""JWT access and pending-2FA token helpers."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt

from app.config import Settings

TokenScope = Literal["access", "pending_2fa"]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _expires(minutes: int) -> datetime:
    return _now() + timedelta(minutes=minutes)


def _encode(payload: dict) -> str:
    # PyJWT requires the secret as a string.
    from app.config import get_settings

    secret = get_settings().JWT_SECRET.get_secret_value()
    return jwt.encode(payload, secret, algorithm="HS256")


def _decode(token: str) -> dict:
    from app.config import get_settings

    secret = get_settings().JWT_SECRET.get_secret_value()
    return jwt.decode(token, secret, algorithms=["HS256"])


def _token(
    user_id: uuid.UUID,
    role: str,
    bank_id: uuid.UUID | None,
    scope: TokenScope,
    expires_at: datetime,
) -> str:
    return _encode(
        {
            "sub": str(user_id),
            "role": role,
            "bank_id": str(bank_id) if bank_id else None,
            "scope": scope,
            "exp": expires_at,
        }
    )


def create_access_token(
    user_id: uuid.UUID,
    role: str,
    bank_id: uuid.UUID | None,
    settings: Settings,
) -> str:
    return _token(
        user_id,
        role,
        bank_id,
        "access",
        _expires(settings.ACCESS_TOKEN_MINUTES),
    )


def create_pending_token(
    user_id: uuid.UUID,
    role: str,
    bank_id: uuid.UUID | None,
    settings: Settings,
) -> str:
    return _token(
        user_id,
        role,
        bank_id,
        "pending_2fa",
        _expires(settings.PENDING_TOKEN_MINUTES),
    )


def _decode_scoped(token: str, expected_scope: TokenScope) -> dict:
    try:
        payload = _decode(token)
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError("invalid token") from exc
    if payload.get("scope") != expected_scope:
        raise TokenError("invalid token scope")
    return payload


class TokenError(Exception):
    """Raised when a token cannot be decoded or has the wrong scope."""


def decode_access_token(token: str) -> dict:
    return _decode_scoped(token, "access")


def decode_pending_token(token: str) -> dict:
    return _decode_scoped(token, "pending_2fa")
