# Multimodal input probe — 2026-10-29

**13 recorded exploratory runs; estimated spend $1.30508830 of the $20 cap.** Text, screenshots, speech and sampled video frames enter the existing post checker. The strongest observed paths reach SEC evidence and program verdicts for all four input types. One true growth claim received a false contradiction after period context was lost, and two voices were merged into one speaker label. Failures and repeats remain below; this is development evidence, not a held-out evaluation.

## Protocol and media

All verifier model calls are Meta models: `muse-spark-1.3` for OCR and hosted text reasoning, `meta-models/muse-spark-open-1026` for Baseten text reasoning, and `muse-voice-transcribe-1.0` for ASR. Keys load through `claimcheck.config` and are excluded from records. SDK retries are disabled; the existing agent's bounded incomplete-response and expired-state retries retain their normal reservations. One locked ledger partitions the total into $10 Meta + $10 Baseten. SEC tools use only committed, hash-checked companyfacts and release snapshots; missing corpus data fails closed. No live SEC retrieval, real earnings-call downloads, or non-Meta runtime inference was used.

Self-made assets use Apple's [committed 8-K Ex 99.1](../../../tests/fixtures/releases/manifest.json) ([SEC source](https://www.sec.gov/Archives/edgar/data/320193/000032019325000071/a8-kex991q3202506282025.htm)). The 47.29-second reading excerpts real release sentences, with **EPS deliberately changed from $1.57 to $1.67**. Slides reproduce $94,036 million sales, $23,434 million net income and $1.57 EPS; the third slide deliberately says $1.67. The PNG says **Example post** and names a fictional author. The smaller PNG, spoken-number text, two-voice clip, silent video and sentence-captioned video are development controls. The captioned control was created after inspecting row-only extraction failures.

**Media-generation deviation:** macOS `say` with Samantha and Fred returned `sandbox_extension_issue_file` and zero audio frames. The committed narration instead uses eSpeak NG 1.53.0 offline formant synthesis, followed by ffmpeg; no generative model created the audio. It is synthetic narration, never the CFO's voice. [Generation record](../../../tests/fixtures/multimodal/generation.json), [input hashes/expected numbers](../../../tests/fixtures/multimodal/manifest.json), [generator](../../../scripts/multimodal/make_media.py).

Each run has `protocol.json` with exact model IDs, source hashes and fixture hashes, `ingest.json`/`ingest.html`, media responses in `calls/`, and post/model/tool traces in `checks/`. Each code revision and repeat is recorded; there was no frozen pre-evaluation protocol. Three frames are sampled at 1/6, 1/2 and 5/6 of the duration. Speech and frame claims are checked independently; disagreement is not automatically fused into one claim.

## Capability matrix

✓ = reached for every relevant channel; ✗ partial = some channels/claims reached it; ✗ = none reached it; — = no speaker attribution applies. Stage 4 requires cited L1–L4 numeric evidence, not merely a successful search. Stage 5 includes a program `insufficient_evidence` decision. Stage 6 means unverified speaker label + whole-turn timestamp, **not a named-person attribution**.

| Input / run | 1 Decode | 2 Text + offsets | 3 Claims | 4 SEC | 5 Program | 6 Attribution | Reason / limit |
|---|---|---|---|---|---|---|---|
| [audio](audio/ingest.html) (audio) | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | audio: pipeline failed (PostError) |
| [audio-baseten](audio-baseten/ingest.html) (audio) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | audio: claim has numbers the quote does not: 28, |
| [audio-r2](audio-r2/ingest.html) (audio) | ✓ | ✓ | ✓ | ✓ | ✗ partial | ✓ | audio: pipeline failed (BadRequestError) |
| [audio-two-voices](audio-two-voices/ingest.html) (audio) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | All applicable stages reached; diarization identities unverified; two known synthetic voices both labeled A |
| [screenshot](screenshot/ingest.html) (image) | ✓ | ✓ | ✓ | ✓ | ✓ | — | Financial numbers preserved; revenue supported, deliberate EPS error contradicted |
| [screenshot-small](screenshot-small/ingest.html) (image) | ✓ | ✓ | ✓ | ✓ | ✓ | — | Financial numbers preserved; revenue supported, deliberate EPS error contradicted |
| [text](text/ingest.html) (text) | ✓ | ✓ | ✓ | ✓ | ✓ | — | Financial numbers preserved; revenue supported, deliberate EPS error contradicted |
| [text-baseten](text-baseten/ingest.html) (text) | ✓ | ✓ | ✓ | ✓ | ✓ | — | Financial numbers preserved; revenue supported, deliberate EPS error contradicted |
| [text-words](text-words/ingest.html) (text) | ✓ | ✓ | ✓ | ✓ | ✓ | — | Financial numbers preserved; revenue supported, deliberate EPS error contradicted |
| [video](video/ingest.html) (video) | ✓ | ✓ | ✗ partial | ✗ partial | ✗ partial | ✗ | audio: pipeline failed (PostError); frame-1: claim has numbers the quote does not: 28, |
| [video-captioned](video-captioned/ingest.html) (video) | ✓ | ✓ | ✓ | ✗ partial | ✗ partial | ✓ | audio: pipeline failed (BadRequestError); frame-2: pipeline failed (InternalServerError) |
| [video-captioned-baseten](video-captioned-baseten/ingest.html) (video) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | All applicable stages reached; diarization identities unverified; growth claim lost period and was falsely contradicted |
| [video-silent](video-silent/ingest.html) (video) | ✗ partial | ✗ partial | ✗ partial | ✗ partial | ✗ partial | ✗ | audio: video has no audio track; frame-2: claim has numbers the quote does not: 28, |

