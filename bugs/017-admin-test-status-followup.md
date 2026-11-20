# 017 — Ambiguous status locator during admin reload

Fourth local attempt: build passed, 6 Chrome journeys passed, admin journey failed, 3 later journeys did not run. The actual role/category mutation succeeded. The test used an unqualified getByRole('status'), which briefly matched both the success confirmation and the loading status during refetch. Playwright correctly rejected the ambiguous locator.

Fix: scope assertions to the success-status content rather than asserting that the page has exactly one status region. Preserve the screenshot and full failing transcript. This is a test harness race, not an invented application failure.
