"""Frozen extraction schemas from SRS section 6.2."""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class UtilityBillHistoryRow(BaseModel):
    month: str | None = None
    due_date: date | None = None
    amount_billed: float | None = None
    amount_paid: float | None = None
    paid_date: date | None = None


class UtilityBill(BaseModel):
    provider: str | None = None
    consumer_name: str | None = None
    reference_no: str | None = None
    billing_month: str | None = None
    due_date: date | None = None
    amount_due: float | None = None
    history: list[UtilityBillHistoryRow] | None = None
    visual_observations: str | None = None


class TransactionRow(BaseModel):
    date: date | None = None
    description: str | None = None
    credit: float | None = None
    debit: float | None = None
    balance: float | None = None
    confidence: float | None = Field(None, ge=0, le=1)


class TransactionStatement(BaseModel):
    source_kind: Literal["printed", "handwritten"] | None = None
    account_holder_name: str | None = None
    institution: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    rows: list[TransactionRow] | None = None
    printed_total_credits: float | None = None
    printed_total_debits: float | None = None


class CNIC(BaseModel):
    full_name: str | None = None
    cnic_number: str | None = None
    date_of_birth: date | None = None


EXTRACTION_SCHEMAS = {
    "utility_bill": UtilityBill,
    "transaction_statement": TransactionStatement,
    "cnic": CNIC,
}
