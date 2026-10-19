"""Frozen section 9 tables. No relationships or later-phase workflows."""
import uuid
from datetime import datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.schema_types import DOC_TYPE, EXTRACTION_STATUS, OUTCOME, ROLE, STATUS


def primary_key():
    return mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)


def timestamp():
    return mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())


class Bank(Base):
    __tablename__ = "banks"
    id: Mapped[uuid.UUID] = primary_key()
    name: Mapped[str] = mapped_column(sa.Text, unique=True)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        sa.CheckConstraint("(role = 'officer') = (bank_id IS NOT NULL)", name="role_bank"),
        sa.CheckConstraint("email = lower(email)", name="lowercase_email"),
    )
    id: Mapped[uuid.UUID] = primary_key()
    email: Mapped[str] = mapped_column(sa.Text, unique=True)
    password_hash: Mapped[str] = mapped_column(sa.Text)
    role: Mapped[str] = mapped_column(ROLE)
    bank_id: Mapped[uuid.UUID | None] = mapped_column(sa.ForeignKey("banks.id"))
    full_name: Mapped[str] = mapped_column(sa.Text)
    totp_secret_enc: Mapped[str | None] = mapped_column(sa.Text)
    totp_enabled: Mapped[bool] = mapped_column(server_default=sa.false())
    totp_last_step: Mapped[int | None] = mapped_column(sa.BigInteger)
    failed_2fa_count: Mapped[int] = mapped_column(server_default="0")
    locked_until: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    created_at: Mapped[datetime] = timestamp()


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        sa.CheckConstraint("amount_pkr > 0", name="positive_amount"),
        sa.Index("uq_applications_active_borrower", "borrower_id", unique=True,
                 postgresql_where=sa.text("status NOT IN ('approved', 'rejected')")),
    )
    id: Mapped[uuid.UUID] = primary_key()
    borrower_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("users.id"))
    bank_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("banks.id"))
    amount_pkr: Mapped[Decimal] = mapped_column(sa.Numeric(14, 2))
    purpose: Mapped[str] = mapped_column(sa.Text)
    business_type: Mapped[str] = mapped_column(sa.Text)
    status: Mapped[str] = mapped_column(STATUS, server_default="draft")
    consent_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    submitted_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    processing_started_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    processing_attempts: Mapped[int] = mapped_column(server_default="0")
    created_at: Mapped[datetime] = timestamp()
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(),
    )


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        sa.UniqueConstraint("application_id", "doc_type", "version"),
        sa.Index("uq_documents_current", "application_id", "doc_type", unique=True,
                 postgresql_where=sa.text("is_current")),
    )
    id: Mapped[uuid.UUID] = primary_key()
    application_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("applications.id"))
    doc_type: Mapped[str] = mapped_column(DOC_TYPE)
    version: Mapped[int]
    is_current: Mapped[bool]
    storage_key: Mapped[str] = mapped_column(sa.Text)
    sha256: Mapped[str] = mapped_column(sa.Text)
    mime: Mapped[str] = mapped_column(sa.Text)
    size_bytes: Mapped[int]
    pages: Mapped[int]
    extraction_status: Mapped[str] = mapped_column(EXTRACTION_STATUS, server_default="pending")
    extracted_json: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = timestamp()


class ExtractionAttempt(Base):
    __tablename__ = "extraction_attempts"
    id: Mapped[uuid.UUID] = primary_key()
    document_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("documents.id"))
    prompt_version: Mapped[str] = mapped_column(sa.Text)
    model: Mapped[str] = mapped_column(sa.Text)
    outcome: Mapped[str] = mapped_column(OUTCOME)
    raw_output: Mapped[str] = mapped_column(sa.Text)
    validation_error: Mapped[str] = mapped_column(sa.Text)
    latency_ms: Mapped[int]
    created_at: Mapped[datetime] = timestamp()


# Import only after shared column helpers exist, registering all eight tables.
from app.review_models import Assessment, AuditLog, Decision  # noqa: E402,F401
