"""Pure feature computation from extracted documents. No database, no Gemini."""
from __future__ import annotations

import re
import statistics
from datetime import date
from decimal import Decimal
from typing import Any

from rapidfuzz import fuzz


def _normalise_name(name: str | None) -> str:
    if not name:
        return ""
    text = name.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    variants = [(r"\bmohammad\b", "muhammad"), (r"\bmohd\b", "muhammad"), (r"\bmd\b", "muhammad")]
    for pattern, repl in variants:
        text = re.sub(pattern, repl, text)
    return text


def names_match(a: str | None, b: str | None) -> bool:
    if not a or not b:
        return False
    na, nb = _normalise_name(a), _normalise_name(b)
    if not na or not nb:
        return False
    if fuzz.token_sort_ratio(na, nb, score_cutoff=85):
        return True
    return na == nb


def _parse_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except Exception:
            return None
    return None


def _days_between(start: date | None, end: date | None) -> int | None:
    if start is None or end is None:
        return None
    return (end - start).days


def _month_key(d: date) -> str:
    return f"{d.year}-{d.month:02d}"


def _monthly_credit_totals(rows: list[dict]) -> dict[str, float]:
    totals: dict[str, float] = {}
    for row in rows or []:
        d = _parse_date(row.get("date"))
        credit = row.get("credit") or 0
        if d is not None and credit:
            key = _month_key(d)
            totals[key] = totals.get(key, 0.0) + float(credit)
    return totals


def _cv(values: list[float]) -> float | None:
    if not values:
        return None
    mean = statistics.mean(values)
    if mean == 0:
        return None
    return statistics.pstdev(values) / mean


