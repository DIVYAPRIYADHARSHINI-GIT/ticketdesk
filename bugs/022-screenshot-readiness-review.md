# 022 — Queue screenshot captured a loading state

Visual inspection of screenshots/local-fourth/07-agent-queue.png showed the loading spinner and temporary zero page counters, not the populated queue. The application subsequently loaded and the journey passed that section; this was a capture timing issue. Earlier evidence is kept unchanged.

Fix: the screenshot helper now waits until all loading spinners are gone before capturing each page. The same wait also ensures the subsequent accessibility audit checks the populated view rather than accidentally auditing its loading placeholder. Final screenshot set will be recorded under a new run name.
