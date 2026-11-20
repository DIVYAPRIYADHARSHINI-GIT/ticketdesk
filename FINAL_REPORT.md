# TicketDesk — Final Build and Verification Report

20 November 2026 · Asia/Kolkata (IST)

## 1. Project overview

TicketDesk is an original, functional office-helpdesk demonstration. Employees raise requests and follow their own conversations; agents work a shared queue; administrators manage the workspace and see service reports. The name, wordmark, illustrations, interface and application code were created for this project. No real helpdesk product's brand or code was copied.

The project is isolated in `ticketdesk`, with separate `frontend` and `backend` projects in one repository. `ARCHITECTURE.md` was written before application code. The frontend uses Vite, React and TypeScript. The backend uses FastAPI, SQLAlchemy, Alembic and Argon2id, with PostgreSQL in hosting and SQLite locally. Production Python is pinned to supported 3.14; final local backend tests used 3.14.6 and Vercel used 3.14.8.

**Live application:** https://ticketdesk-frontend-psi.vercel.app

**Backend health:** https://ticketdesk-backend.vercel.app/health

**Public GitHub repository:** https://github.com/DIVYAPRIYADHARSHINI-GIT/ticketdesk

The repository is public, its branch is `main`, and the project-local Git identity is Divya Priyadharshini / divyapriyadharshini@softage.ai. The two Vercel projects are `ticketdesk-backend` and `ticketdesk-frontend`, under the verified Divya Hobby account. The new Neon resource is `ticketdesk-db`, created on the explicitly selected Free plan in Singapore. No payment details or paid upgrade were used. These are fictional, non-commercial demo resources, not a claim that a commercial office service is eligible for Hobby.

Completed functionality includes signup/sign-in and role-specific demo entry, employee ownership checks, ticket creation, comments, database attachments, status and priority controls, assignment and bulk assignment, private notes, saved replies, history, SLA deadlines and pause/resume, ratings, in-app notifications, queue filters/sorting/pagination, admin management and SQL-aggregated reports/CSV. Light and dark themes, mobile layouts, labelled inputs, focus styles and loading/empty/error states are included. No emails are sent.

The seed script creates the clearly labelled fictional Larkspur Studio organisation: one admin, two agents, four employees and 60 requests over 30 days. All seeded email addresses use the reserved `.invalid` domain. Demo passwords are random unknown values that are hashed, never printed or published; demo login is an explicit configuration-gated sandbox feature. Seed reruns were verified to make no duplicate data.

### Security and cross-domain deployment

Server authorization applies to ticket reads and mutations, comments, history and attachment downloads. Employee access is scoped in SQL before fetching data. Internal notes and their private history entries are excluded from employee responses. Admin-only endpoints reject both employees and agents. Passwords use Argon2id. Sessions are opaque and only their hashes are stored. Unsafe requests require an exact allowed Origin and a session-bound CSRF header. Login and ticket-creation limits are stored in the database rather than process memory.

Attachments are limited to one file per ticket and 1,048,576 bytes, with PNG/JPEG/WebP/PDF extension, MIME and signature checks. An early body bound also protects chunked requests and extra multipart parts are rejected. Downloads are authorized and forced as attachments, with nosniff, no-store and sandbox headers. This is not antivirus scanning.

The browser calls only same-origin `/api`. Vercel rewrites that path to the separate backend project. Live Chrome verified a host-only Secure, HttpOnly, SameSite=Lax cookie on the frontend domain, session persistence across reload, and API requests staying entirely on the frontend origin. Chrome was launched with its third-party-cookie phaseout test flag; the solution does not require third-party cookies. No CORS or unexpected JavaScript console errors occurred in the final live suite.

Migrations and seed ran inside Vercel's build environment through `uv run --python 3.14 python -m app.prepare`, using the integration-injected connection. Production database secrets were not pulled to the local machine. The public backend `/health` returned HTTP 200 with `status: ok` and `database: connected` after executing a real query. A unit test also proves database failure returns 503.

## 2. Testing and evidence

### Final suite results

The final suites contain **171 passing test cases**, with **zero final test failures**. This is 123 backend cases, 30 frontend cases, 10 local Chrome journeys and 8 live Chrome journeys. Earlier attempts did fail; their real results and permanent records follow below. Accessibility audits are part of the browser journeys and are not added again to that total.

