# Providers, input support and cost

Checked 2026-10-30. Scope: the three providers currently integrated in this repository: Meta, Baseten and Fireworks. Account credit balances, expiration and quota were not queried; public availability does not establish account entitlement.

## Platform capability versus integration

| Provider / model | Vendor-declared inputs | Repository use today | Audio / video boundary |
|---|---|---|---|
| Meta / muse-spark-1.3 | Text; repository has a working image OCR path | Text extraction, tool-based verification, image OCR | Audio uses separate muse-voice-transcribe-1.0; video uses local decoding plus OCR/ASR, not a native video endpoint |
| Baseten / Muse Spark Open | Library lists text, image, video, audio | Text extraction and verification with meta-models/muse-spark-open-1026 | Library listing is not an endpoint contract for the pinned model; native audio/video request shapes remain unverified |
| Fireworks / accounts/fireworks/models/muse-spark-open | Text and images, text output | Text extraction and verification | Native audio/video is not established by this model page; image routing is not integrated here |
| Meta / muse-voice-transcribe-1.0 | Audio | File ASR, chunked with overlap | Turn timestamps and session speaker labels; no verified identity or word alignment |

Sources: [Baseten model library](https://www.baseten.co/library/muse-spark-open/), [Fireworks model card](https://fireworks.ai/models/fireworks/muse-spark-open), [Meta pricing and ASR](https://dev.meta.ai/docs/pricing-rate-limits). Meta OCR implementation: [media adapter](../src/claimcheck/ingest_media.py). Vendor modality labels need endpoint probes before enabling another adapter. No unsupported capability is inferred from a shared model family name.

## Current repository input contract

| Input | Support | Limit |
|---|---|---|
| Text | TXT, Markdown | Financial claims; not a universal fact checker |
| Image | PNG, JPEG, WebP through Meta OCR | Reading text is not evidence authentication |
| Audio | WAV, MP3, M4A, FLAC, AIFF, AAC, OGG | Up to 2 hours and 128 MiB; 10-minute ASR chunks; English language bias |
| Video | MP4, MOV, WebM, MKV | Same size/duration limits; only three sampled frames plus audio |
| PDF | Local native text, page-scoped | Up to 100 pages / 128 MiB; scanned/blank pages reported unchecked; no PDF OCR or cross-page context |
| URL | Deferred, direct readable documents only | No general HTML extraction, login or browser automation |

Accepted duration is a decoder limit, not a demonstrated accuracy guarantee. Media read/heard text remains a claim, not financial evidence.

## Recorded input-format probes

The [2026-10-30 format report](evidence/input-formats-2026-10-30/REPORT.md) adds six preselected paid smoke probes across all three text providers: Markdown, JPEG, WebP, MP3, silent MP4 and local native-text PDF. Per-case completion, claim counts, verdicts, latency and ledger costs are public. One example is evidence for that path, not exhaustive codec, language, provider or accuracy validation. Media still uses Meta OCR/ASR before text-provider routing; no native Baseten/Fireworks media endpoint was tested. Unsupported URLs and scanned PDFs remain deferred.

## Price comparison

USD per million tokens; published standard rates, not credit-adjusted prices.

| Provider / model | Input | Cached input | Output | Repo integration |
|---|---:|---:|---:|---|
| Meta Spark 1.3 Standard | 1.25 | 0.15 | 4.25 | Yes |
| Baseten Spark Open | 1.25 | 0.15 | 4.25 | Yes |
| Fireworks Spark Open | 1.25 | 0.15 | 4.25 | Yes |
| Meta Spark Contributor | 0.10 | 0.002 | 0.20 | Not configured in the price ledger; requires training-use consent |

Sources: [Meta rates](https://dev.meta.ai/docs/pricing-rate-limits), [Baseten rates](https://www.baseten.co/pricing/), [Fireworks model rates](https://fireworks.ai/models/fireworks/muse-spark-open).

Meta ASR is $0.18/audio hour ($0.003/minute), separate from downstream claim checks. Official documentation says whole seconds rounded down; the current ledger conservatively reserves rounded-up seconds and retains reservations on failures. Reported ledger estimates are not invoices. Overlapping chunks and retries add processed audio. OCR is token-priced, not a fixed price per image.

Total cost = decoding/storage + OCR/ASR + extraction + every tool-loop model call + retries. Search or licensed market-data charges must be added if introduced. A document may contain many chargeable claims.

## Batch and scale

[Fireworks Batch API](https://docs.fireworks.ai/guides/batch-inference) advertises 50% off serverless token rates, but requires model compatibility. Its model page offers on-demand deployment; exact pinned-model/account batch execution has not been tested here. No provider-native batch adapter is integrated. Meta/Baseten batch discounts for these routes are unverified. Concurrent requests and background responses are not automatically discounted batch inference.

An agent loop has sequential tool dependencies: batch extraction or independent evidence-ready checks first, then resume dependent stages. Shared SEC limits must be enforced across workers before scaling beyond the current process-wide gate. Cache immutable source bytes and successful OCR/ASR; key verification reuse by claim, source, policy and model versions.

## Measured quality and cost

Original 266-claim held-out split, corrected labels; recorded run, not a fresh benchmark of today's code:

| Agent | Accuracy | Reported mean cost USD | Mean latency seconds |
|---|---:|---:|---:|
| Baseten | 90.2% | 0.019880 | 11.307 |
| Fireworks | 89.1% | 0.019973 | 68.530 |
| Meta | 82.0% | 0.025880 | 38.372 |

[Full report and denominator details](evidence/eval-v2-2026-10-27/REPORT.md). Meta has one incomplete agent case; means follow the report's completion accounting. These numbers are not SLAs. Closed Spark and Open Spark are different model variants. Media has only [development probes](evidence/multimodal-2026-10-30b/REPORT.md), not comparable provider-wide accuracy scores. Measure extraction recall separately from verdict accuracy; 50/60 program-checked assertions on frozen ASR is coverage, not 83.3% truth accuracy.

## Paired format evidence (2026-10-30)

The [completed benchmark](evidence/fair-multimodal-v1/REPORT.md) compares identical nine-format inputs with shared frozen Meta preprocessing. Separate native PNG/JPEG/WebP probes completed six control images per format on every provider; native audio/video endpoints were not tested. Native image probes do not change the product adapter: all product image routes still require Meta OCR. [Official price cross-check](evidence/fair-multimodal-v1/RATE_CHECK.md) · [total task spend](evidence/fair-multimodal-v1/task-spend.json). No discounted provider Batch was used.
