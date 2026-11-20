# 021 — Portability and mobile keyboard issues found in review

These were source-review findings, not failed automated checks.

1. The report day bucket used a floating-point-to-integer CAST. PostgreSQL can round that conversion, unlike SQLite's truncation, which could place afternoon tickets on the following UTC day. Fix: use SQL FLOOR before CAST; add an end-of-day grouping regression. This was found before claiming live report correctness.

2. The mobile sidebar was translated offscreen but remained focusable. Keyboard users could tab through invisible navigation. Fix: visibility:hidden on the closed mobile sidebar, visibility:visible when expanded. Update the demo test helper to wait for the workspace URL rather than relying on the now-correctly-hidden desktop Sign out button.
