# Live check and visible agent trace

Implementation and deployment handoff, 2026-11-02. This document does **not** mean the endpoint is deployed. The owner/Claude supplies the secret, deploys the Worker, and deploys Pages. No paid model call is needed to build or test this change.

## Architecture and verdict identity

The browser posts `{ "text": "…" }` to `/api/check` on the same origin. The [Pages Function](../functions/api/check.ts) validates the request and forwards it through the private `LIVE_CHECK` service binding to the [Python Worker](../workers/live/src/entry.py). The Worker calls only Baseten's OpenAI-compatible endpoint, with **`meta-models/muse-spark-open-1026`**. The browser never receives a provider key or talks to Baseten directly.

We chose **the Python core**, rather than a TypeScript port: the checker includes period ambiguity, evidence-kind validation, numeric precision, derivations, first-time/history claims, and provenance checks. [The bundle builder](../scripts/build_live_worker.py) copies the repository's Python modules byte for byte, including [checks.py](../src/claimcheck/checks.py), [numbers.py](../src/claimcheck/numbers.py), [tools.py](../src/claimcheck/tools.py), [edgar.py](../src/claimcheck/edgar.py), and [budget.py](../src/claimcheck/budget.py). Generated copies are ignored; do not edit them. Wrangler's build command refreshes them. The only SEC adapter change is an in-memory document loader on an `EdgarClient` subclass; all fact selection, fiscal normalization, calculations, evidence IDs, and final evaluation remain Python.

[The runner](../workers/live/src/live.py) uses the CLI's strict JSON parser, missing-period guard, `evaluate_verdict`, and program summary. A model proposal cannot override a program verdict. Aggregation remains: any contradiction → `contradicted`; every extracted assertion supported → `supported`; otherwise → `insufficient_evidence`. Individual checks may remain `unchecked`. Missing explicit dated periods abstain without a model call. Extraction can miss assertions; a supported result applies to the assertions actually extracted. SEC evidence can be incomplete or restated. These limitations appear in both recorded and live result views.

[Offline tests](../tests/test_live_check.py) assert bundle source identity, replay all three original Apple Baseten responses (including the malformed JSON / repair turn), exercise all three outcomes, and run all **357 v2 Baseten saved tool transcripts** through both the live finish path and CLI evaluator, comparing complete program checks and verdicts. This is a frozen-response recheck, not a new model evaluation, OCR/ASR test, or independent accuracy measurement. No TypeScript verdict implementation exists.