def _count_credits_per_month(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows or []:
        d = _parse_date(row.get("date"))
        credit = row.get("credit") or 0
        if d is not None and credit:
            counts[_month_key(d)] = counts.get(_month_key(d), 0) + 1
    return counts


def _compute_credit_features(rows: list[dict], period_start: Any, period_end: Any):
    monthly_totals = _monthly_credit_totals(rows)
    start, end = _parse_date(period_start), _parse_date(period_end)
    if start is not None and end is not None and start <= end:
        year, month = start.year, start.month
        while (year, month) <= (end.year, end.month):
            monthly_totals.setdefault(f"{year}-{month:02d}", 0.0)
            year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    months_covered = len(monthly_totals)
    total_values = list(monthly_totals.values())
    credit_cv = _cv(total_values)
    counts = _count_credits_per_month(rows)
    avg_credits_per_month = sum(counts.values()) / months_covered if months_covered else 0.0
    share_months_with_credit = sum(v > 0 for v in monthly_totals.values()) / months_covered if months_covered else 0.0
    period_days = _days_between(_parse_date(period_start), _parse_date(period_end))
    return {
        "months_covered": months_covered,
        "monthly_credit_totals": monthly_totals,
        "credit_cv": credit_cv,
        "avg_credits_per_month": avg_credits_per_month,
        "share_months_with_credit": share_months_with_credit,
        "period_days": period_days,
    }


def _compute_bill_features(history: list[dict]):
    on_time = 0
    months = 0
    for row in history or []:
        due = _parse_date(row.get("due_date"))
        paid = _parse_date(row.get("paid_date"))
        if due is None:
            continue
        months += 1
        if paid is not None and paid <= due:
            on_time += 1
    ratio = on_time / months if months else None
    return {
        "bill_months_covered": months,
        "bill_on_time_ratio": ratio,
    }


def _totals_match(statement: dict) -> bool:
    rows = statement.get("rows") or []
    printed_credits = statement.get("printed_total_credits")
    printed_debits = statement.get("printed_total_debits")
    if printed_credits is None and printed_debits is None:
        return True  # nothing to check
    sum_credits = sum(float(r.get("credit") or 0) for r in rows)
    sum_debits = sum(float(r.get("debit") or 0) for r in rows)
    for printed, summed in ((printed_credits, sum_credits), (printed_debits, sum_debits)):
        if printed is None:
            continue
        if summed == 0:
            if printed == 0:
                continue
            return False
        if abs(printed - summed) / summed > 0.01:
            return False
    return True


REQUIRED_FIELDS = [
    ("cnic", "full_name"),
    ("cnic", "cnic_number"),
    ("cnic", "date_of_birth"),
    ("statement", "account_holder_name"),
    ("statement", "period_start"),
    ("statement", "period_end"),
    ("statement", "rows"),
    ("bill", "consumer_name"),
    ("bill", "due_date"),
    ("bill", "amount_due"),
    ("bill", "history"),
]


def _required_fields_ratio(bill: dict, statement: dict, cnic: dict) -> float:
    values = {
        ("cnic", "full_name"): cnic.get("full_name"),
        ("cnic", "cnic_number"): cnic.get("cnic_number"),
        ("cnic", "date_of_birth"): cnic.get("date_of_birth"),
        ("statement", "account_holder_name"): statement.get("account_holder_name"),
        ("statement", "period_start"): statement.get("period_start"),
        ("statement", "period_end"): statement.get("period_end"),
        ("statement", "rows"): statement.get("rows"),
        ("bill", "consumer_name"): bill.get("consumer_name"),
        ("bill", "due_date"): bill.get("due_date"),
        ("bill", "amount_due"): bill.get("amount_due"),
        ("bill", "history"): bill.get("history"),
    }
    present = sum(1 for field in REQUIRED_FIELDS if values.get(field))
    return present / len(REQUIRED_FIELDS)


def _avg_monthly_net_inflow(rows: list[dict]) -> float | None:
    months: dict[str, list[float]] = {}
    for row in rows or []:
        d = _parse_date(row.get("date"))
        if d is None:
            continue
        key = _month_key(d)
        months.setdefault(key, [0.0, 0.0])
        months[key][0] += float(row.get("credit") or 0)
        months[key][1] += float(row.get("debit") or 0)
    if not months:
        return None
    nets = [c - d for c, d in months.values()]
    return statistics.mean(nets)


def compute_features(
    bill: dict,
    statement: dict,
    cnic: dict,
    requested_amount: Decimal | float,
) -> tuple[dict, list[str]]:
    """Return (features_json, flags)."""
    flags: list[str] = []
    handwritten = statement.get("source_kind") == "handwritten"
    if handwritten:
        flags.append("handwritten_statement_unverified_not_scored")
        # Preserve original extracted data; only the scoring view excludes rows.
        statement = {**statement, "rows": []}
    rows = statement.get("rows") or []
    if not rows:
        flags.append("missing_transaction_rows")
    credit = _compute_credit_features(
        rows, statement.get("period_start"), statement.get("period_end")
    )

    thin_statement = credit["period_days"] is not None and credit["period_days"] < 90
    if thin_statement:
        flags.append("thin_statement_data")

    bill_features = _compute_bill_features(bill.get("history") or [])
    thin_bill = bill_features["bill_months_covered"] < 3
    if thin_bill:
        flags.append("thin_bill_history")

    name_match_statement_cnic = names_match(
        statement.get("account_holder_name"), cnic.get("full_name")
    )
    name_match_bill_cnic = names_match(
        bill.get("consumer_name"), cnic.get("full_name")
    )
    if not name_match_bill_cnic and bill.get("consumer_name"):
        flags.append("bill_name_mismatch")
    if not name_match_statement_cnic and statement.get("account_holder_name"):
        flags.append("statement_name_mismatch")

    totals_match = False if handwritten else _totals_match(statement)
    if not totals_match and not handwritten:
        flags.append("printed_totals_mismatch")

    required_fields_ratio = _required_fields_ratio(bill, statement, cnic)
    if required_fields_ratio < 1:
        flags.append("missing_required_fields")

    if credit["credit_cv"] is None and credit["months_covered"] > 0:
        flags.append("zero_mean_credits")

    avg_net = _avg_monthly_net_inflow(statement.get("rows") or [])

    features = {
        "months_covered": credit["months_covered"],
        "monthly_credit_totals": credit["monthly_credit_totals"],
        "credit_cv": credit["credit_cv"],
        "avg_credits_per_month": credit["avg_credits_per_month"],
        "share_months_with_credit": credit["share_months_with_credit"],
        "bill_months_covered": bill_features["bill_months_covered"],
        "bill_on_time_ratio": bill_features["bill_on_time_ratio"],
        "name_match_statement_cnic": name_match_statement_cnic,
        "name_match_bill_cnic": name_match_bill_cnic,
        "totals_match": totals_match,
        "required_fields_ratio": required_fields_ratio,
        "requested_amount": float(requested_amount),
        "avg_monthly_net_inflow": avg_net,
        "thin_statement": thin_statement,
        "thin_bill": thin_bill,
    }
    if not rows:
        features["credit_cv"] = None
        features["avg_credits_per_month"] = None
        features["share_months_with_credit"] = None
    return features, flags
