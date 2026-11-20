# TicketDesk deployment guide

## Safety and permissions

This session obtained separate explicit approvals for GitHub, Vercel, and a **new** free Neon database plus TicketDesk-only environment changes. Never interpret those approvals as permission to change another project. Account verified: GitHub `DIVYAPRIYADHARSHINI-GIT`; Vercel user `divyapriyadharshini-git`, team `divya-6411` (Divya), plan **Hobby**. Neon was provisioned with plan ID **free_v3**, name **ticketdesk-db**, Singapore region, built-in Neon auth disabled (TicketDesk implements its own sessions).

Use only free plans. No payment details or upgrade. Vercel Hobby is for personal, non-commercial use: this deployment is a fictional public demonstration, **not approval to operate a commercial office helpdesk on Hobby**. If actual use or quota requires payment, stop; do not upgrade automatically.

Do not use `vercel env pull`, `vercel pull`, `vercel env run`, provider connection-string export, or any command that downloads production secrets. Do not paste credentials into chat or commit them. The modern CLI's `vercel link` can automatically create `.env.local` with an OIDC credential; if that happens, delete it unread, verify it is ignored and notify the owner. Prefer the documented no-env-download option where available. `vercel integration add ... --no-env-pull` avoids downloading database secrets.

## Supported runtime and dependencies

Pin **Python 3.14** in `.python-version` and `requires-python = ">=3.14,<3.15"` in `pyproject.toml`. Vercel's documentation lists Python 3.12/3.13/3.14; the real remote build in this session used **3.14.8**. The locally matched suite uses 3.14.6. Both `requirements.txt` and `pyproject.toml` contain identical direct dependency pins; do not maintain only one. A dependency-manifest test checks this. Vercel installs Python dependencies through uv; do not run pip against its externally managed system interpreter.

Official references consulted 20 November 2026:
- https://vercel.com/docs/functions/runtimes/python
- https://vercel.com/docs/functions/runtimes/python/python-version
- https://vercel.com/docs/frameworks/backend/fastapi
- https://vercel.com/docs/routing/rewrites
- https://vercel.com/docs/project-configuration/vercel-json
- https://vercel.com/docs/plans/hobby
- https://vercel.com/docs/functions/limitations
- https://neon.com/pricing

Exact provider quotas may change; confirm the plan card before provisioning. No precise storage/bundle quota is asserted solely from inconsistent search summaries.

## Environment templates (non-secret examples)

Every `.env` filename, including `.env.example`, is ignored by Git as requested. Local example files were provided; repository users can reconstruct them from these blocks. Backend reads process environment, not dotenv automatically. Never put a real hosted credential into a local file for this workflow.

Backend local example:
```dotenv
DATABASE_URL=sqlite:///./ticketdesk.db
FRONTEND_ORIGIN=http://localhost:5173
COOKIE_SECURE=false
DEMO_ENABLED=true
SIGNUP_ENABLED=true
```

Frontend local example:
```dotenv
API_ORIGIN=http://127.0.0.1:8000
```

Production backend variables:
- `DATABASE_URL`: **integration-managed secret** for the new Neon database. Never copy its value to chat or source.
- `FRONTEND_ORIGIN`: exact HTTPS origin of the final frontend deployment, without a trailing slash. Initially use a non-resolving safe origin until the frontend domain is known.
- `COOKIE_SECURE=true`: required for HTTPS; creates the `__Host-ticketdesk` cookie.
- `DEMO_ENABLED=true`: only for this fictional sandbox. False for a real organisation.
- `SIGNUP_ENABLED=true`: demo visitors may create ordinary employee accounts; disable for a restricted installation.

Production frontend variable:
- `API_ORIGIN`: public HTTPS backend origin (not a secret). Used to generate the same-origin rewrite before deployment. Do not put DATABASE_URL or any token in a `VITE_` variable.

The Neon Marketplace integration can automatically add connection aliases such as POSTGRES_URL and PGHOST in addition to DATABASE_URL. TicketDesk only reads DATABASE_URL. Do not inspect their values. CLI environment-list output is not guaranteed to be names-only; avoid writing it to public evidence without sanitisation.

## Exact order

1. After GitHub approval, initialise Git **inside ticketdesk**. Set local-only identity:
   ```sh
   git init -b main
   git config user.name "Divya Priyadharshini"
   git config user.email "divyapriyadharshini@softage.ai"
   ```
   Check staged paths/content for secrets, `.env` files, databases, caches and large binaries before committing. Create a new public `DIVYAPRIYADHARSHINI-GIT/ticketdesk` repository; do not overwrite an existing repository.

2. After Vercel approval, create **ticketdesk-backend** under team `divya-6411`, link only `backend/`, and ensure `backend/vercel.json` explicitly declares `framework: fastapi`. Without the explicit framework, the CLI-created project was treated as static and requested a nonexistent `public` directory. Runtime region is Singapore (`sin1`).

