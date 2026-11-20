# 011 — First Chrome journey stopped on a test locator

First run: 3 passed, 1 failed, 6 did not run. Failure screenshot and transcript are retained with the local-first prefix.

The create-request test timed out using getByLabel('Category', exact=true). Chrome's captured accessibility tree shows a correctly named combobox 'Category', and the page's axe audit passed. The nested label includes select option text for the label-query implementation. Corrected the test to target the actual accessible role/name (combobox Category), likewise Priority. This was a test harness selector issue, not evidence that the dropdown was broken.

Review also corrected a forthcoming assertion: a controlled textarea's content should be tested with toHaveValue, not textContent. Rerun results recorded separately. No original failure renamed or deleted.
