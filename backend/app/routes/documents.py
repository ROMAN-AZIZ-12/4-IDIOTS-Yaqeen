"""Document upload and signed-URL routes."""
from __future__ import annotations

import hashlib
import io
import uuid
from datetime import datetime, timezone
from typing import Annotated

import filetype
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from pypdf import PdfReader
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, assert_application_access, borrower, get_current_user
from app.config import get_settings
from app.db import get_db
from app.models import Application, Document
from app.pipeline.run import run_pipeline
from app.status import validate_transition
from app.storage import build_key, put_file, signed_url

router = APIRouter(tags=["documents"])

MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_PAGES = 5
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
}


class DocumentResponse(BaseModel):
    id: uuid.UUID
    doc_type: str
    version: int
    mime: str
    size_bytes: int
    pages: int
    extraction_status: str
    created_at: datetime


class SignedUrlResponse(BaseModel):
    url: str
    expires_in: int


def _detect_mime(file_bytes: bytes) -> str | None:
    kind = filetype.guess(file_bytes)
    if kind is None:
        return None
    return kind.mime


def _page_count(file_bytes: bytes, mime: str) -> int:
    if mime == "application/pdf":
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            return len(reader.pages)
        except Exception:
            return 0
    if mime.startswith("image/"):
        try:
            with Image.open(io.BytesIO(file_bytes)) as img:
                return getattr(img, "n_frames", 1)
        except Exception:
            return 0
    return 0


def _ext_for_mime(mime: str) -> str:
    mapping = {
        "application/pdf": "pdf",
        "image/jpeg": "jpg",
        "image/png": "png",
    }
    return mapping.get(mime, "bin")


@router.post("/applications/{application_id}/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    application_id: uuid.UUID,
    doc_type: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    background_tasks: BackgroundTasks,
    user: Annotated[CurrentUser, Depends(borrower)],
    db: Annotated[Session, Depends(get_db)],
) -> Document:
    application = db.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    assert_application_access(user, application)
    upload_is_reupload = application.status == "needs_documents"
    if doc_type not in {"cnic", "utility_bill", "transaction_statement"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported document type")

    if application.status not in {"draft", "needs_documents"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Documents cannot be uploaded in the current status",
        )

    from app.review_models import Decision
    if application.status == "needs_documents":
        decision = (
            db.execute(
                select(Decision).where(Decision.application_id == application_id)
                .order_by(Decision.created_at.desc())
                .limit(1)
            )
            .scalar_one_or_none()
        )
        if decision is None or decision.requested_doc_type != doc_type:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Upload does not match the requested document type",
            )

    file_bytes = file.file.read()
    if len(file_bytes) > MAX_FILE_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")

    mime = _detect_mime(file_bytes)
    if mime is None or mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported file type")

    pages = _page_count(file_bytes, mime)
    if pages > MAX_PAGES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Too many pages")

    sha256 = hashlib.sha256(file_bytes).hexdigest()

    # Determine next version and mark older versions as not current.
    existing = (
        db.execute(
            select(Document).where(
                Document.application_id == application_id,
                Document.doc_type == doc_type,
            ).order_by(Document.version.desc())
        )
        .scalars()
        .first()
    )
    version = 1 if existing is None else existing.version + 1
    if existing is not None:
        existing.is_current = False

    settings = get_settings()
    storage_key = build_key(str(application_id), doc_type, version, _ext_for_mime(mime))
    put_file(storage_key, file_bytes, mime, settings)

    document = Document(
        application_id=application_id,
        doc_type=doc_type,
        version=version,
        is_current=True,
        storage_key=storage_key,
        sha256=sha256,
        mime=mime,
        size_bytes=len(file_bytes),
        pages=pages,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    if upload_is_reupload:
        validate_transition(application.status, "processing")
        application.status = "processing"
        application.processing_started_at = datetime.now(timezone.utc)
        application.processing_attempts += 1
        db.commit()
        background_tasks.add_task(run_pipeline, application.id)

    return DocumentResponse(
        id=document.id,
        doc_type=document.doc_type,
        version=document.version,
        mime=document.mime,
        size_bytes=document.size_bytes,
        pages=document.pages,
        extraction_status=document.extraction_status,
        created_at=document.created_at,
    )


@router.get("/documents/{document_id}/url", response_model=SignedUrlResponse)
def document_url(
    document_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> SignedUrlResponse:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    assert_application_access(user, document.application)
    url, expires_in = signed_url(document.storage_key)
    return SignedUrlResponse(url=url, expires_in=expires_in)
