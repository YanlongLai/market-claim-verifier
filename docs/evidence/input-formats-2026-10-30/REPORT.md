# Input-format smoke probes — 2026-10-30

Six cases selected before paid execution; known synthetic Apple US-equity fixtures. One run per case, failures retained. These are integration smoke tests, not held-out accuracy or a controlled provider comparison.

The [frozen probe set](probe-set.json) records input hashes, generation and the $3 shared cap ($1 per provider). SDK retries are disabled; existing bounded transient retries are reserved and traced. SEC data is replayed from committed fixtures, without live SEC requests.

## Recorded results

| Format | Text provider | Status | Proposed / accepted / checked | Verdict counts | Estimated USD | Seconds |
|---|---|---|---|---|---:|---:|
| [markdown](markdown/ingest.html) | fireworks | completed | 2 / 2 / 2 | contradicted: 1, supported: 1 | $0.031686 | 110.4 |
| [jpeg](jpeg/ingest.html) | baseten | completed | 2 / 2 / 2 | contradicted: 1, supported: 1 | $0.039148 | 18.9 |
| [webp](webp/ingest.html) | fireworks | completed | 2 / 2 / 2 | contradicted: 1, supported: 1 | $0.034332 | 163.7 |
| [mp3](mp3/ingest.html) | fireworks | completed | 3 / 3 / 3 | contradicted: 1, supported: 2 | $0.079938 | 444.1 |
| [silent-video](silent-video/ingest.html) | fireworks | partial | 4 / 4 / 4 | contradicted: 1, supported: 3 | $0.089863 | 463.6 |
| [pdf](pdf/ingest.html) | meta | completed | 2 / 2 / 2 | contradicted: 1, supported: 1 | $0.052712 | 71.8 |

## Spend

| Provider | Estimated USD |
|---|---:|
| baseten | $0.03489420 |
| fireworks | $0.22055220 |
| meta | $0.07223290 |
| Total | $0.32767930 |

Usage-based estimates use the repository price ledger, not provider invoices. Unreconciled reservations, if present, remain included. No private account balances are published.

## Interpretation and boundaries

- Markdown, JPEG, WebP and PDF contain the same two known assertions: revenue $94.036 billion (supported) and deliberately wrong diluted EPS $1.67 (contradicted; filed value $1.57), Apple fiscal Q3 2025. Inspect the exact quotes and program checks, not just run completion.
- MP3 re-encodes the existing synthetic release reading, including deliberately incorrect EPS. Silent video reuses the existing table slides. Their assertion counts differ from the two-claim controls; no cross-format accuracy ranking is justified.
- JPEG/WebP use Meta OCR; MP3 uses Meta ASR; silent video uses only three Meta OCR frames. The chosen provider performs text extraction and verification. This does not test Baseten/Fireworks native media endpoints.
- The silent-video run is partial because the input has no audio track. All four extracted visual claims were program-checked (three supported, one contradicted); the missing audio channel is retained, not silently dropped. This does not establish coverage outside the three sampled frames.
- PDF uses local page text extraction, not vendor-native PDF or OCR. Audio does not establish speaker identity; sampled video does not establish whole-video coverage.
- Proposed/accepted/checked counts describe processing, not recall or truth accuracy. Insufficient evidence and missed/rejected assertions remain visible. Small synthetic probes do not validate other codecs, noisy recordings, complex PDFs, or two-hour inputs.
- General URLs and scanned PDFs remain unsupported. No new integration status is inferred solely from a successful smoke probe.

## Validation

[Validation receipt](validation.json) and [full offline log](offline-verification.log) retain commands and results. Final report rebuild/hash/cost checks and final documentation links are checked after paid completion.

## Reproduce and reuse

[Machine-readable index](runs.json) lists each input hash, protocol, outcome, cost, coverage and frozen text. Each run retains calls/ (OCR or ASR requests/responses when applicable), checks/ traces (extraction and verifier requests/responses), ingest.json and ingest.html. Frozen raw/normalized text can be rechecked without paying for OCR/ASR again; that only tests downstream text verification and does not revalidate media extraction, timestamps or attribution.

Replay all registered cases in a fresh output root; the suite retains command arguments, exit codes and stdout/stderr logs:

```sh
.venv/bin/python scripts/multimodal/run_format_suite.py --out-root runs/formats-001
```

For one case:

```sh
.venv/bin/python scripts/multimodal/run_probe.py markdown format-probes/post.md \
  --provider fireworks --out-root runs/format-recheck --budget 3 --max-output-tokens 4000
```

Use the remaining file/provider pairs in probe-set.json with the same output root to share the cap. This makes paid calls. Existing result directories are never overwritten. To rebuild this report offline: `python3 scripts/multimodal/build_format_report.py`.
