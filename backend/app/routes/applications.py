"""Application routes for borrowers and officers."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, assert_application_access, borrower, get_current_user
from app.config import get_settings
from app.db import get_db
from app.models import Application, Bank, Decision, Document, User
from app.pipeline.run import run_pipeline
from app.status import validate_transition

router = APIRouter(prefix="/applications", tags=["applications"])


class ApplicationCreateRequest(BaseModel):
    bank_id: uuid.UUID
    amount_pkr: Decimal = Field(gt=0, decimal_places=2)
    purpose: str = Field(min_length=1)
    business_type: str = Field(min_length=1)


class ApplicationListItem(BaseModel):
    id: uuid.UUID
    bank_id: uuid.UUID
    bank_name: str
    amount_pkr: str
    purpose: str
    business_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class DecisionItem(BaseModel):
    decision: str
    note: str
    requested_doc_type: str | None = None
    created_at: datetime


class DocumentItem(BaseModel):
    id: uuid.UUID
    doc_type: str
    version: int
    mime: str
    size_bytes: int
    pages: int
    extraction_status: str
    created_at: datetime


class BorrowerApplicationDetail(ApplicationListItem):
    documents: list[DocumentItem]
    decision: DecisionItem | None = None


class OfficerApplicationDetail(ApplicationListItem):
    borrower_email: str
    borrower_full_name: str
    documents: list[DocumentItem]
    flags: list[str]
    assessment: dict[str, Any] | None = None
    decision: DecisionItem | None = None


def _latest_decision(session: Session, application_id: uuid.UUID) -> Decision | None:
    return (
        session.execute(
            select(Decision).where(Decision.application_id == application_id)
            .order_by(Decision.created_at.desc())
            .limit(1)
        )
        .scalar_one_or_none()
    )


def _decision_item(decision: Decision | None) -> DecisionItem | None:
    if decision is None:
        return None
    return DecisionItem(
        decision=decision.decision,
        note=decision.note,
        requested_doc_type=decision.requested_doc_type,
        created_at=decision.created_at,
    )


def _application_list_item(app: Application) -> ApplicationListItem:
    return ApplicationListItem(
        id=app.id,
        bank_id=app.bank_id,
        bank_name=app.bank.name,
        amount_pkr=f"{app.amount_pkr:.2f}",
        purpose=app.purpose,
        business_type=app.business_type,
        status=app.status,
        created_at=app.created_at,
        updated_at=app.updated_at,
        submitted_at=app.submitted_at,
    )


@router.post("", response_model=ApplicationListItem, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationCreateRequest,
    user: Annotated[CurrentUser, Depends(borrower)],
    db: Annotated[Session, Depends(get_db)],
) -> Application:
    bank = db.get(Bank, payload.bank_id)
    if bank is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank not found")

    active = db.execute(
        select(Application).where(
            Application.borrower_id == user.user_id,
            Application.status.notin_(["approved", "rejected"]),
        )
    ).scalar_one_or_none()
    if active is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have an active application",
        )

    application = Application(
        borrower_id=user.user_id,
        bank_id=payload.bank_id,
        amount_pkr=payload.amount_pkr,
        purpose=payload.purpose,
        business_type=payload.business_type,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return _application_list_item(application)


@router.get("", response_model=list[ApplicationListItem])
def list_applications(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    status_filter: str | None = None,
) -> list[ApplicationListItem]:
    query = select(Application)
    if user.role == "borrower":
        query = query.where(Application.borrower_id == user.user_id)
    else:
        query = query.where(Application.bank_id == user.bank_id)
    if status_filter:
        query = query.where(Application.status == status_filter)
    query = query.order_by(Application.created_at.desc())
    apps = db.execute(query).scalars().all()
    return [_application_list_item(app) for app in apps]


@router.get("/{application_id}", response_model=BorrowerApplicationDetail | OfficerApplicationDetail)
def get_application(
    application_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> BorrowerApplicationDetail | OfficerApplicationDetail:
    application = db.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    assert_application_access(user, application)

    base = _application_list_item(application)
    decision = _decision_item(_latest_decision(db, application.id))
    docs = [
        DocumentItem(
            id=d.id,
            doc_type=d.doc_type,
            version=d.version,
            mime=d.mime,
            size_bytes=d.size_bytes,
            pages=d.pages,
            extraction_status=d.extraction_status,
            created_at=d.created_at,
        )
        for d in application.documents
    ]

    if user.role == "borrower":
        return BorrowerApplicationDetail(
            **base.model_dump(),
            documents=docs,
            decision=decision,
        )

    borrower_user = db.get(User, application.borrower_id)
    latest_assessment = sorted(application.assessments, key=lambda a: a.created_at, reverse=True)[:1]
    assessment_dict = None
    if latest_assessment:
        a = latest_assessment[0]
        assessment_dict = {
            "score_total": a.score_total,
            "suggestion": a.suggestion,
            "factors_json": a.factors_json,
            "features_json": a.features_json,
            "flags_json": a.flags_json,
            "report_json": a.report_json,
            "report_source": a.report_source,
            "created_at": a.created_at,
        }
    return OfficerApplicationDetail(
        **base.model_dump(),
        borrower_email=borrower_user.email if borrower_user else "",
        borrower_full_name=borrower_user.full_name if borrower_user else "",
        documents=docs,
        flags=latest_assessment[0].flags_json if latest_assessment else [],
        assessment=assessment_dict,
        decision=decision,
    )


@router.post("/{application_id}/submit", status_code=status.HTTP_202_ACCEPTED)
def submit_application(
    application_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    user: Annotated[CurrentUser, Depends(borrower)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    application = db.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    assert_application_access(user, application)

    validate_transition(application.status, "processing")

    current_types = {
        d.doc_type for d in application.documents if d.is_current
    }
    required = {"utility_bill", "transaction_statement", "cnic"}
    if not required.issubset(current_types):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="All three required documents must be uploaded before submitting",
        )

    now = datetime.now(timezone.utc)
    application.status = "processing"
    application.submitted_at = now
    application.processing_started_at = now
    application.processing_attempts += 1
    db.commit()

    background_tasks.add_task(run_pipeline, application.id)
    return {"status": "processing"}
