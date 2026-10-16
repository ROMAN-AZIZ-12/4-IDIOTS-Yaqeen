# Yaqeen

Team: 4 IDIOTS

Yaqeen lets small business owners in Pakistan apply for a bank loan from home by uploading their bills and transactions. AI reads the documents and scores the file. The bank officer reviews it and makes the final call.

## The problem

A lot of shop and workshop owners in Pakistan have no credit file, but they do have proof they earn and pay on time. Utility bills, Easypaisa or JazzCash history, bank transactions. Right now they bring a stack of papers to a branch. The loan officer goes through each one by hand, builds a picture of the business, and often asks for more papers. It takes days. Two officers can reach different answers on the same file. Some applicants are turned down because their paperwork is not in a format the bank knows how to read.

## Who it is for

Borrowers: small business owners who need a loan and want to apply without a branch visit.

Loan officers: SME and merchant desk staff at banks. They have little time per file and need something consistent they can defend.

## What we are building

A borrower signs up, turns on 2FA, and starts a loan application. They upload three kinds of documents: a utility bill, a transaction statement (wallet or bank), and a CNIC. Our backend sends each document to the Gemini vision API and gets structured data back. That data goes to a Gemini text model along with a fixed scoring rubric. The model returns a score, the evidence behind each part of the score, and a short report. The officer sees all of it on a dashboard and approves, rejects, or asks for another document.

The AI never decides. It prepares the file. The officer decides.

## The main user journey

1. Borrower signs up with email and password.
2. Borrower sets up 2FA with an authenticator app.
3. Borrower creates an application: bank, amount, purpose, business type.
4. Borrower uploads documents and submits. Status becomes "processing".
5. Backend extracts fields from each document with Gemini vision and saves them.
6. Backend scores the application with Gemini and saves the assessment. Status becomes "ready for review".
7. Officer signs in with 2FA and opens the application. They see the documents, extracted data, score, evidence and report.
8. Officer approves, rejects, or requests another document.
9. Borrower signs in later and sees the status and decision.

## How AI is used

### Step 1: reading documents

Each document goes to Gemini vision with a prompt that asks for JSON in a set shape for that document type.

- Utility bill: provider, billing month, amount due, amount paid, paid on time or not, due date, paid date.
- Transaction statement: account holder name, period, list of credits with dates, list of debits, total credits, total debits.
- CNIC: name, CNIC number, date of birth. Used to check that the name matches the other documents.

Gemini also returns a list of warnings when something looks off: names that do not match across documents, totals that do not add up, dates that do not fit, signs of editing. These are flags for the officer to look at. We do not claim to prove a document is real or fake.

We validate the JSON against a schema. If it is invalid we retry once. Fields the model cannot read are left empty and shown to the officer as missing. We store the raw output.

### Step 2: scoring and report

The scoring prompt contains a fixed rubric out of 100:

- Income consistency: 30
- Bill payment history: 25
- Transaction regularity: 25
- Document quality and consistency across documents: 20

The model returns points for each factor, the extracted fields it used as evidence, a total, a suggestion and a plain-English report. Temperature is 0.

After the call our code checks that each factor is within its maximum, that the factors add up to the total, and that every evidence field really exists in the extracted data. If a check fails we retry once. If it fails again the application is marked for manual review.

Suggestion bands: 70 and above leans approve, 50 to 69 needs review or more documents, below 50 leans reject. This is a suggestion only.

We store the prompt version, the input and the raw output with every assessment, so any score can be traced back.

## MVP scope

In:
- Sign up, sign in, TOTP 2FA, two roles (borrower and officer)
- Create application, upload three document types, see status and decision
- Extraction and scoring pipeline
- Officer dashboard, application detail, approve / reject / request document
- Postgres storage, public deployment

Out, for now:
- Handwritten khata pages
- Real bank or credit bureau integrations
- SMS and email notifications
- Urdu interface
- Training our own models

## Features

