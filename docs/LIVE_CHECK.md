# Live check and visible agent trace

Implementation and operator handoff, updated 2026-11-03. The owner-selected runtime is Python 3.12 on DappGo's x86_64 k3s host, reached through Cloudflare Tunnel and Access from **free Pages Functions**. This document does not mean the endpoint is deployed. [Exact host, Tunnel, Access and Pages steps](../deploy/README.md). No paid model call is needed to build or test this change.

## Architecture and verdict identity

The browser posts `{ "text": "…", "password": "…" }` to same-origin `/api/check`. The [Pages Function](../functions/api/check.ts) validates the request and forwards only these fields and trusted `CF-Connecting-IP` as `X-Live-Client-IP` to `https://${LIVE_ORIGIN_HOST}/api/check`. It supplies `CF-Access-Client-Id`, `CF-Access-Client-Secret` and `X-Live-Origin-Token` from server-side configuration. No visitor cookies, Authorization or other browser headers are forwarded. Redirects are disabled; a 25-second abort includes response-body reading. Invalid origin responses fail closed to the saved demo; public result fields and budget counters are allowlisted.

The [self-hosted adapter](../server/live/server.py) authenticates **every route**, including `/healthz`, against `LIVE_ORIGIN_TOKEN` using a fixed-size constant-time digest comparison. Missing tokens return 401; wrong tokens return 403. It then authenticates check passwords before budgets, rate limits, SEC or model I/O. Only `GET /api/budget`, `POST /api/check` and `GET /healthz` are exposed. It calls Baseten's OpenAI-compatible endpoint with **`meta-models/muse-spark-open-1026`**. The browser receives no provider key.

The adapter imports the unchanged [gate](../workers/live/src/gate.py), [runner](../workers/live/src/live.py) and claimcheck Python modules directly. The [image](../server/live/Dockerfile) copies these sources, not a TypeScript port. Fact selection, fiscal normalization, calculations, evidence IDs, strict JSON parsing and final evaluation remain Python. A model proposal cannot override a program verdict: any contradiction → `contradicted`; every extracted assertion supported → `supported`; otherwise → `insufficient_evidence`. Individual checks may remain `unchecked`. Missing explicit dated periods abstain without a model call. Extraction can miss assertions; a supported result applies to the assertions actually extracted. SEC evidence can be incomplete or restated.

[Recorded replay tests](../tests/test_live_check.py) reproduce the three Apple Baseten responses, including malformed JSON/repair, and compare all **357 v2 Baseten saved tool transcripts** through live finish and CLI evaluation. Those old companyfacts-only records explicitly treat unavailable earnings-release fallback evidence as unavailable; they do not fetch or synthesize L4 evidence. This is a frozen-response recheck, not a new model evaluation, OCR/ASR test or accuracy measurement. [Server adapter tests](../tests/test_live_server.py) replay Apple through fake HTTP transports and real SQLite.

## Limits and failure behavior

| Limit | Behavior |
| --- | --- |
| Input | 1–600 Unicode characters after trimming; 4 KiB body ceiling, including chunked bodies |
| Password | `LIVE_CHECK_PASSWORD` from env/file; missing/empty disables checks with 503; missing/wrong input returns 401 before reservation/model I/O |
| Failed passwords | Five failures per IP per 15 minutes, then 429 for 15 minutes from the fifth failure; correct passwords remain blocked during lockout; other IPs independent |
| Scope | US SEC issuers and companyfacts; at most two issuers; no prices, investment advice, crypto, forecasts, non-GAAP or issuer-release verification |
| Calls | At most four model calls, 2,000 output tokens each; at most six tool calls; no automatic provider retry |
| Time | 28-second request/runner deadline; 22-second outbound deadline; 25-second Pages timeout; 32-second browser deadline; no measured production SLA |
| Rate | Five accepted checks per IP per ten minutes; raw IP never stored |
| Daily spend | `DAILY_BUDGET_USD`, default $3 per UTC day; zero disables calls; invalid/negative/nonfinite values fail closed |
| Lifetime spend | `TOTAL_BUDGET_USD`, default $20 across all days; lack of reservation room latches a stop |
| Provider credit | 402, or 403/429 with credit/payment/quota exhaustion wording, durably pauses calls; ordinary auth/rate errors do not latch a credit stop |
| SEC cache | Six-hour memory/disk cache of successful JSON bodies only; HTTPS host allowlist `www.sec.gov` / `data.sec.gov`; redirects disabled |

