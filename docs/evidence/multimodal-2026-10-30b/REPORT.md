# Recall fixes — 2026-10-30b

**Two planned post-hoc development probes, one adaptive long-call repeat and one frozen-transcript recheck; new estimated spend $1.55712625 / $8; combined multimodal spend $3.85742535 / $20.** Known self-made fixtures, not a held-out evaluation. No other media probes were rerun. [Frozen selection and budget](probe-set.json), [machine comparison](before-after.json).

## Before / after

Coverage counts expected financial numeric assertions whose values occur in an accepted rewrite and its exact source quote. Dates and period labels are excluded. The deliberate $1.67 EPS error counts as recovered input and must be contradicted. Each repeated source occurrence counts separately; reused verification is disclosed below. Coverage is not verdict accuracy.

| Input | Recovered mentions before → after | Guarded coverage before → after | Program-checked before → after | EPS error before → after |
|---|---:|---:|---:|---|
| [text](text/ingest.html) | 2/2 → 2/2 | 2/2 → 2/2 | 2/2 → 2/2 | insufficient_evidence → contradicted |
| [long-call](long-call/ingest.html) | 56/60 → 59/60 | 19/60 → 0/60 | 19/60 → 0/60 | contradicted → missed |
| [long-call-r2](long-call-r2/ingest.html) | 56/60 → 55/60 | 19/60 → 44/60 | 19/60 → 44/60 | contradicted → contradicted, rejected |
| [long-call-frozen](long-call-frozen/ingest.html) | 56/60 → 55/60 | 19/60 → 50/60 | 19/60 → 50/60 | contradicted → contradicted |

## Diagnosis and changes

- **Extraction, not ASR truncation, dominated the recorded long-call loss.** Its 6,606 normalized characters used two extraction requests, each returning only three surface rewrites of repeated facts. Both responses completed below the 8,000-token ceiling; most output tokens were reasoning. All six surviving proposals were checked, so the old eight-claim cap did not bind this run. The 0–600s / 590–720s audio uploads and absolute tail times were already intact. One non-exact ASR boundary overlap remained unresolved.
- **Long extraction is now local.** Inputs above 6,000 characters use at most 1,400-character windows, prefer individual paragraph/turn boundaries, and retain 200 characters of overlap plus unique nearby stated period context. The default eight-check allowance applies per extraction window; the shared reservation ledger still refuses calls over budget. Quote variants survive screening, duplicate overlap spans merge, and identical final rewrites with the same ticker/kind reuse one verification. Explicit quote spans limit source credit to the extraction window. Semantic paraphrases are not consolidated.
- **The first new long-call run failed visibly.** Fresh ASR recovered 59/60 expected financial mentions, but the first extraction used all 8,000 output tokens (7,997 reasoning) and returned no JSON. It remains a partial failure with zero checked assertions in the table. The adaptive `long-call-r2` requests low reasoning effort for long-input extraction, retains the 8,000-token ceiling and shared dollar cap, and reruns the same affected clip. The changed reasoning setting is a comparison confound; no attempt was discarded.
- **Context and punctuation follow-up.** The adaptive media run exposed two synthetic-context-prefix quotes rejected as non-contiguous, plus a legitimate `2025,` rejected as a new number. Nearby period context now goes in instructions outside the quotable post; fiscal and calendar context must agree before propagation. A trailing comma no longer makes a stated context year fail the period-number exception. Date days and financial quantities still require the quote. The final `long-call-frozen` run rechecks the exact raw ASR text from `long-call-r2` with fresh extraction/verification and no new ASR. [Frozen text and source hashes](frozen-transcript.json). This text projection makes no new timing or speaker-attribution claim.
- **The text EPS miss was evidence routing.** Its exact claim already said fiscal Q3 2025. The model labeled it `reported_in_release` and cited both a failed release search and a valid L2 $1.57 XBRL fact. The release-only path ignored that fact. An ordinary GAAP level claim can now use cited L1/L2 XBRL only when issuer, metric, unit and explicit period match and there is no cited release quote. Guidance/non-GAAP still require release evidence. The saved output stream now deterministically contradicts $1.67. This does not relax missing-period handling.
- **Regression coverage.** Tests retain the original lost-period 12% growth case (1.57 / 1.40 − 1 = 12.14%, supported), undated claims stopping before model/SEC access, date/number invention rejection, overlap deduplication, distinct quote variants, scoped periods, per-window claim limits, tail/context retention and verification reuse. Wrong issuer/metric/calendar-period fallback is rejected.

