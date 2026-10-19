"""Gemini document extraction with validation, retry and attempt logging."""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models import Document, ExtractionAttempt
from app.pipeline.schemas import EXTRACTION_SCHEMAS

try:
    from google import genai
    from google.genai import types
except Exception:  # pragma: no cover - package may not be installed in static checks
    genai = None  # type: ignore
    types = None  # type: ignore


BACKOFF_SECONDS = (2, 4, 8)
PROMPTS_DIR = Path(__file__).resolve().parents[3] / "prompts"


def _load_prompt(version: str) -> str:
    path = PROMPTS_DIR / version
    if not path.exists():
        raise FileNotFoundError(f"prompt file not found: {version}")
    return path.read_text(encoding="utf-8")


def _schema_for_doc_type(doc_type: str) -> type:
    schema = EXTRACTION_SCHEMAS.get(doc_type)
    if schema is None:
        raise ValueError(f"unknown doc_type {doc_type}")
    return schema


def _call_gemini(
    file_bytes: bytes,
    mime: str,
    prompt_text: str,
    schema_cls: type,
    settings: Settings,
) -> tuple[str, float]:
    if genai is None:
        raise RuntimeError("google-genai package is not installed")
    client = genai.Client(api_key=settings.GEMINI_API_KEY.get_secret_value())
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=schema_cls,
        temperature=0,
    )
    contents = [
        types.Part.from_text(text=prompt_text),
        types.Part.from_bytes(data=file_bytes, mime_type=mime),
    ]
    start = time.perf_counter()
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=contents,
        config=config,
    )
    latency = (time.perf_counter() - start) * 1000
    return response.text or "", latency


def _save_attempt(
    session: Session,
    document_id: object,
    prompt_version: str,
    model: str,
    outcome: str,
    raw_output: str,
    validation_error: str,
    latency_ms: int,
) -> None:
    session.add(
        ExtractionAttempt(
            document_id=document_id,
            prompt_version=prompt_version,
            model=model,
            outcome=outcome,
            raw_output=raw_output,
            validation_error=validation_error,
            latency_ms=latency_ms,
        )
    )


def extract_document(
    session: Session,
    document: Document,
    file_bytes: bytes,
    settings: Settings | None = None,
) -> Document:
    """Extract a single document, save attempts, and update document status.

    Returns the updated Document. The caller must commit.
    """
    if settings is None:
        settings = get_settings()
    schema_cls = _schema_for_doc_type(document.doc_type)
    version = f"extract.{document.doc_type}.v1"
    base_prompt = _load_prompt(version)

    # Cache hit: a previous successful attempt with the same prompt version.
    prior_ok = (
        session.query(ExtractionAttempt)
        .filter_by(document_id=document.id, prompt_version=version, outcome="ok")
        .order_by(ExtractionAttempt.created_at.desc())
        .first()
    )
    if prior_ok is not None:
        document.extraction_status = "ok"
        document.extracted_json = json.loads(prior_ok.raw_output)
        return document

    prompt = base_prompt
    model = settings.GEMINI_MODEL
    last_error = ""
    for attempt in range(2):
        raw_output = ""
        latency_ms = 0
        try:
            raw_output, latency = _call_gemini(
                file_bytes, document.mime, prompt, schema_cls, settings
            )
            latency_ms = int(latency)
            parsed = json.loads(raw_output) if raw_output else {}
            validated = schema_cls.model_validate(parsed)
            _save_attempt(
                session, document.id, version, model, "ok",
                raw_output, "", latency_ms,
            )
            document.extraction_status = "ok"
            document.extracted_json = validated.model_dump(mode="json")
            return document
        except (ValidationError, json.JSONDecodeError) as exc:
            last_error = str(exc)
            _save_attempt(
                session, document.id, version, model, "invalid",
                raw_output, last_error, latency_ms,
            )
            prompt = base_prompt + "\n\nPrevious attempt failed validation:\n" + last_error
        except Exception as exc:
            last_error = str(exc)
            # Back off on API errors.
            if attempt < len(BACKOFF_SECONDS) - 1:
                _save_attempt(
                    session, document.id, version, model, "api_error",
                    raw_output, last_error, latency_ms,
                )
                time.sleep(BACKOFF_SECONDS[attempt])
            else:
                _save_attempt(
                    session, document.id, version, model, "api_error",
                    raw_output, last_error, latency_ms,
                )
                document.extraction_status = "failed"
                return document
    document.extraction_status = "failed"
    return document
