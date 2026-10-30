# Review a stock across multiple files

The product accepts local text/Markdown, native-text PDF, PNG/JPEG/WebP, supported audio and video files. `review-stock` checks the batch with frozen SEC evidence, then creates a readable single-stock summary. It uses the existing conservative job queue, not a discounted provider Batch API.

```sh
uv run python -m claimcheck review-stock TSLA notes.txt table.png call.mp3 \
  --provider baseten --evidence-cache .cache/sec-refresh-2026-10-30 \
  --as-of 2026-10-30 --budget 3 --per-job-budget 1 --max-jobs 3 --out runs/tsla-review
```

This makes paid verification calls. Media requires Meta OCR/ASR credentials as well as the chosen text provider. Budgets include preprocessing; the queue admits full job caps before calls. Unsupported or uncertain jobs stay visible. Repeat the exact command to resume jobs left by the per-invocation job limit when admission budget remains; completed jobs are hash-verified and reused, unknown outcomes do not auto-retry. Budget-blocked jobs do not become runnable just by repeating the command. Changing inputs or budget requires a new review directory and deliberate budget allocation. Each invocation writes a new `summary-NNN/stock-review.html` and JSON so previous partial summaries remain available.

**Batch limits:** 1–100 input files; the default processes at most 10 jobs per invocation (`--max-jobs`). `--max-claims` defaults to 8 per post/extraction window, not an assurance that every statement in a long document is checked. Ingestion retains its 128 MiB file limit, two-hour media limit, 100-page native-text PDF limit and three sampled video frames. The report must be read with its partial/unchecked coverage.

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

## Product workflow and next priorities

1. **Available now:** choose a US ticker, provide up to 100 local files, set a total and per-file budget, run a bounded number of jobs, and open the stock summary. Each report links back to its source file, extracted quotation, page/frame/audio location where available, and SEC evidence. Re-running resumes the same batch; it does not silently replace completed results.
2. **Available now:** inspect contradicted claims first and read their evidence-backed numeric corrections. Inspect pending, partial, unassigned and insufficient-evidence findings before sharing. A document can contain both correct and wrong statements; the summary does not stamp an entire file as true.
3. **Next product priority:** a ticker-and-multi-file upload screen with progress, per-file cost and the same saved HTML/JSON export. Keep the queue and evidence contract as the backend; avoid a separate UI-only verification path. Acceptance: a partial job and a mixed-company upload must remain visible after refresh/resume.
4. **Next quality priority:** independently annotate real issuer tables, earnings-call excerpts and noisy screenshots, including missing/uncheckable facts. Add fiscal-period, GAAP/non-GAAP and units to the annotation. Publish misses and reviewer disagreements before claiming real-world recall.
5. **Optional narrative:** summarize only recorded findings into “what the supplied documents say,” “what conflicts with evidence,” and “what remains unknown.” Require source IDs for every financial assertion, validate all numbers against the structured review, preserve the deterministic summary on failure, and charge generation to an explicit remaining budget. Compare narrative factuality with a human-reviewed set before enabling it by default.
6. **Later:** incremental additions to an existing stock workspace, semantic deduplication with provenance, user-selected authoritative evidence connectors, long-recording chunk resume, native media adapters and discounted vendor batch APIs. Each needs its own benchmark and migration policy.

Uploaded files are **claims to verify**, not automatically trusted evidence. Today the frozen SEC cache supplies the factual reference. Adding a company presentation does not let it override SEC facts or resolve non-GAAP claims by itself. Supporting user-supplied evidence requires provenance, period/units, source authority and conflict handling; that is a separate planned feature.
