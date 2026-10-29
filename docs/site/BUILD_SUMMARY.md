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

XBRL cards use the first filing of each unchanged fact, re-extracted from `tests/fixtures/sec-filings/`. L4 cards re-extract exact quotes and numeric highlights from hash-checked release snapshots, validate both endpoints or the scalar against the independent gold, and validate Item 2.02 and filing dates against saved SEC index pages. Audio/screenshot cards retain the recorded ingest and program verdict; input media is never filing evidence. No network or model call is needed.

| Card | Post date | Displayed filing | First-filed basis (accession) |
| --- | --- | --- | --- |
| demo-thread-baseten-1 (AMZN) | 2025-11-03 | 10-Q, 2023-10-27 | 2023-10-27 (0001018724-23-000018) |
| demo-thread-baseten-3 (AAPL) | 2025-11-03 | 10-K, 2025-10-31 | 2025-10-31 (0000320193-25-000079); 2025-08-01 (0000320193-25-000073) |
| demo-thread-baseten-4 (NVDA) | 2025-11-03 | No filing — opinion / forecast | Not checked |
| l4-01 (META) | 2025-07-31 | 8-K Ex 99.1, 2025-07-30 | 2025-07-30 (0001628280-25-036719) |
| input-audio-two-voices-2 (AAPL) | 2026-10-29 | 10-Q, 2025-08-01 | 2025-08-01 (0000320193-25-000073) |
| l4-27 (ADBE) | 2025-09-12 | 8-K Ex 99.1, 2025-09-11 | 2025-09-11 (0000796343-25-000102) |
| input-screenshot-2 (AAPL) | 2026-10-29 | 10-Q, 2025-08-01 | 2025-08-01 (0000320193-25-000073) |
| demo-thread-baseten-2 (NVDA) | 2025-11-03 | 10-K, 2024-02-21 | 2024-02-21 (0001045810-24-000029); 2023-02-24 (0001045810-23-000017) |
| bigtech-thread-baseten-3 (TSLA) | 2026-02-03 | 10-K, 2026-01-29 | 2026-01-29 (0001628280-26-003952); 2025-01-30 (0001628280-25-003063) |
| tw-social-post-meta-1 (MSFT) | 2025-02-24 | 10-K, 2024-07-30 | 2024-07-30 (0000950170-24-087843); 2023-07-27 (0000950170-23-035122) |
| bigtech-thread-baseten-5 (AAPL) | 2026-02-03 | No filing — opinion / forecast | Not checked |
| bigtech-thread-baseten-4 (AAPL) | 2026-02-03 | 10-K, 2024-11-01 | 2024-11-01 (0000320193-24-000123) |
| tw-social-post-meta-3 (KO) | 2025-02-24 | 10-K, 2025-02-20 | 2025-02-20 (0000021344-25-000011) |
| banana-news-article (AMZN) | 2023-10-27 | 10-Q, 2023-10-27 | 2023-10-27 (0001018724-23-000018) |
| market-recap-repost (KO) | 2025-02-25 | 10-K, 2025-02-20 | 2025-02-20 (0000021344-25-000011) |

## Day-4 cards and recorded sources

Two furnished, unaudited L4 releases and two self-made synthetic input examples join the original eleven cards. The L4 set is a development regression set; the media probe is exploratory. Neither is a held-out benchmark. The audio's two synthetic voices were both labeled A; only whole-turn timing and an unverified session label are shown. Neither L4 card has an invented scalar accuracy score.

| Card | Input / evidence | Recorded verdict | Recorded source |
| --- | --- | --- | --- |
| l4-01 | text / 8-K Item 2.02 · Ex 99.1 · L4 | supported | [docs/evidence/eval-l4-2026-10-29/traces/L4-01.json](../evidence/eval-l4-2026-10-29/traces/L4-01.json) |
| input-audio-two-voices-2 | audio / SEC 10-Q · L2 | contradicted | [docs/evidence/multimodal-2026-10-29/audio-two-voices/ingest.json](../evidence/multimodal-2026-10-29/audio-two-voices/ingest.json) |
| l4-27 | text / 8-K Item 2.02 · Ex 99.1 · L4 | supported | [docs/evidence/eval-l4-2026-10-29/traces/L4-27.json](../evidence/eval-l4-2026-10-29/traces/L4-27.json) |
| input-screenshot-2 | screenshot / SEC 10-Q · L2 | contradicted | [docs/evidence/multimodal-2026-10-29/screenshot/ingest.json](../evidence/multimodal-2026-10-29/screenshot/ingest.json) |

## Files changed

- `docs/site/index.html`
- `docs/site/script.js`
- `docs/site/styles.css`
- `docs/site/data/site.json`
- `docs/scripts/build_site.py`
- `scripts/build_site_filing_fixtures.py`
- `docs/site/img/inputs/example-post.png` (exact recorded test input)
- `docs/site/STAMP-V2-KEYFRAMES.md`
- `tests/test_site_day4.py`
- `tests/test_site_stamps.py`
- `tests/test_site_stamps_runtime.py`
- `tests/test_site_polish.py`
- `tests/test_site_filing_fixtures.py`
- `docs/site/BUILD_SUMMARY.md`
