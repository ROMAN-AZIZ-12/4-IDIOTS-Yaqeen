"""Shared PostgreSQL enum names and values; no application behavior."""
from sqlalchemy import Enum

ROLE = Enum("borrower", "officer", name="user_role")
STATUS = Enum(
    "draft", "processing", "ready_for_review", "needs_manual_review",
    "processing_failed", "needs_documents", "approved", "rejected",
    name="application_status",
)
DOC_TYPE = Enum("utility_bill", "transaction_statement", "cnic", name="document_type")
EXTRACTION_STATUS = Enum("pending", "ok", "failed", name="extraction_status")
OUTCOME = Enum("ok", "invalid", "api_error", name="extraction_outcome")
SUGGESTION = Enum("lean_approve", "review", "lean_reject", name="suggestion")
REPORT_SOURCE = Enum("model", "template", name="report_source")
DECISION = Enum("approved", "rejected", "request_document", name="decision_type")
