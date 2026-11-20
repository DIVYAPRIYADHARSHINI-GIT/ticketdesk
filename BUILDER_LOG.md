# Builder experience log

## 20 November 2026 — Stage 0 (Asia/Kolkata)
- User explicitly approved local runtime checks, public dependency downloads/documentation and installed Chrome testing. Separately approved local SQLite only. No GitHub, Vercel or hosted database account permission yet.
- Wrote ARCHITECTURE.md before application code. Kept all writes in the new ticketdesk directory; did not inspect sibling projects.
- Runtime check succeeded: Node 26.13.1, npm 11.20.0, Python 3.11.15, installed Google Chrome available. Python 3.12/3.13 were not found via command lookup. This is a local/hosting runtime mismatch to resolve or disclose, not a passing hosting check.
- Public documentation search reports Vercel Python 3.12/3.13/3.14 support. Pin production to 3.12; verify exact documentation before final deployment instructions. Search summary incorrectly conflates external rewrites with middleware proxy; inspect primary docs before using configuration.
- Tool file edits return version identifiers, helping avoid overwriting unrelated edits. No application tests have run yet.

## Stages 1–3 progress
- First Python dependency install failed on unavailable psycopg-binary 3.2.9; preserved 002, changed both manifests to available 3.3.9, retry succeeded.
- Alembic generated explicit schema migration, upgrade succeeded; 9 foundation tests passed in 0.17 s.
- Virtual environment reports Python 3.15.2 despite initial python3 reporting 3.11.15. Recorded follow-up 001; actual pytest runs use 3.15.2, not the production pin. This remains unverified hosting parity.
- First full backend suite: 114 passed in 3.43 s, with 70 dependency deprecation warnings. Role/IDOR/internal-note, transitions, SLA, rate-limit, notification, upload, CSV and report tests all passed. These are SQLite tests, not PostgreSQL claims.
- Ran local fictional seed twice: created 60 tickets first, reported no changes second. No hosted DB touched.
- Built original React UI with home/auth, queues, forms, ticket controls, reports and administration; all fetches use same-origin /api.
- npm initial install succeeded but reported 5 vulnerabilities (1 moderate, 3 high, 1 critical); retained full audit as 006. Selected newer published Vite/React Router/Vitest packages. Upgrade encountered ERESOLVE against installed older dependency tree; retained transcript 007 and preparing a clean dependency resolution (no --force bypass).
- Source review found chunked-request/multiple-multipart-part gaps. Recorded diagnostic 008 and implemented an early bounded-body middleware plus exactly-one-part validation. Regression checks pending.

## Stage 4 — real Chrome, accessibility and fixes
- Clean patched npm resolution succeeded with zero reported vulnerabilities. React production build/typecheck and 26 frontend unit tests passed.
- Hardened backend suite: 122 passed; current suite with UTC day-floor regression: 123 passed on Python 3.14.6 (one third-party httpx/TestClient deprecation warning).
- Chrome run history: local-first 3 passed / 1 failed / 6 not run (exact label locator); local-second 3 / 1 / 6 (serious invalid SLA definition-list markup); third attempt failed TypeScript before browser execution (Playwright Page type mismatch); local-fourth 6 / 1 / 3 (ambiguous save-status test locator); local-fifth 10 / 0; local-final 10 / 0 with populated-page screenshots and audits.
- Retained screenshots and diagnostics for all failures. A mistaken placeholder edit and a package exports inspection command also failed; recorded separately as builder/tool errors 013 and 015.
- Visual inspection caught a queue screenshot taken while loading. Added explicit screenshot readiness waits. Inspected the original home, populated reports, queue and mobile-dark captures through Designer's image view.
- Source review fixed a PostgreSQL rounding difference in UTC day grouping and hidden-but-focusable mobile navigation. Added regression coverage and repeated browser tests.
- uv found installed Python 3.14.6 and created only project-local .venv314/cache files. First command used the wrong working directory and failed test collection (023); correct-folder retry passed all 123. Production pin updated to documented-supported 3.14 and observed hosting 3.14.8.

