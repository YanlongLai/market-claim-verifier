# Self-hosted live-check adapter — local validation

Date: 2026-11-03. Scope: adapter and deployment artifacts only, on `site/live-check-trace` after main was merged. **Not deployed.** No real Baseten/SEC requests, Cloudflare changes, secret provisioning or push. No quality/accuracy or OCR/ASR claim is made.

The [Python adapter](../../../server/live/server.py) directly imports the unchanged Worker [gate](../../../workers/live/src/gate.py), [runner](../../../workers/live/src/live.py) and claimcheck core. One locked SQLite transaction protects each transition/prune; WAL and FULL synchronous writes retain lifetime totals/stops across restarts. Pages uses Access service-token headers plus a separate origin token, a 25-second abort, redirect rejection and allowlisted responses. [Operator handoff](../../../deploy/README.md).

## Retained attempts

| Record | Result |
| --- | --- |
| [01 focused tests](01-focused.log) | 126 passed, 1 failed: merged core now probes an L4 release fallback absent from old companyfacts-only replay records; fake transport rejected it, without network access |
| [02 focused tests](02-focused.log) | 127 passed after explicitly modelling unavailable historical release evidence in that replay test; no product/core/recorded evidence change |
| [03 Docker build](03-docker-build.log) | Failed because default Buildx activity metadata is outside the writable workspace |
| [04 Docker build](04-docker-build.log) | Successful Linux amd64 build using a temporary `BUILDX_CONFIG`; pinned/hash-checked dependencies on `python:3.12-slim` |
| [05 container smoke](05-container-smoke.log) | Python 3.12, UID 10001, read-only root, network disabled, authenticated health/budget, disabled checks, body ceiling, unknown route, silent application logs and SQLite creation |
| [06 Pages boundary](06-pages.log) | 9 passed; headers, visitor-header stripping, mock/validation, no secret echo, origin failure fallback, abort during fetch/body, partial error traces |
| [07 manifest](07-manifest.log) | Local YAML syntax/resource/probe checks; no cluster connection or admission check |
| [08 full verifier](08-verify.log) | 1,137 product tests passed; demo suite 197 passed / 1 failed on a stale merged preview source hash |
| [09 final focused tests](09-focused-final.log) | 127 passed, including distinct origin-auth errors so Pages can return a 503 configuration fallback while retaining review-password 401s |
| [10 final Pages tests](10-pages-final.log) | 9 passed, including JSON/HTML Access denials and origin-token denials |
| [11 final Docker image](11-docker-build-final.log) | Linux amd64 build passed; local image `live-check:selfhost-local`, image ID `sha256:9b91995bc26124c9316e653a59653c1cb33842d7beb58ddbd69f78f706708c0c` |
| [12 preview refresh](12-demo-preview-refresh.log) | `demo/motion_v3.py --preview-only` changed one current-source SHA-256 line; no narration, timing, media, host outputs or recorded result changed |
| [13 final container smoke](13-container-smoke-final.log) | Read-only, network-disabled Python 3.12 image smoke passed; [reusable script](container-smoke.py) |
| [14 final full verifier](14-verify-final.log) | `bash scripts/verify.sh` passed: 1,137 product tests, 198 demo Python tests, 97 standalone demo Node tests; figures rebuild/check, three byte-identical explorer/site outputs, byte-identical wild output, links and credential/network guards |

Focused invocation: `python -m pytest -q tests/test_live_server.py tests/test_live_check.py tests/test_live_budget.py tests/test_live_password.py tests/test_live_password_edges.py tests/test_site_live_runtime.py`. Server tests use fake HTTPX transports, aiohttp request objects without sockets, frozen Apple/SEC responses and temporary SQLite. They cover budget arithmetic, $3/day and $20 lifetime stops, parallel reservations, restart persistence, rollback, 402 unreadable bodies, credit/error classification, missing/wrong credentials, origin authentication, IP trust, body validation, SEC allowlist/cache/redirects, file/env configuration and timeout holds.

All test attempts are retained; no paid retry was made. Docker smoke networking was disabled and no provider key/review password was supplied. Kubernetes scheduling/storage, Tunnel/Access policy and Pages production configuration remain operator verification tasks.

[Source SHA-256 hashes](source-sha256.json) cover changed implementation/deployment/test inputs plus the unchanged gate, runner and claimcheck modules. Final whitespace and local link checks also pass. Package installation/build downloads are separate from the verifier's network-disabled test/build phase.

To repeat the container smoke after the build:

```sh
docker run --rm -i --platform linux/amd64 --read-only --network none --tmpfs /data:uid=10001,gid=10001,size=64m --tmpfs /tmp:uid=10001,gid=10001,size=16m -e LIVE_ORIGIN_TOKEN=offline-container-token --entrypoint python live-check:selfhost-local - < docs/evidence/live-selfhost-2026-11-03/container-smoke.py
```

The four pre-existing `live-check-*.bundle` files are owner artifacts and remain untouched. Git metadata for this worktree is outside the writable roots; delivery uses a temporary local repository with the same parent commit and a verified incremental `live-selfhost.bundle` exporting `refs/heads/site/live-check-trace`. It requires parent `d00e890f24cea3d26c2e0377a776d975b2d92be0`. The commit has the requested co-author footer. No remote is contacted for delivery.
