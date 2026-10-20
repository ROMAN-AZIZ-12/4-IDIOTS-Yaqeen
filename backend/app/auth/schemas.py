"""Pydantic request/response models for authentication routes."""
from __future__ import annotations

import uuid
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, ValidatorFunctionWrapHandler, WrapValidator


def _login_email(value: object, handler: ValidatorFunctionWrapHandler) -> str:
    # Login-only compatibility for existing synthetic seed identities.
    # All other addresses retain EmailStr validation, including signup.
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"officer.a@example.invalid", "officer.b@example.invalid"}:
            return normalized
    return handler(value)


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1)


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: Annotated[EmailStr, WrapValidator(_login_email)]
    password: str


class LoginSuccessResponse(BaseModel):
    status: str = "ok"
    access_token: str


class LoginPendingResponse(BaseModel):
    status: str
    pending_token: str


class SetupResponse(BaseModel):
    otpauth_uri: str
    secret: str


class VerifyRequest(BaseModel):
    pending_token: str
    code: str = Field(min_length=6, max_length=6)


class VerifyResponse(BaseModel):
    access_token: str