Cloudflare references: [Python Worker basics](https://developers.cloudflare.com/workers/languages/python/basics/), [Python packages and pywrangler](https://developers.cloudflare.com/workers/languages/python/packages/), [Python Durable Objects example](https://developers.cloudflare.com/workers/languages/python/examples/), and [Pages service bindings](https://developers.cloudflare.com/pages/functions/bindings/).

## Limits and failure behavior

| Limit | Behavior |
| --- | --- |
| Input | 1–600 Unicode characters after trimming; 4 KiB request-body ceiling, including chunked bodies |
| Scope | US SEC issuers, financial companyfacts; at most two issuers per check. No market prices, investment advice, crypto, forecasts, non-GAAP or issuer-release verification |
| Calls | At most four model calls, 2,000 output tokens each; at most six tool calls; no automatic provider retry |
| Time | 28-second runner deadline; each outbound fetch also has a 22-second abort signal; browser gives up at 32 seconds. Around 30 seconds is a target, not a measured production SLA |
| Rate | Five accepted requests per IP in a ten-minute window, enforced in the same globally consistent Durable Object, across regions |
| Daily spend | Default $3 per UTC day, configurable with Worker `DAILY_BUDGET_USD`. Zero disables paid calls; invalid/negative/nonfinite settings fail closed |
| SEC cache | Public ticker directory and companyfacts JSON cached for six hours with Cache API; only successful valid JSON is cached; no KV namespace needed |

SEC requests use exactly `User-Agent: DappGo market-claim-verifier admin@dappgo.com`. The only network destinations in the backend are the fixed SEC ticker/facts endpoints and Baseten. Tool arguments cannot supply a fetch URL. The public endpoint checks same-origin browser requests, accepts JSON only, replaces any client-provided forwarding header with Cloudflare's `CF-Connecting-IP`, and returns `Cache-Control: no-store`. [Routes](./_routes.json) run Functions only for `/api/check`; the existing [CSP](./_headers), language switch, color schemes, cache-busted assets and reduced-motion behavior remain in use.

Provider errors, truncated responses, invalid model JSON after the call limit, SEC failures, and timeouts issue **no financial verdict**. Costs already reserved remain accounted for and available partial steps are shown. Exhausted budget returns HTTP 429 / `budget_exhausted`; the UI says to try again tomorrow (UTC) and keeps the saved Apple demo visible. Rate limits also return 429. Missing bindings, unavailable counters and absent keys fail closed to the saved demo.

## Atomic cost cap

`SPEND_GATE` binds the SQLite-backed `SpendGate` Durable Object. Every request uses the same object name, **`baseten-live-global-v1`**. A reservation is committed before **each** model fetch, including a JSON repair call. A synchronous SQLite read/check/write section has no intervening `await`; simultaneous requests cannot each spend the same remaining balance. KV eventual consistency would not provide this guarantee.

Prices are imported from the same provider registry used by the CLI ledger: input $1.25/M, cached input $0.15/M, output $4.25/M. The base reservation uses `Ledger.estimate`: compact Unicode JSON characters / 3, rounded up, plus the maximum output tokens. The public service additionally holds an input ceiling of serialized UTF-8 bytes + 4,096 template/control tokens, priced at the uncached input rate. This avoids treating the CLI character heuristic as a hard upper bound, especially for Chinese text. Cached-token discounts are applied only when usage is returned. The output limit includes the provider's billed completion budget; a model ID, pricing or token-accounting change requires reviewing this contract before enabling calls.

Successful usage reconciles using `Ledger.reconcile`. Missing/invalid usage, failed fetches and cancellations retain the full ceiling. Settlements are idempotent. Durable totals use integer nano-USD, rounding holds upward and the configured cap downward. Unexpected usage above the ceiling closes the day's remaining budget. The limit covers **model spend**, not Cloudflare infrastructure charges. Calls are charged to their reservation's UTC start day, including calls that finish after midnight. Never rename the singleton, change namespace bindings, or delete its storage to reset a limit during the day. Ledger metadata expires after 48 hours; rate buckets expire after ten minutes and are also pruned by Durable Object alarms.

## Privacy

User text, model responses and tool results exist in request memory and are returned to that visitor. This application stores **no user text or transcript**, including in logs. It sends the post and needed SEC tool results to Baseten for inference; Baseten and Cloudflare have their own service policies. Application code persists only the site's existing language preference; it writes no post or result to browser storage. Refreshing discards the live result.

The Durable Object persists only UTC budget totals, random reservation IDs/amounts/status, expiry times, and rate counts keyed by a salted HMAC of the IP. Raw IP addresses are never persisted. Rate buckets become invalid at ten minutes; cleanup alarms remove expired buckets (subject to Cloudflare alarm scheduling). The random HMAC salt is stored with the ledger and erased when the object has no remaining metadata. Cache API stores only public SEC documents. There is no anonymous text log to retain. Worker observability is disabled in configuration; do not enable request-body logging, tails or tracing that capture user content. Platform access metadata is outside this application's transcript storage.

The published [Apple view](site/data/live-demo.json) is derived from the pre-existing [R06 result](evidence/eval-v2-2026-10-27/R06--agent@baseten.json) and its [raw trace](evidence/eval-v2-2026-10-27/traces/20261028T061222Z-6f6be742.json). It preserves the source hash, recorded start/end, $0.01221725 model cost and 8,294.411 ms model latency. Individual tool/check timestamps were not recorded and are explicitly null, rather than invented. Private model reasoning is omitted. The same renderer shows each live response with freshly measured timestamps, tool names/arguments/results, SEC evidence IDs, program checks, and cost. Keep new test evidence under the [test-record policy](TEST_RECORDS.md); do not archive arbitrary visitor posts as tests.

## Offline development

The normal verification command needs no Wrangler, npm install, provider key or SEC requests:

```sh
UV_OFFLINE=1 sh scripts/verify.sh
```

Focused tests, using an existing environment with repository dependencies:

```sh
python -m pytest -q tests/test_live_check.py tests/test_site_live_runtime.py tests/test_site_asset_versions.py
python scripts/build_live_demo.py --check
```

The Node boundary tests run through pytest on Node 22+, using the same plain-JavaScript request boundary that the Pages Function exports. They inject service/model responses and never fetch a remote endpoint. Saved demo reproduction is independent of the three byte-identical explorer/site outputs in the main verifier.

For a local interactive Pages preview, first install Wrangler once (package setup requires network), then:

```sh
wrangler pages dev docs/site --binding LIVE_CHECK_MOCK=1 --ip 127.0.0.1 --port 8788
```

Open `http://127.0.0.1:8788/#live-check`, choose **Use Apple example**, then **Check against SEC**. This mode returns the stored Apple result, labelled **Offline replay**, and accepts only that exact example. It never pretends to verify a changed input. Mock mode also requires the request hostname to be `localhost`, `127.0.0.1` or `[::1]`; setting the variable on a production hostname cannot activate it. Full raw Baseten-response / SEC-fixture replay runs in the Python tests above. Do not set a key for mock mode. Static-only previews still display the saved trace; the live form falls back when `/api/check` is unavailable.

For Worker development/builds, Python 3.13+ and `uv` 0.13.4+ are required by the locked pywrangler toolchain:

```sh
cd workers/live
uv sync --frozen
uv run pywrangler deploy --dry-run --outdir /tmp/market-claim-worker-build
uv run pywrangler dev --ip 127.0.0.1 --port 8789
```

The dry run **does not deploy**. Without a secret, the real local Worker returns `unavailable`. The core is automatically bundled by its build hook. `uv.lock` pins the toolchain; `pylock.toml` pins WASM runtime packages. If a restricted workspace cannot write Wrangler's usual home registry/logs, set `WRANGLER_REGISTRY_PATH` and `WRANGLER_LOG_PATH` to temporary paths. `CHOKIDAR_USEPOLLING=true` avoids native watcher limits in constrained environments. Generated runtime/package directories are excluded from repository verification and link scanning.

## Exact handoff for Claude / owner

Do these **after reviewing the local commit**. These are deployment instructions, not actions already performed by this change.

1. Use an account with **Workers Paid**, Python Workers and SQLite Durable Objects. The Worker sets `limits.cpu_ms=30000` for Python/SEC document processing; the [Free plan's 10 ms CPU limit](https://developers.cloudflare.com/workers/platform/limits/) is unsuitable for this path. Cloudflare infrastructure costs are separate from the $3/day model cap; this change does not upgrade an account. Keep the existing Pages project **`market-claim-verifier`**, output directory **`docs`**, and its existing build command copying `docs/site/{index.html,styles.css,script.js,data,img}` to the output root. The new JSON is inside `data`, so no new static-copy rule is necessary. Keep `docs/_headers`, `docs/_redirects` and `docs/_routes.json` in the output. Functions live at repository-root `functions`, which Pages builds separately.
2. From `workers/live`, run `uv sync --frozen`, then **`uv run pywrangler deploy`**. The Worker name is **`market-claim-verifier-live`**. This creates the `SpendGate` class and SQLite namespace via migration `v1`. Keep `workers_dev=false`, `preview_urls=false` and no public routes. Deploying without a key is safe: all requests abstain at the service boundary.
3. Still in `workers/live`, set the **Worker secret** with **`uv run pywrangler secret put BASETEN_API_KEY`** and paste the key only into its hidden interactive prompt. Do not put the key in Pages, a `.toml` file, `.dev.vars`, a command argument, the browser, or Git. This step belongs to Claude/owner. No other secret is needed.
4. Verify the Worker binding **`SPEND_GATE` → Durable Object class `SpendGate` in `market-claim-verifier-live`**. `DAILY_BUDGET_USD="3"` is in the Worker config; change it there and redeploy if needed, keeping the same object and namespace. No KV binding or namespace is required. `0` disables model calls. Keep observability disabled and avoid body logging.
5. Deploy Pages using the root [wrangler.toml](../wrangler.toml), or confirm its equivalent dashboard service binding: **`LIVE_CHECK` → `market-claim-verifier-live`**. Re-deploy Pages after binding changes. Existing secret/configuration elsewhere must not be copied into client assets. Production has **no `LIVE_CHECK_MOCK` variable**. Preview deployments may omit `LIVE_CHECK` to disable paid calls, or deliberately share the same Worker/cap; do not create a second unmetered backend.
6. After owner deployment, use the Apple example once on the live site: confirm the badge says **Live check**, a supported claim has `E1`, the correct fiscal period and an SEC filing URL, and the trace contains actual model, tool, program-check and verdict steps with cost/latency. This is a paid smoke check covered by the cap; retain its nonprivate test record if executing it. Check the Chinese switch, phone view, both color schemes, and a missing-period sentence. Setting `DAILY_BUDGET_USD="0"` and redeploying the same Worker can test exhausted-budget fallback without spending; restore the intended limit afterwards. Never reset the object to test a limit.

Local validation and its remaining limits are recorded in [the implementation receipt](evidence/live-check-2026-11-02/REPORT.md).
