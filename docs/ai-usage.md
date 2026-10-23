# AI usage

2026-10-19 repair pass: AI updated multipart upload binding, extraction failure classification/backoff and retry eligibility, handwritten-row exclusion and monthly scoring inputs, explanation fallback, current-document display, borrower polling/re-upload handling, and separate officer affordability information. Human review and all testing/runtime verification remain pending; no tests were added or run, and no migrations, seeds, commits, or pushes were performed.

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

Preview authentication fix was AI-assisted: the DevMarketplace preview proxy strips
the standard Authorization header, so a proxy-safe X-Yaqeen-Token fallback was added.
The FastAPI auth dependency now prefers Authorization, accepts X-Yaqeen-Token only when
Authorization is absent, rejects a malformed Authorization header (never bypassing it via
the fallback), and rejects conflicting tokens. CORS was extended to allow X-Yaqeen-Token,
the React API client now sends both headers, and the startup sweep's variable scope bug
was corrected. Focused tests cover Authorization, fallback, missing/conflicting/malformed
headers, invalid fallback tokens, and CORS preflight. Human review and actual pytest and
frontend build verification remain pending; no migrations, data changes, commits or pushes
were performed, and existing API contracts and unrelated files were left unchanged.
