# POST-HOC FIX RECHECK

**Inputs were seen before these fixes. This is not a held-out result.** Original text and gold are unchanged; publication-date context is now supplied. No OCR/ASR was retested.

One append-only ledger covers News and later Threads sets, including retries, failures and unreconciled reservations. Cap: $5 per provider.

| Set / provider / path | Primary SEC positives before → after | Supported / contradicted / insufficient after | Failed / stopped |
|---|---:|---:|---:|
| news/baseten/agent | 0/4 → 3/4 | 4 / 0 / 76 | 0 / 0 |
| news/baseten/post | 0/4 → 3/4 | 3 / 1 / 39 | 0 / 0 |
| news/fireworks/agent | 0/4 → 3/4 | 4 / 0 / 75 | 1 / 0 |
| news/fireworks/post | 0/4 → 3/4 | 3 / 1 / 37 | 4 / 0 |
| news/meta/agent | 0/4 → 4/4 | 5 / 0 / 75 | 0 / 0 |
| news/meta/post | 0/4 → 4/4 | 4 / 1 / 39 | 0 / 0 |

Costs include unknown-usage reservations (estimates, not invoices): baseten $1.107125, fireworks $1.351275, meta $1.292588.

The News truth panel has only four independently SEC-confirmed positives. The other labels are scope expectations or unresolved review cases. Before/after fixes, source-date context and execution concurrency changed together; these counts do not establish broad real-world accuracy or a hosting effect.

News and Threads sets use separate frozen manifests under `sets/`; every trace, failed CLI exit and result is retained there. Four concurrent workers per provider share an atomically locked ledger. Original evidence remains under `../real-world-2026-11-02/`.

Threads inputs are pending the phase-2 merge unless a frozen `sets/threads/` manifest is present. Add them with `prepare --input-set threads=PATH`, commit the manifest, then `run --set threads`; the same root ledger and remaining caps apply.
