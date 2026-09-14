# Student Mentoring Agent (Agent 45)

A mentoring platform that turns faculty–student mentoring into a continuous,
measurable workflow: balanced mentor allocation, AI-assisted pre-meeting
briefs with cited evidence, structured meeting notes, action-item tracking,
deterministic escalation routing, and institutional compliance reporting.

## Structure

- `backend/` — FastAPI + SQLAlchemy + Alembic + Postgres. All business rules
  (RBAC, escalation routing, compliance math) are deterministic; an LLM
  (Groq) is used only for optional action-item extraction from a meeting
  transcript, with a graceful fallback if no API key is configured.
- `web/` — Next.js + TypeScript + Tailwind frontend (the only frontend; the
  original Streamlit UI has been removed in favor of this one).

The backend optionally enriches student briefs from a shared institutional
Postgres schema (`people.v_student_profile`, `agentops.v_open_flags`, etc. —
see `backend/app/institutional.py`) owned by other agents in this system. It
degrades gracefully to the mentoring app's own data when that schema isn't
present, so it is not required to run Agent 45 on its own.

## Running locally

### 1. Database

```bash
# create a Postgres database, then from backend/:
cp .env.example .env         # fill in DATABASE_URL, AUTH_SECRET, etc.
alembic upgrade head
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Create your first login with the bootstrap endpoint (needs `AUTH_BOOTSTRAP_TOKEN`
set in `.env`):

```bash
curl -X POST http://localhost:8000/auth/bootstrap-admin \
  -H "x-bootstrap-token: <AUTH_BOOTSTRAP_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.edu", "password": "a-long-password"}'
```

`AUTH_ALLOW_DEV_HEADER` defaults to `false`; only set it `true` in your own
local `.env` if you want to authenticate via an `x-user-id` header instead of
a password (never in a shared/deployed environment).

### 3. Frontend (web)

```bash
cd web
npm install
cp .env.local.example .env.local
npm run dev     # http://localhost:3000
```

Log in with the account you created above.

## Tests

```bash
cd backend
AUTH_ALLOW_DEV_HEADER=true pytest
```

The tests are integration tests against a migrated, seeded Postgres database
(see `backend/tests/test_member1.py` for the expected seed shape).