## Observed limits and protocol

- **text:** status `completed`; 2 accepted claim rows, 2 unique verification traces, 0 reused checks; 2/2 expected numeric assertions program-checked; 0 extra input financial mentions. Verdicts: `{"contradicted": 1, "supported": 1}`. [Protocol](text/protocol.json), [raw ingest](text/ingest.json).
- **long-call:** status `partial`; 0 accepted claim rows, 0 unique verification traces, 0 reused checks; 0/60 expected numeric assertions program-checked; 5 extra input financial mentions. Verdicts: `{}`. [Protocol](long-call/protocol.json), [raw ingest](long-call/ingest.json).
- **long-call-r2:** status `completed`; 35 accepted claim rows, 29 unique verification traces, 6 reused checks; 44/60 expected numeric assertions program-checked; 9 extra input financial mentions. Verdicts: `{"contradicted": 12, "insufficient_evidence": 4, "rejected": 3, "supported": 19}`. [Protocol](long-call-r2/protocol.json), [raw ingest](long-call-r2/ingest.json).
  Rejected proposals remain in the raw report: 3; no rejected rewrite earns coverage.
- **long-call-frozen:** status `completed`; 43 accepted claim rows, 32 unique verification traces, 11 reused checks; 50/60 expected numeric assertions program-checked; 9 extra input financial mentions. Verdicts: `{"contradicted": 15, "insufficient_evidence": 1, "supported": 27}`. [Protocol](long-call-frozen/protocol.json), [raw ingest](long-call-frozen/ingest.json).
  On identical heard text: guarded/program-checked coverage 44/60 → 50/60. Fresh extraction is still stochastic.

Fresh ASR can change number recovery, wording and speaker labels, so the live long-call comparison also reflects ASR variability. The synthetic 720-second clip repeats one short eSpeak NG narrator with silence. Whole-turn times and chunk-scoped labels do not prove speaker identity or diarization. Exact-quote coverage can remain incomplete; eight unique checks per window, output limits and the dollar cap still bound recall. No real-call or exhaustive-video benchmark is claimed. The earlier seven-run evidence and all failures remain unchanged.

Some date-bearing revenue rows remain `insufficient_evidence`: their numeric revenue/growth checks pass, but a separate period-end-date `other` subclaim is unchecked. Model summaries can disagree with program results (including whole-percent rounding); only program verdicts are counted. All 39 growth checks in the final frozen report are supported (including reused checks); its numeric contradictions are the deliberate EPS error. The final frozen text still misses expected numeric assertions despite retaining all accepted quotes. A frozen text recheck is not a successful fresh media or attribution run.

Runtime models are Meta Muse Spark 1.3 (text control), Meta Muse Spark Open via Baseten (long-call text) and Muse Voice Transcribe 1.0 (ASR). Keys load only through `claimcheck.config` and are redacted; SEC access uses committed snapshots only. Text retains 4,000 output tokens and long-call retains 8,000, matching their baselines. The adaptive media repeat and frozen-text recheck explicitly request low reasoning effort for extraction. Protocols record actual UTC times, hashes and model IDs. HTTP 5xx retries retain separate reservations/traces. The shared new ledger has an $8 total cap and $4 provider partitions.

Each live protocol preserves the hashes actually used. The final source hashes are in the validation receipt; the comparison JSON lists source drift for each run. The XBRL fallback was tightened to require the exact source level literal after the frozen probe launched; the saved final text/frozen output streams replay through that final guard with unchanged verdicts. Legacy long extraction replay retains its archived windows/context transport; the intermediate media repeat is kept as a historical run, not relabeled as final-code inference.

## Reproduce offline

```sh
python3 scripts/multimodal/build_recall_report.py
UV_OFFLINE=1 sh scripts/verify.sh
```

The builder reads saved evidence only. Paid probes are separate and refuse to overwrite runs. Full-suite and disconnected-verifier results are recorded in [validation.json](validation.json).