3. After separate database/environment approval, provision the free database through the supported CLI:
   ```sh
   vercel integration add neon --plan free_v3 --name ticketdesk-db --metadata region=sin1 --metadata auth=false --no-env-pull --environment production --scope divya-6411
   ```
   Run from the linked backend folder. Verify the plan says Free. Add the four non-credential flags/origin above through the Vercel dashboard or stdin to `vercel env add`; do not retrieve DATABASE_URL locally.

   **If dashboard consent is required instead:** open the new backend project in https://vercel.com/dashboard → Storage → Create Database → Marketplace → Neon → Continue → select Free → Singapore → name `ticketdesk-db` → Create → Connect Project → select only `ticketdesk-backend` → Production → Connect. Approve provider terms yourself if shown. In project Settings → Environment Variables, verify `DATABASE_URL` exists without revealing/copying its value. Add `FRONTEND_ORIGIN`, `COOKIE_SECURE`, `DEMO_ENABLED`, `SIGNUP_ENABLED` for Production. Stop if the screen asks for payment or has no free option.

4. Deploy backend **first**, from `backend/`:
   ```sh
   vercel deploy --prod --yes --scope divya-6411
   ```
   The explicit build command is `uv run --python 3.14 python -m app.prepare`. It runs Alembic and the idempotent demo seed **inside Vercel**, where the integration injects credentials. It prints only success messages or an exception type, not credential-bearing exception details. This avoids pulling production secrets to a local machine. Build-time schema changes must stay backward-compatible for future rolling deployments. Do not run concurrent migrations.

5. Request the backend `/health` endpoint and require HTTP 200 plus `{"status":"ok","database":"connected"}`. This performs a real database query. A successful build alone is insufficient. Do not deploy frontend until this passes.

6. Generate the frontend rewrite using the actual backend origin:
   ```sh
   cd frontend
   API_ORIGIN=https://YOUR-BACKEND.vercel.app npm run configure:hosting
   ```
   This writes public routing configuration only. Create/link **ticketdesk-frontend** separately, set its public `API_ORIGIN` variable, and deploy `frontend/` with Vite build/output `dist`. Linking may create `.env.local`; delete it unread before any build.

7. Set backend `FRONTEND_ORIGIN` to the actual frontend HTTPS origin. Redeploy the backend; this also reruns migrations and the safe seed. If the frontend hostname differs from the anticipated alias, update the exact origin before testing sign-in.

8. Test in real Chrome using the frontend URL: demo employee, new request and attachment, agent queue/reply/resolve, employee rating, demo admin reports/CSV. Verify host-only Secure HttpOnly cookie storage, reload persistence, no CORS errors and no unexpected console errors. Record live test tickets/accounts or remove them using a deliberate demo-only cleanup procedure. Never remove someone else's ticket.

9. Commit the final tested configuration and evidence, rescan staged files, push `main`, and optionally connect each Vercel project to the GitHub repository with root directories `backend` and `frontend`. Auto-deploy is not verified merely because a CLI deployment succeeded.

## Why cross-site cookies are avoided

The frontend and backend have different Vercel domains, but **the browser never calls the backend domain directly**. `frontend/vercel.json` rewrites `/api/:path*` to `https://BACKEND/api/:path*` before the SPA fallback. A host-only Set-Cookie returned through that proxy belongs to the frontend domain. Cookie attributes are Secure, HttpOnly, SameSite=Lax and Path=/; no Domain attribute is set. Third-party cookies are therefore unnecessary. The browser sends its real frontend Origin; the backend accepts only that configured origin and a matching CSRF header on unsafe requests. CORS is exact-origin, not wildcard credentials.

Locally, Vite proxies the same path across ports 5174 → 8001 in the Chrome suite. That proves local proxy/cookie behavior, not Vercel behavior. Consult FINAL_REPORT.md for whether the live rewrite was actually verified; do not substitute a claim based on configuration alone.

## Free-plan and product limits

Serverless cold starts and an idle database waking up can delay the first request. Free invocation/compute/bandwidth/storage limits are provider-dependent; inspect current dashboards and stop if exceeded. Database attachments consume the database's free storage, which is finite even with a 1 MiB per-ticket cap. Vercel function payload limits are above this app's deliberately smaller 1.1 MB request envelope. No email, external file storage, SSO, password reset, antivirus scanning, business-hour calendar, background SLA scheduler or enterprise compliance claim is included. The UI calculates current SLA state when loaded/refreshed; notification polling is every 30 seconds.

The public sandbox uses shared demo identities and configuration. It is not suitable for confidential HR data or a real company without isolation, retention controls, secure organisation onboarding, operational monitoring/backups and a hosting plan appropriate to that use.
