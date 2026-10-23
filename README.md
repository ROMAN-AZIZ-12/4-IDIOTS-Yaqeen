Yaqeen — AI-Assisted Loan Application Review
Take the next step for your business, with confidence.

Yaqeen is an English–Urdu MVP that connects borrowers with bank officers through a document-based loan application workflow. Borrowers submit applications and supporting documents; Google Gemini extracts information, Python calculates an explainable assessment, and a bank officer makes the final decision.
The complete borrower-to-officer workflow has been manually tested locally by the project team.
Features
- Borrower signup and login.
- Bank selection and loan application creation.
- CNIC, utility bill, and transaction statement uploads.
- Private document storage and versioned replacements.
- AI-assisted extraction with structured validation and bounded retries.
- Rule-based scoring, consistency flags, and officer-readable reports.
- Officer login with authenticator-based two-factor authentication.
- Bank-scoped officer review and approve, reject, or request-document actions.
- Borrower-visible application status and decision notes.
- English–Urdu interface with right-to-left support.
Technology stack
Area	Technologies
Frontend	React, Vite, JavaScript, HTML, CSS
Backend	Python, FastAPI, Uvicorn, Pydantic
Database	Supabase PostgreSQL, SQLAlchemy, Alembic
Document storage	Private Supabase Storage bucket
AI	Google Gemini
Authentication	bcrypt, JWT, TOTP, Fernet encryption for TOTP secrets


Requirements
- Python 3.11 or newer with pip.
- Node.js and npm compatible with the Vite version installed by this repository.
- An existing Supabase project, PostgreSQL connection, and private storage bucket.
- A Gemini API key with access to the configured model.
- Internet access for installation and external services.
First-time setup — Windows PowerShell
Run these commands from the repository root.
1. Install dependencies
python -m venv backend/.venv
.\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
npm install
If a working backend/.venv already exists, skip its creation. If the launcher reports that Vite is missing and the frontend has its own package manifest, install its dependencies:
npm --prefix frontend install
2. Configure the backend
Create backend/.env using the repository's environment example. If backend/.env.example is present, this command copies it only when no local configuration exists:
if (!(Test-Path backend/.env)) {
    Copy-Item backend/.env.example backend/.env
}
If the example is stored at the repository root instead, copy .env.example to backend/.env. Edit the resulting file and supply the required values.
The updated backend settings loader reads backend/.env independently of the working directory. Existing process environment variables, including injected workspace Secrets, take precedence over the file.
Variable	Purpose
ENV	local for local development or production for production configuration
DATABASE_URL	Supabase PostgreSQL connection using the postgresql+psycopg:// driver
SUPABASE_URL	Supabase project URL
SUPABASE_SERVICE_ROLE_KEY	Backend-only credential used for storage access
STORAGE_BUCKET	Name of the existing private document bucket, such as documents
GEMINI_API_KEY	Backend-only Gemini API key
GEMINI_MODEL	Explicit model identifier available to the project
JWT_SECRET	Strong random secret used to sign authentication tokens
ACCESS_TOKEN_MINUTES	Access-token lifetime; the local demo configuration uses 30
PENDING_TOKEN_MINUTES	Pending two-factor token lifetime; the local demo configuration uses 5
FERNET_KEY	Valid Fernet key for encrypting stored TOTP secrets
FRONTEND_ORIGIN	Frontend origin; normally http://localhost:5173 locally
SEED_PASSWORD	Password for initial synthetic officer accounts; required only for seeding


Use the connection details provided by your existing Supabase project. The project's documented setup uses the Session pooler on port 5432 with its project-qualified username.
Keep .env, API keys, database passwords, signing secrets, and real personal documents out of Git. Backend credentials must not be placed in VITE_* variables.
3. Check configuration
node scripts/backend.cjs check
This validates backend configuration. It does not prove that the database, storage service, or Gemini is reachable.
4. Apply migrations and create demo accounts
Set-Location backend
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m app.seed
Set-Location ..
The seed creates two synthetic banks and their officer accounts:
Bank	Officer email
Yaqeen Synthetic Bank A	officer.a@example.invalid
Yaqeen Synthetic Bank B	officer.b@example.invalid


