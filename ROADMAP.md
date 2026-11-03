# Product roadmap

The [Day 5 delivery plan](docs/DAY5_PLAN.md) defines current priority and acceptance gates. US equities only; Taiwan filings are outside this hackathon scope.

Current financial evidence tiers are **L1–L3 SEC XBRL** ([source policy](docs/DATA_SOURCES.md#sec-evidence-tiers), [registry](sources/registry.yaml)) and **L4 8-K earnings releases** (built 2026-10-29: [README section](README.md#l4-earnings-release-evidence), [evaluation](docs/evidence/eval-l4-2026-10-29/ANALYSIS.md)). The remaining items below are plans, without delivery dates or completed-work claims.

| Planned capability | Intended evidence and boundary | Current reference |
| --- | --- | --- |
| **L5 — earnings-call audio** | Use a **Meta speech model** to locate and transcribe earnings-call statements with speaker/timestamp evidence. Answer **“did the company say it?”**; a statement's presence does not verify the forecast or assertion itself. Model selection and evaluation remain planned. | [Current evidence policy](docs/DATA_SOURCES.md), [current model adapters](src/claimcheck/providers.py) |
| **Market-multiple claims** | Check a stated multiple against cited market data and a period-specific financial denominator, retaining timestamp, units and calculation. Keep valuation opinions separate from checkable arithmetic. | [Currently skipped valuation example](examples/posts/bigtech-thread.txt), [post classification](src/claimcheck/post.py) |

These plans do not expand the scope of the [recorded benchmark](docs/evidence/eval-v2-2026-10-27/REPORT.md) or the [current limitations](JUDGES.md#limits-to-keep-in-view).

## Next after the real-world News probe

The [80-item News study](docs/evidence/real-world-2026-11-02/REPORT.md) freezes the current implementation before execution. Its [review list](docs/evidence/real-world-2026-11-02/GOLD_REVIEW.md) separates unresolved truth from expected abstention; these are development priorities, not delivered capabilities.

| Next work | Evidence and acceptance boundary |
|---|---|
| Bind claim issuer to SEC entity before arithmetic | [Baseten post RW046](docs/evidence/real-world-2026-11-02/baseten/post/RW046/report.json) maps Taiwan's Hon Precision to Honeywell (`HON`) and returns a contradiction. Require independently resolved issuer/CIK identity; ambiguous aliases and non-US companies must fail closed before accepting numeric comparisons. Replay the retained failure as a regression. |
| Review paraphrase identity before the next paid sample | [Input errata](docs/evidence/real-world-2026-11-02/PARAPHRASE_REVIEW.md): one translated company-name error and one ambiguous forecast issuer. Keep authoritative name/issuer-ID provenance and route truncated or multi-company snippets to review before freezing model inputs. Preserve this run's original inputs and separately labelled sensitivity analysis. |
| Route unsupported scope early and finalize pending tool calls safely | Non-financial statements still consume tool turns; [Meta AWS RW002](docs/evidence/real-world-2026-11-02/meta/agent/RW002/trace.json) ends with HTTP 400 because a function call lacks its tool output at finalization. Add explicit source/domain routing and replay tests for turn-limit transitions before another paid repeat. Report safe skips and provider failures separately. |
| Bound post extraction and expose failed coverage | [RW060](docs/evidence/real-world-2026-11-02/findings.md) produces an incomplete extraction on Meta and a 90-second timeout on Fireworks. Preserve failure/cost records, distinguish extraction failure from abstention, and replay these cases when changing extraction completion and timeout handling. |
| Resolve news periods before claiming wider accuracy | Obtain explicit article/issuer period context for the 23 ambiguous US claims; retain separate reviewed-gold records. Publication date or a matching number cannot supply a missing reporting period. |
| Extend release coverage for actual news metrics | Check investment-income labels, US comparable-store sales and other segment KPIs against dated, definition-specific issuer tables. Add foreign-issuer 6-K discovery for cases such as Shell. Preserve GAAP/non-GAAP and consolidated/segment distinctions. |
| Make annual guidance period handling auditable | Investigate the UnitedHealth 2026 adjusted-EPS minimum case; only accept period/comparator normalization when primary context and issuer fiscal calendar establish it. Keep explicit minimum guidance distinct from a point forecast. |
| Add market-data evidence for price moves | Require exchange/instrument, session or observation timestamp, currency, adjusted/unadjusted prices and a reproducible return calculation. Opinion and merger hypotheticals remain outside numeric filing verification. |
| Treat Taiwan as a separately validated evidence domain | Add MOPS/TWSE issuer filings, ROC-year conversion, TWD units and quarterly/YTD alignment with independent gold before claiming TW coverage. Current Taiwan outcomes measure abstention only. |
| Add article and social sources with a frozen URL list | Follow [NEXT_SOURCES](docs/evidence/real-world-2026-11-02/NEXT_SOURCES.md): Owner-provided URLs, permitted acquisition, paraphrase-only public records, dated engagement criteria and current Threads API/terms verification. No Threads collection occurred in this task. |
