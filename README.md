# TicketDesk

**A little help for a better workday.** An original internal-helpdesk product with a React web application and a separate FastAPI API. This repository is a clearly labelled fictional **Larkspur Studio** sandbox, not a production employee-data service.

## What it does

Employees raise IT, HR, Admin and Facilities requests, follow their own conversations, attach a file, close/reopen tickets and rate support. Agents work a shared searchable, filterable, sorted, paginated queue; bulk-assign work, send public replies, use saved replies and keep private internal notes. Administrators also manage users/roles, categories, SLA targets and saved replies, and view SQL-aggregated reports and CSV exports.

The responsive interface includes light/dark themes, in-app notifications with unread counts, history timelines, keyboard focus styles, labelled forms, loading/empty/error states and an original TicketDesk wordmark. No emails are sent.

## Two projects, one repository

- `frontend/`: Vite, React, TypeScript, React Router. Browser requests use **same-origin `/api` only**.
- `backend/`: FastAPI, SQLAlchemy, Alembic, Argon2id and psycopg. PostgreSQL in hosting, SQLite for local work/tests.
- `ARCHITECTURE.md`: architecture written before application code, including roles, schema, transitions and data flow.
- `screenshots/`: actual installed-Chrome screenshots, organised by test run.
- `bugs/`: permanent failure transcripts, diagnostics and screenshots. Failed attempts are never erased by successful retries.
- `evidence/`, `BUILDER_LOG.md`, `FINAL_REPORT.md`: verification evidence and builder experience.

Production Python is pinned to **3.14**, supported by Vercel's documented runtime and observed in the remote build (3.14.8). The final backend suite ran locally on 3.14.6. Both dependency manifests declare the same exact direct dependency pins; `uv.lock` and `package-lock.json` pin resolved dependencies.

## Run locally

From this directory, with Python 3.14 and Node 22.12+ (or a compatible newer release):

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
cd backend
../.venv/bin/python -m alembic upgrade head
../.venv/bin/python -m app.seed
DEMO_ENABLED=true FRONTEND_ORIGIN=http://localhost:5173 ../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

In another terminal:

```sh
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`. Use that exact hostname: the development CSRF origin is intentionally exact, not a wildcard. The Vite proxy forwards `/api` to `http://127.0.0.1:8000`. `API_ORIGIN` can override that target as a process environment variable. Backend configuration is read from process environment, not automatically from `.env` files. Example files are supplied locally but **all `.env` variants, including examples, are gitignored by request**; the complete non-secret templates also appear in `DEPLOY.md` for repository users.

## Demo accounts — no shared password

Use **Try the demo** on the sign-in page. There is no published demo password; the seed hashes random unknown values with Argon2id and only the explicit, configuration-gated demo endpoint grants these sandbox sessions.

| Role | Fictional people | Demo sign-in |
|---|---|---|
| Admin | Morgan Vale | Admin button |
| Agents | Jordan Reed, Casey Rowan | Agent button signs in as Jordan |
| Employees | Avery Lane, Riley Hart, Quinn Ellis, Robin Wren | Employee button signs in as Avery |

Emails are fictional addresses ending in `@demo.ticketdesk.invalid`. Seed data includes 60 tickets over 30 days, replies, private notes, statuses, ratings and SLA breaches. `python -m app.seed` is safe to run twice and refuses to mix demo accounts into an existing non-demo organisation. Demo role identities cannot be changed, so visitors cannot accidentally remove the demo entry points. Normal signup creates an employee only; administrators can manage those normal accounts.

**This is a shared public sandbox.** Visitors with demo-admin access can change shared categories and saved replies. Do not enter real personal data, credentials, attachments containing confidential information or real workplace requests. Real organisations must disable demo login, bootstrap their own admin securely and review the deployment/compliance requirements before use.

## Server-enforced roles

