# SEC snapshot refresh — 2026-10-30

Fetched fresh data for the existing **23 US-equity evaluation companies**: **47 JSON responses** (one ticker map, 23 companyfacts, 23 submissions), with **zero fetch errors**. No paid model calls. The [manifest](manifest.json) records every URL, retrieval time, byte count and SHA-256; gzip archives in `snapshots/` retain the exact original response bytes for offline reuse.

This is a snapshot fetched during October 30, America/Los_Angeles, **not a complete end-of-day archive or a claim that every issuer filed that day**. Companyfacts and submissions can expose different update times and filing coverage. Latest fact dates below are observed `filed` fields, not an independently reconciled filing-level completeness guarantee. Raw responses are preserved; summaries and the example CLI use a 2026-10-30 filing-date cutoff.

## Observed coverage

| Ticker | Latest companyfacts filing date | Latest fact period end | Latest recent financial filing |
|---|---|---|---|
| AAPL | 2026-07-31 | 2026-07-17 | 8-K/A · 2026-09-01 |
| ADBE | 2026-09-22 | 2026-09-18 | 10-Q · 2026-09-22 |
| AMD | 2026-08-14 | 2026-08-14 | 8-K · 2026-09-28 |
| AMZN | 2026-10-30 | 2026-10-21 | 10-Q · 2026-10-30 |
| COST | 2026-10-07 | 2026-09-29 | 8-K · 2026-10-16 |
| CRM | 2026-09-11 | 2026-09-11 | 8-K · 2026-10-20 |
| CSCO | 2026-10-29 | 2026-08-27 | 8-K · 2026-10-09 |
| GOOGL | 2026-10-29 | 2026-09-30 | 10-Q · 2026-10-29 |
| INTC | 2026-10-30 | 2026-10-23 | 10-Q · 2026-10-30 |
| JNJ | 2026-10-21 | 2026-10-15 | 10-Q · 2026-10-21 |
| JPM | 2026-10-30 | 2026-10-30 | 8-K · 2026-10-20 |
| KO | 2026-10-28 | 2026-10-26 | 10-Q · 2026-10-28 |
| META | 2026-10-28 | 2026-10-27 | 8-K · 2026-10-29 |
| MSFT | 2026-10-28 | 2026-10-22 | 8-K · 2026-10-28 |
| NFLX | 2026-10-21 | 2026-09-30 | 10-Q · 2026-10-21 |
| NKE | 2026-10-02 | 2026-08-31 | 10-Q · 2026-10-02 |
| NVDA | 2026-08-26 | 2026-08-21 | 8-K · 2026-09-03 |
| ORCL | 2026-09-25 | 2199-12-31 | 8-K · 2026-10-28 |
| PEP | 2026-10-13 | 2026-10-09 | 8-K · 2026-10-16 |
| TSLA | 2026-10-22 | 2026-10-15 | 10-Q · 2026-10-22 |
| UNH | 2026-08-10 | 2026-07-31 | 8-K · 2026-10-13 |
| V | 2026-04-29 | 2026-04-13 | 8-K · 2026-10-27 |
| WMT | 2026-10-21 | 2026-10-20 | 8-K · 2026-10-23 |

Companyfacts supplies XBRL financial facts. Submissions supplies filing discovery metadata; it is not the filing body. This refresh does not download all 10-K/10-Q HTML, historical submission shards or L4 8-K release exhibits. The release adapter retains its own URL-keyed cache and fetch workflow. A missing fact remains missing rather than being filled from an issuer slide.

## Use the refreshed snapshot

The existing default `.cache` and all historical benchmark fixtures/results are unchanged. Use the new snapshot explicitly to avoid mixing evaluation vintages. On this workspace it is already at `.cache/sec-refresh-2026-10-30`. On a fresh clone, restore the committed compressed responses offline into a new directory:

```sh
python3 scripts/restore_sec_snapshot.py docs/evidence/sec-refresh-2026-10-30 .cache/sec-restored-2026-10-30
CLAIMCHECK_CACHE_DIR=.cache/sec-restored-2026-10-30 uv run python -m claimcheck edgar AMZN revenue FY2026Q3 --as-of 2026-10-30
```

Restoration refuses an existing destination and verifies hashes before writing. To fetch a newer snapshot, choose new directories and the desired cutoff:

```sh
.venv/bin/python scripts/refresh_sec_snapshot.py --as-of 2026-10-30 \
  --cache-dir .cache/sec-new-run --record-dir runs/sec-new-run
```

The cutoff filters the summary; it does not make the current SEC API a historical time-machine. Requests use the existing identified User-Agent and shared SEC fair-access gate. [SEC API update behavior](https://www.sec.gov/search-filings/edgar-application-programming-interfaces).

## Validation

[Offline lookup records](lookup-checks.json) resolve FY2026Q3 revenue for AMZN, INTC and TSLA from the new cache with network access prohibited by the injected fetcher. These are deterministic data lookups, not new model accuracy scores. [Validation receipt](validation.json) and [fetch log](fetch.log) retain the checks. SEC EDGAR remains the source of the archived public data.
