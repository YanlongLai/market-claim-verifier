# Protocol provenance errata

The original [protocol](protocol.json) remains byte for byte as committed before paid execution. Its phase-2 `seed`, `sources`, `targets`, `selection`, `paraphrase`, `gold`, `execution`, `metrics` and `limits` specify this Threads run.

The drafting step also retained News-only metadata at the bottom of that JSON: `registered_protocol_commit`, `collection`, `screening`, `gold_partitions`, `recorded_at` and `paths`. Those fields describe phase 1 and must not be read as Threads collection, screening or gold counts. This carry-over was noticed during execution and is disclosed here without rewriting the frozen file.

Threads protocol registration is commit `9dee36ba46c7e016e981694cc2feade0d11e68a5`; gold, inputs and runtime were committed in `3ae0040` before the first model request, as shown by [RUN_START.json](RUN_START.json). The actual frozen Threads [selection](selection.json) is 30 of 107 own posts plus all 48 external paraphrases. Its [gold](gold.jsonl) contains **5 primary truth items, 36 scope-policy items and 37 review items**; [media gold](media-gold.jsonl) contains two review-only cards. Collection is Owner-authorised logged-in Threads browsing on 2026-11-02, search Top ordering; no reliable engagement metrics were recorded.

No labels, inputs, source values, model settings, caps, execution order or scoring are changed by this correction. The runner reads `execution` for the model IDs and the frozen claims/gold files for the actual sample. The [machine-readable notice](PROTOCOL_METADATA_ERRATA.json) records the original protocol hash and correct counts. Source-tier corrections are separately documented in [GOLD_METADATA_ERRATA.md](GOLD_METADATA_ERRATA.md).
