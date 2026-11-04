# Live determinism session fixture

`session-20261104T021100641318Z.json` is a byte-for-byte copy of the owner-supplied production capture at `/Users/yan/git/market-claim-verifier-video/demo/cache/live-takes/v4/session-20261104T021100641318Z.json`, recorded 2026-11-04 UTC (2026-11-03 America/Los_Angeles).

SHA-256: `a4deb207015512ae3d4e9020636b2ae626e8ff24bfd29121bfa47bd1e864ad3e`.

The public result retains the failed Apple check, both quarter/annual evidence IDs, tool-call arguments/results, all other assertions, costs and timings. Its original verdict is `insufficient_evidence`; it is not replaced with the improved replay result. No credentials or account balances are included.

[Replay tests](../../test_live_determinism.py) restore proposals from the public checks and verbatim number literals, then run the normal program checker and correction builder. The capture does not contain the model's raw final JSON, so this is a public-envelope regression, not a raw-response replay or a new live evaluation. It does not retest OCR/ASR. [Validation receipts](../../../docs/evidence/live-determinism-2026-11-03/REPORT.md) retain the baseline failure and subsequent offline checks.
