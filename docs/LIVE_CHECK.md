# Live check and visible agent trace

Implementation and operator handoff, updated 2026-11-03. The owner-selected runtime is Python 3.12 on DappGo's x86_64 k3s host, reached through Cloudflare Tunnel and Access from **free Pages Functions**. This document does not mean the endpoint is deployed. [Exact host, Tunnel, Access and Pages steps](../deploy/README.md). No paid model call is needed to build or test this change.

## Architecture and verdict identity

The browser posts `{ "text": "…", "password": "…", "provider": "baseten" }` to same-origin `/api/check`; provider is optional and defaults to Baseten. The [Pages Function](../functions/api/check.ts) validates the request and forwards only these fields, trusted `CF-Connecting-IP` as `X-Live-Client-IP`, and at most 1,024 User-Agent characters for history parsing to `https://${LIVE_ORIGIN_HOST}/api/check`. It supplies `CF-Access-Client-Id`, `CF-Access-Client-Secret` and `X-Live-Origin-Token` from server-side configuration. Visitor cookies, Authorization and other browser headers are not forwarded. Redirects are disabled; a 25-second abort includes response-body reading. Invalid origin responses fail closed to the saved demo; public result fields and budget counters are allowlisted.

The [self-hosted adapter](../server/live/server.py) authenticates **every route**, including `/healthz`, against `LIVE_ORIGIN_TOKEN` using a fixed-size constant-time digest comparison. Missing tokens return 401; wrong tokens return 403. It then authenticates check/compare passwords before budgets, rate limits, SEC or model I/O. Routes are `GET /api/budget`, `POST /api/check`, `POST /api/check-example`, `POST /api/compare`, `GET /api/history`, `GET /api/history/{id}`, and `GET /healthz`. History and budget reads need no review password. The browser receives no provider key.

The adapter imports the [gate](../workers/live/src/gate.py), [runner](../workers/live/src/live.py) and claimcheck Python modules directly. The [image](../server/live/Dockerfile) copies these sources, not a TypeScript port. Fact selection, fiscal normalization, calculations, evidence IDs, strict JSON parsing and final evaluation remain Python. A model proposal cannot override a program verdict: any contradiction → `contradicted`; every extracted assertion supported → `supported`; otherwise → `insufficient_evidence`. Individual checks may remain `unchecked`. Missing explicit dated periods abstain without a model call. Extraction can miss assertions; a supported result applies to the assertions actually extracted. SEC evidence can be incomplete or restated.

[Recorded replay tests](../tests/test_live_check.py) reproduce the three Apple Baseten responses, including malformed JSON/repair, and compare all **357 v2 Baseten saved tool transcripts** through live finish and CLI evaluation. Those old companyfacts-only records explicitly treat unavailable earnings-release fallback evidence as unavailable; they do not fetch or synthesize L4 evidence. This is a frozen-response recheck, not a new model evaluation, OCR/ASR test or accuracy measurement. [Server adapter tests](../tests/test_live_server.py) replay Apple through fake HTTP transports and real SQLite.

## Provider receipts, compare and history

Provider IDs are exactly `baseten`, `fireworks`, and `meta`. The runner reuses the [existing adapters and pricing](../src/claimcheck/providers.py) with fixed models `meta-models/muse-spark-open-1026`, `accounts/fireworks/models/muse-spark-open`, and `muse-spark-1.3`, respectively. Unknown providers return 400 / `unknown_provider` before reservation. Meta OCR/ASR preprocessing is independent of the verifier choice; each paid call reserves from the same durable ledger before network I/O. Missing/invalid usage retains the conservative hold, reflected by `cost_is_bound`.

JSON POST bodies are at most 1 KiB, including chunked bodies. Extra request keys, query strings and cross-origin browser requests are rejected. Routes accept exactly:

```text
POST /api/check         {text, password, provider?}
POST /api/check-example {example_id, password, provider?}
POST /api/compare       {text, password, providers:[provider, provider, provider?]}
                    or {example_id, password, providers:[provider, provider, provider?]}
GET  /api/history?limit=50
GET  /api/history/{id}
```