| Suite | Passed | Failed | Actual scope and evidence |
|---|---:|---:|---|
| Final backend pytest, Python 3.14 | 123 | 0 | Roles/IDOR, private-note isolation, all status pairs, SLA pause/resume and SQL parity, history, files, notifications, CSRF/auth, rate limits, aggregates, CSV and seed. `evidence/backend-final.txt` |
| Frontend Vitest | 30 | 0 | Component semantics, loading/error states, formatting, upload prechecks and four saved-reply regressions. `evidence/composer-unit.txt` |
| Local real-Chrome journeys | 10 | 0 | Normal signup/sign-in, all three roles, attachment, queue/bulk actions, private/public replies, resolution/rating/reopen, admin changes, CSV, mobile, dark and keyboard entry. `evidence/local-composer-browser.txt` |
| Live real-Chrome journeys | 8 | 0 | Actual Vercel frontend/backend and Neon DB, all roles, Secure cookie/rewrite, attachment, private notes, resolution/rating/closure, reports/export, admin pages and mobile/dark. `evidence/live-third-browser.txt` |
| Local axe page/state audits | 18 | 0 violations | WCAG 2 A/AA and 2.1 A/AA rules in the browser. `evidence/local-composer-axe-*.json` |
| Live axe page/state audits | 16 | 0 violations | Live public, auth, employee, agent, admin, reports and mobile/dark views. `evidence/live-third-axe-*.json` |
| TypeScript and production build | Successful | 0 errors | Final composer build and both hosted projects built successfully. `evidence/composer-build.txt` and deployment logs |
| Final npm dependency audit | Completed | 0 vulnerabilities | Zero informational, low, moderate, high or critical findings. `evidence/npm-audit-final.json` |

Axe's zero findings are an automated audit result, **not a complete accessibility certification**. Manual screen-reader testing, every keyboard interaction and other browser engines were not exhaustively tested. The backend suite reports one third-party TestClient/httpx deprecation warning; it is not hidden as an error-free dependency ecosystem.

### Historical stage and retry results

| Stage/run | Passed | Failed or blocked | Not run |
|---|---:|---|---:|
| Database foundation | 9 | 0 | 0 |
| First full backend stage | 114 | 0; 70 dependency deprecation warnings | 0 |
| Backend hardening stage | 122 | 0; 1 dependency warning after dependency update | 0 |
| First Python 3.14 command | 0 executed | Collection error: wrong working directory | All cases |
| Python 3.14 correct-folder rerun | 123 | 0 | 0 |
| Initial frontend suite | 26 | 0 | 0 |
| Local Chrome first | 3 | 1: exact label locator | 6 |
| Local Chrome second | 3 | 1: invalid SLA definition list | 6 |
| Third local attempt | 0 executed | TypeScript Page-version conflict before browser launch | All journeys |
| Local Chrome fourth | 6 | 1: ambiguous save-status locator | 3 |
| Local Chrome fifth | 10 | 0 | 0 |
| Local Chrome populated-screenshot rerun | 10 | 0 | 0 |
| Local Chrome after composer fix | 10 | 0 | 0 |
| Live Chrome first | 2 | 1: saved-reply composer stalled | 5 |
| Live Chrome second | 2 | 1: stall reproduced | 5 |
| Live Chrome after composer fix | 8 | 0 | 0 |

The first Python dependency install failed, the first npm upgrade failed dependency resolution, and the first two backend deployments failed configuration/build checks. They are not counted as passing tests. Their transcripts remain under `bugs`. Backend deployment three and the exact-origin redeployment succeeded; both frontend deployments succeeded. The first successful backend build also confirmed the seed remained unchanged after the earlier successful database-preparation step.

### Live testing screenshots

These are real screenshots from installed Google Chrome against the deployed product, captured in the successful `live-third` run. Each caption states what the image shows. Earlier screenshots, including failures and a prematurely captured loading screen, are retained separately rather than replaced.

![Live home page — original TicketDesk identity, explanatory hero and explicitly illustrative preview.](screenshots/live-third/01-home.png)

