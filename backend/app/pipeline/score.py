"""Pure scoring functions. Code computes the score; no model involvement."""
from __future__ import annotations

from typing import Any


def _clamp(value: float | None) -> float:
    return value if value is not None else 0.0


def _income_points(cv: float | None, thin: bool) -> tuple[int, str]:
    if cv is None:
        return 0, "income data missing or zero mean"
    thresholds = [(0.25, 30), (0.5, 20), (0.8, 10)]
    for threshold, points in thresholds:
        if cv <= threshold:
            max_points = 15 if thin else 30
            actual = min(points, max_points)
            return actual, f"CV {cv:.2f}; capped at {max_points}" if thin else f"CV {cv:.2f}"
    return 0, f"CV {cv:.2f}; high variability"


def _bill_points(ratio: float | None, thin: bool) -> tuple[int, str]:
    if ratio is None:
        return 0, "bill payment history missing"
    thresholds = [(0.90, 25), (0.75, 18), (0.50, 10)]
    for threshold, points in thresholds:
        if ratio >= threshold:
            max_points = 12 if thin else 25
            actual = min(points, max_points)
            return actual, f"on-time ratio {ratio:.0%}; capped at {max_points}" if thin else f"on-time ratio {ratio:.0%}"
    return 0, f"on-time ratio {ratio:.0%}"


def _regularity_points(avg_credits: float, share: float, thin: bool) -> tuple[int, str]:
    max_total = 12 if thin else 25
    credit_thresholds = [(20, 15), (10, 10), (4, 5)]
    credit_points = 0
    for threshold, points in credit_thresholds:
        if avg_credits >= threshold:
            credit_points = points
            break
    share_points = 10 if share >= 1.0 else 6 if share >= 0.75 else 2
    # Scale proportionally when capped.
    if thin:
        credit_points = min(credit_points, 7)
        share_points = min(share_points, 5)
    total = credit_points + share_points
    return total, f"avg {avg_credits:.1f} credits/month, {share:.0%} months with credit"


def _quality_points(
    name_statement: bool,
    name_bill: bool,
    totals_match: bool,
    required_ratio: float,
) -> tuple[int, str]:
    points = 0
    if name_statement:
        points += 8
    if name_bill:
        points += 4
    if totals_match:
        points += 4
    points += int(4 * required_ratio)
    return points, (
        f"statement name {name_statement}, bill name {name_bill}, "
        f"totals match {totals_match}, fields {required_ratio:.0%}"
    )


def _suggestion(total: int) -> str:
    if total >= 70:
        return "lean_approve"
    if total >= 50:
        return "review"
    return "lean_reject"


def score(features: dict[str, Any]) -> dict[str, Any]:
    """Return factors with points and evidence, total, and suggestion."""
    income_points, income_ev = _income_points(
        features.get("credit_cv"), features.get("thin_statement", False)
    )
    bill_points, bill_ev = _bill_points(
        features.get("bill_on_time_ratio"), features.get("thin_bill", False)
    )
    reg_points, reg_ev = _regularity_points(
        features.get("avg_credits_per_month", 0.0),
        features.get("share_months_with_credit", 0.0),
        features.get("thin_statement", False),
    )
    quality_points, quality_ev = _quality_points(
        features.get("name_match_statement_cnic", False),
        features.get("name_match_bill_cnic", False),
        features.get("totals_match", True),
        features.get("required_fields_ratio", 0.0),
    )
    factors = {
        "income_consistency": {"points": income_points, "evidence": income_ev},
        "bill_payment": {"points": bill_points, "evidence": bill_ev},
        "transaction_regularity": {"points": reg_points, "evidence": reg_ev},
        "document_quality": {"points": quality_points, "evidence": quality_ev},
    }
    total = income_points + bill_points + reg_points + quality_points
    suggestion = _suggestion(total)
    return {
        "factors": factors,
        "score_total": total,
        "suggestion": suggestion,
    }
