# 018 — First backend deployment failed in custom build command

Vercel resolved and installed the declared Python dependencies, but the custom command redundantly ran pip install into Vercel's externally managed Python installation. PEP 668 rejected that operation (externally-managed-environment). The error was not bypassed with --break-system-packages.

Full transcript is retained as 018-backend-deploy-first.txt. Fix: use the platform's uv environment to execute the migration/seed module without modifying its managed interpreter. No application health success is claimed for this failed deployment.
