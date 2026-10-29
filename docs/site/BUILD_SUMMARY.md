# Site build summary

- The bilingual site reads both example `report.json` files directly and writes the checked claims, SEC facts, filing excerpts, and original-filing links to `docs/site/data/site.json`.
- SEC downloads use the required User-Agent, are limited to five requests per second, and are cached under `.cache/filings/`.

## Filing excerpt results

### en: bigtech-thread-baseten — 7 matched, 0 unmatched component facts

- Claim 1: Amazon reported revenue of $143.1 billion in calendar Q3 2023. — 1 matched, 0 unmatched.
  - Modal block after dedupe: E1 — highlighted value: 143,083.
- Claim 2: NVIDIA reported revenue of $60.9 billion in fiscal 2024, more than double the year before. — 3 matched, 0 unmatched.
  - Modal block after dedupe: E1 · E4 this period — highlighted value: 60,922.
  - Modal block after dedupe: E4 comparison — highlighted value: 26,974.
- Claim 3: Tesla grew revenue 3% in full-year 2025. — 2 matched, 0 unmatched.
  - Modal block after dedupe: E3 this period — highlighted value: 94,827.
  - Modal block after dedupe: E3 comparison — highlighted value: 97,690.
- Claim 4: Apple reported revenue of $391.0 billion in fiscal 2024. — 1 matched, 0 unmatched.
  - Modal block after dedupe: E1 — highlighted value: 391,035.

### zh: tw-social-post-meta — 7 matched, 0 unmatched component facts

- Claim 1: Microsoft's fiscal 2024 revenue was $245.1 billion, up 16%. — 3 matched, 0 unmatched.
  - Modal block after dedupe: E1 · E4 this period — highlighted value: 245,122.
  - Modal block after dedupe: E4 comparison — highlighted value: 211,915.
- Claim 2: Meta's 2024 net profit was $62.3 billion, almost double the previous year. — 3 matched, 0 unmatched.
  - Modal block after dedupe: E1 · E4 this period — highlighted value: 62,360.
  - Modal block after dedupe: E4 comparison — highlighted value: 39,098.
- Claim 3: Coca-Cola's 2024 revenue exceeded $50 billion. — 1 matched, 0 unmatched.
  - Modal block after dedupe: E1 — highlighted value: 47,061.

## On-screen filing chronology

Each checkable card uses the first filing of its unchanged fact. Complete, lossless iXBRL documents are committed under `tests/fixtures/sec-filings/`; offline builds re-extract the rows and validate dates and values. All 11 component facts match their recorded values; no later comparative-column fallback is needed. Saved report/modal provenance is preserved separately.

| Card | Post date | Displayed filing | First-filed basis (accession) |
| --- | --- | --- | --- |
| demo-thread-baseten-1 (AMZN) | 2025-11-03 | 10-Q, 2023-10-27 | 2023-10-27 (0001018724-23-000018) |
| demo-thread-baseten-3 (AAPL) | 2025-11-03 | 10-K, 2025-10-31 | 2025-10-31 (0000320193-25-000079); 2025-08-01 (0000320193-25-000073) |
| demo-thread-baseten-4 (NVDA) | 2025-11-03 | No filing — opinion / forecast | Not checked |
| demo-thread-baseten-2 (NVDA) | 2025-11-03 | 10-K, 2024-02-21 | 2024-02-21 (0001045810-24-000029); 2023-02-24 (0001045810-23-000017) |
| bigtech-thread-baseten-3 (TSLA) | 2026-02-03 | 10-K, 2026-01-29 | 2026-01-29 (0001628280-26-003952); 2025-01-30 (0001628280-25-003063) |
| tw-social-post-meta-1 (MSFT) | 2025-02-24 | 10-K, 2024-07-30 | 2024-07-30 (0000950170-24-087843); 2023-07-27 (0000950170-23-035122) |
| bigtech-thread-baseten-5 (AAPL) | 2026-02-03 | No filing — opinion / forecast | Not checked |
| bigtech-thread-baseten-4 (AAPL) | 2026-02-03 | 10-K, 2024-11-01 | 2024-11-01 (0000320193-24-000123) |
| tw-social-post-meta-3 (KO) | 2025-02-24 | 10-K, 2025-02-20 | 2025-02-20 (0000021344-25-000011) |
| banana-news-article (AMZN) | 2023-10-27 | 10-Q, 2023-10-27 | 2023-10-27 (0001018724-23-000018) |
| market-recap-repost (KO) | 2025-02-25 | 10-K, 2025-02-20 | 2025-02-20 (0000021344-25-000011) |

## Files changed

- `docs/site/index.html`
- `docs/site/script.js`
- `docs/site/styles.css`
- `docs/site/data/site.json`
- `docs/scripts/build_site.py`
- `docs/scripts/filing_excerpts.py`
- `tests/test_filing_excerpts.py`
- `docs/site/BUILD_SUMMARY.md`
