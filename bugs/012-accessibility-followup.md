# 012 — Invalid definition list in SLA inspector

The second real Chrome run passed 3 journeys and failed journey 4 during its axe audit; 6 subsequent serial journeys did not run. Upload and ticket creation had worked before the audit stopped the run.

Axe found one serious definition-list violation: .sla-dates contained div > small as a sibling of dt/dd. Screenshot: local-second-axe-ticket-detail.png. JSON diagnostic and journey transcript are retained.

Fix: move each target-duration small element inside its associated dd. This preserves the visible target labels while restoring valid definition-list semantics. Rerun follows separately.
