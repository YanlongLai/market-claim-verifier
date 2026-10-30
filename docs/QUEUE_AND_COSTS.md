# Bounded ingestion queue and cost accounting

## Local queue

`queue` processes local text, native-text PDF, image, audio or video inputs using the existing ingestion pipeline. It is a **serial local queue**, not a provider Batch API, distributed scheduler or batch discount. Maximum 100 inputs; one worker holds a nonblocking POSIX file lock.

Example (paid model calls when keys are configured):

```sh
uv run python -m claimcheck queue article.txt screenshot.png \
  --out runs/review-queue --evidence-cache .cache \
  --provider baseten --budget 2 --per-job-budget 1 --max-jobs 1 \
  --as-of 2025-07-30
```

Repeat the same command to process the next pending input. `--max-jobs` limits work per invocation and can change on resume. Other options and input contents must match. Completed report status means the ingestion pipeline completed, not that every claim was supported or all input assertions were found.

## Frozen inputs and evidence

Before work starts, input bytes and SEC cache files are copied into the queue directory. A populated cache is required: `company_tickers.json`, `companyfacts-*.json` and/or the `releases/` cache. Source-network fallback is disabled; missing evidence remains unavailable rather than silently fetching a newer source. Model calls still require network access.

The identity records input hashes, evidence hashes, provider/model, extraction options, policy identity, package source/prompt hashes and the dependency lockfile. Price constants are covered by the package-code fingerprint. Resume refuses changed inputs, evidence, model, policy, prompt/code/prices or budgets. The copied evidence is checked before jobs and on resume. Successful output artifacts are hash-checked before reuse. This is job-level reuse, not a global cache for semantically equivalent claims or shared OCR segments.

Updating the original cache also changes identity; create a new queue for new evidence. Do not edit queue state to bypass integrity checks. Cache and input snapshots may contain private local data and remain in the chosen local output directory; this command does not publish them.

## Budget behavior

Both total and per-job budgets must be positive and finite. Before starting a job, the queue admits its **full per-job allowance** against the queue total. Unused allowance is not recycled. For example, a $1.50 total with a $1 per-job allowance admits one job, even if it used only $0.01. The remaining job stays pending.

Each worker uses a job-local reservation ledger. Mixed-provider ingestion partitions the allowance equally between Meta OCR/ASR and the selected text provider, as the existing ingestion path does. These are conservative admission/reservation limits, not a guarantee that a provider invoice can never exceed an estimate. An unknown/nonfinite/out-of-range worker cost stops further admission and requires review.

Changing the cap on an existing queue is deliberately refused. Inspect prior spend before explicitly creating a new queue containing only the intended remaining files.

## Resume and uncertain outcomes

| State | Resume behavior |
|---|---|
| pending | Eligible to start within limits |
| completed | Verify artifact hashes, skip without new API calls |
| running left by a stopped process | Mark needs_review; do not retry |
| partial/failed worker result | Mark needs_review; do not retry |
| unknown cost or cost overrun | Stop future admission until reviewed; do not retry |

There is no exactly-once guarantee for remote APIs. A process can stop after a provider accepts a request but before local completion is saved. Such work must be reviewed, not automatically sent again. The ledger and channel traces remain under `jobs/NNNN/`; `queue.json` records overall state. A review-required job does not itself stop other independent pending jobs unless there is a budget/cost review flag. There is no automatic retry/reset command in this version.

## Cost fields

New ingestion reports include `cost_breakdown`:

- `original_reservations_usd`: sum of amounts initially reserved for API attempts; not an extra charge to add to estimates.
- `estimated_or_reserved_usd`: usage-based estimates where reconciliation exists, retained reservations otherwise.
- `by_stage_usd`: OCR, ASR, claim extraction and claim verification, as incurred.
- `attempts`: reservation ID, stage, provider/model, original reservation, latest estimate and estimate basis. Retry attempts remain included.
- `rates`: configured token-price snapshot; ASR reservation rate is recorded separately.
- `billed_usd`: null. No provider billing reconciliation is implemented.

Post-only reports expose extraction versus verification totals from their traces; ingestion exposes per-attempt detail. Audio retains duration-based reservations using the existing conservative rounding policy. Missing-usage and failed token calls remain reservations. Neither an SDK token-usage report nor a successful HTTP response is a billing invoice. Local compute/storage and licensed source costs are not measured.

HTML reports display the breakdown and billing limitation. Old reports without this field remain readable, with missing cost stages labeled rather than invented. The existing `cost_usd` field remains the compatible estimate.

## Validation and remaining work

[Queue tests](../tests/test_job_queue.py) cover bounded admission, resume, changed identities, altered outputs, duplicate inputs, active locks, crashes, partial results and cost overruns. [Cost tests](../tests/test_cost_breakdown.py) distinguish usage reconciliation from retained reservations and check stage totals. Existing recorded ingestion tests verify no change to model request replay or total estimates.

Parallel/distributed execution, provider Batch adapters, invoice imports and per-channel resume remain future work. This milestone does not claim provider-scale throughput or savings without a measured benchmark.