## Number recovery, cost and latency

Number recovery is measured against the known self-made source: financial numeric mentions only, excluding calendar dates and quarter/year labels. Program normalization expands bounded English numbers, joined tens, decimal digits, grouped numerals and ordinal quarters; unsupported verbal forms stay unchanged. Million/billion comparisons here use the explicit unit. A correct transcription of the deliberate $1.67 error counts as correct **recovery**, while SEC verification must contradict the claim. This does not measure word error rate, semantic claim recall, OCR pixel localization or general financial accuracy. All observed tokens and expected values are retained in [number-accuracy.json](number-accuracy.json).

| Run | Financial mentions recovered / expected (extras) | Estimated cost USD | Wall seconds | Text provider |
|---|---|---:|---:|---|
| audio | audio: 5/5 (+0) | $0.02000625 | 21.917 | meta |
| audio-baseten | audio: 5/5 (+0) | $0.05492670 | 41.411 | baseten |
| audio-r2 | audio: 5/5 (+1) | $0.14798160 | 164.064 | meta |
| audio-two-voices | audio: 2/2 (+0) | $0.04339320 | 69.977 | meta |
| screenshot | image: 2/2 (+0) | $0.04134545 | 63.740 | meta |
| screenshot-small | image: 2/2 (+0) | $0.05829315 | 53.743 | meta |
| text | text: 2/2 (+0) | $0.04107640 | 61.421 | meta |
| text-baseten | text: 2/2 (+0) | $0.02624945 | 14.803 | baseten |
| text-words | text: 2/2 (+0) | $0.04250775 | 59.228 | meta |
| video | audio: 5/5 (+0); frame-1: 2/2 (+0); frame-2: 1/1 (+0); frame-3: 1/1 (+0) | $0.12916725 | 163.195 | meta |
| video-captioned | audio: 5/5 (+0); frame-1: 2/2 (+0); frame-2: 1/1 (+0); frame-3: 1/1 (+0) | $0.26119700 | 278.599 | meta |
| video-captioned-baseten | audio: 5/5 (+0); frame-1: 2/2 (+0); frame-2: 1/1 (+0); frame-3: 1/1 (+0) | $0.29306645 | 168.952 | baseten |
| video-silent | audio: unavailable; frame-1: 2/2 (+0); frame-2: 1/1 (+0); frame-3: 1/1 (+0) | $0.14587765 | 191.248 | meta |

