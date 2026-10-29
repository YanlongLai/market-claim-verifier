# Multimodal input probe — 2026-10-30

**7 exploratory hardening runs; estimated new spend $0.99521080; combined with the recorded $1.30508830: $2.30029910, below the $15 task cap.** This is a post-hoc development probe on known synthetic media, not a held-out evaluation. Every stop state, rejected rewrite and insufficient-evidence result remains in the records.

## Protocol and media

Runtime inference uses only Meta models: `muse-spark-1.3` for OCR/Meta text, `meta-models/muse-spark-open-1026` for Baseten text, and `muse-voice-transcribe-1.0` for ASR. Keys load through `claimcheck.config` and are redacted. SDK retries are zero. HTTP 500/502/503/504 gets at most three attempts with 1s/2s backoff; each attempt has its own reservation and trace. Other errors are not retried by this policy. Failed attempts retain conservative reservations. The new locked ledger is capped at $13.69 (Meta $8, Baseten $5.69), reserving $1.31 for prior spend. All SEC retrieval is restricted to committed hash-checked snapshots; no live SEC or external call media is used.

[Probe set and baseline choices](probe-set.json) list the seven cases. The evidence directory uses the requested 2026-10-30 label; actual UTC execution times are in each `protocol.json`. Text and screenshot retain the baseline 4,000-token limit; remaining cases use 8,000 (the row-only baseline used 4,000, a comparison confound). Source hashes, provider IDs, input hashes, usage, failure attempts and post/tool traces are retained per run.

The short media are unchanged from the [2026-10-29 report](../multimodal-2026-10-29/REPORT.md): Apple FY2025 Q3 release excerpts with EPS deliberately changed from $1.57 to $1.67; row slides retain both correct and wrong EPS. All voices are self-made eSpeak NG offline formant narration, not any executive. The new [720-second FLAC](../../../tests/fixtures/multimodal/long-call.flac) repeats the committed narration once per minute, with disclosed silence; it is not a real long earnings call. [Long generation record and speech windows](../../../tests/fixtures/multimodal/long-generation.json), [generator](../../../scripts/multimodal/make_long.py), [all fixture hashes](../../../tests/fixtures/multimodal/manifest.json).

Period introductions and nearby headings now enter claim extraction. A source-backed program fallback carries a unique nearby fiscal period into otherwise undated claims and records the original rewrite plus context spans. Mixed context stays unresolved. A numeric financial claim with no dated period gets program `insufficient_evidence` with `missing_period`, before any verifier-model or SEC call. Date-day and financial-number inventions still fail the quote guard; the extractor must include a date heading in its exact contiguous quote or use the stated fiscal quarter. Long audio is decoded without truncation into <=600s WAVs with 10s overlap; turn timestamps are offset to absolute media time. Only exact intersecting suffix/prefix words are removed, with an edit record. Non-exact overlaps are retained and flagged. Speaker labels are chunk-scoped; no cross-chunk speaker identity is inferred. Long transcripts use bounded, overlapping extraction windows.

## Capability matrix

✓ means reached for all relevant channels; ✗ partial means some; ✗ means none; — means not applicable. Stage 4 needs cited numeric SEC evidence. Stage 5 includes program `insufficient_evidence`. Stage 6 means unverified labels and whole-turn times, never named-person attribution or successful diarization.

| Input / run | 1 Decode | 2 Text + offsets | 3 Claims | 4 SEC | 5 Program | 6 Attribution | Reason / limit |
|---|---|---|---|---|---|---|---|
| [audio](audio/ingest.html) (baseten) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Applicable stages reached; see verdicts and attribution limits below |
| [audio-two-voices](audio-two-voices/ingest.html) (meta) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Applicable stages reached; see verdicts and attribution limits below |
| [long-call](long-call/ingest.html) (baseten) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Applicable stages reached; see verdicts and attribution limits below |
| [screenshot](screenshot/ingest.html) (meta) | ✓ | ✓ | ✓ | ✓ | ✓ | — | Applicable stages reached; see verdicts and attribution limits below |
| [text](text/ingest.html) (meta) | ✓ | ✓ | ✓ | ✓ | ✓ | — | insufficient_evidence: 1 |
| [video](video/ingest.html) (meta) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Applicable stages reached; see verdicts and attribution limits below |
| [video-captioned](video-captioned/ingest.html) (baseten) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Applicable stages reached; see verdicts and attribution limits below |

## Before / after on the recorded media

