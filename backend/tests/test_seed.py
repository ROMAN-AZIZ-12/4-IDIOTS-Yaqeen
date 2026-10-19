"""Pure seed flow test using a statement-aware in-memory double, not another DB."""
from types import SimpleNamespace

import bcrypt
from sqlalchemy.sql.dml import Insert
from sqlalchemy.sql.selectable import Select

from app.seed import SYNTHETIC_BANKS, seed


class MemorySession:
    def __init__(self):
        self.banks = {}
        self.users = {}

    def scalar(self, statement):
        params = statement.compile().params
        if isinstance(statement, Insert):
            if statement.table.name == "banks":
                if params["name"] in self.banks:
                    return None
                self.banks[params["name"]] = params["id"]
            else:
                if params["email"] in self.users:
                    return None
                self.users[params["email"]] = SimpleNamespace(**params)
            return params["id"]
        assert isinstance(statement, Select)
        key = next(iter(params.values()))
        if statement.get_final_froms()[0].name == "banks":
            return self.banks.get(key)
        return self.users.get(key)


def test_seed_twice_creates_no_duplicates():
    session = MemorySession()
    # Generated only in memory; no reusable password is stored in the repository.
    import secrets
    password = secrets.token_urlsafe(16)
    assert seed(session, password) == {"banks": 2, "officers": 2}
    original = {email: user.password_hash for email, user in session.users.items()}
    assert seed(session, password) == {"banks": 0, "officers": 0}
    assert len(session.banks) == len(session.users) == 2
    assert set(session.banks) == {row[0] for row in SYNTHETIC_BANKS}
    for email, user in session.users.items():
        assert user.role == "officer" and user.totp_enabled is False
        assert user.password_hash == original[email]
        assert bcrypt.checkpw(password.encode(), user.password_hash.encode())
