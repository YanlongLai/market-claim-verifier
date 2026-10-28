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

## Files changed

- `docs/site/index.html`
- `docs/site/script.js`
- `docs/site/styles.css`
- `docs/site/data/site.json`
- `docs/scripts/build_site.py`
- `docs/scripts/filing_excerpts.py`
- `tests/test_filing_excerpts.py`
- `docs/site/BUILD_SUMMARY.md`
