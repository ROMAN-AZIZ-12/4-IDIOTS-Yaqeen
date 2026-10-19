"""TOTP secret handling with Fernet-encrypted storage and replay prevention."""
from __future__ import annotations

import time
import uuid
from typing import NamedTuple

import pyotp
from cryptography.fernet import Fernet

from app.config import Settings


class VerificationResult(NamedTuple):
    valid: bool
    step: int | None


def _fernet(settings: Settings) -> Fernet:
    return Fernet(settings.FERNET_KEY.get_secret_value().encode("ascii"))


def generate_secret() -> str:
    """Return a new base32 TOTP secret."""
    return pyotp.random_base32()


def encrypt_secret(secret: str, settings: Settings) -> str:
    """Encrypt a base32 secret for database storage."""
    return _fernet(settings).encrypt(secret.encode("utf-8")).decode("ascii")


def decrypt_secret(enc_secret: str, settings: Settings) -> str:
    """Decrypt a stored TOTP secret."""
    return _fernet(settings).decrypt(enc_secret.encode("ascii")).decode("utf-8")


def build_otpauth_uri(secret: str, email: str, issuer: str = "Yaqeen") -> str:
    """Return the otpauth URI used by authenticator apps."""
    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=issuer)


def _totp(secret: str) -> pyotp.TOTP:
    return pyotp.TOTP(secret)


def verify_code(code: str, secret: str, last_step: int | None) -> VerificationResult:
    """Verify a TOTP code, allowing one interval of clock drift.

    Returns the matched time step so callers can enforce replay prevention.
    """
    if not code or len(code) != 6 or not code.isdigit():
        return VerificationResult(False, None)
    totp = _totp(secret)
    now = time.time()
    interval = totp.interval
    # Try the current interval and one step in either direction.
    for offset in (0, -1, 1):
        candidate = now + offset * interval
        if totp.at(candidate) == code:
            step = int(candidate // interval)
            if last_step is not None and step <= last_step:
                return VerificationResult(False, step)
            return VerificationResult(True, step)
    return VerificationResult(False, None)


def generate_demo_code(secret: str, for_time: float | None = None) -> str:
    """Generate a code for the current (or supplied) time; tests only."""
    return _totp(secret).now() if for_time is None else _totp(secret).at(for_time)


def user_email_for_totp(user_id: uuid.UUID, email: str) -> str:
    """Build a stable account label for the authenticator app."""
    return email
