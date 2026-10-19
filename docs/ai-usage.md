# AI usage

Phase 1 backend foundation was AI-assisted: configuration, SQLAlchemy models/sessions,
initial Alembic migration, health/CORS, synthetic seeding, focused tests, preview bridge
and setup/dependency notes. Human review is pending for schema/nullability/defaults,
factor JSON interpretation, migration, configuration, dependencies and actual test results.
No terminal/test/database/git verification was available to this agent. No human review
or completed execution is claimed. No push performed. No token reset performed.

Phase 2 preflight was AI-assisted: inspected repository instructions, existing backend
configuration/database/models/health and Phase 1 tests. No authentication, schema,
frontend or dependency changes were made. Execution tools were unavailable, so imports,
pytest, startup and git/artifact checks were not run. The file reader has no section/range
support; the frozen auth/banks SRS contracts were not read because whole-SRS reading
is prohibited. Implementation is blocked pending the permitted SRS excerpts (sections
2, 5 FR-1–FR-3, 10 auth and banks, 11 SEC-1–SEC-4/SEC-6, 15.4). Phase 1 runtime gate
remains unverified, not failed. Human review and all execution verification remain pending.

Phase 2 authentication and roles was AI-assisted: JWT access/pending tokens, bcrypt
password hashing, officer-only TOTP enrollment/verification with Fernet-encrypted
secrets and replay/lockout logic, role and bank/owner scoping helpers, /auth/* routes,
GET /banks, CORS updates, and deterministic auth/access-control tests. Existing Phase 1
schema, migration, config and health endpoint were preserved unchanged. Human review is
pending for security-sensitive code, token scoping, TOTP edge cases, dependency licenses
and actual pytest/database/git verification.

Phase 4 demo-ready MVP was AI-assisted: application create/list/detail routes with
role-shaped responses, document upload/versioning with content-type and page checks,
private Supabase Storage upload and 60-second signed URLs, Gemini extraction with
prompt versioning, validation and retry, feature/scoring engine, explanation call with
number-check fallback, officer decision and retry routes, startup sweep, and a React/Vite
borrower/officer frontend. Existing Phase 1/2 schema, auth and config were reused.
Human review is pending for extraction prompts, scoring edge cases, access control,
Supabase integration, frontend error handling, dependency licenses and actual
pytest/database/run verification. The demo flow is implemented but must be exercised
with configured integrations before presentation.
