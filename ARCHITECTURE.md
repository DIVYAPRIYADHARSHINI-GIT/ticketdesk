# TicketDesk architecture — implementation plan

Written before application code, 20 November 2026 (Asia/Kolkata).

## Boundary and stages
All work belongs to this isolated directory. No sibling project may be read or modified. Local runtime/dependency/browser checks are approved. Database creation needs a separate approval. GitHub, Vercel and hosted database/environment access each require a separate explicit yes. Use only free plans; never supply payment details or retrieve production secrets.

1. Architecture, tooling and database foundation; migration and schema tests.
2. Secure API and domain logic; backend role, SLA, upload, reporting and security tests.
3. Responsive React interface; component/unit tests, typecheck and production build.
4. Real Chrome role journeys, accessibility, mobile/dark checks and screenshots; keep every failure transcript in bugs/.
5. Permission-gated publication and live verification, if approved and feasible.
6. README, deployment instructions, running builder log and final report/PDF with actual evidence.

## Repository structure
- frontend/: Vite + React + TypeScript, src/, tests/, package.json, vercel.json, .env.example.
- backend/: FastAPI + SQLAlchemy, app/{models,schemas,security,domain,main,seed}.py, migrations/, tests/, requirements.txt and pyproject.toml with matching pinned dependencies, .python-version, .env.example.
- screenshots/: actual browser captures, never illustrations presented as captures.
- bugs/: immutable numbered diagnostic records and failure screenshots.
- evidence/: test logs and machine-readable results (no credentials).
- ARCHITECTURE.md, BUILDER_LOG.md, README.md, DEPLOY.md, FINAL_REPORT.md.

## Product and visual direction
Original TicketDesk wordmark and simple geometric ticket icon. Quiet navy/ink, indigo actions, cool white surfaces, distinct accessible dark tokens. Desktop left navigation, responsive mobile navigation, strong headings, concise supporting text, labelled inputs, visible focus and text alongside status colours. Persistent fictional-demo notice. No third-party brand or code copied.

## Database
PostgreSQL in hosting; SQLite locally and in isolated tests. SQLAlchemy portable ORM and Alembic migrations. Store UTC timestamps as epoch seconds to keep arithmetic and aggregate semantics identical on both engines. Use integer primary keys and derive TD-(1000+id) numbers.

Tables: users (name, unique email, role, Argon2id password hash, active, demo); sessions (hashed opaque session identifier, hashed CSRF secret, user, expiry); categories (unique name, active); sla_rules (priority, response/resolution minutes); tickets (requester, assignee, category, title, description, priority/status, creation/update/response/resolution times, due times, waiting_since, paused seconds, snapshot targets); comments (ticket, author, body, internal); attachments (unique ticket FK enforcing one lifetime attachment, safe filename, MIME, bytes <= 1 MiB); history (ticket, actor, field, old/new values, timestamp, internal flag); notifications (recipient, ticket, safe event kind, read time); ratings (unique ticket, author, stars, optional comment); saved_replies; rate_buckets (hashed key, fixed-window count); seed_markers (idempotence).

Indexes: queue status/priority/category/assignee/created, requester/created, response and resolution due times; comments/history ticket+time, notifications recipient+read time; expiring sessions and rate buckets. Foreign keys, unique constraints, bounded strings and check constraints complement strict request validation. Row locks serialize changes to a ticket in PostgreSQL; SQLite tests run serially.

## Server role rules
All endpoints default to authentication except health and CSRF/auth bootstrap. Public signup always creates employee; no role input accepted. Employee queries add requester=user predicates before fetching; inaccessible ticket IDs return 404, including comments/history/attachment endpoints. Internal notes are filtered at SQL query level and their text never appears in public history or notifications. Employees can create tickets, reply/upload on their own tickets, close or reopen them according to transitions, and rate a resolved/closed own ticket. They cannot assign, reprioritize, change arbitrary status or write internal notes.

Agents and admins see the shared queue, assign to active agents/admins, change priority/status, post public replies/internal notes and use saved replies. Only admins manage users/roles, categories, SLA rules and saved replies, and access reports/CSV. Do not permit removal/demotion of the final active admin. Demo accounts are explicitly fictional; demo authentication is enabled only by configuration. A public demo is a sandbox, not an access path into a real organisation.

## Status and SLA
Open -> In progress / Waiting for requester / Resolved / Closed.
In progress -> Waiting for requester / Resolved / Closed.
Waiting for requester -> In progress / Resolved / Closed.
Resolved -> Closed / Reopened. Closed -> Reopened. Reopened -> In progress / Waiting for requester / Resolved / Closed.
Employees may only close an active/resolved own ticket or reopen a resolved/closed own ticket. First public staff reply records first_response_at once; internal notes do not. Resolved/Closed freezes resolution clock; reopening clears current resolved time and resumes against original target with time in terminal states excluded. Every transition is audited. SLA targets are snapshots at creation; priority changes do not silently rewrite contractual targets (shown in UI/docs). Waiting pauses BOTH outstanding clocks, shifting deadlines on resume. Active pause is included dynamically for badge/filter/report calculations. At risk means >=80% of the relevant active-time target consumed; breached means outstanding or completed deadline exceeded. Completed obligations retain breach history. 24/7 elapsed-time rules, not business calendars.