**Total: $1.30508830 across 178 reserved API attempts.** Meta: $0.94696195; Baseten: $0.35812635. Token costs use recorded usage at $1.25/M input, $0.15/M cached input and $4.25/M output. ASR reserves `ceil(audio_seconds) × $0.18 / 3600` before upload. Failed or usage-less attempts retain the conservative reservation, so totals are estimates/bounds, not provider invoices. Each row includes decoding, OCR/ASR, extraction and verification. Runs sometimes overlap; their wall times are per input, not additive elapsed time. [Ledger](ledger.jsonl), [Meta prices](https://dev.meta.ai/docs/pricing-rate-limits), [Baseten prices](https://www.baseten.co/pricing/).

## Attribution and honest failures

The transcript is a timestamped lead. It is never L5 financial evidence: every accepted numeric claim still needs SEC L1–L4 evidence and a program check. Heard/read values, their normalized replacements, original character spans, and each claim's matching source turns remain in the ingest JSON. Repeated occurrences retain all matching turns. The HTML shows the original quote and speaker/time bracket alongside the verdict and links to filing evidence. No program mapping from diarization letters to names or roles exists. Meta documents [turn timestamps, not word timestamps](https://dev.meta.ai/docs/speech-to-text) and [session-scoped speaker labels](https://dev.meta.ai/docs/api-reference/voice/schemas).

- **audio:** labels A; A: 0–34620 ms; A: 34620–44860 ms; A: 44940–46860 ms.
- **audio-baseten:** labels A; A: 0–34540 ms; A: 34540–45020 ms; A: 45020–46860 ms.
- **audio-r2:** labels A; A: 0–34380 ms; A: 34540–44540 ms; A: 45180–46860 ms.
- **audio-two-voices:** labels A; A: 0–13660 ms; A: 14060–25820 ms.
- **video:** labels A; A: 60–34380 ms; A: 34460–45020 ms; A: 45020–46860 ms.
- **video-captioned:** labels A; A: 60–46860 ms.
- **video-captioned-baseten:** labels A; A: 0–34060 ms; A: 34620–44700 ms; A: 45100–46860 ms.

Observed limits:

- The first audio run returned a usable, labeled transcript but stopped at post extraction (`PostError`). Its extraction response was not retained by the then-current post checker. The same omission affected the first video's failed audio extraction. Their costs and stop states are preserved; the precise provider text cannot be reconstructed. The implementation now persists extraction/claim traces in `finally`, including failed attempts. Subsequent runs raised the per-call output limit from 4,000 to 8,000 and tried Baseten text reasoning; these are explicitly repeats.
- The Meta audio repeat failed later with `BadRequestError`, retaining one completed claim and the remaining extraction/source maps. That earlier revision did not yet persist the failed claim trace; the ledger reservation is kept. Provider failures are not program verdicts. See each ingest record for exactly how far it got.
- ASR duplicated words and rendered the written name **Kevan Parekh** as **Kevan Park** in the first recording. Preserved financial numbers do not establish quote fidelity or who actually spoke. Whole-turn spans can cover tens of seconds; a number does not inherit a fabricated word timestamp.
- **Diarization failure:** the two-voice fixture contains two deliberately different synthetic voices, but ASR labeled both turns **A**. Stage 6 records that labeled timestamps exist; it does not mean speaker separation or identity was correct.
- **Known false contradiction:** `video-captioned-baseten` extracted the true FY2025Q3 EPS-growth statement as `Apple reported EPS growth of 12%.`, dropping its period context. The agent compared FY2026Q3 EPS (2.02) with FY2025Q3 (1.57), 28.66% growth, and the program contradicted it. The intended release growth is 1.57 / 1.40 − 1 = 12.14%, which supports 12%. This is an end-to-end context-loss failure despite correct ASR numbers and successful tool/program stages. The saved verdict remains unchanged. In `audio-baseten`, two larger financial clauses were rejected for adding the date `28`; only the growth clause was checked. Reaching a stage is not complete claim recall or a correctness score.
- Row-only slides expose extraction/context and routing limits: some rewrites add `28` from the date heading, which the existing post guard correctly rejects because that number is absent from the selected quote. Another filed EPS can return insufficient evidence. Captioned slides are a separate post-hoc control, not a replacement for those failures.
- Silent video has no speech channel; its frame results remain usable. Sampling only three frames can miss other visual claims, and a frame timestamp provides no speaker identity. No full-video understanding, public replay ingestion, long-call chunking, word alignment, verified CFO attribution, overlap benchmark or human-name verification is implemented.
- The first text/screenshot runs overlapped before own-input cost accounting was added. Their corrected cost is the sum of their recorded calls; `initial-ingest.json` and `original_recorded_cost_usd` retain the initial shared-delta values. Later runs track their own reservation IDs over the shared locked budget. The corrected per-run total reconciles to the ledger.

## Reproduce offline

```sh
python3 scripts/multimodal/build_report.py
sh scripts/verify.sh
UV_OFFLINE=1 sh scripts/verify.sh
```

The report builder only reads saved records. Offline tests replay the actual Meta OCR/ASR/text and Baseten text responses against committed SEC data, including deliberate false numbers. Codec checks are optional when ffmpeg/ffprobe are absent; response replay does not require those binaries. No keys, external audio or ignored caches are needed. [Runtime](../../../src/claimcheck/ingest.py), [offline tests](../../../tests/test_ingest.py), [paid probe runner](../../../scripts/multimodal/run_probe.py). The paid runner is intentionally separate from verification and refuses to overwrite a saved run.

Validation: **372 product tests, 83 demo tests and 41 standalone Node tests passed**; `UV_OFFLINE=1 sh scripts/verify.sh` passed all five final checks. [Verification receipt](validation.json).