![Live sign-in — normal authentication form and three clearly labelled fictional demo-role entry points.](screenshots/live-third/02-sign-in.png)

![Live employee list — Avery Lane's requests only, server-side filters, priorities and SLA states.](screenshots/live-third/03-employee-ticket-list.png)

![Live new-request form — category, priority, description and the clearly stated one-file / 1 MB attachment limit.](screenshots/live-third/04-new-ticket-form.png)

![Live ticket detail — TD-1063, database attachment link, conversation and on-track SLA deadlines.](screenshots/live-third/05-ticket-detail-sla.png)

![Live agent queue — populated shared queue with search, filters, selection, assignment context and pagination.](screenshots/live-third/06-agent-queue.png)

![Live internal note — staff-only conversation entry; the employee journey separately verified that this text was absent.](screenshots/live-third/07-agent-internal-note.png)

![Live SLA pause — waiting for the requester pauses outstanding service clocks.](screenshots/live-third/08-sla-paused.png)

![Live history timeline — assignment, replies and status changes carry an actor and timestamp.](screenshots/live-third/09-history.png)

![Live notifications — status/reply events and unread indicators, without email delivery.](screenshots/live-third/10-notifications.png)

![Live resolution feedback — the requester rated the support and closed the verification ticket.](screenshots/live-third/11-closed-and-rated.png)

![Live reports in light theme — real SQL aggregates from the fictional dataset, date range and CSV export.](screenshots/live-third/12-reports-light.png)

![Live reports in dark theme — the same report data after theme persistence across a reload.](screenshots/live-third/13-reports-dark.png)

![Live admin people and roles — protected fictional identities; normal-account role changes were exercised locally.](screenshots/live-third/14-admin-users.png)

![Live admin categories — the four support teams, names and active-state controls.](screenshots/live-third/15-admin-categories.png)

![Live admin SLA rules — first-response and resolution targets by priority, with snapshot and pause explanations.](screenshots/live-third/16-admin-sla.png)

![Live admin saved replies — seeded reusable responses and create/edit controls.](screenshots/live-third/17-admin-saved-replies.png)

![Live mobile home — 390-pixel viewport capture, not a simulated design mockup.](screenshots/live-third/18-mobile-home.png)

![Live mobile employee workspace — responsive navigation, request action, counters and filters.](screenshots/live-third/19-mobile-workspace.png)

![Live mobile dark theme — responsive workspace with separately tested dark colours.](screenshots/live-third/20-mobile-dark.png)

### Test-data inventory and cleanup

All local browser-test accounts, tickets, attachments and configuration fixtures were deleted by removing only the hardcoded disposable `backend/e2e.db`, after the test servers stopped. The final cleanup recorded 8 users, 61 tickets, 72 comments, 1 attachment, 196 history rows, 21 ratings, 5 categories and 4 saved replies in that disposable database. Those counts include its independent copy of the demo seed. `evidence/e2e-composer-final-cleanup.txt` records the deletion. Backend pytest databases were in memory. The normal local development demo database was not deleted.

The user allowed live test data to be listed instead of deleted. **Three live verification tickets are intentionally retained and explicitly inventoried below.** They use existing fictional demo accounts; no new live user account was created. Their attachments and comments contain only labelled fictional test text.

| Ticket | Exact test title | Final observed state |
|---|---|---|
| TD-1061 / ID 61 | LIVE E2E TEST — fictional headset check 1795168640064 | Open, assigned to Jordan; first failed journey left an internal test note and test PDF |
| TD-1062 / ID 62 | LIVE E2E TEST — fictional headset check 1795168828128 | Open, assigned to Jordan; second failed journey left an internal test note and test PDF |
| TD-1063 / ID 63 | LIVE E2E TEST — fictional headset check 1795169019589 | Closed after public reply, waiting/resolution, 5-star test rating and test PDF |

Each uses `live-e2e-fictional.pdf`. The existing demo identities used were Avery Lane, Jordan Reed and Morgan Vale. Machine-readable inventories are `evidence/live-first-test-data.json`, `live-second-test-data.json` and `live-third-test-data.json`. No test data was inserted into any pre-existing production database or other project.

## 3. Bugs, issues and permanent failure records

### Runtime and dependency problems

**001 — Runtime mismatch.** The initial command reported Python 3.11.15, while the first virtual environment actually ran 3.15.2. This was recorded rather than calling it hosting parity. Later uv found installed 3.14.6, and the final backend suite passed on that supported runtime line. Production is pinned to 3.14 and the remote build reported 3.14.8. Records: `bugs/001-runtime-version-diagnostic.md`, `001-runtime-version-followup.txt` and the 023 follow-up. Resolved at the supported minor-version level; patch versions differ.

**002 — Unavailable PostgreSQL driver pin.** The first install could not obtain psycopg-binary 3.2.9. Both manifests were changed to the same available 3.3.9 pin, and installation succeeded. Original transcript: `bugs/002-dependency-install.txt`.

**006/007 — Dependency vulnerabilities and failed upgrade.** Initial npm installation reported five vulnerabilities, including one critical. The complete audit was retained. Updating Vite, React Router and Vitest encountered an ERESOLVE conflict against the old installed tree. A clean local resolution, without forcing incompatible peers, succeeded. Final audit reports zero findings. Records: `bugs/006-initial-npm-audit.json` and `007-frontend-install-patched.txt`.

**014/015 — Browser test tool mismatch and an inspection error.** TypeScript detected that pinned Playwright and axe's newer playwright-core exposed different Page types. Playwright was aligned to 1.65.1; the build then passed. A diagnostic `require` of an unexported package.json subpath also failed and was recorded rather than omitted. Records: `bugs/014-browser-build-type-mismatch.txt` and `015-package-inspection-tool-error.txt`.

**023 — Wrong working directory for the matched-runtime test command.** uv created the intended local environment, but the root-directory pytest invocation could not import the backend app. Running from `backend` fixed collection and all 123 cases passed. Records: `bugs/023-python314-tests.txt` and its follow-up. This was a builder command error, not a failed business-rule assertion.

### Application, accessibility and browser issues

**008 — Upload envelope gaps found in source review.** The initial endpoint bounded the file after multipart parsing and trusted Content-Length for its early check. Chunked requests and multiple file parts needed an earlier guard. A bounded ASGI body middleware and exactly-one-part check were added, with passing regression tests. Record: `bugs/008-upload-review-diagnostic.md`. This record is labelled as review evidence, not a fabricated failed test.

**011 — Exact label query stalled the first Chrome journey.** The browser accessibility tree showed a valid Category combobox, but the test's exact label-text query did not match the nested label implementation. The test now targets the accessible role and name. The first run's failure screenshot and transcript remain. Record: `bugs/011-browser-locator-followup.md` and `011-local-first-browser.txt`.

**012 — Invalid definition-list markup.** Axe found one serious issue in the SLA inspector: target text was a small element outside its associated definition. Moving it inside the dd restored valid semantics. Subsequent local and live audits passed. Diagnostic: `bugs/local-second-axe-ticket-detail.json`.

![Accessibility failure evidence — the original ticket detail whose SLA definition list produced one serious axe finding; its visual appearance alone did not reveal the semantic defect.](bugs/local-second-axe-ticket-detail.png)

**013 — Rejected source patch.** A mistaken placeholder patch was submitted during the accessibility fix. Designer rejected it because the hunk did not exist; no source was changed. Exact replacements were then used. Record: `bugs/013-patch-tool-error.txt`. This is an AI builder editing mistake, not an application bug.

**017 — Ambiguous test status region.** During admin refetch, the test briefly found both loading and success status regions. Its unqualified locator failed even though the mutation succeeded. The assertion was scoped to the success content. Record: `bugs/017-admin-test-status-followup.md` and the matching local-fourth failure artifacts.

**021 — Portability and keyboard findings.** Review found PostgreSQL's floating-point integer-cast rounding could put late-day requests in the next UTC bucket. SQL FLOOR now precedes CAST and an end-of-day regression passes. Review also found offscreen mobile navigation remained focusable; closed navigation now uses visibility hiding. Record: `bugs/021-portability-and-mobile-review.md`.

**022 — Premature screenshot.** Visual inspection caught a queue screenshot showing its loading state rather than the populated table. Screenshot helpers now wait for loading spinners to disappear before both capture and audit. Earlier images remain unchanged. Record: `bugs/022-screenshot-readiness-review.md`.

**032/033 — Saved reply stalled only in the complete live sequence.** The first two live runs reached agent assignment and an internal note, then left an empty composer after choosing a saved reply. A standalone check on the same site did populate an 85-character reply, so the exact low-level event ordering was not proven. The implementation nevertheless had fragile imperative select resetting, empty-choice draft clearing and editable controls during a pending send.

The composer was extracted into a component with a controlled picker that ignores empty choices, pending-send controls are disabled, and completion clears only the submitted draft. Four new unit regressions and all local journeys passed. After redeploying, the entire live suite passed all eight journeys, including saved reply, public response, resolution and rating. The observed failure is resolved in the final tested build; the precise original browser event race remains an inference, not a claimed measurement. Records: `bugs/032-live-first-browser.txt`, `033-live-second-browser.txt`, diagnostic metadata and both follow-ups.

![First live failure — the saved-reply action left the composer empty and Send reply disabled; the screenshot is retained even though the final build passed.](bugs/live-first-03-agent-queue-assignment-public-reply-internal-note-and-resolution.png)

![Repeated live failure — the second run reproduced the empty composer on TD-1062 before the controlled-picker fix.](bugs/live-second-03-agent-queue-assignment-public-reply-internal-note-and-resolution.png)

### Deployment and tool-side issues

**016 — Automatic credential-file side effect.** Vercel link automatically created `.env.local` with an OIDC credential for each new project. Neither file was opened or read; both were immediately deleted and ignored. The owner was informed. No credential value was committed or printed. The Neon provisioning command used `--no-env-pull`. Records: `bugs/016-automatic-credential-file.txt` and `016-frontend-link-followup.txt`.

**018 — Managed Python build failure.** The first backend build redundantly ran pip against Vercel's uv-managed interpreter and PEP 668 rejected it. The fix was to use the supported uv environment, not `--break-system-packages`. Record: `bugs/018-backend-deploy-first.txt` and its follow-up.

**019 — Incorrect static-framework detection.** The second build successfully migrated and seeded PostgreSQL, then expected a static `public` directory. Declaring `framework: fastapi` fixed the project classification. The next deployment and exact-origin redeployment succeeded, and seed remained unchanged. Record: `bugs/019-backend-deploy-second.txt` and its follow-up.

Native Chrome allocator/display-link warnings appeared in a failed-run browser-process transcript. Final JavaScript console monitoring recorded zero unexpected errors, but that does not imply those native platform warnings were fixed. Vercel emitted an npm cache-config warning and dependency deprecation notices in successful builds; these are retained in deployment logs. Public production aliases worked without Vercel login despite the CLI's generic Deployment Protection notice.

All failures, retries and review findings above have retained records. A missing numbered file means no failure record was created for that reserved command, not that an existing failure was removed. No failure screenshot was renamed or deleted.

## 4. Advantages of Designer, based on this build

Designer let the builder create the architecture, two application projects, tests and documentation inside one clearly scoped folder. File-edit tools returned revision identifiers and rejected a bad exact patch instead of silently changing unrelated text. This was useful for preserving the surrounding project collection.

Background shell tasks made it possible to run installations, tests and deployments while preparing independent documentation. Their real exit codes and output were available for evidence, so a successful build was not confused with a successful health check or browser journey.

The editor's image-observation tool made actual Chrome screenshots inspectable in the same workflow. That visual review caught the prematurely captured queue image and supported checks of the home, live ticket detail, light/dark reports and mobile layout. The tool was useful for verifying output, not merely generating code.

Permission questions produced separate explicit decisions before GitHub, Vercel and database access. The existing authenticated CLIs and supported Neon integration allowed publication on the selected free plans without asking the owner to paste a token or connection string into chat.

## 5. Disadvantages and limits of Designer, based on this build

The workflow still required careful manual coordination across local runtimes, package versions, Vercel framework selection and a separate database. Designer did not automatically prevent the mismatched initial Python environment, stale npm peer tree or managed-interpreter build mistake. Those were discovered through real checks and corrected by the builder.

Long command outputs could be truncated in the tool excerpt, so full evidence files and additional output reads were necessary. Browser interaction assertions and screenshot timing also required explicit orchestration; an early image showed loading, and a live-only composer stall required multiple attempts and a separate diagnostic.

External CLI behavior was not fully predictable. `vercel link` automatically created a credential file despite no explicit environment-pull command, and environment-list output showed encrypted/truncated config previews rather than being purely names-only. The files were deleted unread, but this is an important safety limitation when strict no-local-secret handling is required.

Public documentation search summaries were inconsistent about some runtime/proxy/plan details. The report therefore relies on actual CLI plan selection, observed runtime/build output and live browser behavior where available, and does not invent precise quotas from those summaries. A package metadata lookup earlier omitted the local npm-cache flag and may have used npm's default metadata cache; subsequent calls used the project cache. No sibling project was inspected or modified.

The final source is functional and separated by responsibility, but some generated JSX/CSS remains densely formatted. It would benefit from a consistent formatter and further component decomposition before long-term team maintenance. This is a code-maintainability limitation, not hidden behind passing tests.

## 6. Scope for improving future Designer versions

A secret-aware CLI wrapper could detect commands that automatically download credentials, block or sandbox those side effects, and redact values while preserving names and failure reasons. In this build that would have avoided the two automatic `.env.local` incidents and the need to reason about environment-list previews.

A runtime/deployment preflight could compare the actual interpreter, project pin, dependency manifests, lockfile and hosting framework before the first deploy. A supported FastAPI-plus-frontend-rewrite recipe could flag static-project detection and avoid redundant system pip commands.

A first-class evidence journal could automatically retain immutable failure logs/screenshots, group retries and calculate honest final-versus-historical counts. A browser capture helper that waits for populated views and offers readable mobile viewport images would reduce premature or excessively tall screenshots.

Richer source-edit batching and built-in formatting could make generated application code easier to maintain while preserving revision checks. A deployment/browser verification panel could make the distinction between build success, real database health, cookie correctness and completed role journeys more explicit.

## 7. What remains unverified and TicketDesk's known limits

This is a **single-organisation fictional sandbox**, not a security certification or enterprise production rollout. Demo users are shared, and demo admins can change shared configuration. Confidential HR or office data should not be entered. Real use needs organisation onboarding, an appropriate hosting plan, isolation/retention policies, backups, monitoring and a security review. Demo-role protection is an intentional exception to unrestricted admin editing of those sandbox identities.

The full backend suite used SQLite, not a separate automated PostgreSQL test database. The live workflows did exercise real PostgreSQL migrations, seed, authentication, reads/writes, attachments and aggregate reports. Cross-database concurrency, deadlock behavior, large-scale load, quota exhaustion, backup restoration and sustained uptime were not exhaustively tested. No load capacity or cold-start latency guarantee is claimed.

Only installed Chrome was used for automated end-to-end verification. Safari, Firefox, assistive-technology sessions and a complete manual keyboard audit are not verified. The third-party-cookie phaseout launch flag was recorded; the stronger directly observed fact is that all browser API requests and the session cookie used the frontend origin.

SLA targets use 24/7 elapsed time, not office calendars or holidays. Priority changes preserve the original target. SLA badges refresh when ticket data is fetched, not through a background scheduler. Notifications poll every 30 seconds. The users list is capped at 1,000 entries. Password reset, email, SSO, multitenancy, antivirus scanning and external attachment storage are not implemented.

Attachment signature checks do not prove a file is harmless or fully decodable. One 1 MiB database attachment per ticket still consumes finite free storage. Cold starts and idle database wake-up are expected free-hosting constraints. No paid upgrade was made, and no promise is made that a real commercial deployment qualifies for Vercel Hobby.

The GitHub repository and both Vercel projects are published, but GitHub-triggered automatic deployment is **not connected or verified**; the verified deployments were performed through the CLI. Future source changes require the documented deploy steps or an explicitly configured Git integration with the correct project root directories.

Three live verification tickets remain, deliberately listed above. All disposable local test data was deleted. Every failure record remains available. The report PDF is generated from this Markdown and the actual screenshot files; its export and visual inspection are recorded alongside the final delivery.
