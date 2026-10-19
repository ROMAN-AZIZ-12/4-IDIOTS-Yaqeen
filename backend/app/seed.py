"""Run from backend/: python -m app.seed. Synthetic identities only."""
import uuid

import bcrypt
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import ConfigurationError, SeedSettings, load_settings
from app.db import get_session_factory
from app.models import Bank, User

SYNTHETIC_BANKS = (
    ("Yaqeen Synthetic Bank A", "officer.a@example.invalid", "Synthetic Officer A"),
    ("Yaqeen Synthetic Bank B", "officer.b@example.invalid", "Synthetic Officer B"),
)


def seed(session: Session, password: str) -> dict[str, int]:
    """Caller owns transaction. Conflict-safe inserts never reset existing accounts."""
    encoded = password.encode("utf-8")
    if not 8 <= len(encoded) <= 72:
        raise ConfigurationError("Missing or invalid environment variables: SEED_PASSWORD")
    counts = {"banks": 0, "officers": 0}
    for bank_name, email, full_name in SYNTHETIC_BANKS:
        bank_id = session.scalar(
            insert(Bank).values(id=uuid.uuid4(), name=bank_name)
            .on_conflict_do_nothing(index_elements=[Bank.name]).returning(Bank.id)
        )
        if bank_id is not None:
            counts["banks"] += 1
        else:
            bank_id = session.scalar(select(Bank.id).where(Bank.name == bank_name))
        existing = session.scalar(select(User).where(User.email == email))
        if existing is not None:
            if existing.role != "officer" or existing.bank_id != bank_id:
                raise RuntimeError("Synthetic seed identity conflicts with an existing account")
            continue
        password_hash = bcrypt.hashpw(encoded, bcrypt.gensalt(rounds=12)).decode("ascii")
        officer_id = session.scalar(
            insert(User).values(
                id=uuid.uuid4(), email=email, full_name=full_name,
                password_hash=password_hash, role="officer", bank_id=bank_id,
                totp_enabled=False, failed_2fa_count=0,
            ).on_conflict_do_nothing(index_elements=[User.email]).returning(User.id)
        )
        if officer_id is not None:
            counts["officers"] += 1
    return counts


def main() -> None:
    try:
        settings = load_settings(SeedSettings)
        with get_session_factory().begin() as session:
            counts = seed(session, settings.SEED_PASSWORD.get_secret_value())
    except ConfigurationError as exc:
        raise SystemExit(str(exc)) from None
    except SQLAlchemyError:
        # DB driver exceptions may include connection parameters or row contents.
        raise SystemExit("Seed database operation failed; verify DATABASE_URL and migration state") from None
    print(f"Created banks: {counts['banks']}; officers: {counts['officers']}")


if __name__ == "__main__":
    main()
