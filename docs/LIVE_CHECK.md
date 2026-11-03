# Live check and visible agent trace

Implementation and deployment handoff, 2026-11-02. This document does **not** mean the endpoint is deployed. The owner/Claude supplies the secret, deploys the Worker, and deploys Pages. No paid model call is needed to build or test this change.

## Architecture and verdict identity

The browser posts `{ "text": "…", "password": "…" }` in the body to `/api/check` on the same origin. The [Pages Function](../functions/api/check.ts) validates the request envelope and forwards only those fields and the trusted Cloudflare client IP through the private `LIVE_CHECK` service binding to the [Python Worker](../workers/live/src/entry.py). The Worker authenticates before inspecting budgets, reserving spending or calling SEC/Baseten. It calls only Baseten's OpenAI-compatible endpoint, with **`meta-models/muse-spark-open-1026`**. The browser never receives a provider key or talks to Baseten directly. Only `fetch` is exposed on the Worker entrypoint; model helpers are on an ordinary class, with no model RPC entrypoint.

We chose **the Python core**, rather than a TypeScript port: the checker includes period ambiguity, evidence-kind validation, numeric precision, derivations, first-time/history claims, and provenance checks. [The bundle builder](../scripts/build_live_worker.py) copies the repository's Python modules byte for byte, including [checks.py](../src/claimcheck/checks.py), [numbers.py](../src/claimcheck/numbers.py), [tools.py](../src/claimcheck/tools.py), [edgar.py](../src/claimcheck/edgar.py), and [budget.py](../src/claimcheck/budget.py). Generated copies are ignored; do not edit them. Wrangler's build command refreshes them. The only SEC adapter change is an in-memory document loader on an `EdgarClient` subclass; all fact selection, fiscal normalization, calculations, evidence IDs, and final evaluation remain Python.

[The runner](../workers/live/src/live.py) uses the CLI's strict JSON parser, missing-period guard, `evaluate_verdict`, and program summary. A model proposal cannot override a program verdict. Aggregation remains: any contradiction → `contradicted`; every extracted assertion supported → `supported`; otherwise → `insufficient_evidence`. Individual checks may remain `unchecked`. Missing explicit dated periods abstain without a model call. Extraction can miss assertions; a supported result applies to the assertions actually extracted. SEC evidence can be incomplete or restated. These limitations appear in both recorded and live result views.

[Offline tests](../tests/test_live_check.py) assert bundle source identity, replay all three original Apple Baseten responses (including the malformed JSON / repair turn), exercise all three outcomes, and run all **357 v2 Baseten saved tool transcripts** through both the live finish path and CLI evaluator, comparing complete program checks and verdicts. This is a frozen-response recheck, not a new model evaluation, OCR/ASR test, or independent accuracy measurement. No TypeScript verdict implementation exists.

