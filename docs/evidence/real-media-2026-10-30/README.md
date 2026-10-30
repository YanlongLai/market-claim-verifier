# Real issuer media candidates — 2026-10-30

These are **real company materials**, separate from the previous synthetic Apple controls. They are candidate inputs, **not an evaluated benchmark or automatic ground truth**. [Catalogue](catalogue.json) records source URLs, periods, hashes and preparation status. No paid model calls were made during initial collection. Subsequently, the three Tesla PNGs were used in [unscored three-provider diagnostics](../fair-multimodal-v1/REPORT.md) and [two retained Baseten product checks](../stock-context-posthoc-2026-10-30/REPORT.md). They still lack complete independent gold and are not an accuracy benchmark.

| Material | Available now | Intended check |
|---|---|---|
| Tesla Q3 2026 [financial table, page 4](images/tesla-q3-2026-04.png) | Source-faithful PNG, visually inspected | Columns/periods, units, GAAP versus non-GAAP; SEC-backed facts where available |
| Tesla Q3 2026 [operating table, page 5](images/tesla-q3-2026-05.png) | Source-faithful PNG, visually inspected | Operating metrics; unsupported metrics must not receive invented SEC evidence |
| Tesla Q3 2026 [charts, page 23](images/tesla-q3-2026-23.png) | Source-faithful PNG, visually inspected | Axis/series/period extraction; graph-only values may need abstention |
| Microsoft FY2027 Q1 [earnings slides](https://aka.ms/slidesfy27q1) | Official PPTX downloaded locally; container validated | Convert to PDF/images before ingestion; PPTX is not supported directly |
| Microsoft FY2027 Q1 [call and transcript](https://www.microsoft.com/en-us/Investor/events/fy-2027/earnings-fy-2027-q1) | Official player and transcript page verified | Real speech, guidance versus reported facts; no recording downloaded yet |
| Tesla Q3 2026 [webcast](https://ir.tesla.com/webcast-2026-10-21) | Official replay page verified | Real Q&A and speech; no recording downloaded yet |

## Provenance and reuse

The three PNGs are unmodified page renderings from Tesla's [official Q3 2026 update PDF](https://assets-ir.tesla.com/tesla-contents/IR/TSLA-Q3-2026-Update.pdf), linked by its [IR results table](https://ir.tesla.com/). Original deck: 33 pages; raw PDF retained locally at `.cache/real-media-2026-10-30/tesla-q3-2026.pdf`. The catalogue records its SHA-256 and reproducible render commands. Tesla owns the slide content; these attributed test excerpts are not relicensed under the repository's MIT code license.

The webcasts are source-discovery entries, **not local MP3/MP4 test files**. No login, stream extraction or browser automation was added. General URL ingestion remains unsupported. A player link or transcript is not evidence that an audio/video path was tested.

## Next independent accuracy evaluation gate

Before a new accuracy study, independently label selected claims, source locations and expected supported/contradicted/insufficient outcomes using the [new SEC snapshot](../sec-refresh-2026-10-30/REPORT.md). Freeze the set, budget and sampling policy. Keep real inputs separate from any deliberately altered negative controls. Measure numeric extraction and claim recall separately from verdict accuracy, cost and latency. Archive every attempt under a new evidence directory. Do not tune on these pages and later call them unseen test data.

Microsoft’s original deck is retained locally at `.cache/real-media-2026-10-30/microsoft-fy27q1.pptx`; its hash and direct official download URL are in the catalogue. It has not been converted or tested by the verifier.
