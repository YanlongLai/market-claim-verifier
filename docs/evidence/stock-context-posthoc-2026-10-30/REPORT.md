# Stock-context product check — post-hoc

This is a known-failure product check, not a vendor comparison or independent accuracy estimate. The original paired benchmark stays unchanged. Three real Tesla pages reuse their frozen Meta OCR; OCR/ASR is not rerun. Code/protocol were committed in `f6e668a` before the calls; exact hashes are in [freeze](freeze.json).

## Attempt 1

Bounded extraction with a user-supplied TSLA hint avoids the original table-extraction truncation, but does not yet complete the financial-page checks:

| Page | Proposed | Program-checked | Finding |
| --- | ---: | ---: | --- |
| [Financial summary](REAL-TSLA-4/ingest.json) | 4 | 0 | All four quotations concatenate a header and a nonadjacent row; exact-span screening correctly rejects them |
| [Operational summary](REAL-TSLA-5/ingest.json) | 4 | 4 | All four are insufficient evidence in the frozen SEC tools; these are not supported answers |
| [Chart page](REAL-TSLA-23/ingest.json) | 0 | 0 | No numeric claims extracted; no chart-value inference is asserted |

The [stock summary](summary/stock-review.html) flags documents without target-company program checks. There is no claim that the three documents were fully verified. Attempt 1 cost is **$0.06092540 estimated/reserved**, with [all calls](ledger.jsonl) and [snapshot](spend.json) retained.

The next targeted change is to request an exact row-only quotation for tables, keeping nonadjacent headers as context rather than concatenating them into a fake contiguous quote. It must retain exact-span screening and preserve this failed attempt. Further attempts share the same $1 post-hoc ledger ceiling; there is no new $1 allowance per attempt.
