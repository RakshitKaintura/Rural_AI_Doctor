# Rural AI Doctor

AI-powered rural healthcare backend and frontend platform designed for low-resource environments. The project combines clinical triage, follow-up workflows, medication safety checks, offline sync, and explainability/audit capabilities in a production-style FastAPI stack.

## Why This Project Is Resume-Ready

- Solves a real-world healthcare problem in constrained environments.
- Implements decision-support safety layers, not just chat UX.
- Includes offline-first synchronization with conflict resolution.
- Adds traceable AI audit logs for explainability and clinician override.
- Uses clean API modularization with migration and test coverage updates.

## Architecture

### Backend

- Framework: FastAPI (async)
- Database: PostgreSQL + SQLAlchemy
- Migrations: Alembic
- AI Services: Gemini-based chat and symptom analysis
- Observability: Prometheus metrics, structured logging, Sentry hooks

Core backend modules:

- `app/api/v1/endpoints`: versioned API routers
- `app/db/models.py`: SQLAlchemy data model layer
- `app/schemas`: Pydantic request/response contracts
- `app/services`: AI, voice, email, and domain service integrations

### Frontend

- Next.js application for clinical dashboard and patient workflows
- Integrates with backend REST APIs

## New Advanced Clinical Features Implemented

### 1. Clinical Triage and Escalation

- Rule-driven urgency classification (`emergency`, `urgent`, `routine`)
- Red flag extraction
- Escalation workflow with ticket generation

### 2. Follow-up Care Workflow

- Follow-up scheduling and tracking
- Status lifecycle (`scheduled`, `completed`, `missed`, `cancelled`)
- Reminder metadata and outcome notes

### 3. Medication Safety Layer

- Drug-drug interaction checks
- Contraindication detection (allergy, pregnancy, condition)
- Risk level scoring and recommendation output

### 4. Offline Sync for Rural Connectivity

- Batched device push sync
- Pull by `since` timestamp
- Conflict detection and deterministic resolution strategies

### 5. Explainability and Audit Trail

- AI decision event logging
- Model usage reporting
- Clinician override and feedback capture

## API Endpoint Map

Base URL: `/api/v1`

### Authentication

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `PUT /auth/me`
- `POST /auth/change-password`
- `POST /auth/forgot-password`

### Chat and Symptom Analysis

- `POST /chat/chat`
- `POST /chat/analyze-symptoms`
- `GET /chat/history/{session_id}`

### Triage

- `POST /triage/assess`
- `GET /triage/protocols`
- `POST /triage/escalate`
- `GET /triage/history`

### Follow-ups

- `POST /followups/schedule`
- `GET /followups/patient/{patient_id}`
- `GET /followups/pending`
- `PATCH /followups/{followup_id}`
- `PATCH /followups/{followup_id}/status`

### Medication Safety

- `POST /medications/check-interactions`
- `POST /medications/recommend`

### Offline Sync

- `POST /sync/push`
- `GET /sync/pull`
- `POST /sync/conflicts/resolve`

### Audit and Explainability

- `GET /audit/decision/{session_id}`
- `GET /audit/model-usage`
- `POST /audit/feedback`

### Vision

- `POST /vision/analyze`
- `POST /vision/xray/analyze`
- `GET /vision/analysis/{analysis_id}`
- `GET /vision/history`

### Voice

- `GET /voice/languages`
- `POST /voice/transcribe`
- `POST /voice/tts`
- `POST /voice/speak`
- `POST /voice/diagnose`

### Scheduling and User Insights

- `POST /appointments/`
- `GET /appointments/`
- `GET /appointments/{appointment_id}`
- `PUT /appointments/{appointment_id}`
- `DELETE /appointments/{appointment_id}`
- `GET /appointments/slots/available`
- `GET /users/dashboard`
- `GET /users/history/diagnoses`
- `GET /users/history/diagnoses/search`
- `GET /users/stats`
- `DELETE /users/history/diagnosis/{diagnosis_id}`

### Reporting, Export, Admin, Backup

- `GET /diagnosis/{diagnosis_id}/pdf`
- `GET /diagnoses/csv`
- `GET /diagnoses/excel`
- `GET /diagnoses/json`
- `GET /stats/overview`
- `GET /stats/diagnoses-by-day`
- `GET /stats/distribution`
- `GET /users/recent`
- `GET /diagnoses/recent`
- `POST /create` (backup)
- `GET /list` (backup)
- `POST /restore` (backup)
- `POST /rotate` (backup)

## Database Migrations Added

New Alembic revision:

- `alembic/versions/8b1d2c3a4f5e_add_clinical_workflow_tables.py`

Creates the following tables:

- `triage_assessments`
- `followup_plans`
- `medication_safety_checks`
- `sync_events`
- `ai_decision_audits`

## Tests Added

New API coverage for feature modules and edge cases:

- `tests/test_clinical_workflows.py`

Covers:

- triage assess plus escalate flow
- follow-up status transitions
- medication safety critical contraindication edge
- sync conflict detection plus merge resolution edge
- audit feedback not-found and override update flow

## Local Development

### Backend

1. Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

2. Run migrations:

```bash
alembic upgrade head
```

3. Start API:

```bash
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Suggested Next Production Steps

- Add CI pipeline to run lint, tests, and migration checks.
- Add role-based authorization policies per endpoint category.
- Add alerting rules on triage emergency rate and sync conflict spikes.