Cloudflare references: [Python Worker basics](https://developers.cloudflare.com/workers/languages/python/basics/), [Python packages and pywrangler](https://developers.cloudflare.com/workers/languages/python/packages/), [Python Durable Objects example](https://developers.cloudflare.com/workers/languages/python/examples/), and [Pages service bindings](https://developers.cloudflare.com/pages/functions/bindings/).

## Limits and failure behavior

| Limit | Behavior |
| --- | --- |
| Input | 1–600 Unicode characters after trimming; 4 KiB request-body ceiling, including chunked bodies |
| Password | Required during hackathon review, checked against the Worker secret `LIVE_CHECK_PASSWORD` using `hmac.compare_digest` on two 32-byte SHA-256 digests. Missing/empty secret disables checks with 503; missing/wrong password returns 401 before any budget reservation or model call |
| Failed passwords | Five failures per IP in a 15-minute window, then 429 for 15 minutes from the fifth failure, including for the correct password. Blocked retries do not extend the lock. Other IPs remain independent. No spending or accepted-request rate count is consumed |
| Scope | US SEC issuers, financial companyfacts; at most two issuers per check. No market prices, investment advice, crypto, forecasts, non-GAAP or issuer-release verification |
| Calls | At most four model calls, 2,000 output tokens each; at most six tool calls; no automatic provider retry |
| Time | 28-second runner deadline; each outbound fetch also has a 22-second abort signal; browser gives up at 32 seconds. Around 30 seconds is a target, not a measured production SLA |
| Rate | Five accepted requests per IP in a ten-minute window, enforced in the same globally consistent Durable Object, across regions |
| Daily spend | Default $3 per UTC day, configurable with Worker `DAILY_BUDGET_USD`. Zero disables paid calls; invalid/negative/nonfinite settings fail closed |
| Lifetime spend | Default $20 across UTC days, configurable with Worker `TOTAL_BUDGET_USD`. Hitting the cap, or lacking room for the next conservative reservation, latches a stop until an admin reset |
| Provider credit | HTTP 402, or HTTP 403/429 with credit/payment/quota exhaustion wording, durably pauses model calls until an admin reset |
| SEC cache | Public ticker directory and companyfacts JSON cached for six hours with Cache API; only successful valid JSON is cached; no KV namespace needed |

SEC requests use exactly `User-Agent: DappGo market-claim-verifier admin@dappgo.com`. The only network destinations in the backend are the fixed SEC ticker/facts endpoints and Baseten. Tool arguments cannot supply a fetch URL. `/api/check` checks same-origin browser requests, accepts JSON only, replaces any client-provided forwarding header with Cloudflare's `CF-Connecting-IP`, and returns `Cache-Control: no-store`. [Routes](./_routes.json) run Functions for `/api/check` and `/api/budget`; the existing [CSP](./_headers), language switch, color schemes, cache-busted assets and reduced-motion behavior remain in use.

Provider errors, truncated responses, invalid model JSON after the call limit, SEC failures, and timeouts issue **no financial verdict**. Costs already reserved remain accounted for and available partial steps are shown. Exhausted daily budget returns HTTP 429 / `budget_exhausted`; lifetime and provider stops return HTTP 503 / `total_budget_exhausted` or `credit_exhausted`. The server checks the ledger before starting a check and reserves again before **every** model call. A refused reservation never calls Baseten. Rate limits also return 429. Missing bindings, unavailable counters and absent keys fail closed to the saved demo.

## Public remaining-budget display

`GET /api/budget` is handled by [the budget Function](../functions/api/budget.ts) through the same private Worker and globally named Durable Object as checks. No key is needed to read this aggregate. The [Pages boundary](../workers/pages/check.mjs) allowlists only these fields:

```json
{"day":"2026-11-02","daily_limit_usd":3.0,"daily_spent_usd":0.59,"daily_remaining_usd":2.41,"resets_at":"2026-11-03T00:00:00Z","status":"ready"}
```

`status` is `ready`, `budget_exhausted`, `total_budget_exhausted` or `credit_exhausted`. This is an application spending allowance, not the provider account balance. Responses contain no holds, IP buckets, keys, user text, provider error bodies or account details. Successful responses allow five seconds of shared caching (`max-age=0, s-maxage=5, must-revalidate`); errors are `no-store`. Requests with `Cache-Control: no-cache` return `no-store` and read the ledger afresh.

The live box fetches this endpoint on page load, after every attempted check (including errors), when the page becomes visible, and at the server's next UTC midnight. Its own requests bypass caching. The English/Chinese text and accessible progress bar use `daily_remaining_usd`, including reserved-but-unreconciled costs. Below $0.10 it shows “Almost used up” / “預算即將用完”. A daily stop disables the input and submit button, links to the saved examples, and gives the next reset date at 00:00 UTC. Provider credit shows “Live checks paused (provider credit)” / “即時查核暫停（供應商額度已用完）”. Lifetime/provider stops do not promise a midnight restart. An unavailable budget read also disables submission until a successful refresh.

## Atomic cost cap

`SPEND_GATE` binds the SQLite-backed `SpendGate` Durable Object. Every request uses the same object name, **`baseten-live-global-v1`**. A reservation is committed before **each** model fetch, including a JSON repair call. A synchronous SQLite read/check/write section has no intervening `await`; simultaneous requests cannot each spend the same remaining balance. KV eventual consistency would not provide this guarantee.

Both caps use integer nano-USD (reservations rounded up, caps rounded down). Reservation and reconciliation update the original UTC day's counter and the nonexpiring lifetime counter in that same critical section. Late reconciliation after midnight refunds the original day only. Daily counters roll over by UTC date; holds without verified usage remain spent. Alarms may prune old daily/rate/hold rows, but never delete the lifetime counter or pause flags. Reaching the lifetime limit latches the stop even if a later reconciliation releases some reserved cost; increasing the configured limit or restarting/redeploying does not clear it. Upgrades adopt all retained legacy daily rows into lifetime spending; an old daily-only ledger cannot reconstruct already-pruned historical spend, so reconcile any such history administratively before enabling an existing deployment.

[Baseten's inference errors](https://docs.baseten.co/inference/errors) distinguish 402 billing failures from 403 authentication failures and 429 rate/capacity failures. [Its limits documentation](https://docs.baseten.co/inference/model-apis/pricing-and-limits) also describes enforced workspace budgets. We therefore latch `credit_exhausted` for every 402, and for 403/429 only when the body/code describes exhausted credit, balance, funds, quota, budget or a spending limit. Ordinary authentication/rate/capacity errors do not set the flag. There are no provider retries, and error bodies are discarded. Already admitted in-flight calls retain their holds; later reservations are refused once the flag is stored.

### Admin reset

There is **no public reset endpoint**. After reviewing the retained spend and resolving the provider issue, an admin may set a new, nonsecret Worker deployment variable `BUDGET_RESET_ID` (a unique incident/date identifier) and redeploy the **same Worker and Durable Object namespace**. The next ledger operation consumes that identifier once, clears the lifetime/provider latches, and starts a new lifetime allowance while retaining today's spending and every unsettled hold. Keeping the same identifier on future deploys never resets twice. Changing it deliberately performs another admin reset; deleting it does not reset anything. To drain calls first, set `DAILY_BUDGET_USD="0"`, redeploy, wait at least 32 seconds, then restore `3` with the new reset identifier. Keep the stop in place if the provider cannot fund further checks. Never delete or rename the namespace to bypass a cap, and never add a reset identifier merely to test the feature.

Prices are imported from the same provider registry used by the CLI ledger: input $1.25/M, cached input $0.15/M, output $4.25/M. The base reservation uses `Ledger.estimate`: compact Unicode JSON characters / 3, rounded up, plus the maximum output tokens. The public service additionally holds an input ceiling of serialized UTF-8 bytes + 4,096 template/control tokens, priced at the uncached input rate. This avoids treating the CLI character heuristic as a hard upper bound, especially for Chinese text. Cached-token discounts are applied only when usage is returned. The output limit includes the provider's billed completion budget; a model ID, pricing or token-accounting change requires reviewing this contract before enabling calls.

Successful usage reconciles using `Ledger.reconcile`. Missing/invalid usage, failed fetches and cancellations retain the full ceiling. Settlements are idempotent. Unexpected usage above the ceiling closes the day's remaining budget and latches the lifetime stop. Caps cover **model spend**, not Cloudflare infrastructure charges. Calls are charged to their reservation's UTC start day, including calls that finish after midnight. Daily/hold rows expire after 48 hours; lifetime spending, admin reset identifiers and pause flags never expire. Rate buckets expire after ten minutes and are also pruned by Durable Object alarms.

## Privacy

User text, model responses and tool results exist in request memory and are returned to that visitor. This application stores **no user text or transcript**, including in logs. It sends the post and needed SEC tool results to Baseten for inference; Baseten and Cloudflare have their own service policies. It writes no post or result to browser storage. Refreshing discards the live result.

The password travels only in the POST body to Pages and the private Worker/Durable Object authentication action. It is removed before the claim runner, never sent to Baseten, never echoed in responses, and never stored in the ledger or logs, even as a digest. The bilingual password field uses `type="password"` and `autocomplete="off"`; the form also declares `method="post"` so a native submission cannot put the password in a URL. After a successful check only, the browser keeps it under `claimcheck.livePassword` in **sessionStorage for that tab**. Reloading that tab restores it; a 401 clears it. If browser storage is blocked, checks still work and it must be entered again after a reload. Application code never writes the password to localStorage, cookies, URLs or rendered results. The site's existing language preference still uses localStorage.

The Durable Object persists only budget totals, stop flags, the nonsecret admin reset identifier, random reservation IDs/amounts/status, expiry times, and rate/failed-password counts keyed by a salted HMAC of the IP. Raw IP addresses are never persisted. Accepted-request buckets become invalid at ten minutes; failure buckets and lockouts expire at 15 minutes. Cleanup alarms remove expired buckets (subject to Cloudflare alarm scheduling). Successful authentication and budget resets do not clear prior failed attempts. Password rotation also preserves existing lockouts. The random HMAC salt stays with the lifetime ledger. Cache API stores only public SEC documents. There is no anonymous text log to retain. Worker observability is disabled in configuration; do not enable request-body logging, tails or tracing that capture user content or passwords. Platform access metadata is outside this application's transcript storage.

The published [Apple view](site/data/live-demo.json) is derived from the pre-existing [R06 result](evidence/eval-v2-2026-10-27/R06--agent@baseten.json) and its [raw trace](evidence/eval-v2-2026-10-27/traces/20261028T061222Z-6f6be742.json). It preserves the source hash, recorded start/end, $0.01221725 model cost and 8,294.411 ms model latency. Individual tool/check timestamps were not recorded and are explicitly null, rather than invented. Private model reasoning is omitted. The same renderer shows each live response with freshly measured timestamps, tool names/arguments/results, SEC evidence IDs, program checks, and cost. Keep new test evidence under the [test-record policy](TEST_RECORDS.md); do not archive arbitrary visitor posts as tests.

## Offline development

The normal verification command needs no Wrangler, npm install, provider key or SEC requests:

```sh
UV_OFFLINE=1 sh scripts/verify.sh
```

Focused tests, using an existing environment with repository dependencies:

```sh
python -m pytest -q tests/test_live_check.py tests/test_live_budget.py tests/test_live_password.py tests/test_live_password_edges.py tests/test_site_live_runtime.py tests/test_site_asset_versions.py
python scripts/build_live_demo.py --check
```

The Node boundary tests run through pytest on Node 22+, using the same plain-JavaScript request boundary that the Pages Function exports. They inject service/model responses and never fetch a remote endpoint. Password tests cover fail-closed configuration, fixed-size digest comparisons (not a statistical timing claim), 401 before budget/model work, concurrent failures and SQLite restart/cleanup, independent IP buckets, unchanged authenticated replay, redacted responses/storage/logs, and tab-session success/restore/rotation/blocked-storage behavior. Saved demo reproduction is independent of the three byte-identical explorer/site outputs in the main verifier. The verification runner also strips `LIVE_CHECK_*` settings from its test environment.

For a local interactive Pages preview, first install Wrangler once (package setup requires network), then:

```sh
wrangler pages dev docs/site --binding LIVE_CHECK_MOCK=1 --ip 127.0.0.1 --port 8788
```

Open `http://127.0.0.1:8788/#live-check`, choose **Use Apple example**, enter any nonempty placeholder in the password field, then **Check against SEC**. This mode returns the stored Apple result, labelled **Offline replay**, and accepts only that exact example. It cannot call a model and does not authenticate against the Worker secret. Its budget endpoint returns a clearly labelled mock allowance without spending. Mock mode also requires the request hostname to be `localhost`, `127.0.0.1` or `[::1]`; setting the variable on a production hostname cannot activate it. Full raw Baseten-response / SEC-fixture replay runs in the Python tests above. Do not set real credentials for mock mode. Static-only previews still display the saved trace; the live form is disabled when `/api/budget` is unavailable.

For Worker development/builds, Python 3.13+ and `uv` 0.13.4+ are required by the locked pywrangler toolchain:

```sh
cd workers/live
uv sync --frozen
uv run pywrangler deploy --dry-run --outdir /tmp/market-claim-worker-build
uv run pywrangler dev --ip 127.0.0.1 --port 8789
```

The dry run **does not deploy**. Without `LIVE_CHECK_PASSWORD`, the real local Worker returns `unavailable` before checking the provider key. The core is automatically bundled by its build hook. `uv.lock` pins the toolchain; `pylock.toml` pins WASM runtime packages. If a restricted workspace cannot write Wrangler's usual home registry/logs, set `WRANGLER_REGISTRY_PATH` and `WRANGLER_LOG_PATH` to temporary paths. `CHOKIDAR_USEPOLLING=true` avoids native watcher limits in constrained environments. Generated runtime/package directories are excluded from repository verification and link scanning.

## Exact handoff for Claude / owner

Do these **after reviewing the local commit**. These are deployment instructions, not actions already performed by this change.

1. Use an account with **Workers Paid**, Python Workers and SQLite Durable Objects. The Worker sets `limits.cpu_ms=30000` for Python/SEC document processing; the [Free plan's 10 ms CPU limit](https://developers.cloudflare.com/workers/platform/limits/) is unsuitable for this path. Cloudflare infrastructure costs are separate from the $3/day model cap; this change does not upgrade an account. Keep the existing Pages project **`market-claim-verifier`**, output directory **`docs`**, and its existing build command copying `docs/site/{index.html,styles.css,script.js,data,img}` to the output root. The new JSON is inside `data`, so no new static-copy rule is necessary. Keep `docs/_headers`, `docs/_redirects` and `docs/_routes.json` in the output. Functions live at repository-root `functions`, which Pages builds separately.
2. From `workers/live`, run `uv sync --frozen`, then **`uv run pywrangler deploy`**. The Worker name is **`market-claim-verifier-live`**. This creates the `SpendGate` class and SQLite namespace via migration `v1`. Keep `workers_dev=false`, `preview_urls=false` and no public routes. Deploying without either required secret is safe: all paid requests fail closed.
3. Still in `workers/live`, set both **Worker secrets** with **`uv run pywrangler secret put BASETEN_API_KEY`** and **`uv run pywrangler secret put LIVE_CHECK_PASSWORD`**, entering each value only in its hidden interactive prompt. Use a strong review password and share it privately with intended reviewers. Do not put either secret in Pages, a `.toml` file, `.dev.vars`, a command argument, client assets, or Git. These steps belong to Claude/owner; this change creates no secrets. With the password secret missing or empty, live checking stays disabled even if the provider key is present. To rotate the password, replace the same Worker secret; existing lockouts remain and an old browser value is cleared on its next 401. See [Cloudflare's secret configuration](https://developers.cloudflare.com/workers/configuration/secrets/).
4. Verify the Worker binding **`SPEND_GATE` → Durable Object class `SpendGate` in `market-claim-verifier-live`**. The Worker [config](../workers/live/wrangler.toml) must contain **`DAILY_BUDGET_USD="3"`** and **`TOTAL_BUDGET_USD="20"`**; these are Worker variables, not Pages secrets. Keep the existing object name, namespace and migration `v1` on upgrades so spending and flags survive. No KV binding or new namespace is required. Zero disables model calls; invalid settings fail closed. Leave optional `BUDGET_RESET_ID` unset except for a deliberate admin reset. Keep observability disabled and avoid body logging.
5. Deploy Pages using the root [wrangler.toml](../wrangler.toml), or confirm its equivalent dashboard service binding: **`LIVE_CHECK` → `market-claim-verifier-live`**. Re-deploy Pages after binding changes. Existing secret/configuration elsewhere must not be copied into client assets. Production has **no `LIVE_CHECK_MOCK` variable**. Preview deployments may omit `LIVE_CHECK` to disable paid calls, or deliberately share the same Worker/cap; do not create a second unmetered backend.
6. After owner deployment, first read **`GET /api/budget`** without a password and confirm the $3 limit, UTC reset time, safe public fields and cache lifetime of five seconds or less. Confirm missing/wrong passwords return 401 without reducing the allowance; retain no password values in test commands or logs. Test lockouts with offline doubles so reviewer IPs remain usable. Then enter the password in the browser and use the Apple example once: confirm the badge says **Live check**, the remaining allowance refreshes, a supported claim has `E1`, the correct fiscal period and an SEC filing URL, and the trace contains actual model, tool, program-check and verdict steps with cost/latency. This is a paid smoke check covered by both caps; retain its nonprivate test record if executing it. Check the Chinese switch, phone view, both color schemes, and a missing-period sentence. Setting `DAILY_BUDGET_USD="0"` and redeploying the same Worker can test disabled input / exhausted-budget fallback without spending; restore `3` afterwards. Test lifetime/provider stops with the offline mocks, rather than exhausting credit or resetting production storage.

Local validation and its remaining limits are recorded in [the implementation receipt](evidence/live-check-2026-11-02/REPORT.md).
The budget follow-up is recorded separately in [its receipt](evidence/live-budget-2026-11-02/REPORT.md).
The password follow-up is recorded separately in [its receipt](evidence/live-password-2026-11-02/REPORT.md).
