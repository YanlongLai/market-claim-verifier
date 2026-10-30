# Public rate cross-check — 2026-10-30

These official pages were checked during execution and agree with the frozen ledger rates. Amounts below are USD per one million tokens, not measured cost per document or an account balance.

| Platform / model family | Input | Cached input | Output | Official source |
| --- | ---: | ---: | ---: | --- |
| Meta / Muse Spark, Standard mode | 1.25 | 0.15 | 4.25 | [Meta pricing](https://dev.meta.ai/docs/pricing-rate-limits) |
| Baseten / Muse Spark Open | 1.25 | 0.15 | 4.25 | [Baseten model library](https://www.baseten.co/library/muse-spark-open/) |
| Fireworks / Muse Spark Open serverless | 1.25 | 0.15 | 4.25 | [Fireworks model card](https://fireworks.ai/models/fireworks/muse-spark-open) |

The [actual model IDs and configured rates](cost-basis.json) identify the pinned endpoints used. No Contributor-mode model or discounted native Batch API was used.

Meta lists Muse Voice Transcribe at **$0.18 per audio hour**, metered separately from text tokens, with audio time rounded down to whole seconds. The repository reserves rounded-up seconds conservatively and keeps unknown outcomes reserved. [Official audio pricing](https://dev.meta.ai/docs/pricing-rate-limits).

Matching token prices do not imply matching workflow bills: token counts, reasoning, cache usage, tool turns, preprocessing and failures differ. The [ledger](ledger.jsonl) is the experiment's estimated/reserved spending record; supplier invoices were not reconciled.