Compare requires 2–3 distinct providers and returns `{ "runs": [envelope, …] }` in request order. Each member checks budget before starting and reserves before each paid call. A budget, lifetime, credit or rate stop ends the sequence; the final attempted member is an error envelope. Completed and failed members are retained separately. Other provider failures allow the next provider to run. The shared per-IP rate counter counts each member. Compare authentication/validation errors use the ordinary error response; an accepted comparison returns HTTP 200 even when a member fails.

Every live run envelope, including a failed attempt, adds these fields (numeric values below are illustrative, not measurements):

```json
{
  "receipt": {
    "provider": "baseten",
    "model": "meta-models/muse-spark-open-1026",
    "latency_ms": 6300,
    "cost_usd": 0.0099,
    "preprocessing": null
  },
  "input": {"kind": "text", "text_read": "Apple FY2025 revenue was $416.2B."}
}
```

`receipt.cost_usd` and `receipt.latency_ms` cover verification. Media examples have `preprocessing: {"model":"muse-voice-transcribe-1.0","latency_ms":1200,"cost_usd":0.001}` (model depends on input kind). Native text/PDF examples use `native-text` / `native-pdf` with zero preprocessing cost. Pasted text uses `null`. Top-level `cost_usd` and `latency_ms` include preprocessing; their values equal the sum of the two receipt portions. Costs are USD estimates or retained upper bounds, not provider invoice amounts.

`input` is `{kind, example_id?, story?, text_read}`. `kind` is `text|image|pdf|audio|video`, and `story` is `a|b|c`. Original unprefixed IDs (`text` through `video`) mean story A; prefixed IDs (`a-text` through `c-video`) are supported when packaged as ready, hash-matching entries. W1 does not create the other stories' assets. Example inputs also retain the existing `input.preprocessing: {model, provider, latency_ms, cost_usd}` for compatibility; receipt preprocessing has exactly the three fields above. Media `text_read` may contain at most 12,000 characters; the public row keeps only its first 600.

`GET /api/history` returns `{ "rows": [row, …] }`, newest first. `limit` defaults to 50 and accepts a single integer from 1 to 50; duplicate/unknown query keys are rejected. Summary rows have exactly this shape:

```json
{
  "id": "0123456789abcdef0123456789abcdef",
  "at": "2026-11-04T01:00:00.000Z",
  "ip_masked": "192.0.*.*#1234abcd",
  "device": "Windows / desktop",
  "browser": "Edge",
  "kind": "text",
  "example_id": null,
  "story": null,
  "input_text": "Apple FY2025 revenue was $416.2B.",
  "provider": "baseten",
  "model": "meta-models/muse-spark-open-1026",
  "verdict": "supported",
  "corrections_count": 0,
  "latency_ms": 6300,
  "cost_usd": 0.0099,
  "preprocessing_cost_usd": 0
}
```

`GET /api/history/{id}` returns the same row plus `envelope`, the retained public run envelope (≤65,536 serialized bytes). Unknown, expired or pruned IDs return 404 / `not_found`; malformed IDs return 400. Failed attempts have `verdict: null` and normally zero corrections. `corrections_count` counts edits in the original result. When an envelope is too large, `history_truncated: true` marks removal of trailing trace/evidence/claim items; the receipt and input are retained, with input limited to 600 characters if needed and corrections omitted as a last resort. Such a reopened result is partial. History responses are `no-store` and pass strict row/receipt/input allowlists, including on detail reads.

History resides in `/data/ledger.sqlite3` on the existing PVC. Only authenticated, validated attempts are stored, including paid failures, budget/rate stops and each compare member; authentication and input-validation rejections create no row. Retention is 14 days and at most 5,000 rows, enforced on insert and by the existing 60-second periodic prune. Reads immediately exclude expired rows. IPv4 retains only its first two octets and an eight-hex keyed hash; IPv6 uses its first two hextets, and invalid/missing addresses become `unknown`. The private hash salt persists across restarts. User-Agent is reduced to deterministic browser family plus OS/device class by a small parser, with no external UA library; raw IP and UA are never retained. [Provider/history tests](../tests/test_live_providers_history.py) and [Pages contract tests](../tests/node/live-v3-boundary.test.mjs) use fake transports and temporary SQLite, not fresh provider or OCR/ASR execution.

