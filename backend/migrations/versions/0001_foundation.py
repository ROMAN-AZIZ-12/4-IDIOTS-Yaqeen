"""Phase 1 frozen section 9 schema.

Revision ID: 0001_foundation
Revises: None
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "0001_foundation"
down_revision = None
branch_labels = None
depends_on = None

ENUMS = {
    "user_role": ("borrower", "officer"),
    "application_status": ("draft", "processing", "ready_for_review", "needs_manual_review",
                           "processing_failed", "needs_documents", "approved", "rejected"),
    "document_type": ("utility_bill", "transaction_statement", "cnic"),
    "extraction_status": ("pending", "ok", "failed"),
    "extraction_outcome": ("ok", "invalid", "api_error"),
    "suggestion": ("lean_approve", "review", "lean_reject"),
    "report_source": ("model", "template"),
    "decision_type": ("approved", "rejected", "request_document"),
}


def enum(name):
    return pg.ENUM(*ENUMS[name], name=name, create_type=False)


def col(name, kind=sa.Text(), nullable=False, **kw):
    return sa.Column(name, kind, nullable=nullable, **kw)


def pk():
    return sa.Column("id", sa.Uuid(), primary_key=True)


def fk(name, target, nullable=False):
    return sa.Column(name, sa.Uuid(), sa.ForeignKey(target), nullable=nullable)


def ts(name="created_at", nullable=False, default=True):
    return col(name, sa.DateTime(timezone=True), nullable,
               server_default=sa.func.now() if default else None)


def upgrade():
    for name, values in ENUMS.items():
        pg.ENUM(*values, name=name).create(op.get_bind(), checkfirst=False)
    # SQL CHECK cannot contain a subquery. This immutable helper safely sums
    # numeric points for either an array or keyed object, without new fields.
    op.execute("""
        CREATE FUNCTION yaqeen_factor_total(factors jsonb) RETURNS numeric
        LANGUAGE plpgsql IMMUTABLE STRICT AS $$
        DECLARE item jsonb; items jsonb; total numeric := 0;
        BEGIN
          IF jsonb_typeof(factors) = 'object' THEN
            SELECT jsonb_agg(value) INTO items FROM jsonb_each(factors);
          ELSIF jsonb_typeof(factors) = 'array' THEN items := factors;
          ELSE RETURN NULL;
          END IF;
          IF items IS NULL OR jsonb_array_length(items) = 0 THEN RETURN NULL; END IF;
          FOR item IN SELECT value FROM jsonb_array_elements(items) LOOP
            IF jsonb_typeof(item) <> 'object'
               OR (jsonb_typeof(item->'points') = 'number') IS NOT TRUE
            THEN RETURN NULL; END IF;
            IF (item->>'points')::numeric < 0 THEN RETURN NULL; END IF;
            total := total + (item->>'points')::numeric;
          END LOOP;
          RETURN total;
        END $$
    """)
    op.create_table("banks", pk(), col("name"), sa.UniqueConstraint("name"))
    op.create_table("users", pk(), col("email"), col("password_hash"),
        col("role", enum("user_role")), fk("bank_id", "banks.id", True), col("full_name"),
        col("totp_secret_enc", nullable=True), col("totp_enabled", sa.Boolean(), server_default=sa.false()),
        col("totp_last_step", sa.BigInteger(), True), col("failed_2fa_count", sa.Integer(), server_default="0"),
        ts("locked_until", True, False), ts(), sa.UniqueConstraint("email"),
        sa.CheckConstraint("(role = 'officer') = (bank_id IS NOT NULL)", name=op.f("ck_users_role_bank")),
        sa.CheckConstraint("email = lower(email)", name=op.f("ck_users_lowercase_email")))
    op.create_table("applications", pk(), fk("borrower_id", "users.id"), fk("bank_id", "banks.id"),
        col("amount_pkr", sa.Numeric(14, 2)), col("purpose"), col("business_type"),
        col("status", enum("application_status"), server_default="draft"),
        ts("consent_at", True, False), ts("submitted_at", True, False),
        ts("processing_started_at", True, False), col("processing_attempts", sa.Integer(), server_default="0"),
        ts(), ts("updated_at"),
        sa.CheckConstraint("amount_pkr > 0", name=op.f("ck_applications_positive_amount")))
    op.create_index("uq_applications_active_borrower", "applications", ["borrower_id"], unique=True,
                    postgresql_where=sa.text("status NOT IN ('approved', 'rejected')"))
    op.create_table("documents", pk(), fk("application_id", "applications.id"),
        col("doc_type", enum("document_type")), col("version", sa.Integer()), col("is_current", sa.Boolean()),
        col("storage_key"), col("sha256"), col("mime"), col("size_bytes", sa.Integer()), col("pages", sa.Integer()),
        col("extraction_status", enum("extraction_status"), server_default="pending"),
        col("extracted_json", pg.JSONB(), True), ts(),
        sa.UniqueConstraint("application_id", "doc_type", "version"))
    op.create_index("uq_documents_current", "documents", ["application_id", "doc_type"], unique=True,
                    postgresql_where=sa.text("is_current"))
    op.create_table("extraction_attempts", pk(), fk("document_id", "documents.id"),
        col("prompt_version"), col("model"), col("outcome", enum("extraction_outcome")),
        col("raw_output"), col("validation_error"), col("latency_ms", sa.Integer()), ts())
    op.create_table("assessments", pk(), fk("application_id", "applications.id"),
        col("rubric_version"), col("prompt_version"), col("model_name"),
        col("features_json", pg.JSONB()), col("factors_json", pg.JSONB()), col("flags_json", pg.JSONB()),
        col("score_total", sa.Integer()), col("suggestion", enum("suggestion")),
        col("report_json", pg.JSONB()), col("report_source", enum("report_source")), col("raw_output"), ts(),
        sa.CheckConstraint("score_total BETWEEN 0 AND 100", name=op.f("ck_assessments_score_bounds")),
        sa.CheckConstraint("(yaqeen_factor_total(factors_json) = score_total) IS TRUE",
                           name=op.f("ck_assessments_factor_total")))
    op.create_table("decisions", pk(), fk("application_id", "applications.id"), fk("officer_id", "users.id"),
        col("decision", enum("decision_type")), col("requested_doc_type", enum("document_type"), True),
        col("note"), ts(),
        sa.CheckConstraint("decision <> 'request_document' OR requested_doc_type IS NOT NULL",
                           name=op.f("ck_decisions_requested_document")),
        sa.CheckConstraint("decision NOT IN ('rejected', 'request_document') OR length(btrim(note)) > 0",
                           name=op.f("ck_decisions_required_note")))
    op.create_table("audit_log", pk(), fk("actor_id", "users.id"), col("action"), col("entity_type"),
                    col("entity_id"), col("meta", pg.JSONB()), ts())


def downgrade():
    for table in ("audit_log", "decisions", "assessments", "extraction_attempts",
                  "documents", "applications", "users", "banks"):
        op.drop_table(table)
    op.execute("DROP FUNCTION yaqeen_factor_total(jsonb)")
    for name, values in reversed(list(ENUMS.items())):
        pg.ENUM(*values, name=name).drop(op.get_bind(), checkfirst=False)
