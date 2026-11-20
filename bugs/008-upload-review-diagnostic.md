# 008 — Upload envelope gaps found during source review

Stage 2 hardening review, 20 November 2026 IST. This is a source diagnostic, not a fabricated failed test.

Observed: the middleware trusted Content-Length for its early bound; the endpoint read at most 1 MiB + 1 only after the multipart parser had already consumed the request. Chunked requests could therefore consume resources before that endpoint check. FastAPI's single UploadFile argument also did not prove that a client supplied exactly one multipart part.

Fix: added a pure ASGI middleware that bounds the complete request to 1,100,000 bytes before parsing, even without Content-Length. Added an explicit exactly-one-part check. Kept the 1,048,576-byte file limit, MIME, extension and signature checks. Added regression tests for two files, chunked oversize and an exact-limit file. No failure record removed.