Recall here means **expected financial numeric assertions covered by an accepted rewrite and its exact source quote**. The rewrite must contain the value; a broad quote alone cannot recover another row. Dates/quarter labels are excluded. Both level and growth mentions count; the two 12% assertions are separate source occurrences. Correctly recovering the deliberate $1.67 error counts toward recall, while verification must contradict it. Failed/absent extraction counts as missed. This metric is narrower than semantic claim recall and is not a correctness score. [Per-channel measurements and definitions](before-after.json). Baselines and new runs use matching text providers; there is one planned new run per case and no discarded repeats.

| Input | Baseline run | Before accepted / expected | After accepted / expected | After program-checked / expected |
|---|---|---:|---:|---:|
| text | [text](../multimodal-2026-10-29/text/ingest.html) | 2/2 | 2/2 | 2/2 |
| screenshot | [screenshot](../multimodal-2026-10-29/screenshot/ingest.html) | 2/2 | 2/2 | 2/2 |
| audio | [audio-baseten](../multimodal-2026-10-29/audio-baseten/ingest.html) | 1/5 | 5/5 | 5/5 |
| audio-two-voices | [audio-two-voices](../multimodal-2026-10-29/audio-two-voices/ingest.html) | 2/2 | 2/2 | 2/2 |
| video | [video](../multimodal-2026-10-29/video/ingest.html) | 2/9 | 8/9 | 8/9 |
| video-captioned | [video-captioned-baseten](../multimodal-2026-10-29/video-captioned-baseten/ingest.html) | 9/9 | 9/9 | 9/9 |
| long-call | New 12-minute control | — | 19/60 | 19/60 |

## Number recovery, cost and latency

Ordered financial mentions recovered from OCR/ASR are scored separately from extraction recall. No word error rate, OCR pixel boxes or real-call generalization is claimed. [All numbers and spans](number-accuracy.json).

| Run | Financial mentions recovered / expected (extras) | Estimated USD | Wall seconds | Verdict / stop counts |
|---|---|---:|---:|---|
| audio | audio: 5/5 (+0) | $0.07906405 | 56.432 | contradicted: 1, supported: 2 |
| audio-two-voices | audio: 2/2 (+0) | $0.04922765 | 69.825 | contradicted: 1, supported: 1 |
| long-call | audio: 56/60 (+6) | $0.24054155 | 258.776 | contradicted: 2, supported: 4 |
| screenshot | image: 2/2 (+0) | $0.07378115 | 59.651 | contradicted: 1, supported: 1 |
| text | text: 2/2 (+0) | $0.06123945 | 85.545 | insufficient_evidence: 1, supported: 1 |
| video | audio: 5/5 (+2); frame-1: 2/2 (+0); frame-2: 1/1 (+0); frame-3: 1/1 (+0) | $0.33594730 | 312.059 | contradicted: 2, supported: 5 |
| video-captioned | audio: 5/5 (+0); frame-1: 2/2 (+0); frame-2: 1/1 (+0); frame-3: 1/1 (+0) | $0.15540965 | 106.602 | contradicted: 2, supported: 5 |

**Total: $0.99521080 across 120 reserved API attempts.** Token pricing: $1.25/M input, $0.15/M cached input, $4.25/M output; ASR `ceil(upload_seconds) × $0.18 / 3600`, including overlap on both uploads. Costs are ledger estimates, not a provider invoice. Failed/usage-less reservations stay charged.

## ASR timing, labels and observed limits

- **audio:** labels A; A: 60–34220 ms; A: 34460–44780 ms; A: 45100–46860 ms.
- **audio-two-voices:** labels A; A: 220–13980 ms; A: 14060–23820 ms; A: 24060–25820 ms.
- **long-call:** labels chunk-1:A, chunk-2:A; chunk-1:A: 9820–57020 ms; chunk-1:A: 70220–117180 ms; chunk-1:A: 129900–177420 ms; chunk-1:A: 190060–237100 ms; chunk-1:A: 249820–297420 ms; chunk-1:A: 310060–357100 ms; chunk-1:A: 370060–417020 ms; chunk-1:A: 429820–477260 ms; chunk-1:A: 490060–537260 ms; chunk-1:A: 550140–597020 ms; chunk-2:A: 590300–597020 ms; chunk-2:A: 610380–644300 ms; chunk-2:A: 644300–655180 ms; chunk-2:A: 655180–657100 ms; chunk-2:A: 670060–704220 ms; chunk-2:A: 704540–717100 ms.
- **video:** labels A; A: 0–34300 ms; A: 34620–45100 ms; A: 45100–46860 ms.
- **video-captioned:** labels A; A: 0–34380 ms; A: 34380–44780 ms; A: 44940–46860 ms.