## Corrected draft

Successful checks also return `corrections`, generated by the pure Python [correction builder](../src/claimcheck/correction.py). The site labels it **Corrected draft — only listed assertions checked**. This is a partial draft, never article approval. No extra model call is made and no model rewrite, summary or proposed replacement supplies its numbers.

The corrections object contains `original_text`, `span_unit: "unicode_codepoints"`, ordered `edits`, and `not_corrected` records with localized reasons. Supported assertions get `supported` (no edit needed), unchecked opinions/out-of-scope assertions get `not_judged`, and insufficient evidence gets `insufficient_evidence` (not corrected). Single-assertion inputs and the [saved Apple demo](site/data/live-demo.json) also include this object. Each edit includes `start`, `end`, `original`, `replacement`, program `actual_value`, evidence `unit`, `period`, optional `base_period`, `evidence_ids` and `citations`. The replacement preserves the original scale, precision and grouping, using decimal half-up rounding. Examples include `$416.2B` → `$102.5B` and the corresponding Traditional Chinese hundred-million-unit amounts.

Directly below the draft, the site states: “Only the assertions listed below were checked; nothing else in the text was verified.”

An edit needs a unique literal assertion or unique original number, matching stated units and periods, a finite contradicted program value and complete SEC citations. The original context must identify the checked issuer and financial metric uniquely; a matching number cannot move a revenue fact onto a cash assertion or another company. If a model normalized the assertion's wording, the unique number must bind within an original sentence with the checked period. Duplicate or overlapping spans, missing evidence or component citations, unresolved periods, inequalities, ranges, compound amounts and qualitative claims such as “first ever” retain their original text and receive a reason under **Not corrected**. Directional growth can substitute a magnitude only when the verified direction agrees with the original wording. Supported assertions remain unchanged. The draft cannot cover assertions extraction missed.

For derived results without a top-level `filing_url`, the builder recursively cites every component filing, reconstructing SEC archive links from recorded CIK/accession metadata when necessary. It never fetches a filing. The saved [Apple revenue case](evidence/posts-2026-10-28/demo-thread-baseten/report.json) yields:

> Apple pulled in ~~$416.2 billion~~ → **$102.5 billion** of revenue in fiscal Q4 2025 alone.

Its [retained trace](evidence/posts-2026-10-28/demo-thread-baseten/traces/20261029T023240Z-12ac28b8.json) records $416.161B annual minus $313.695B nine-month revenue, yielding $102.466B. Both recorded component filings are cited; this offline recheck does not revalidate them against today's SEC data. [Correction tests and validation records](evidence/corrected-draft-2026-11-03/REPORT.md) cover the retained case, span binding, units/periods, citations and hostile-text rendering. The site uses text nodes, `<del>` and `<strong>` and converts code-point offsets explicitly, including emoji. Pages passes corrections through its public allowlist. No separate model rewrite or budget action is needed for corrections.

## Limits and failure behavior

| Limit | Behavior |
| --- | --- |
| Input | 1–600 Unicode characters after trimming; 1 KiB JSON body ceiling, including chunked bodies |
| Password | `LIVE_CHECK_PASSWORD` from env/file; missing/empty disables checks with 503; missing/wrong input returns 401 before reservation/model I/O |
| Failed passwords | Five failures per IP per 15 minutes, then 429 for 15 minutes from the fifth failure; correct passwords remain blocked during lockout; other IPs independent |
| Scope | US SEC issuers and companyfacts; at most three issuers; no prices, investment advice, crypto, forecasts, non-GAAP or issuer-release verification |
| Calls | At most four model calls, 2,000 output tokens each; at most six tool calls; no automatic provider retry |
| Time | 28-second text / 60-second example run; 22-second verifier/SEC and 50-second Meta preprocessing I/O; Pages: 25-second text / 65-second example / 195-second compare; browser timing belongs to the site; no measured production SLA |
| Rate | Five accepted checks per IP per ten minutes; raw IP never stored |
| Daily spend | `DAILY_BUDGET_USD`, deployment $10 per UTC day; zero disables calls; invalid/negative/nonfinite values fail closed |
| Lifetime spend | `TOTAL_BUDGET_USD`, deployment $60 across all days; lack of reservation room latches a stop |
| Provider credit | 402, or 403/429 with credit/payment/quota exhaustion wording, durably pauses calls; ordinary auth/rate errors do not latch a credit stop |
| SEC cache | Six-hour memory/disk cache of successful JSON bodies only; HTTPS host allowlist `www.sec.gov` / `data.sec.gov`; redirects disabled |

