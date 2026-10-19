"""Private Supabase Storage wrapper. Only storage keys are persisted."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from supabase import Client, create_client

from app.config import Settings, get_settings


def _client(settings: Settings) -> Client:
    return create_client(
        settings.SUPABASE_URL.get_secret_value(),
        settings.SUPABASE_SERVICE_ROLE_KEY.get_secret_value(),
    )


def _bucket(settings: Settings) -> str:
    return settings.STORAGE_BUCKET


def build_key(application_id: str, doc_type: str, version: int, ext: str) -> str:
    """Return a deterministic storage key with a random suffix for collision safety."""
    suffix = uuid.uuid4().hex[:12]
    return f"{application_id}/{doc_type}/{version}/{suffix}.{ext}"


def put_file(storage_key: str, file_bytes: bytes, mime: str, settings: Settings | None = None) -> None:
    if settings is None:
        settings = get_settings()
    client = _client(settings)
    bucket = _bucket(settings)
    # Supabase upload returns a response object; raise on HTTP errors.
    result = client.storage.from_(bucket).upload(
        path=storage_key,
        file=file_bytes,
        file_options={"content-type": mime, "upsert": "false"},
    )
    if hasattr(result, "is_success") and not result.is_success:
        raise RuntimeError("storage upload failed")


def signed_url(storage_key: str, settings: Settings | None = None) -> tuple[str, int]:
    if settings is None:
        settings = get_settings()
    client = _client(settings)
    bucket = _bucket(settings)
    expires_in = 60
    response = client.storage.from_(bucket).create_signed_url(
        path=storage_key, expires_in=expires_in
    )
    url = response.get("signedURL") if isinstance(response, dict) else getattr(response, "signedURL", None)
    if not url:
        raise RuntimeError("signed URL generation failed")
    # Supabase signed URLs are relative; prepend the public URL if needed.
    if url.startswith("/"):
        url = settings.SUPABASE_URL.get_secret_value().rstrip("/") + url
    return url, expires_in


def get_file(storage_key: str, settings: Settings | None = None) -> bytes:
    if settings is None:
        settings = get_settings()
    client = _client(settings)
    bucket = _bucket(settings)
    result = client.storage.from_(bucket).download(storage_key)
    if isinstance(result, bytes):
        return result
    # Some client versions wrap bytes in a response object.
    data = getattr(result, "content", None)
    if data is None:
        raise RuntimeError("storage download failed")
    return data


def delete_file(storage_key: str, settings: Settings | None = None) -> None:
    if settings is None:
        settings = get_settings()
    client = _client(settings)
    bucket = _bucket(settings)
    client.storage.from_(bucket).remove([storage_key])
