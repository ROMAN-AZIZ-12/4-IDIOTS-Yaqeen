"""Application status machine (SRS section 8)."""
from fastapi import HTTPException, status

STATUSES = {
    "draft", "processing", "ready_for_review", "needs_manual_review",
    "processing_failed", "needs_documents", "approved", "rejected",
}

# Allowed transitions: current -> {next_status: requires_reason?}.
# Guards are enforced in the route layer; this only validates the transition.
ALLOWED = {
    "draft": {"processing"},
    "processing": {"ready_for_review", "needs_manual_review", "processing_failed"},
    "processing_failed": {"processing"},
    "ready_for_review": {"approved", "rejected", "needs_documents"},
    "needs_manual_review": {"approved", "rejected", "needs_documents"},
    "needs_documents": {"processing"},
    "approved": set(),
    "rejected": set(),
}

TERMINAL = {"approved", "rejected"}


def validate_transition(current: str, next_status: str) -> None:
    if current not in STATUSES:
        raise ValueError(f"unknown status {current}")
    if next_status not in STATUSES:
        raise ValueError(f"unknown status {next_status}")
    if next_status not in ALLOWED.get(current, set()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"cannot move from {current} to {next_status}",
        )