- Email and password auth
- TOTP 2FA setup and login
- Role-based access for borrowers and officers
- Loan application form
- Document upload
- Gemini vision extraction with schema validation
- Gemini scoring with rubric and code checks
- Officer dashboard and detail view
- Officer decision: approve, reject, request document
- Borrower status page
- Cross-document consistency flags
- Re-upload when an officer requests a document
- Decision history (if time allows)

## Who sees what

A borrower sees only their own applications, documents and assessments. An officer belongs to one bank and sees only applications sent to that bank. Every API route checks role and ownership on the server, not only in the UI. We will test this with two borrower accounts and two banks before submitting.

## Data model

```
users
  id, email (unique), password_hash, role (borrower | officer),
  bank_id (null for borrowers), totp_secret, totp_enabled, created_at

banks
  id, name

applications
  id, borrower_id, bank_id, amount, purpose, business_type,
  status (draft | processing | ready_for_review | needs_documents |
          approved | rejected | needs_manual_review),
  created_at, updated_at

documents
  id, application_id, doc_type (utility_bill | transaction_statement | cnic),
  file_url, extracted_json, flags_json, extraction_status, created_at

assessments
  id, application_id, rubric_version, factors_json, score_total,
  suggestion, report_text, raw_output, created_at

decisions
  id, application_id, officer_id,
  decision (approved | rejected | request_document), note, created_at
```

## Tech

- Frontend: React
- Backend: FastAPI
- Database: PostgreSQL (hosted, Neon or Supabase) with SQLAlchemy
- File storage: Supabase Storage or similar
- Auth: hashed passwords, JWT sessions, TOTP with pyotp
- AI: Gemini API, vision for extraction and a text model for scoring
- Deployment: hosted frontend and backend with a public URL

We are not using OpenCV or a separate OCR library. Documents go straight to Gemini vision.

Main routes:
- POST /auth/signup, /auth/login, /auth/2fa/setup, /auth/2fa/verify
- POST /applications, GET /applications, GET /applications/{id}
- POST /applications/{id}/documents, POST /applications/{id}/submit
- POST /applications/{id}/decision (officers only)

Scoring runs as a background task after submit so the upload returns fast and the status updates when the assessment is ready.

## Reuse and code gigs

Open source we expect to use: FastAPI, SQLAlchemy, React, pyotp, a UI component library. All will be listed with licences in AI_DISCLOSURE.md. We will also check Devmarketplace for existing gigs on auth, uploads and UI before writing our own, and credit anything we use.

Code gigs we plan to publish from code written during the event:
1. A Gemini document-to-JSON extractor with schema validation and retry.
2. A TOTP 2FA and role guard module for FastAPI.
3. If there is time, the rubric scorer with output validation.

The name Yaqeen comes from an earlier concept our team worked on for another hackathon. This build has a different pipeline, a different user flow and a new codebase. Any earlier code we carry over will be declared in PRIOR_WORK.md before the kickoff checkpoint.

## Team

- Muhammad Roman Aziz Khan: AI pipeline, prompts, validation
- [Member 2]: backend, auth, 2FA, database
- [Member 3]: frontend, borrower flow
- [Member 4]: frontend, officer dashboard, testing, deployment

Between us we cover React, FastAPI, PostgreSQL, LLM integration, UI design and QA.

## Plan for 19 to 22 October

Monday: kickoff, repo scaffold, database, signup, login and 2FA working, show an organiser the app in progress. Start the extractor gig.

Tuesday: application form, uploads, Gemini extraction working end to end. Publish gig 1.

Wednesday: scoring and report, officer dashboard, decisions. Publish gig 2.

Thursday: deploy, test two accounts and 2FA, record the demo, finish README and AI_DISCLOSURE, submit before 11:00 PM.

We will commit every day.

## Risks

- Gemini returns bad or partial JSON: schema check, one retry, empty fields shown as missing.
- Scores vary between runs: fixed rubric, temperature 0, code checks, raw output stored.
- AI cannot prove a document is genuine: we show consistency flags and say so. The officer decides.
- Sensitive data: the demo uses synthetic documents only. No real CNICs or statements in the repo.
- Four days is short: three document types, no handwriting.
- Officer sees the wrong borrower's data: officers are scoped to their bank, checks run on the server, and we test with multiple accounts.
