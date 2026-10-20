"""Officer decision and retry routes."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, assert_application_access, officer
from app.db import get_db
from app.models import Application
from app.pipeline.run import run_pipeline
from app.review_models import Decision
from app.status import validate_transition

router = APIRouter(tags=["decisions"])


class DecisionRequest(BaseModel):
    decision: str = Field(pattern=r"^(approved|rejected|request_document)$")
    requested_doc_type: str | None = None
    note: str = ""


class DecisionResponse(BaseModel):
    id: uuid.UUID
    decision: str
    requested_doc_type: str | None = None
    note: str
    created_at: datetime


@router.post("/applications/{application_id}/decision", response_model=DecisionResponse, status_code=status.HTTP_201_CREATED)
def create_decision(
    application_id: uuid.UUID,
    payload: DecisionRequest,
    user: Annotated[CurrentUser, Depends(officer)],
    db: Annotated[Session, Depends(get_db)],
) -> Decision:
    application = db.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    assert_application_access(user, application)

    if payload.decision == "request_document":
        if not payload.requested_doc_type:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="requested_doc_type is required",
            )
    if payload.decision in {"rejected", "request_document"} and not payload.note.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="note is required",
        )

    next_status = payload.decision if payload.decision in {"approved", "rejected"} else "needs_documents"
    validate_transition(application.status, next_status)

    decision = Decision(
        application_id=application.id,
        officer_id=user.user_id,
        decision=payload.decision,
        requested_doc_type=payload.requested_doc_type,
        note=payload.note.strip(),
    )
    db.add(decision)
    application.status = next_status
    db.commit()
    db.refresh(decision)
    return DecisionResponse(
        id=decision.id,
        decision=decision.decision,
        requested_doc_type=decision.requested_doc_type,
        note=decision.note,
        created_at=decision.created_at,
    )


@router.post("/applications/{application_id}/retry", status_code=status.HTTP_202_ACCEPTED)
def retry_application(
    application_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    user: Annotated[CurrentUser, Depends(officer)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    application = db.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    assert_application_access(user, application)

    if application.status != "processing_failed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only failed processing can be retried",
        )
    validate_transition(application.status, "processing")
    application.status = "processing"
    application.processing_started_at = datetime.now(timezone.utc)
    application.processing_attempts += 1
    db.commit()

    background_tasks.add_task(run_pipeline, application.id)
    return {"status": "processing"}
