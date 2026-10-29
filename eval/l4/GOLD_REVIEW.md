# L4 gold registration — 2026-10-29

32 atomic claims, eight companies: 13 supported, 10 contradicted numeric perturbations, nine insufficient. All claim text is generated from real issuer releases and is labeled `source_tier: generated`; these are not scraped real-world social claims. No model generated the labels or reference numbers.

`annotations.json` registers literal sentence patterns or explicit table/column coordinates, period headings, units, and insufficient reasons. `build_gold.py` independently reads the raw SEC HTML with its own coordinate reader and compares `Decimal` values. It imports no runtime `claimcheck` code, does not call any provider, and produces byte-reproducible `claims.jsonl`, `gold_facts.json`, and `MANIFEST.json`. Annotations were transcribed and checked during implementation; there has been no independent human review. The same fixtures informed the runtime, so this set is a regression benchmark, not a blinded held-out test.

| Issuer | Filing date | Accession | Primary exhibit |
|---|---|---|---|
| META | 2025-07-30 | 0001628280-25-036719 | [Earnings release](https://www.sec.gov/Archives/edgar/data/1326801/000162828025036719/meta-06302025xexhibit991.htm) |
| AAPL | 2025-07-31 | 0000320193-25-000071 | [Earnings release](https://www.sec.gov/Archives/edgar/data/320193/000032019325000071/a8-kex991q3202506282025.htm) |
| NVDA | 2025-08-27 | 0001045810-25-000207 | [Earnings release](https://www.sec.gov/Archives/edgar/data/1045810/000104581025000207/q2fy26pr.htm) |
| AMD | 2025-08-05 | 0000002488-25-000106 | [Earnings release](https://www.sec.gov/Archives/edgar/data/2488/000000248825000106/q22025991.htm) |
| INTC | 2025-07-24 | 0000050863-25-000107 | [Earnings release](https://www.sec.gov/Archives/edgar/data/50863/000005086325000107/q225_earningsrelease.htm) |
| CRM | 2025-09-03 | 0001108524-25-000083 | [Earnings release](https://www.sec.gov/Archives/edgar/data/1108524/000110852425000083/crm-q2fy26xexhibit991.htm) |
| ADBE | 2025-09-11 | 0000796343-25-000102 | [Earnings release](https://www.sec.gov/Archives/edgar/data/796343/000079634325000102/adbeex991q325.htm) |
| AMZN | 2025-07-31 | 0001018724-25-000084 | [Earnings release](https://www.sec.gov/Archives/edgar/data/1018724/000101872425000084/amzn-20250630xex991.htm) |

The exact [source manifest](../../tests/fixtures/releases/manifest.json) records URL, accession, filed date, index hash and exhibit hash. Full raw submissions/index/release documents and their metadata are in `tests/fixtures/releases/releases/`. `record_sources.py` records them from SEC with the shared fair-access gate. XBRL fixtures are explicitly trimmed to five concepts and 2024–2026 period ends; `xbrl/SNAPSHOTS.json` retains the original and trimmed hashes and original cache metadata. `record_xbrl.py` reproduces that trim from the repository's existing SEC cache. These fixtures are ordinary committed files, not the shared `.cache` or `.venv` symlinks.

Insufficient cases cover Apple without numeric guidance, missing adjusted EPS/EBITDA, a period outside the recorded corpus, verbal-range claims with no numeric policy mapping, and Amazon free cash flow reported only for trailing twelve months. GAAP and basic EPS cannot stand in for adjusted diluted EPS. A point in an outlook range is not asserted to equal the entire range.

Before **any** model run, commit the gold, annotations, builder, manifest and fixtures. `run_agent.py --check` verifies every byte against local HEAD before reading a key. The agent receives only claim text, ordinary tools and their results; it never receives the gold verdict or reference coordinates. One Baseten `meta-models/muse-spark-open-1026` run is planned, with a shared $5 ledger, SDK retries disabled, five tool turns and 2,200 output tokens per request. All 32 claims stay in the denominator; transport errors and budget stops score as insufficient. Report accuracy with a Wilson 95% interval, false-supported / all non-supported gold (plus Wilson interval), estimated spend, median/p95 wall latency and individual traces. Do not rerun to select a better score.

This session's managed sandbox makes the shared main-checkout `.git` read-only. The local commits therefore use an isolated Git directory under `/private/tmp`, on `feature/l4-earnings-release` from `f06ac10743ac72b35a84a8ff2527c2e84574da1f`. The runner accepts `--git-dir /private/tmp/market-claim-verifier-l4-local.git` and still verifies real committed gold/source bytes before a call. A portable Git bundle carries the commits for import; the shared worktree branch ref cannot be updated in this session. This changes Git storage location, not the gold, evidence or comparison rules.