## Authentication and cross-domain flow
Browser calls only same-origin /api. Local Vite proxy sends /api to the local API. Production frontend Vercel rewrite forwards /api/:path* to the separate backend domain /api/:path*. Backend also exposes /health. Cookie is host-only, HttpOnly, Secure in production, SameSite=Lax, Path=/; never set a Domain attribute. Therefore the browser stores the proxied cookie on the FRONTEND host and third-party cookie blocking is irrelevant. Exact FRONTEND_ORIGIN is checked for every unsafe request. CSRF bootstrap returns a short-lived secret bound to an HttpOnly bootstrap/session cookie; every unsafe fetch includes X-CSRF-Token. Auth rotates the session. Persist only hashes in DB, never log tokens or request bodies. Development permits insecure cookies only on loopback. CORS is restricted to one configured frontend origin, never wildcard credentials.

Passwords never printed or written as plaintext; Argon2id hashes only. Demo accounts use random unknown passwords and explicit role demo endpoints. Tests generate passwords in process. DB-backed fixed-window rate limits on login/signup/demo and ticket creation survive serverless instance recycling; keys are hashed. Safe generic errors; no request-body logging. Health performs SELECT 1 and returns failure if DB unavailable.

## Attachments and notifications
Exactly one attachment per ticket, <=1,048,576 bytes, PNG/JPEG/WebP/PDF only. Check extension, declared MIME and file signature, reject SVG/HTML/executable formats, sanitize filename; download only after ticket authorization with attachment Content-Disposition, nosniff, private/no-store and restrictive CSP. No external object storage or ephemeral-disk dependency. Streaming input is bounded before full buffering. This is not antivirus scanning and is documented.

Assignments, public replies and status changes create in-app notifications transactionally; internal notes never notify requesters. No email. UI polls notifications with unread count and supports mark-read.

## Reports and data flow
React form -> same-origin typed fetch + CSRF -> strict Pydantic schema -> session/role check -> transactional domain change -> history/notification rows -> response. Ticket list uses server-side search/filter/sort/pagination and computed SLA SQL expressions. Bulk assignment is bounded and atomic. Reports are SQL GROUP BY/COUNT/AVG/SUM over the chosen UTC date range: status/category/priority/day, first response and resolution active durations, completed SLA compliance, agent workload, satisfaction. CSV streams aggregate rows, neutralizing spreadsheet formula prefixes (=,+,-,@, tabs, CR/LF including leading whitespace). No loading all tickets into Python for reporting.

## Test and evidence strategy
Isolated temporary SQLite for pytest; test all roles and IDOR paths, note leakage, status graph, pause/resume, history, notifications, file size/type/header rules, CSRF/session security, rates and known-value report/CSV fixtures. Frontend unit tests cover labels and helpers. Real installed Chrome via Playwright uses a separate local E2E DB with visibly named E2E tickets/accounts. Test employee create -> agent reply/resolve -> employee rate, admin CRUD/report/export, cookies across reload, dark/mobile/layout and axe audits. Capture every failure permanently before fixing; report first-run failures separately from final successful suites. Never claim PostgreSQL/live/cross-Vercel validation without actually running it. No production test data unless separately approved; list or remove any test fixtures.

## Deployment readiness
Check current official Vercel Python support before pinning. Same dependency pins in both manifests. Frontend API proxy target configured at build, never expose secrets through VITE_ variables. Environment examples are documentation only and gitignored per user request. All env variants, databases, venvs, caches, tokens, local Vercel metadata and generated large files ignored. No hosted credentials read or downloaded. Migration/seed require an explicitly approved connection provided through the service dashboard or secure process environment. Public demo hosting is conditional on free-plan personal/non-commercial eligibility and limits.

## Implementation refinements recorded after the initial plan
- Final supported runtime is Python 3.14: local verification on 3.14.6, Vercel native FastAPI build on 3.14.8. Direct dependency pins match across both manifests; uv.lock also records resolution.
- Migrations and seed run in the remote Vercel build with `uv run --python 3.14 python -m app.prepare`. Credentials remain injected on the host; they are never pulled to local files. Explicit framework=fastapi avoids a static-project misclassification. Both the backend runtime and Neon are in Singapore.
- Request bodies are bounded to a 1,100,000-byte envelope before parsing; the exact file limit remains 1,048,576 bytes. Uploads reject multiple multipart parts.
- PostgreSQL/SQLite UTC day grouping explicitly applies SQL FLOOR before integer conversion. CSV is assembled from bounded aggregate rows, not streamed from raw tickets. All report calculations remain SQL aggregations.
- The public demo is single-organisation, not multitenant. Demo role identities are protected from role/deactivation changes. The users screen currently caps its list at 1,000 users.
- Actual deployed frontend origin is https://ticketdesk-frontend-psi.vercel.app; backend is https://ticketdesk-backend.vercel.app. GitHub repository is https://github.com/DIVYAPRIYADHARSHINI-GIT/ticketdesk. Live browser verification is reported separately in FINAL_REPORT.md.
