# Real Microsoft webcast audio/video results

One genuine CFO segment, 60 seconds (source 18:14–19:14), tested as WAV and MP4 across three text routes. Audio and visuals originate in the official webcast; no synthetic narration or replacement slides. This is a six-run **smoke test on one scene**, not six independent examples or a provider accuracy ranking.

[Inputs and preregistered protocol](../../../eval/real-av-v1/README.md) · [Exact media/source manifest](../../../eval/real-av-v1/manifest.json) · [Publisher caption reference](../../../eval/real-av-v1/caption-reference.json) · [Machine results](summary.json)

| Route / format | Pipeline | Caption numeric tokens found* | Proposed / program-checked | Recorded outcomes | Cost USD |
| --- | --- | ---: | ---: | --- | ---: |
| [meta / wav](meta/wav/ingest.html) | partial | 11/11 | 4 / 3 | {'insufficient_evidence': 3, 'failed': 1} | 0.082919 |
| [meta / mp4](meta/mp4/ingest.html) | partial | 11/11 | 12 / 4 | {'insufficient_evidence': 4, 'rejected': 8} | 0.061106 |
| [baseten / wav](baseten/wav/ingest.html) | completed | 11/11 | 4 / 4 | {'insufficient_evidence': 4} | 0.052462 |
| [baseten / mp4](baseten/mp4/ingest.html) | partial | 11/11 | 12 / 4 | {'insufficient_evidence': 4, 'rejected': 8} | 0.044378 |
| [fireworks / wav](fireworks/wav/ingest.html) | completed | 11/11 | 4 / 4 | {'insufficient_evidence': 4} | 0.008371 |
| [fireworks / mp4](fireworks/mp4/ingest.html) | completed | 11/11 | 16 / 4 | {'insufficient_evidence': 4, 'rejected': 12} | 0.046936 |

*Numeric presence checks 11 reference occurrences including repeated values; it does not prove the number belongs to the correct metric, period or accounting basis. Captions are publisher reference material, not independently reviewed gold. No word error rate or financial accuracy score is claimed.

## What this exercises

- Each case makes fresh Meta ASR calls; MP4 also uses three sampled Meta OCR frames. Raw media requests/responses, normalized text and model/tool traces are retained under each case. Fresh preprocessing may vary, so this does not isolate verifier differences like the earlier frozen-preprocessing benchmark.
- One source scene becomes two encodings. The clip has genuine speech over financial slides, not fast-moving footage or multiple visible speakers. It does not measure long-call recall, speaker identity, or audio/video synchronization.
- Four proposals per extraction window/channel are selected; bounded extraction cannot promise all eleven spoken numeric mentions are checked. Failed, rejected and insufficient results remain public.
- One Baseten WAV model narrative claims the operating margin is contradicted using other periods, but the final program verdict is insufficient_evidence with unchecked_other_claim. That narrative is not a validated correction; see the retained result and Chinese diagnosis.
- The speaker discusses adjusted EPS $4.89 while the displayed GAAP table shows $4.92. Those differing bases are not automatically a contradiction. The current pipeline checks audio and frames separately; it does not reconcile them.
- The audio says “this quarter”; the source FY27 Q1 label is preserved as metadata but not injected into the transcript. Missing explicit periods must fail closed. Video frames contain their own period headers.
- Frozen SEC evidence is used without network fetching. Missing release, constant-currency or adjusted-metric evidence is an expected product limitation; this suite does not prove those claims false.

## Cost and reuse

All amounts are estimates/reservations, not invoices or remaining account balances. Shared preprocessing is charged to Meta. Costs include recorded failures and transient retries. New caps are Meta $3, Baseten $2, Fireworks $2; combined task totals remain under $40 each.

| Platform | New suite USD | Combined task USD |
| --- | ---: | ---: |
| meta | 0.21419575 | 4.45021510 |
| baseten | 0.05921035 | 2.15855835 |
| fireworks | 0.02276475 | 2.03641025 |

Run `python3 scripts/report_real_av.py` to rebuild this report offline. Do not rerun the paid runner merely to inspect results. Each original clip offset is 1094 seconds: add it to the per-clip ASR/frame times to find the source-webcast location. ASR timestamps describe turns, not verified word timestamps.

The original short media files and all decoded media used by the pipeline are retained. Microsoft retains rights to webcast/slide content; media excerpts are not relicensed under MIT. No signed player URLs or credentials are needed to inspect committed inputs.

[Meta stock summary](meta/summary/stock-review.html) · [Baseten stock summary](baseten/summary/stock-review.html) · [Fireworks stock summary](fireworks/summary/stock-review.html)

See [Chinese findings and next steps](ANALYSIS.zh-TW.md) for the completed case diagnosis.
