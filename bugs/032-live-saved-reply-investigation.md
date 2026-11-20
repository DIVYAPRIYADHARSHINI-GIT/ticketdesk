# 032 — Live saved-reply interaction did not populate the composer

Live first run: 2 passed, 1 failed, 5 did not run. The agent had successfully assigned TD-1061 and added an internal note, but Send reply remained disabled after selecting a saved reply. Screenshot and full browser transcript are retained. The transcript also contains native Chrome allocator/display-link warnings; these are browser-process diagnostics, not JavaScript console errors from TicketDesk.

A separate real-Chrome diagnostic on the same live ticket verified that the API returned three saved replies with numeric IDs and non-empty string bodies (lengths only logged). Selecting Taking a look then produced an 85-character composer and an enabled Send reply button. The original failure therefore was not reproduced in that isolated check.

The live journey now explicitly asserts the populated textarea value before clicking Send, as the local suite already did. This improves diagnosis but is not yet proof of a root-cause fix. The first live test ticket remains inventoried in evidence/live-first-test-data.json; no failure evidence has been deleted. Rerun outcome will be recorded separately.