Every ticket read or mutation first checks ownership for employees, including comments, history and downloads; inaccessible IDs return 404. Employees cannot assign, reprioritise, write internal notes or resolve arbitrary tickets. Staff can see the shared queue. Only admins can manage configuration/users or request report aggregates/CSV. Internal notes and their private history events are filtered in SQL before an employee response is built. Notifications contain event labels, never note bodies. Changing a user's role or deactivating them revokes their sessions. The last active administrator is protected.

## SLA rules

| Priority | First response | Resolution |
|---|---:|---:|
| Low | 8 hours | 72 hours |
| Medium | 4 hours | 24 hours |
| High | 1 hour | 8 hours |
| Urgent | 15 minutes | 2 hours |

Targets are **24/7 elapsed time**, not a business-day calendar. Targets and due times are snapshotted when a ticket is created; later priority or rule changes do not reset that ticket's promise. A public staff reply records first response; an internal note does not. Waiting for requester pauses both outstanding clocks. Resolution/closure freezes resolution time, and reopening excludes the time spent in that terminal state while keeping the original budget. At risk starts at 80% of the outstanding target; breached means an outstanding or completed target was exceeded. Completed breaches remain visible.

Status transitions are enforced on the server: Open/In progress/Reopened can move through active work, waiting, resolution and closure; Waiting can return to In progress or finish; Resolved can close/reopen; Closed can reopen. Employees may only close or reopen their own ticket. Ratings are 1–5 stars, once per resolved/closed ticket, with an optional comment.

## Attachments and security

Exactly **one attachment per ticket, at most 1 MiB (1,048,576 bytes)**. PNG, JPEG, WebP and PDF only; extension, declared MIME and signature must match. A bounded request middleware also limits chunked uploads before multipart parsing. Bytes are stored in the database, not ephemeral hosting disk. Downloads require ticket authorization, force attachment disposition and use nosniff, no-store and sandbox headers. This is file-type validation, **not antivirus scanning or complete file decoding**.

Opaque sessions use HttpOnly host-only cookies, Secure in production, SameSite=Lax. Only hashes of session/CSRF tokens are stored. Unsafe requests require both an exact Origin and a session-bound CSRF header. DB-backed rate limits apply to authentication and ticket creation. Passwords use Argon2id. Request bodies and credentials are not logged; SQL parameters are hidden and database errors are sanitised. No API keys or database secrets are included in frontend code.

## Reports

SQL COUNT/AVG/SUM/GROUP BY aggregates cover open versus resolved/closed, category, priority, UTC creation-day trend, average active first-response/resolution time, completed-ticket SLA compliance, agent open workload and satisfaction. The selected date range filters tickets by creation date; averages exclude missing observations. A dash means unavailable data, not an assumed score. CSV exports these aggregates and prefixes spreadsheet-formula-like text with a quote. Workload excludes unassigned tickets and is explicitly labelled.

## Tests and cleanup

```sh
cd backend
../.venv/bin/python -m pytest
cd ../frontend
npm test
npm run build
TD_RUN=my-local-run npm run test:e2e
```

The Chrome suite uses installed Google Chrome and starts a separate API and production frontend preview on ports 8001/5174. Its SQLite file is **backend/e2e.db**, not the development or hosted database. Auth credentials are generated only in memory; no traces/HAR/session-state files are written. Every failure is captured in `bugs/`. Before a fresh local run, after servers have stopped:

```sh
.venv/bin/python backend/tools/reset_e2e.py
```

That script deletes only the hardcoded disposable E2E database and prints row counts; it never reads a hosted connection string. Backend tests use in-memory databases. For current actual test counts, failure history, live fixture inventory and screenshot captions, see `FINAL_REPORT.md` rather than assuming all historical logs passed.

## Deploy

See `DEPLOY.md` for the separate-project workflow, same-origin Vercel rewrite, free-plan restrictions, exact variables, migration/seed handling and credential safety. `/health` performs a real `SELECT 1` and returns 503 when the database query fails. No permanent-disk fallback is allowed in hosting.
