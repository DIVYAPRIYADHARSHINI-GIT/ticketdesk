# 019 — Database preparation succeeded, but Vercel expected a static directory

Second backend deployment used CPython 3.14.8 and completed real PostgreSQL migrations and the 60-ticket fictional seed. It then failed with STATIC_BUILD_NO_OUT_DIR: no public output directory. The newly CLI-created project had been treated as a generic/static project rather than FastAPI.

Fix: declare framework: fastapi explicitly in backend/vercel.json, and select the Singapore runtime region near the new Singapore Neon database. Keep the uv build command. No static-directory workaround or fake health endpoint is used. The full failed deployment transcript remains in 019-backend-deploy-second.txt. The database exists and is seeded even though this deployment failed; subsequent seed runs must remain idempotent.
