# Student Mentoring Agent — Web

Next.js (App Router) + TypeScript + Tailwind frontend for the Agent 45 mentoring platform. Replaces the previous Streamlit UI in `frontend/`.

## Setup

```bash
npm install
cp .env.local.example .env.local   # point NEXT_PUBLIC_API_BASE_URL at the backend
npm run dev                        # http://localhost:3000
```

The backend (`../backend`) must be running with a real Postgres database migrated
(`alembic upgrade head`) and at least one user with a password set via
`POST /auth/password` or `/auth/bootstrap-admin` — this app authenticates with
real email/password login against that backend, the same as the previous
Streamlit app did.

## Structure

- `src/lib/api.ts` — typed fetch client for every backend endpoint used by the UI
- `src/lib/auth.tsx` — auth context (token + user in `localStorage`), role-based home routing
- `src/lib/hooks.ts` — SWR data hooks per page
- `src/components/` — shared UI (Sidebar, cards, badges, states) and the mentee-detail form
- `src/app/<role>/...` — one route tree per role (student, mentor, hod, counsellor), plus
  shared `/reports` and `/announcements`

## Roles → routes

| Role | Home | Other routes |
|---|---|---|
| student | `/student/dashboard` | `/student/meetings`, `/student/actions`, `/student/messages` |
| mentor | `/mentor/dashboard` | `/mentor/mentees`, `/mentor/mentees/[id]`, `/mentor/actions`, `/mentor/alerts` |
| hod / admin | `/hod/dashboard` | `/hod/allocations`, `/hod/audit`, `/reports` |
| counsellor | `/counsellor/dashboard` | `/reports` |

All roles can reach `/announcements`.
