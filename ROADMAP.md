# Product roadmap

Current financial evidence tiers are **L1–L3 SEC XBRL** ([source policy](docs/DATA_SOURCES.md#sec-evidence-tiers), [registry](sources/registry.yaml)) and **L4 8-K earnings releases** (built 2026-10-29: [README section](README.md#l4-earnings-release-evidence), [evaluation](docs/evidence/eval-l4-2026-10-29/ANALYSIS.md)). The remaining items below are plans, without delivery dates or completed-work claims.

| Planned capability | Intended evidence and boundary | Current reference |
| --- | --- | --- |
| **L5 — earnings-call audio** | Use a **Meta speech model** to locate and transcribe earnings-call statements with speaker/timestamp evidence. Answer **“did the company say it?”**; a statement's presence does not verify the forecast or assertion itself. Model selection and evaluation remain planned. | [Current evidence policy](docs/DATA_SOURCES.md), [current model adapters](src/claimcheck/providers.py) |
| **Market-multiple claims** | Check a stated multiple against cited market data and a period-specific financial denominator, retaining timestamp, units and calculation. Keep valuation opinions separate from checkable arithmetic. | [Currently skipped valuation example](examples/posts/bigtech-thread.txt), [post classification](src/claimcheck/post.py) |
| **Taiwan filings** | Add Taiwan filing sources, company/period/unit mappings and cited reference cases. Evaluate source-specific parsing and period ambiguity before describing them as supported evidence. | [Current SEC-only ground truth](docs/DATA_SOURCES.md#ground-truth-sources), [Chinese post example](examples/posts/tw-social-post.txt) |

These plans do not expand the scope of the [recorded benchmark](docs/evidence/eval-v2-2026-10-27/REPORT.md) or the [current limitations](JUDGES.md#limits-to-keep-in-view).
