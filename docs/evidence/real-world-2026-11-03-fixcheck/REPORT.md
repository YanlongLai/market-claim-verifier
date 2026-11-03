# POST-HOC FIX RECHECK

**Inputs were seen before these fixes. This is not a held-out result.** Original text and gold are unchanged; publication-date context is now supplied. No OCR/ASR was retested.

One append-only ledger covers News and later Threads sets, including retries, failures and unreconciled reservations. Cap: $5 per provider.

The first attempt (`news`) and adaptive routing repair (`news-r2`) are separate, fully retained executions. First-attempt outputs were inspected before the second repair; see [decision record](ADAPTATION.json) and [diagnosis](FINDINGS.md). Each row compares with the original 2026-11-02 run, never with a selected best result.

| Attempt / provider / path | Primary SEC positives before → after | Supported before → after | Contradicted before → after | Insufficient before → after | Skipped before → after | Failed before → after / stopped after |
|---|---:|---:|---:|---:|---:|---:|
| news/baseten/agent | 0/4 → 3/4 | 0 → 4 | 0 → 0 | 80 → 76 | 0 → 0 | 0 → 0 / 0 |
| news/baseten/post | 0/4 → 3/4 | 0 → 3 | 1 → 1 | 43 → 39 | 36 → 37 | 0 → 0 / 0 |
| news/fireworks/agent | 0/4 → 3/4 | 0 → 4 | 1 → 0 | 79 → 75 | 0 → 0 | 0 → 1 / 0 |
| news/fireworks/post | 0/4 → 3/4 | 0 → 3 | 1 → 1 | 42 → 37 | 36 → 35 | 1 → 4 / 0 |
| news/meta/agent | 0/4 → 4/4 | 0 → 5 | 1 → 0 | 77 → 75 | 0 → 0 | 2 → 0 / 0 |
| news/meta/post | 0/4 → 4/4 | 0 → 4 | 1 → 1 | 42 → 39 | 36 → 36 | 1 → 0 / 0 |
| news-r2/baseten/agent | 0/4 → 4/4 | 0 → 5 | 0 → 0 | 80 → 75 | 0 → 0 | 0 → 0 / 0 |
| news-r2/baseten/post | 0/4 → 4/4 | 0 → 5 | 1 → 0 | 43 → 38 | 36 → 37 | 0 → 0 / 0 |
| news-r2/fireworks/agent | 0/4 → 4/4 | 0 → 5 | 1 → 0 | 79 → 74 | 0 → 0 | 0 → 1 / 0 |
| news-r2/fireworks/post | 0/4 → 3/4 | 0 → 4 | 1 → 0 | 42 → 39 | 36 → 35 | 1 → 2 / 0 |
| news-r2/meta/agent | 0/4 → 4/4 | 0 → 5 | 1 → 0 | 77 → 75 | 0 → 0 | 2 → 0 / 0 |
| news-r2/meta/post | 0/4 → 4/4 | 0 → 5 | 1 → 0 | 42 → 38 | 36 → 36 | 1 → 1 / 0 |

Costs include unknown-usage reservations (estimates, not invoices): baseten $2.172972, fireworks $2.695390, meta $2.728004.

The News truth panel has only four independently SEC-confirmed positives. The other labels are scope expectations or unresolved review cases. Before/after fixes, source-date context and execution concurrency changed together; these counts do not establish broad real-world accuracy or a hosting effect.

News and Threads sets use separate frozen manifests under `sets/`; every trace, failed CLI exit and result is retained there. Four concurrent workers per provider share an atomically locked ledger. Original evidence remains under `../real-world-2026-11-02/`.

Threads inputs are pending the phase-2 merge unless a frozen `sets/threads/` manifest is present. Add them with `prepare --input-set threads=PATH`, commit the manifest, then `run --set threads`; the same root ledger and remaining caps apply.
