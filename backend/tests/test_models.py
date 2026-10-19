import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

from app.db import Base
from app import models  # noqa: F401


def test_exact_table_set_and_primary_keys():
    assert set(Base.metadata.tables) == {
        "banks", "users", "applications", "documents", "extraction_attempts",
        "assessments", "decisions", "audit_log",
    }
    for table in Base.metadata.tables.values():
        assert [c.name for c in table.primary_key] == ["id"]
        assert isinstance(table.c.id.type, sa.Uuid)
        for column in table.c:
            if isinstance(column.type, sa.DateTime):
                assert column.type.timezone
        # Compilation is offline; this does not claim the SQL ran on PostgreSQL.
        assert "CREATE TABLE" in str(CreateTable(table).compile(dialect=postgresql.dialect()))


def test_important_constraints():
    expected = {
        "users": {"ck_users_role_bank", "ck_users_lowercase_email"},
        "applications": {"ck_applications_positive_amount"},
        "assessments": {"ck_assessments_score_bounds", "ck_assessments_factor_total"},
        "decisions": {"ck_decisions_required_note", "ck_decisions_requested_document"},
    }
    for table, names in expected.items():
        assert names <= {c.name for c in Base.metadata.tables[table].constraints}
    for table_name, index_name, predicate in [
        ("applications", "uq_applications_active_borrower", "status NOT IN"),
        ("documents", "uq_documents_current", "is_current"),
    ]:
        index = next(i for i in Base.metadata.tables[table_name].indexes if i.name == index_name)
        assert index.unique
        assert predicate in str(CreateIndex(index).compile(dialect=postgresql.dialect()))
    users = Base.metadata.tables["users"]
    assert users.c.bank_id.nullable and users.c.locked_until.nullable
    assert users.c.totp_enabled.server_default is not None
    assert len(Base.metadata.tables["applications"].c.status.type.enums) == 8
    documents = Base.metadata.tables["documents"]
    assert any(isinstance(c, sa.UniqueConstraint) and
               [x.name for x in c.columns] == ["application_id", "doc_type", "version"]
               for c in documents.constraints)
