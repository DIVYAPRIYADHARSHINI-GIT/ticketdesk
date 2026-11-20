# 001 — Local Python does not match hosting pin

Stage: environment checks, 20 November 2026 IST.
Observed transcript (no secrets):
```
python3 --version -> Python 3.11.15
command -v python3.12 -> no path
command -v python3.13 -> no path
command -v uv -> no path
```
Official Vercel documentation search lists 3.12/3.13/3.14, so production is pinned to 3.12. Local checks initially run on available Python 3.11. This does not verify the 3.12 deployment environment. No global runtime installation attempted. Status: open until 3.12 checks actually run.