Use the SEED_PASSWORD value supplied when the accounts were first created. Running the seed again does not reset existing passwords or two-factor authentication. These identities are for demonstration only.
5. Start the application
node scripts/backend.cjs dev
The combined launcher starts both Vite and FastAPI. With no port overrides:
- Frontend: http://localhost:5173
- Backend health endpoint: http://localhost:8000/health
For subsequent sessions, run the same start command from the repository root. Virtual-environment activation is not required because the launcher selects backend/.venv directly. Stop the application with Ctrl+C.
Ports and preview routing
The corrected launcher and Vite configuration use matching settings:
Setting	Resolution order
Frontend listener	PORT, then FRONTEND_PORT, then 5173
Backend listener	BACKEND_PORT, then 8000
Vite API proxy	/api/* forwards to http://127.0.0.1:<backend port>/*, removing /api


If a preview platform supplies PORT=3000, Vite listens on 3000 and FastAPI remains on 8000 unless BACKEND_PORT is set. The platform's public preview must point to Vite. The frontend and backend must use different ports.
Port overrides for the Node launcher must be provided through the shell or platform environment; the Python loader does not export backend/.env values back to Node.
The frontend normally uses relative /api requests. VITE_API_URL can provide an explicit API origin for a separately configured deployment. Set FRONTEND_ORIGIN to the appropriate frontend origin when changing the deployment configuration.
Demo walkthrough
1. Register and sign in as a borrower.
2. Select a bank and create an application with the requested amount, purpose, and business details.
3. Upload a CNIC, utility bill, and transaction statement using synthetic test data.
4. Submit the application and wait for processing.
5. Sign in as the seeded officer for the selected bank.
6. On first officer login, enroll an authenticator app and verify its code. On later logins, enter the current authenticator code.
7. Review the supporting documents, factor scores, flags, and report.
8. Approve, reject, or request a replacement document. Rejection and document requests require a note.
9. Sign back in as the borrower to view the status and decision note.
Uploading the requested replacement document starts reprocessing. Borrower responses intentionally exclude the internal assessment scores and report.
Extraction and assessment
Gemini extracts structured document data, which is validated using Pydantic. Python computes the numeric score from the extracted inputs; Gemini does not assign the factor points.
Factor	Maximum points
Income consistency	30
Bill payment history	25
Transaction regularity	25
Document consistency and completeness	20
Total	100


The current rubric suggests lean_approve at 70 or above, review from 50 to 69, and lean_reject below 50. These are review suggestions, not automatic decisions. Requested amount and net inflow are separate affordability information and do not contribute points to this rubric.
The score is a prototype assessment, not a probability of approval or repayment. Structured validation checks data shape and types; it does not authenticate documents or independently verify their facts. Short histories and missing fields can reduce scores even when images are clear.
Processing states
Status	Meaning
draft	Application is being prepared
processing	Extraction and assessment are running
ready_for_review	An assessment is available for officer review
needs_documents	The officer requested a replacement document
needs_manual_review	Extraction validation could not produce a usable result
processing_failed	Processing encountered a service or other failure
approved	Officer approved the application
rejected	Officer rejected the application


Main API routes
Paths below are backend paths. Browser requests through Vite use the /api prefix.
Method	Path	Purpose
POST	/auth/signup	Register a borrower
POST	/auth/login	Authenticate a borrower or begin officer TOTP flow
POST	/auth/2fa/setup	Set up officer TOTP using a pending token
POST	/auth/2fa/verify	Verify officer TOTP and issue an access token
GET	/banks	List banks for an authenticated user
POST	/applications	Create an application
GET	/applications	List applications accessible to the caller
GET	/applications/{id}	Retrieve an accessible application
POST	/applications/{id}/documents	Upload a document
POST	/applications/{id}/submit	Submit for processing
GET	/documents/{id}/url	Request a temporary document URL
POST	/applications/{id}/decision	Record an officer decision
POST	/applications/{id}/retry	Retry eligible failed processing
GET	/health	Application health response


Standard authenticated requests use Authorization: Bearer <token>. Officer login issues a pending token until TOTP verification succeeds. Token lifetimes come from the configured environment values.
Checks and local testing
Check the running health endpoint:
Invoke-RestMethod http://localhost:8000/health
Expected response:
{"status":"ok"}
The health endpoint does not check database, storage, or Gemini connectivity.
Run backend tests from the repository root:
Set-Location backend
.\.venv\Scripts\python.exe -m pytest
Set-Location ..
The project team has manually exercised the complete workflow locally. Test results depend on the checked-out revision and environment; run the available tests after making changes. Successful local testing does not establish production readiness.
Current scope and next steps
The MVP uses seeded officers; public officer registration and bank approval are planned improvements. Document name consistency checks do not establish verified borrower identity. Document hashes are stored, but cross-application duplicate detection is a planned capability.
Next steps include stronger identity consistency checks, document-reuse review signals, bank-approved officer onboarding, broader scoring evaluation, and production deployment testing.
Contributing and sharing
Use synthetic examples for demos. Review staged changes before committing, and exclude local environments, credentials, uploaded personal documents, dependencies, and caches. Apply schema changes through Alembic; do not replace migrations with Base.metadata.create_all().
Additional requirements and AI development notes are available in docs/SRS.md and docs/ai-usage.md.