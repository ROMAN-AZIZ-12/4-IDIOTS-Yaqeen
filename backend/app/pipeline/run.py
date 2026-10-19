"""End-to-end pipeline runner. Safe to run more than once."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_session_factory
from app.models import Application, Assessment, Document
from app.pipeline.explain import run_explain
from app.pipeline.extract import extract_document
from app.pipeline.features import compute_features
from app.pipeline.score import score
from app.storage import get_file


RUBRIC_VERSION = "1"
EXTRACTION_PROMPT_VERSION = "extract.{doc_type}.v1"
EXPLAIN_PROMPT_VERSION = "explain.v1"


def _current_documents(session: Session, application_id: object) -> list[Document]:
    return list(
        session.execute(
            select(Document).where(
                Document.application_id == application_id, Document.is_current.is_(True)
            )
        ).scalars().all()
    )


def _load_extracted_json(doc: Document) -> dict[str, Any]:
    return doc.extracted_json or {}


def _do_extraction(session: Session, application: Application, settings: Settings) -> list[Document]:
    docs = _current_documents(session, application.id)
    for doc in docs:
        if doc.extraction_status != "pending":
            continue
        file_bytes = get_file(doc.storage_key, settings)
        extract_document(session, doc, file_bytes, settings)
    return docs


def _any_status(docs: list[Document], status: str) -> bool:
    return any(doc.extraction_status == status for doc in docs)


def _missing_doc_type(docs: list[Document], doc_type: str) -> bool:
    return not any(doc.doc_type == doc_type for doc in docs)


def run_pipeline(application_id: object, settings: Settings | None = None) -> None:
    """Run the pipeline synchronously. Idempotent for extraction cache hits."""
    if settings is None:
        settings = get_settings()
    factory = get_session_factory()
    with factory.begin() as session:
        application = session.get(Application, application_id)
        if application is None:
            return
        if application.status != "processing":
            return

        docs = _do_extraction(session, application, settings)

        # Missing required document types -> manual review.
        for doc_type in ("utility_bill", "transaction_statement", "cnic"):
            if _missing_doc_type(docs, doc_type):
                doc = Document(
                    application_id=application.id,
                    doc_type=doc_type,
                    version=1,
                    is_current=True,
                    storage_key="",
                    sha256="",
                    mime="",
                    size_bytes=0,
                    pages=0,
                    extraction_status="failed",
                )
                session.add(doc)
                docs.append(doc)

        if _any_status(docs, "failed"):
            application.status = "needs_manual_review"
            application.processing_started_at = None
            return
        if _any_status(docs, "pending"):
            # Still waiting; leave in processing for sweep/retry.
            return

        bill = _load_extracted_json(next(d for d in docs if d.doc_type == "utility_bill"))
        statement = _load_extracted_json(next(d for d in docs if d.doc_type == "transaction_statement"))
        cnic = _load_extracted_json(next(d for d in docs if d.doc_type == "cnic"))

        features, flags = compute_features(bill, statement, cnic, application.amount_pkr)
        score_result = score(features)
        report_json, report_source = run_explain(features, score_result, settings)

        assessment = Assessment(
            application_id=application.id,
            rubric_version=RUBRIC_VERSION,
            prompt_version=EXPLAIN_PROMPT_VERSION,
            model_name=settings.GEMINI_MODEL,
            features_json=features,
            factors_json=score_result["factors"],
            flags_json=flags,
            score_total=score_result["score_total"],
            suggestion=score_result["suggestion"],
            report_json=report_json,
            report_source=report_source,
            raw_output=json.dumps(report_json),
        )
        session.add(assessment)
        application.status = "ready_for_review"
        application.processing_started_at = None