SEC requests use exactly `User-Agent: DappGo market-claim-verifier admin@dappgo.com`. Tool arguments cannot supply fetch URLs. [Pages routes](_routes.json) include `/api/check`, `/api/check-example`, `/api/compare`, `/api/history`, `/api/history/*` and `/api/budget`. The [CSP](_headers), language switch, color schemes, cache-busted assets and reduced-motion behavior remain in use.

Provider errors, incomplete/model-invalid responses, SEC failures and timeouts issue no financial verdict. Reserved costs remain accounted for and available partial steps are shown. Daily exhaustion returns 429 / `budget_exhausted`; lifetime/provider stops return 503 / `total_budget_exhausted` or `credit_exhausted`. Rate limits return 429; timeouts return 504 / `timeout` from Python. Missing origin configuration, unavailable counters or absent keys fail closed to the saved demo.

## Public remaining-budget display

`GET /api/budget` uses [the budget Function](../functions/api/budget.ts) and the same persistent ledger as checks. Visitors need no review password to read the aggregate; Pages still authenticates to Access and the origin. The [boundary](../workers/pages/check.mjs) returns only:

```json
{"day":"2026-11-02","daily_limit_usd":10.0,"daily_spent_usd":0.59,"daily_remaining_usd":9.41,"resets_at":"2026-11-03T00:00:00Z","status":"ready"}
```

Status is `ready`, `budget_exhausted`, `total_budget_exhausted` or `credit_exhausted`. This is an application allowance, not the provider balance. Successful responses allow five seconds of shared caching; errors are `no-store`. A visitor request with `Cache-Control: no-cache` receives `no-store` and a fresh ledger read, without forwarding that header.

The live box in each language refreshes on page load, attempted checks, visibility and the next UTC midnight. The accessible meter includes reservations. Below $0.10 it shows “Almost used up”. Daily stops disable submission and show the next UTC reset. Lifetime/provider stops show a pause without promising a midnight restart. Unavailable budgets disable submission until refreshed successfully.

## Atomic cost cap

One Python process and one replica use a PVC-backed SQLite ledger with one JSON state row, WAL and `synchronous=FULL`. Every read/check/write, including prune, holds a process-wide `asyncio.Lock` and `BEGIN IMMEDIATE` transaction. A reservation commits before every model fetch, including repairs. The [Deployment](../deploy/k8s/live-check.yaml) uses **replicas=1, strategy=Recreate**; no multi-worker server or HPA is supported.

Both caps use integer nano-USD: holds round up and caps round down. Reconciliation updates the reservation's UTC start day and lifetime counter atomically. Missing/invalid usage, failed fetches and cancellation retain the entire ceiling. Settlement is idempotent. Usage above the reservation closes the daily budget and latches the lifetime stop. A lifetime stop remains latched even if a later settlement refunds reserved cost. Increasing a limit or restarting cannot clear it.

There is **no reset endpoint or reset setting** in the self-hosted adapter. `BUDGET_RESET_ID` is ignored. Never replace/delete the PVC or reset lifetime counters to bypass a stop. Periodic pruning runs every 60 seconds; transitions also prune expired buckets. Day/hold rows expire after 48 hours, accepted-rate buckets after ten minutes and failed-auth buckets after 15 minutes. Lifetime totals, pause flags and the HMAC salt remain.

Pricing and arithmetic come from the CLI ledger/provider registry. The additional conservative hold uses serialized UTF-8 bytes plus 4,096 template/control tokens and the maximum output tokens, without cached discounts. Successful verified usage reconciles using the same pricing calculation. Review model/pricing/token contract changes before enabling them. Caps cover model estimates; host/infrastructure costs are separate.