## Stage 5 — separately approved external work
- User gave three separate explicit yes answers for GitHub, Vercel, and new free Neon/database/environment work before those tools were checked or used.
- Verified GitHub DIVYAPRIYADHARSHINI-GIT; Vercel divyapriyadharshini-git, team Divya (divya-6411), Hobby plan. Created only new ticketdesk-backend and new Neon ticketdesk-db (free_v3, Singapore, provider auth disabled).
- Vercel link unexpectedly downloaded an OIDC .env.local. Deleted it unread immediately, confirmed ignores, and told the user. Never printed/committed the credential. Integration provisioning used --no-env-pull. Neon automatically added provider connection aliases; app reads DATABASE_URL only. CLI env listing unexpectedly showed encrypted/truncated config envelopes, not plaintext credentials; avoid that listing in public evidence.
- Initial backend deployment failed PEP 668 because custom build redundantly ran pip into a managed interpreter (018). Switched to uv run, without bypassing the managed-environment protection.
- Second deployment migrated PostgreSQL and seeded 60 tickets, then failed static-project output detection (019). Declared FastAPI explicitly. Third deployment succeeded in 34 seconds, read Python 3.14 pin, reran migration/seed unchanged, and aliased https://ticketdesk-backend.vercel.app. Public DB health check pending at this log entry.
- Package version metadata lookups earlier omitted the local npm-cache flag; they may have used npm's default metadata cache. Subsequent registry/install calls explicitly used the project cache. No sibling project was inspected or modified.

## Final live verification and delivery
- Public backend /health returned 200 and a real connected-database response. Only then created/deployed the separate frontend. Actual alias is https://ticketdesk-frontend-psi.vercel.app; updated the backend exact origin and redeployed, with migrations/seed unchanged.
- Created the approved public GitHub repository and pushed main after a staged-file scan found no secret/environment/large-file findings. Verified PUBLIC visibility, main branch and the requested local commit identity.
- Frontend link also auto-created an OIDC .env.local; deleted it unread immediately. Both incidents retained under 016. A filename-only check confirmed only the intentionally authored .env.example files remained.
- Live first and second runs each passed 2 journeys, failed the agent saved-reply sequence, and skipped 5 dependent journeys. No CORS/session failure occurred: login, secure host-only cookies, reload, ticket creation and DB attachment had already passed. Preserved both screenshots/transcripts and their three-role fixture inventories.
- Standalone live diagnostic showed valid saved-reply IDs/nonempty bodies and a working 85-character selection; exact original browser event ordering was not captured. Replaced imperative picker reset with a controlled, empty-choice-safe component, guarded pending controls and preserved drafts against stale send completion. Four regression tests added.
- Latest local composer build/typecheck succeeded, 30 frontend tests passed, 10 Chrome journeys passed (19.0 s), and 18 axe audits reported zero violations. Final backend source passed 123 tests on Python 3.14 (4.23 s; one dependency deprecation warning). Final npm audit reported zero vulnerabilities.
- Redeployed the composer fix. Live third run passed all 8 journeys (31.6 s), with 16 axe audits and zero violations. Browser API-origin inventory contains only the frontend origin; Secure/HttpOnly/host-only cookie and reload checks passed with the third-party-cookie phaseout flag. No unexpected JS console errors. Native Chrome warnings observed in failed-run browser-process logs remain disclosed.
- All local disposable E2E data was deleted again after the last local run. Three live test tickets remain deliberately listed: TD-1061 and TD-1062 from failed attempts, TD-1063 closed and rated in the successful run. No new live user accounts were created. Existing demo accounts and the intended 60-ticket seed remain.
- Inspected actual live ticket detail, dark reports and the readable mobile viewport screenshot. Wrote the seven-section FINAL_REPORT.md with full historical counts, screenshot captions, failure records, tool experience and limits.
- Exported the report through real Chrome to an 18-page PDF (3,227,401 bytes, valid %PDF- signature). Inspected rendered pages 1, 3, 8 and 17 through Designer's PDF viewer; text, screenshot figures and captions were present. The PDF is included as an intentional reviewed document below the 5 MiB staged-file gate.
- Final staged-file checks scanned 155 files, then 156 including the scan evidence, with zero findings. The source, screenshots, permanent failures, Markdown report and 18-page PDF were committed and pushed as ad654240b864e4607afb8f714f8ac81ad9836446. Remote main matched the local commit and the working tree was clean. Both public health paths again returned 200 with a connected real database. This closing log entry is a documentation-only follow-up. No GitHub-triggered auto-deploy connection is claimed.

Failure evidence policy: numbered records in bugs/ are permanent, including failed tests and tool errors. Successful reruns do not erase original results. Credentials, cookies, CSRF values, request text and attachments must never enter transcripts.
