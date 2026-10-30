# Review a stock across multiple files

The product accepts local text/Markdown, native-text PDF, PNG/JPEG/WebP, supported audio and video files. `review-stock` checks the batch with frozen SEC evidence, then creates a readable single-stock summary. It uses the existing conservative job queue, not a discounted provider Batch API.

```sh
uv run python -m claimcheck review-stock TSLA notes.txt table.png call.mp3 \
  --provider baseten --evidence-cache .cache/sec-refresh-2026-10-30 \
  --as-of 2026-10-30 --budget 3 --per-job-budget 1 --max-jobs 3 --out runs/tsla-review
```

This makes paid verification calls. Media requires Meta OCR/ASR credentials as well as the chosen text provider. Budgets include preprocessing; the queue admits full job caps before calls. Unsupported or uncertain jobs stay visible. Repeat the exact command to resume pending jobs; completed jobs are hash-verified and reused, unknown outcomes do not auto-retry. Each invocation writes a new `summary-NNN/stock-review.html` and JSON so previous partial summaries remain available.

## Reuse results without another API call

```sh
uv run python -m claimcheck stock-summary AAPL \
  docs/evidence/input-formats-2026-10-30/jpeg/ingest.json \
  docs/evidence/input-formats-2026-10-30/mp3/ingest.json \
  docs/evidence/input-formats-2026-10-30/pdf/ingest.json \
  --out runs/aapl-summary
```

[Saved example](evidence/stock-review-example/stock-review.html) · [machine-readable summary](evidence/stock-review-example/stock-review.json). This example reuses three earlier synthetic-control reports, not a new real-world evaluation. Its seven extracted occurrences include repeated statements; they are not seven independent facts.

The summary includes every input report, incomplete/pending files, target-company claims, other-company and unresolved-ticker claims, source quotations/locations, program verdicts and corrections with evidence units/periods. Repeated statements retain every occurrence; disagreeing recorded verdicts are flagged rather than voting away a failure. Report hashes identify exactly what was summarized, but do not authenticate arbitrary externally supplied JSON.

## What the summary means

It explains which supplied claims are supported, contradicted or unresolved, and what the recorded evidence says instead. A missing claim is not implicitly correct. It does not infer a buy/sell rating or invent a company's future performance. Historical and current evidence/policy versions remain visible per file.

The current summary is deterministic and costs **$0 incremental model fees**. An optional AI explanation is planned only after citation/number validation and a separate budget are wired into the narrative layer; it is not implemented or silently called today. See the [delivery plan](FAIR_BENCHMARK_AND_STOCK_REVIEW_PLAN.md) for the remaining real-recording and narrative gates.
