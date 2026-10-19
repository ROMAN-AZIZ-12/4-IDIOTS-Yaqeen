"""Assessment, decision and audit tables, re-exported by app.models."""
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models import primary_key, timestamp
from app.schema_types import DECISION, DOC_TYPE, REPORT_SOURCE, SUGGESTION


class Assessment(Base):
    __tablename__ = "assessments"
    __table_args__ = (
        sa.CheckConstraint("score_total BETWEEN 0 AND 100", name="score_bounds"),
        sa.CheckConstraint(
            "(yaqeen_factor_total(factors_json) = score_total) IS TRUE",
            name="factor_total",
        ),
    )
    id: Mapped[uuid.UUID] = primary_key()
    application_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("applications.id"))
    rubric_version: Mapped[str] = mapped_column(sa.Text)
    prompt_version: Mapped[str] = mapped_column(sa.Text)
    model_name: Mapped[str] = mapped_column(sa.Text)
    features_json: Mapped[dict] = mapped_column(JSONB)
    factors_json: Mapped[dict | list] = mapped_column(JSONB, nullable=False)
    flags_json: Mapped[list] = mapped_column(JSONB)
    score_total: Mapped[int]
    suggestion: Mapped[str] = mapped_column(SUGGESTION)
    report_json: Mapped[dict] = mapped_column(JSONB)
    report_source: Mapped[str] = mapped_column(REPORT_SOURCE)
    raw_output: Mapped[str] = mapped_column(sa.Text)
    created_at: Mapped[datetime] = timestamp()


class Decision(Base):
    __tablename__ = "decisions"
    __table_args__ = (
        sa.CheckConstraint(
            "decision <> 'request_document' OR requested_doc_type IS NOT NULL",
            name="requested_document",
        ),
        sa.CheckConstraint(
            "decision NOT IN ('rejected', 'request_document') OR length(btrim(note)) > 0",
            name="required_note",
        ),
    )
    id: Mapped[uuid.UUID] = primary_key()
    application_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("applications.id"))
    officer_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"))
    decision: Mapped[str] = mapped_column(DECISION)
    requested_doc_type: Mapped[str | None] = mapped_column(DOC_TYPE)
    note: Mapped[str] = mapped_column(sa.Text)
    created_at: Mapped[datetime] = timestamp()


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[uuid.UUID] = primary_key()
    actor_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(sa.Text)
    entity_type: Mapped[str] = mapped_column(sa.Text)
    entity_id: Mapped[str] = mapped_column(sa.Text)
    meta: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = timestamp()