- **Period regression fixed on the recorded case:** the new captioned Baseten-text video retains FY2025 Q3 and supports the 12% EPS-growth clause using 1.57 / 1.40 − 1 = 12.14%. The short audio and row-only video also support this growth clause. The original false contradiction in the 2026-10-29 evidence is unchanged. Offline regression uses that exact lost-period extraction and the previously recorded correct SEC/tool responses; period-less growth and level claims stop before model/SEC calls.
- **Recall improved on short media, with remaining misses:** short audio numeric-assertion coverage rose from 1/5 to 5/5; row-only video from 2/9 to 8/9 (its frames alone rose from 2/4 to 4/4). No new rewrite was rejected for adding the date 28. The guard still rejects the original date-inventing quotes in regression tests; a real date heading must be included in the selected contiguous quote. The row-only ASR has two extra financial mentions and one of its recovered repeated 12% mentions is not covered by a guarded rewrite. All input numbers and all proposals are retained.
- **Remaining verdict miss:** the new text control returns `insufficient_evidence` for the deliberate $1.67 EPS error, despite a model summary saying contradicted. The program rejects its release citation with `release_quote_issuer_metric_kind_unit_or_period_mismatch`. It is not counted as a contradiction or provider failure. The screenshot, short audio, two-voice, both videos and long clip do contradict their deliberate EPS errors. There were no false-supported verdicts observed in these controls; this is not a general error-rate claim.
- **Actual provider recovery:** the row-only Meta-text video encountered two HTTP 503 persistence-service failures. Both retried once after 1s and continued; failed-attempt reservations and retry metadata remain in the model traces. Separate expired-state HTTP 400 responses in screenshot/video used the existing one-time history fallback, not the 5xx retry policy. No provider failure was converted to a program verdict. Offline fault tests exercise retry exhaustion, nontransient rejection, reservation refusal and trace redaction for extraction, verification, OCR and ASR.
- **Diarization remains wrong:** the two deliberately different synthetic voices still share label A. Whole-turn times and labels do not identify Kevan Parekh, a CFO or any real speaker. Names can still be misspelled and words duplicated.
- **Long-call limits:** the 720s clip uploaded as 0–600000ms and 590000–720000ms segments. The final returned turn is 704540–717100ms, correctly beyond the first upload, within the last known speech window. ASR recovered 56/60 expected financial mentions with six extras. Guarded exact-quote coverage is only 19/60 numeric assertions; six surface-form rewrites repeat three semantic facts, and one quoted variant does not cover all repeated readings. This remains incomplete recall, even though all six stage types were reached. One non-exact boundary overlap was retained and explicitly marked unresolved; no word timing or perfect overlap benchmark is claimed. Chunk labels `chunk-1:A` and `chunk-2:A` do not establish two distinct speakers. The synthetic clip repeats one short narrator with silence and cannot establish performance on a heterogeneous real call.
- **Scope and final-code replay:** audio/video accepts local inputs up to 128 MiB and two hours, with at most eight verified claims per channel by default; video still samples only three frames and can miss other visuals. Long-text extraction is windowed and exact-string rewrites are deduplicated, not semantically consolidated. After probe launch, conservative edge handling was added for spelled-out undated quantities, calendar-basis preservation and period phrases following a row; all seven recorded output streams replay through the final runtime without new inference, including the real 503s and expired-state fallbacks. Each live protocol keeps the hashes of the source actually used. These development fixes, reused media and output-limit changes preclude a held-out accuracy claim.

## Reproduce offline

```sh
python3 scripts/multimodal/build_hardening_report.py
sh scripts/verify.sh
UV_OFFLINE=1 sh scripts/verify.sh
```

Report rebuilding reads saved evidence only. The paid [probe runner](../../../scripts/multimodal/run_probe.py) refuses to overwrite runs and is separate from verification. [Runtime](../../../src/claimcheck/ingest.py), [hardening regressions](../../../tests/test_ingest_hardening.py). Codec integration is optional without ffmpeg/ffprobe; the full verifier does not render media or call models.

Validation: **777 product, 83 demo and 41 standalone Node tests passed**; full suite and `UV_OFFLINE=1 sh scripts/verify.sh` passed. [Receipt](validation.json).