## Examples

The Try section contains five self-made inputs of the [saved Big Tech post](site/data/live-demo-post.json): text, screenshot, one-page native-text PDF, Breeze narration and a narrated still video. [The manifest](examples/manifest.json) records IDs (`text`, `image`, `pdf`, `audio`, `video`), filenames, root-relative `/examples/` URLs, SHA-256 hashes, bytes, measured media durations and English/Traditional Chinese descriptions. Assets live in `docs/examples/`, inside the Pages output. The screenshot is the committed copy of `demo/assets/saved-post-v4.png` from the video worktree; the PDF uses Times, the site's document serif family. No third-party post or new financial result is invented.

**Current preparation:** all five input files are ready. The [MP3](examples/post.mp3) is 32.96 s; the [H.264/AAC MP4](examples/post.mp4) ends at 33.46 s, 0.5 s after narration. Both have native playback controls in the cards. The host's locked Breeze synthesis receipts and the offline packaging receipt are retained in [the asset evidence](evidence/example-assets/), indexed in [the packaging report](evidence/media-examples-2026-11-03/REPORT.md#round-3--finished-media-package). No Meta model was invoked to package these files. Only [the text card's saved result](site/data/examples/text.json) reuses a real historical envelope, preserving its original cost, latency, evidence, corrections and source hashes. Its native reading time is unknown (`null`). The other four saved verification results remain **Saved result pending** until a host records them; this describes verification results, not asset availability. A missing saved media result never falls back to the text result. These demonstrations are not an accuracy benchmark.

`POST /api/check-example` accepts only `{ "example_id": "image", "password": "…" }`, as JSON of at most **1 KiB** (also for chunked bodies). [The Pages Function](../functions/api/check-example.ts) uses the same origin, Access, origin-token, trusted-IP and response allowlists as `/api/check`; no uploads, paths or URLs are accepted. [The origin](../server/live/server.py) authenticates first, looks up the ID in `/app/examples/manifest.json`, verifies filename/size/hash, and applies the same rate and durable daily/lifetime gates. Unknown IDs return 400; unavailable/pending/tampered files return 503 without a model reservation. `/api/check` and its 600-character boundary are unchanged.

The [existing ingest code](../src/claimcheck/ingest_media.py) extracts PDF text locally, reads images with **`muse-spark-1.3`** and transcribes audio with **`muse-voice-transcribe-1.0`**, both via **provider `meta` / the Meta Model API**. Video uses ASR plus all three existing frame samples (1/6, 1/2, 5/6 of duration). OCR/ASR text is untrusted input, not SEC evidence. The text enters the unchanged live claim runner and deterministic `corrections` builder. Fixed video inputs may contain multiple readings; the 12,000-character post-ingest ceiling does not change arbitrary pasted-text limits.

The envelope adds `input: {example_id, kind, preprocessing: {model, provider, cost_usd, latency_ms}, text_read}`. Top-level cost/latency include preprocessing; preprocessing metrics are a subset, not an additional charge. Native extraction uses provider `local` and costs zero. Every OCR/ASR attempt reserves against the **same SQLite ledger before external I/O**; missing usage/errors/timeouts retain holds. OCR adds an image-patch ceiling; ASR uses rounded-second pricing. The sync ingest functions receive bridges to the async transport/gate. Cancellation aborts pending I/O and seals the bridge, so a still-decoding thread cannot start a late paid call. No automatic provider retry is enabled by the live adapter. The whole example request has **60 s**, Pages allows **65 s** including the body, and the browser allows **70 s**. The 28/25/32 s text path is unchanged.

The bilingual renderer uses text nodes for the read text and preprocessing fields. Order: **What the model read → verdict → corrected draft → SEC evidence → agent trace (collapsed)**. Saved buttons need no password and remain available at budget stops. All five ready live cards require the same password and share the five-check/ten-minute limit. Media playback needs no password. Root-relative paths work on `/zh/`; the site CSP allows media from the same origin only.