SEC requests use exactly `User-Agent: DappGo market-claim-verifier admin@dappgo.com`. Tool arguments cannot supply fetch URLs. [Pages routes](_routes.json) invoke Functions only for `/api/check` and `/api/budget`. The [CSP](_headers), language switch, color schemes, cache-busted assets and reduced-motion behavior remain in use.

Provider errors, incomplete/model-invalid responses, SEC failures and timeouts issue no financial verdict. Reserved costs remain accounted for and available partial steps are shown. Daily exhaustion returns 429 / `budget_exhausted`; lifetime/provider stops return 503 / `total_budget_exhausted` or `credit_exhausted`. Rate limits return 429; timeouts return 504 / `timeout` from Python. Missing origin configuration, unavailable counters or absent keys fail closed to the saved demo.

## Public remaining-budget display

`GET /api/budget` uses [the budget Function](../functions/api/budget.ts) and the same persistent ledger as checks. Visitors need no review password to read the aggregate; Pages still authenticates to Access and the origin. The [boundary](../workers/pages/check.mjs) returns only:

```json
{"day":"2026-11-02","daily_limit_usd":3.0,"daily_spent_usd":0.59,"daily_remaining_usd":2.41,"resets_at":"2026-11-03T00:00:00Z","status":"ready"}
```

Status is `ready`, `budget_exhausted`, `total_budget_exhausted` or `credit_exhausted`. This is an application allowance, not the provider balance. Successful responses allow five seconds of shared caching; errors are `no-store`. A visitor request with `Cache-Control: no-cache` receives `no-store` and a fresh ledger read, without forwarding that header.

The bilingual live box refreshes on page load, attempted checks, visibility and the next UTC midnight. The accessible meter includes reservations. Below $0.10 it shows “Almost used up” / “預算即將用完”. Daily stops disable submission and show the next UTC reset. Lifetime/provider stops show a pause without promising a midnight restart. Unavailable budgets disable submission until refreshed successfully.

## Atomic cost cap

One Python process and one replica use a PVC-backed SQLite ledger with one JSON state row, WAL and `synchronous=FULL`. Every read/check/write, including prune, holds a process-wide `asyncio.Lock` and `BEGIN IMMEDIATE` transaction. A reservation commits before every model fetch, including repairs. The [Deployment](../deploy/k8s/live-check.yaml) uses **replicas=1, strategy=Recreate**; no multi-worker server or HPA is supported.

Both caps use integer nano-USD: holds round up and caps round down. Reconciliation updates the reservation's UTC start day and lifetime counter atomically. Missing/invalid usage, failed fetches and cancellation retain the entire ceiling. Settlement is idempotent. Usage above the reservation closes the daily budget and latches the lifetime stop. A lifetime stop remains latched even if a later settlement refunds reserved cost. Increasing a limit or restarting cannot clear it.

There is **no reset endpoint or reset setting** in the self-hosted adapter. `BUDGET_RESET_ID` is ignored. Never replace/delete the PVC or reset lifetime counters to bypass a stop. Periodic pruning runs every 60 seconds; transitions also prune expired buckets. Day/hold rows expire after 48 hours, accepted-rate buckets after ten minutes and failed-auth buckets after 15 minutes. Lifetime totals, pause flags and the HMAC salt remain.

Pricing and arithmetic come from the CLI ledger/provider registry. The additional conservative hold uses serialized UTF-8 bytes plus 4,096 template/control tokens and the maximum output tokens, without cached discounts. Successful verified usage reconciles using the same pricing calculation. Review model/pricing/token contract changes before enabling them. Caps cover model estimates; host/infrastructure costs are separate.

