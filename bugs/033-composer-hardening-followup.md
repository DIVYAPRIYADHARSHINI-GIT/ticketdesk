# 033 — Live saved-reply journey reproduced the stall

Second live run again passed 2 tests and failed the agent journey (5 later tests not run), leaving TD-1062 inventoried. The screenshot again shows an empty composer after the internal note, despite a successful standalone saved-reply check. The exact browser event ordering was not captured, so a specific timing root cause is not asserted as proven.

Source inspection identified fragile behavior: the handler imperatively reset the native select and set the draft to an empty string if a subsequent change carried an empty value. The draft and reply mode could also be edited while an earlier send was pending, and send completion unconditionally cleared the draft.

Fix: extract ReplyComposer; use a controlled picker, ignore empty/nonmatching choices, disable composer/mode controls while pending, and clear only the draft that was actually submitted. Add four focused unit regressions. Rebuild, repeat the complete local suite and redeploy before another live run. Original two failure screenshots/transcripts remain unchanged.
