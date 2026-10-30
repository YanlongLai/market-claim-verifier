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

## Attempt 2 — usable source-linked review

The row-only prompt and attempt isolation were committed in `f954508` before the second calls. The exact-span guard is unchanged. [Frozen configuration](attempt-2/freeze.json) · [readable three-document summary](attempt-2/summary/stock-review.html) · [JSON summary](attempt-2/summary/stock-review.json).

| Page | Proposed / program-checked | Recorded result |
| --- | --- | --- |
| [Financial summary](attempt-2/REAL-TSLA-4/ingest.json) | 4 / 4 | Revenue, GAAP net income and GAAP diluted EPS supported; operating cash flow insufficient evidence |
| [Operational summary](attempt-2/REAL-TSLA-5/ingest.json) | 4 / 4 | Four operating KPIs remain insufficient evidence |
| [Chart page](attempt-2/REAL-TSLA-23/ingest.json) | 0 / 0 | Explicitly counted as a document without target-company program checks |

The eight extracted occurrences contain **three supported and five insufficient-evidence** outcomes, not “8/8 accurate” or full-page coverage. The cash-flow trace reports that the metric is outside the current lookup enum and the frozen release lookup cannot fetch additional evidence. Operating KPIs need additional suitable issuer evidence. An unresolved claim is not thereby false.

Attempt 2 cost is **$0.08645635**; both attempts together cost **$0.14738175 estimated/reserved** against the single $1 ceiling. [Shared ledger](ledger.jsonl) · [second spend snapshot](attempt-2/spend.json) · [audit](audit.json). The original failed quotes and paired-benchmark scores were not replaced. This smoke check used four requested proposals per window, rather than asserting quality at larger limits.

## Reuse and boundaries

Run `python scripts/audit_stock_context_posthoc.py` after dependencies are installed; it makes no model calls and checks both source archives, ledger/account/raw-request identity, costs and local HTML links. Frozen code is available for [attempt 1](frozen-source.zip) and [attempt 2](attempt-2/frozen-source.zip), including the exact earlier versions even after later product changes. All 41 raw requests reconcile with the retained case accounting.

The existing `stock-summary` command can recombine retained reports for $0 incremental inference. This follow-up does not retest image recognition, establish a general accuracy rate, authenticate the uploaded issuer, validate the default eight-claim setting, or add an AI narrative. Next priorities are authenticated issuer evidence for cash-flow/KPI gaps and an independently labeled real-document set.
