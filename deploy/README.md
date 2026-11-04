# Self-hosted live check

The owner-selected path is **free Pages Functions → Cloudflare Access + Tunnel → Python 3.12 on the x86_64 DappGo k3s host**. No Workers Paid subscription or Durable Object is required. This is an operator handoff; nothing here has been deployed.

The [HTTP adapter](../server/live/server.py) exposes `GET /api/budget`, `POST /api/check`, `POST /api/check-example`, `POST /api/compare`, `GET /api/history`, `GET /api/history/{id}`, and `GET /healthz` on `0.0.0.0:8080`. Every route, including health and unknown paths, requires `X-Live-Origin-Token`. Missing headers return 401; incorrect tokens return 403, both with `origin_rejected`. Pages maps origin-auth failures to the 503 demo fallback, while wrong review passwords still return 401 / `unauthorized`. Checks and compare additionally require the review password; history reads are public through Pages. Only `X-Live-Client-IP` supplies the rate/auth IP; Pages replaces it with `CF-Connecting-IP` and forwards at most 1,024 User-Agent characters for deterministic browser/device parsing.

## Configuration and persistence

The [manifest](k8s/live-check.yaml) references an **existing** `live-check-secrets` Secret in `dappgo-hackathon`; it contains no Secret resource or values. Have the host's secret-management workflow provision these keys before rollout:

| Key | Where used |
| --- | --- |
| `BASETEN_API_KEY` | Python only; Baseten verifier, `meta-models/muse-spark-open-1026` (default); omit to disable this provider |
| `FIREWORKS_API_KEY` | Python only; Fireworks verifier, `accounts/fireworks/models/muse-spark-open`; omit to disable this provider |
| `META_MODEL_API_KEY` | Python only; Meta verifier, `muse-spark-1.3`, and all example OCR/ASR; omit to disable this provider and live image/audio/video preprocessing |
| `LIVE_CHECK_PASSWORD` | Python only; missing/empty disables checks with 503 |
| `LIVE_ORIGIN_TOKEN` | Python and Pages; required, identical strong random value |
| `LIVE_ACCESS_CLIENT_ID` / `LIVE_ACCESS_CLIENT_SECRET` | Pages only, from the Access service token; do not add to the pod |

The Python process also accepts `BASETEN_API_KEY_FILE`, `FIREWORKS_API_KEY_FILE`, `META_MODEL_API_KEY_FILE`, `LIVE_CHECK_PASSWORD_FILE`, and `LIVE_ORIGIN_TOKEN_FILE`. An explicitly set environment value wins, including an empty password; files have trailing line endings removed. A configured unreadable secret file prevents startup. The checked-in manifest has explicit placeholders for all six provider caps and the two global ceilings; fill them before rollout. Runtime paths default to `LIVE_DATA_DIR=/data` and `LIVE_EXAMPLES_DIR=/app/examples`. Provider keys are independent: Fireworks and Meta checks do not require a Baseten key. Model IDs and provider endpoints are fixed by the existing adapters; request bodies cannot override them.

