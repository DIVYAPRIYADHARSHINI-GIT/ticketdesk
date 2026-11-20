# 023 — Hosting-matched test command used the wrong working directory

uv successfully found installed Python 3.14.6 and created a project-local .venv314. This resolves the earlier absence of a hosting-matched interpreter without a global install. However, `uv run --project backend ... pytest backend/tests` retained the repository-root working directory, so conftest could not import app. Test collection failed with ModuleNotFoundError, not an application assertion failure.

Original transcript: 023-python314-tests.txt. Fix: run ../.venv314/bin/python -m pytest with backend as the working directory. Result is recorded separately. Production remains pinned to supported Python 3.14 (remote build reported 3.14.8).