## Privacy

Posts, model responses and tool results stay in request memory and the response to that visitor. There is no application transcript/request-body/exception log. Baseten receives the post and necessary SEC tool results; providers have their own policies. The ledger stores only totals, stop flags, reservation IDs/amounts/status, expiries and salted HMAC IP buckets. The SEC cache stores public JSON bodies, never posts or provider responses. Access/hosting metadata is outside application transcript storage; do not enable body tracing or diagnostic credential dumps.

The review password travels only in the POST body, is removed before the runner and is never sent to Baseten, persisted in the ledger, echoed or logged. After successful authentication/check only, the UI stores it in `sessionStorage` for that tab; reload restores it and a 401 clears it. Blocked browser storage still permits checks. It never enters localStorage, cookies, URLs or rendered results. The password input remains masked with autocomplete off, and the form declares POST.

The [saved Apple view](site/data/live-demo.json) derives from the original [R06 result](evidence/eval-v2-2026-10-27/R06--agent@baseten.json) and [raw trace](evidence/eval-v2-2026-10-27/traces/20261028T061222Z-6f6be742.json), retaining recorded timestamps, cost and latency. Unrecorded event timestamps remain null; private reasoning is omitted. Follow the [test-record policy](TEST_RECORDS.md); do not archive arbitrary visitor posts as test cases.

## Offline development

```sh
sh scripts/verify.sh
# Once the locked dependency cache is populated:
UV_OFFLINE=1 sh scripts/verify.sh
```

The verifier installs locked dependencies, strips all `LIVE_*` credentials/settings and disables network access for Python/Node suites and builders. Server HTTP tests use aiohttp request objects, fake HTTPX transports, frozen SEC fixtures and temporary SQLite without sockets. Pages tests stub fetch. No model/SEC request, Docker daemon, Wrangler or npm installation is needed for verification.

For focused tests in a dependency-equipped environment:

```sh
python -m pytest -q tests/test_live_server.py tests/test_live_check.py tests/test_live_budget.py tests/test_live_password.py tests/test_live_password_edges.py tests/test_site_live_runtime.py
node --test tests/node/live-boundary.test.mjs
python scripts/build_live_demo.py --check
```

An interactive local mock needs no credentials:

```sh
wrangler pages dev docs/site --binding LIVE_CHECK_MOCK=1 --ip 127.0.0.1 --port 8788
```

Open `http://127.0.0.1:8788/#live-check`, choose **Use Apple example**, enter a nonempty placeholder password and submit. Only that recorded input is accepted, labelled **Offline replay**, with a mock budget. Mock mode requires a loopback hostname and cannot activate on the production hostname. Static previews still display saved traces while live controls stay disabled if the budget route is unavailable.

## Optional paid-plan Cloudflare adapter

[workers/live](../workers/live/src/entry.py) remains available for a future explicit **Workers Paid** decision, with Python Workers and a SQLite Durable Object. Its [Wrangler configuration](../workers/live/wrangler.toml) retains the original CPU allowance and migration. It is not referenced by the current Pages proxy; no plan upgrade or Worker deployment is required for the self-hosted route. The [bundle builder](../scripts/build_live_worker.py) still copies core source bytes unchanged. Historical Worker receipts retain their original deployment assumptions. Do not run independent spending ledgers simultaneously or discard prior spending when changing adapters.

## Exact handoff for Claude / owner

Use the [host operator commands and Tunnel/Access/Pages setup](../deploy/README.md#host-operator-commands), followed by a budget-only smoke check. This handoff does not authorize a fresh paid model call. Keep the PVC and the same spend history across upgrades and rollback.

Retained receipts: [original live check](evidence/live-check-2026-11-02/REPORT.md), [budget](evidence/live-budget-2026-11-02/REPORT.md), [password](evidence/live-password-2026-11-02/REPORT.md), and [self-hosted adapter](evidence/live-selfhost-2026-11-03/REPORT.md).