The Docker image copies committed `docs/examples/` into **`/app/examples`** and installs FFmpeg/ffprobe for the existing decoder. That directory is read-only at runtime; no download or upload endpoint populates it. The packaged manifest's hashes and the site's hashes must agree. Prepare narration/video on the host before building a release image; currently both have clearly named `.pending.txt` placeholders. [Exact preparation and one-run recording commands](../docs/LIVE_CHECK.md#examples). IDs may be `a-text` through `c-video` (three stories × five formats); the original unprefixed IDs remain valid for story A. Only ready, hash-matching manifest entries run. Meta preprocessing charges Meta; each verifier charges its selected provider. Provider-credit stops are independent. Pages receives no provider key.

Run **replicas=1, strategy=Recreate, one Python process**. Do not use multiple workers, an HPA, or another copy of this service with a separate ledger. Each gate read/check/write and prune holds one process-wide asyncio lock and a SQLite `BEGIN IMMEDIATE` transaction, with WAL and `synchronous=FULL`. The 1 GiB PVC stores `/data/ledger.sqlite3` plus its WAL files and public SEC JSON cache. The same SQLite file holds authenticated run history and its private IP-hash salt. Preserve this PVC through upgrades and rollback. Never delete, reinitialize, rename, or restore an older ledger to make spending room. For backups, stop the pod or use SQLite's backup API; copying a live `.sqlite3` file alone can omit committed WAL writes. A k3s local-path PVC is tied to its node; moving nodes requires preserving that storage.

Pruning runs every 60 seconds and on gate transitions. Expired auth/rate/day/hold rows may disappear; lifetime spending and provider/lifetime stops never expire. History retains at most 5,000 rows for 14 days; inserts and the existing periodic prune enforce this bound, and expired rows are immediately hidden from reads. `BUDGET_RESET_ID` is deliberately ignored by this adapter. Restarting, changing caps, and deploying another image cannot clear a latched stop. Budget snapshots expose public provider daily/lifetime counters, compatibility sums and the separate global guard counters.

Authenticated, validated attempts (including failures and compare members) store public result envelopes of at most 64 KiB, input text of at most 600 characters, masked IP and parsed device/browser families. History is publicly readable without the review password. Passwords, raw IP/User-Agent, raw provider bodies, private reasoning and secrets are not stored in history or application logs. The SEC disk cache contains public JSON bodies only, valid for six hours. [Exact API and retained-row shapes](../docs/LIVE_CHECK.md#provider-receipts-compare-and-history).

All outbound calls disallow redirects. SEC/verifier calls have a 22-second deadline. The text request/runner deadline is 28 seconds; Pages aborts at 25 seconds. Examples have a 60-second total deadline, individual Meta preprocessing I/O allows 50 seconds, and Pages allows 65 seconds including body consumption. Compare runs 2–3 providers sequentially, checks the budget before every member, and labels/skips members whose provider budget or credit is exhausted, and stops the sequence on rate exhaustion. Pages allows 195 seconds for compare; aiohttp also allows 195 seconds to drain active requests during shutdown, within the pod's 200-second termination grace. Each provider has separate daily/lifetime caps; the global caps additionally bound aggregate spending. Reservations remain charged if a response is lost.

## Setting provider caps

Set all of the following in the deployment before rolling the image. The defaults are development safeguards, not the real provider balances:

| Provider | Daily environment variable | Lifetime environment variable | Code defaults (USD) |
| --- | --- | --- | --- |
| Meta Model API | `META_DAILY_BUDGET_USD` | `META_LIFETIME_BUDGET_USD` | 30 / 20 |
| Baseten | `BASETEN_DAILY_BUDGET_USD` | `BASETEN_LIFETIME_BUDGET_USD` | 30 / 20 |
| Fireworks | `FIREWORKS_DAILY_BUDGET_USD` | `FIREWORKS_LIFETIME_BUDGET_USD` | 30 / 20 |

The lifetime cap is an **absolute ledger ceiling**, not a fresh allowance on deployment. Inspect each provider's recorded lifetime spend and reconcile it with all other recorded account spend (including offline experiments and failed/partial paid calls). A safe cap is no more than the live ledger's charged lifetime total **plus the credits still available to that provider account**, minus any room needed for other consumers. Do not add original promotional credits again or subtract previous charges twice. The operator supplies the real values; this change makes no account-balance claims and performs no rollout.

V1 ledger totals were aggregate and holds had no provider IDs. On first upgrade, the transaction conservatively carries that unattributed lifetime/day spend and stop flags into **every** provider; it keeps the original aggregate and existing history rows. This avoids reopening spend when a historical split cannot be proved. `provider_migration` retains the carried amount privately in SQLite. Read the migrated snapshot before permitting paid traffic, then derive caps using those charged totals and independently audited remaining credits. Do not estimate a lifetime split from the 14-day public history, reset totals, or restore an older ledger. Increasing caps cannot clear a latched lifetime/credit stop. Any rollback image must understand the provider ledger schema and enforce the same caps; the former aggregate-only image cannot provide that protection.

Keep `DAILY_BUDGET_USD` and `TOTAL_BUDGET_USD` as additional aggregate ceilings (code defaults $3/day and $20 lifetime). Set them deliberately: use the sum of the approved provider caps if no stricter shared ceiling is wanted. A zero provider cap disables that provider; a zero global ceiling disables all. Negative, invalid and nonfinite values fail closed. A lifetime cap of zero also latches its permanent lifetime stop; set real caps before the first budget read. Fill the eight placeholders in [the manifest](k8s/live-check.yaml) with quoted decimal USD values and retain the same PVC.

After rollout, use the budget-only command below and check `providers.{meta,baseten,fireworks}` against the approved limits and recorded lifetime totals, plus `global`. Top-level `*_usd` fields are provider sums for one-release compatibility, not additional spending room. Check the bilingual chooser and switching between providers without a paid run. The operator sets caps and rolls the immutable image.

## Host operator commands

Use a checkout of the reviewed commit on the x86_64 host with Docker, k3s and kubectl configured. These commands build/import locally; they do not push an image. If the cluster has several eligible amd64 nodes, import the same image on each eligible node before applying, or constrain scheduling to the node that holds the PVC/image.

```sh
LIVE_VERSION=$(git rev-parse HEAD)
docker build --platform linux/amd64 -f server/live/Dockerfile -t "live-check:${LIVE_VERSION}" .
docker save "live-check:${LIVE_VERSION}" -o "/tmp/live-check-${LIVE_VERSION}.tar"
sudo k3s ctr images import "/tmp/live-check-${LIVE_VERSION}.tar"
kubectl create namespace dappgo-hackathon --dry-run=client -o yaml | kubectl apply -f -
```

Provision `live-check-secrets` through the operator's secret manager, then verify its name without printing values and apply the image-pinned manifest:

```sh
kubectl -n dappgo-hackathon get secret live-check-secrets -o name
sed "s/live-check:REPLACE_WITH_COMMIT/live-check:${LIVE_VERSION}/" deploy/k8s/live-check.yaml > "/tmp/live-check-${LIVE_VERSION}.yaml"
kubectl apply -f "/tmp/live-check-${LIVE_VERSION}.yaml"
kubectl -n dappgo-hackathon rollout status deployment/live-check --timeout=300s
kubectl -n dappgo-hackathon get pods,pvc,service -l app=live-check
kubectl -n dappgo-hackathon get pvc live-check-data
```

The manifest's readiness/liveness **exec probes** call the authenticated `/healthz` using the pod's environment token, never a literal secret in YAML. The container runs as UID/GID 10001, drops all capabilities, and has a read-only root filesystem; only `/data` and a small `/tmp` volume are writable. To read the aggregate through the pod without a model or SEC call:

```sh
kubectl -n dappgo-hackathon exec deployment/live-check -- python -c 'import os,urllib.request; r=urllib.request.Request("http://127.0.0.1:8080/api/budget",headers={"X-Live-Origin-Token":os.environ["LIVE_ORIGIN_TOKEN"]}); print(urllib.request.urlopen(r,timeout=3).read().decode())'
```

## Tunnel and Access

Choose `LIVE_ORIGIN_HOST` as a dedicated hostname, for example `live-origin.example.com`. In Zero Trust, create a self-hosted Access application covering the **entire hostname**, including `/healthz`. Add a **Service Auth** policy whose Include rule selects only the Pages service token. Do not add an anonymous Bypass or browser Allow policy. Supply the service token's Client ID/Secret to Pages. Access expects the two `CF-Access-Client-Id` / `CF-Access-Client-Secret` headers; see [Cloudflare's service-token instructions](https://developers.cloudflare.com/cloudflare-one/access-controls/service-credentials/service-tokens/).

For an existing **in-cluster cloudflared** connector, add this ingress rule before its catch-all. Replace the literal `LIVE_ORIGIN_HOST` placeholder with the chosen hostname. Keep existing tunnel identity, credentials, other routes and final catch-all intact:

```yaml
ingress:
  - hostname: LIVE_ORIGIN_HOST
    service: http://live-check.dappgo-hackathon.svc.cluster.local:8080
  # Preserve the connector's other existing rules here.
  - service: http_status:404
```

The ClusterIP is private; no Ingress, NodePort or LoadBalancer is created. The connector must resolve Kubernetes service DNS and reach this service. For a locally managed tunnel, validate its existing config, route the hostname, and reload its existing connector through the host's normal process:

```sh
# Set these nonsecret variables to the operator's existing tunnel/config.
cloudflared tunnel --config "$TUNNEL_CONFIG" ingress validate
cloudflared tunnel route dns "$TUNNEL_ID" "$LIVE_ORIGIN_HOST"
```

For a remotely managed tunnel, add the equivalent published application route in its dashboard and let the existing connector receive the change. Ensure Access protects the hostname **before** publishing its DNS route. [Cloudflare ingress configuration](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/local-management/configuration-file/).

## Pages configuration and publish

Keep project `market-claim-verifier` and the existing `docs` build output/copy step, including `docs/_headers`, `_redirects`, `_routes.json`, `data/examples/` and **`examples/`** (copy `docs/examples/` alongside the site's other root assets). The route list includes `/api/check`, `/api/check-example`, `/api/compare`, `/api/history`, `/api/history/*` and `/api/budget`. The repository-root Functions remain the proxy. The root [wrangler.toml](../wrangler.toml) has no `[[services]]` binding. Pages never receives `BASETEN_API_KEY`, `FIREWORKS_API_KEY`, `META_MODEL_API_KEY` or the configured review password.

In the Pages project's production environment, set `LIVE_ORIGIN_HOST` to the hostname **without** scheme, slash, port or path. Supply the three credentials as secrets. The following commands use interactive prompts; enter values there, never in shell arguments or committed files. A hostname may also be stored as a secret with the same binding name:

```sh
wrangler pages secret put LIVE_ORIGIN_HOST --project-name market-claim-verifier
wrangler pages secret put LIVE_ACCESS_CLIENT_ID --project-name market-claim-verifier
wrangler pages secret put LIVE_ACCESS_CLIENT_SECRET --project-name market-claim-verifier
wrangler pages secret put LIVE_ORIGIN_TOKEN --project-name market-claim-verifier
```

Apply the same configuration only to previews explicitly intended to share the **same** backend and spending caps; otherwise leave preview credentials unset. Remove any old `LIVE_CHECK` service binding and leave `LIVE_CHECK_MOCK` unset in production. Redeploy through the existing Pages build/publish workflow after changing bindings. [Pages environment/secret bindings](https://developers.cloudflare.com/pages/functions/bindings/).

Verify `/api/budget` through Pages first: it uses no model or SEC requests. With Access missing/bad configuration, the proxy returns 503 plus `demo: "data/live-demo.json"`. With configuration correct, it returns the three provider daily/lifetime meters, compatibility sums and the global guard. Visiting the tunnel hostname without service credentials should be denied by Access; requests that bypass Access but lack the origin token must still fail. Any fresh paid model smoke check requires a separate operator decision; no paid check is part of this handoff.

## Tail real request logs

After the owner deploys this image, SSH to cp-1 and follow the real process output:

```sh
ssh dappgo-ha-cp-1
sudo k3s kubectl -n dappgo-hackathon logs -f deployment/live-check
```

Each INFO line starts with `live id=<request_id> +<elapsed>s event=<name>`, followed by
safe `key=value` summaries. The response envelope carries the same `request_id`; each compare
member has its own ID. Start, model, tool-call/result, program-check and verdict/error events
contain no secrets, IP addresses, raw input or private model reasoning. A final verdict includes
claim count, cost and whether any cost remains a reservation. Logging does not change gate
transitions, ledger settlement, history retention or the existing public input/history policy.

For host-side JSONL capture alongside the video recorder, use
[`scripts/tail_live_log.py`](../scripts/tail_live_log.py) with `DAPPGO_HA_SUDO_FILE` pointing
to a private password file. It sends the password to `sudo -S` over SSH stdin, retains every
live line in a separate spool, and supports a response ID learned after the verdict.
[Exact capture commands and the two on-screen labels](../docs/REAL_TRACES.md).

## Rollback and optional Worker

Rollback by importing/reapplying the previous immutable image tag against the **same PVC**, still one replica with Recreate. Preserve current lifetime/credit stops; never restore an earlier ledger. Rotating Kubernetes secrets requires `kubectl -n dappgo-hackathon rollout restart deployment/live-check`; rotate the matching Pages origin token and redeploy Pages together.

The [Cloudflare adapter](../workers/live/src/entry.py) and its [configuration](../workers/live/wrangler.toml) remain as an **optional Workers Paid path** for a future explicit plan change. They are not used by this Pages proxy. Reusing that path would require a separately reviewed Pages binding change and preserving all previously retained spending; do not run both backends with independent allowances. See [live-check behavior](../docs/LIVE_CHECK.md) and the [local validation receipt](../docs/evidence/live-selfhost-2026-11-03/REPORT.md).