Prepare the locked voice and H.264/AAC video **on the host** (this command invokes Breeze locally, seed 2026, the exact v4 clone reference/transcript; it never substitutes another voice):

```sh
python3 scripts/build_examples.py --synthesize --video-repo /Users/yan/git/market-claim-verifier-video
python3 scripts/build_example_results.py
python3 scripts/build_examples.py --check
```

The builder retains jobs, input/reference hashes, synthesis logs and receipts under `docs/evidence/example-assets/<timestamp>/`, including failed attempts; it does not copy the licensed reference into this repository. The MP4 is 1920×1080, H.264/AAC, at most 2,000,000 bytes, with an explicit endpoint 0.5 s after narration. Media duration must be at most 60 s. Ready files do not regenerate pending notices during offline rebuilds. Build the image **after** preparing media, so `/app/examples` contains the same hashes the site publishes. Package/publish static `examples/` alongside `data/`, `img/`, HTML, CSS and JS in the existing Pages copy step; this is a handoff, not authorization to deploy.

After the host separately enables the reviewed service/site, record exactly one real request per ID:

```sh
# Reads LIVE_CHECK_PASSWORD(_FILE), or prompts without echo. No key in argv.
python3 scripts/run_example_records.py --origin https://hackathon.dappgo.com --max-spend-usd 3 --execute
# Use the exact new directory printed by that command:
python3 scripts/build_example_results.py --records docs/evidence/example-records/REPLACE_WITH_RUN_ID
python3 scripts/stamp_site_assets.py
python3 scripts/build_zh_page.py
bash scripts/verify.sh
```

[The recorder](../scripts/run_example_records.py) freezes cases/hashes/budget before requests, refuses existing output directories, makes no retries, and retains failed/partial public responses, public model/tool/program events, costs, budget snapshots and receipts. Preflight requires the server's whole daily limit to fit the frozen cap; the recorder never resets a ledger, starts no case within 75 seconds of UTC reset, and stops further cases on a day change. Provider-private raw responses are not exposed by the public API and are not claimed as retained. [The result builder](../scripts/build_example_results.py) publishes only complete, explicitly selected, hash-matched retained runs. An incomplete set stays incomplete; keep it before recording any separately named follow-up. Follow [test-record policy](TEST_RECORDS.md).

Offline mock mode also accepts these IDs via `/api/check-example`, but replays only each ID's own saved envelope. Unrecorded IDs return `saved_result_pending`; it never performs OCR/ASR or SEC requests and never fabricates a media result. [Asset/record tests](../tests/test_example_assets.py), [server tests](../tests/test_live_examples.py), [proxy tests](../tests/node/live-boundary.test.mjs) and [hostile-text UI tests](../tests/test_site_examples_runtime.py) run offline. The verifier rebuilds the example assets, index and selected envelopes byte for byte.

## Privacy

Authenticated, validated runs publish their input and public result in the bounded history described above, including failed/partial attempts. This is an intentional change from the original response-only storage policy. There is no application request-body/exception log. The selected verifier receives the post and necessary SEC tool results; Meta receives media for OCR/ASR regardless of verifier choice. Providers have their own policies. Spending state retains totals, stop flags, reservation IDs/amounts/status, expiries and salted HMAC IP buckets; history is a separate table in the same SQLite file. The SEC cache stores public JSON bodies only. Access/hosting metadata is outside application history storage; do not enable body tracing or diagnostic credential dumps.

The review password travels only in the POST body, is removed before the runner and is never sent to a provider, persisted in the ledger/history, echoed or logged. After successful authentication/check only, the UI stores it in `sessionStorage` for that tab; reload restores it and a 401 clears it. Blocked browser storage still permits checks. It never enters localStorage, cookies, URLs or rendered results. The password input remains masked with autocomplete off, and the form declares POST.

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
python -m pytest -q tests/test_live_server.py tests/test_live_examples.py tests/test_live_providers_history.py tests/test_live_check.py tests/test_live_budget.py tests/test_live_password.py tests/test_live_password_edges.py tests/test_site_live_runtime.py
node --test tests/node/live-boundary.test.mjs tests/node/live-v3-boundary.test.mjs
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
