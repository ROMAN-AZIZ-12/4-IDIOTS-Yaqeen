"""Authentication routes: signup, login, TOTP setup and TOTP verify."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import jwt, totp
from app.auth.dependencies import CurrentUser, get_pending_user
from app.auth.password import hash_password, verify_password
from app.auth.schemas import (
    LoginPendingResponse,
    LoginRequest,
    LoginSuccessResponse,
    SetupResponse,
    SignupRequest,
    UserResponse,
    VerifyRequest,
    VerifyResponse,
)
from app.config import Settings, get_settings
from app.db import get_db
from app.models import User

router = APIRouter()

MAX_2FA_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


def _generic_login_error() -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(
    payload: SignupRequest,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    existing = db.execute(select(User).where(User.email == payload.email.lower())).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        id=uuid.uuid4(),
        email=payload.email.lower(),
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role="borrower",
        bank_id=None,
        totp_enabled=False,
        failed_2fa_count=0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login")
def login(
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LoginSuccessResponse | LoginPendingResponse:
    user = db.execute(select(User).where(User.email == payload.email.lower())).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise _generic_login_error()

    if user.role == "borrower":
        token = jwt.create_access_token(user.id, user.role, user.bank_id, settings)
        return LoginSuccessResponse(status="ok", access_token=token)

    # Officers always require TOTP, even on first login.
    pending = jwt.create_pending_token(user.id, user.role, user.bank_id, settings)
    if user.totp_enabled:
        return LoginPendingResponse(status="2fa_required", pending_token=pending)
    return LoginPendingResponse(status="2fa_enroll_required", pending_token=pending)


@router.post("/2fa/setup", response_model=SetupResponse)
def setup_2fa(
    user: Annotated[CurrentUser, Depends(get_pending_user)],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SetupResponse:
    if user.role != "officer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    db_user = db.get(User, user.user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if db_user.totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="TOTP is already enabled",
        )

    secret = totp.generate_secret()
    db_user.totp_secret_enc = totp.encrypt_secret(secret, settings)
    db_user.totp_enabled = False
    db.commit()

    return SetupResponse(
        otpauth_uri=totp.build_otpauth_uri(secret, db_user.email),
        secret=secret,
    )


@router.post("/2fa/verify", response_model=VerifyResponse)
def verify_2fa(
    payload: VerifyRequest,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> VerifyResponse:
    try:
        token_payload = jwt.decode_pending_token(payload.pending_token)
    except jwt.TokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired pending token")

    if token_payload.get("role") != "officer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    user = db.get(User, uuid.UUID(token_payload["sub"]))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    now = datetime.now(timezone.utc)
    if user.locked_until is not None and user.locked_until > now:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account locked due to repeated failed attempts",
        )

    if user.totp_secret_enc is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TOTP not set up")

    plain_secret = totp.decrypt_secret(user.totp_secret_enc, settings)
    result = totp.verify_code(payload.code, plain_secret, user.totp_last_step)

    if not result.valid:
        user.failed_2fa_count += 1
        if user.failed_2fa_count >= MAX_2FA_ATTEMPTS:
            user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
            user.failed_2fa_count = 0
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Account locked due to repeated failed attempts",
            )
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid code")

    # Successful verification: enable TOTP, reset failures, record step.
    user.totp_enabled = True
    user.failed_2fa_count = 0
    user.totp_last_step = result.step
    db.commit()

    access_token = jwt.create_access_token(user.id, user.role, user.bank_id, settings)
    return VerifyResponse(access_token=access_token)
