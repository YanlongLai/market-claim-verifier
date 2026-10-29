# L4 implementation and experiment design — 2026-10-29

The model proposes a tool query and selects a span. Python discovers the SEC source, parses its numbers and table coordinates, checks the issuer/metric/unit/period, and decides the verdict. Final model numeric fields and verdicts do not supply an L4 answer.

| File | Responsibility |
|---|---|
| `src/claimcheck/sec_transport.py` | Shared SEC nine-request/second start gate and contact User-Agent |
| `src/claimcheck/release_fetch.py` | Submissions Item 2.02 filtering, historical shards, SEC filing-index exhibit discovery, cached raw bytes and integrity hashes |
| `src/claimcheck/release_text.py` | Standard-library HTML parsing, canonical text, colspan/rowspan coordinates, literal periods and point/range tokens |
| `src/claimcheck/release.py` | Deterministic label/column/period binding, source metadata, candidate lookup and re-extraction |
| `src/claimcheck/release_tools.py` | Strict find/quote contracts; no numeric input to quote selection |
| `src/claimcheck/release_checks.py` | Original-claim comparisons, missing/ambiguous evidence, XBRL precedence and mismatch flag |
| `src/claimcheck/release_report.py` | Escaped quote rendering with exact numeric highlights |
| `eval/l4/build_gold.py` | Independent manual-coordinate/sentence-anchor gold builder, using Decimal and no runtime imports |
| `eval/l4/run_agent.py` | Committed-byte preflight, Baseten-only run, shared $5 budget, traces, Wilson intervals and error-inclusive scoring |

Existing-module edits are limited to shared transport, tool registration, a release-check dispatch hook, agent integration, and report/extraction fields. `checks.py` retains its original GAAP checking implementation. Prompt exports and the source registry are synchronized. Pytest explicitly imports this checkout's `src`; the shared virtualenv's editable install points at another worktree and is not changed. `.venv` and `.cache` symlinks remain untracked.

Gold was committed before any model call. Source fixtures were committed separately first. Full-suite validation before the run: **325 passed** (`.venv/bin/python -m pytest -q`). Staged changes were scanned against locally configured key values and credential patterns before each commit; keys were neither printed nor written to artifacts.

The benchmark uses one release per issuer from 2025, recorded via SEC source chains, plus explicitly trimmed companyfacts replay snapshots. It is a regression set developed alongside the parser, not a blinded holdout or a measure of unrestricted live-SEC discovery. Every case is retained; no model-assisted gold corrections or score-selected reruns are permitted. The protocol records the exact gold commit, code revision, prompt versions, hashes, model identifier, rate source and request limits.

Supported scope and remaining limitations:

- Literal USD amounts, explicit ranges, adjusted diluted EPS, adjusted operating income and (adjusted) free cash flow. Segment/constant-currency revenue, basic EPS substitutions, unsupported currencies and inequality-only claims fail closed.
- Verbal bounds such as “low to mid single digits” have no numeric mapping. A point inside a stated range is insufficient unless the issuer explicitly states that point as its plus/minus center.
- Explicit period identity is required. Fiscal/calendar equivalence requires companyfacts evidence. YTD/TTM cannot answer a quarterly claim. Complex or unresolved period/header layouts may reduce recall.
- No PDF/OCR or image-only slides. HTML Ex 99.2 is supported by discovery and the same parser; the recorded eight-release benchmark is Ex 99.1.
- Discovery considers up to 32 Item 2.02 filings in a broad explicit-year window and returns up to 24 candidate spans. Search truncation and fetch failures are exposed. Conflicting same-period candidate values produce insufficient evidence rather than a model-selected winner.
- L4 is furnished and unaudited, medium strength at most. Exact-period, matching-unit L1/L2 XBRL outranks a reported release conflict; both citations and `release_vs_filing_mismatch` remain visible.
- SEC response caches are immutable snapshots for reproducibility. A new cache/snapshot is required to refresh source bytes. The shared SEC rate gate is process-wide; callers running separate processes must coordinate aggregate request rates.
- The managed sandbox blocks writes to the main checkout's shared `.git`. Actual commits are held in `/private/tmp/market-claim-verifier-l4-local.git`, on the requested feature branch from the original base. The evaluation verifies those committed bytes via `--git-dir`. A portable bundle is provided for Claude; the original worktree branch ref remains unchanged.
