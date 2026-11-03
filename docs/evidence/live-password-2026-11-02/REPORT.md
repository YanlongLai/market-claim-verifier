# Password protection for live checks

Local implementation and offline verification, 2026-11-02. No push, deployment, real credential configuration, model call or SEC fetch was performed.

## Behavior

The private [Worker](../../../workers/live/src/entry.py) authenticates `POST /api/check` through the existing globally named SQLite `SpendGate`, before reading budgets, incrementing the accepted-check rate or creating a `LiveRun`. Missing/empty `LIVE_CHECK_PASSWORD` disables paid checks with 503. Missing/wrong credentials return 401. The [gate](../../../workers/live/src/gate.py) hashes attempted and configured passwords with SHA-256 and compares fixed 32-byte digests with `hmac.compare_digest`. No model/gate helper is exposed on the Worker entrypoint as an RPC method. The [Cloudflare RPC visibility documentation](https://developers.cloudflare.com/workers/runtime-apis/rpc/visibility/) and [Python comparison documentation](https://docs.python.org/3/library/hmac.html#hmac.compare_digest) explain these boundaries.

Five failures per IP within 15 minutes establish a 15-minute lock from the fifth failure. The first five return 401; subsequent attempts, including a correct password, return 429 until expiry. Blocked retries do not extend the lock. Failed attempts do not consume spending or accepted-check counts. Salted IP buckets, counts and expiry/lock timestamps survive a Durable Object restart and are pruned by alarms. Raw IPs, attempted values and password digests are never stored or logged. Successful authentication, password rotation and budget resets preserve unexpired failed-attempt counts.

The bilingual form explains the review password requirement, uses a masked input, and declares POST even without JavaScript. It saves the password to this tab's sessionStorage only after a successful check, restores it on reload, and clears it on 401. Blocked browser storage remains usable. The password stays out of localStorage, URLs, results, provider payloads and public budget requests. The saved demo and aggregate budget remain public. The loopback-only offline replay cannot call Baseten and uses a nonsecret placeholder password.

[Deployment steps](../../LIVE_CHECK.md#exact-handoff-for-claude--owner) now require the `LIVE_CHECK_PASSWORD` Worker secret alongside `BASETEN_API_KEY`, supplied through separate interactive `pywrangler secret put` prompts. No Pages secret, namespace or migration change is needed.

## Validation and retained attempts

[Focused tests](targeted-attempt-2.log): **79 passed**, including the shipped Worker and synchronous SQLite adapter, concurrent lockout/restart/alarm tests, the constant-size digest path, malformed credentials, authentication before budget/model work, original Apple response replay, no password in responses/storage/logs/model payloads, request forwarding, and English/Chinese sessionStorage behavior. [Input/source hashes](inputs.json) identify the final implementation, tests and reused fixtures. These are offline doubles and frozen-response rechecks, not new model evaluations or statistical timing measurements.

[The first focused attempt](targeted-attempt-1.log) retained five failures: one assertion used the wrong response field name; four exposed missing focus/default-value behavior in the DOM test adapter and incorrect repeated initialization in the test. The production response contract was preserved and the tests corrected. Earlier numbered logs are retained unchanged, including the failed full verifier's stale generated hover-source hash. Only that generated adapter's site hash was refreshed; narration, measured timing and media were preserved. The standalone preview-artifact check also reports the already stale host `data.js`/`keyframes.json`; these measured host artifacts are intentionally preserved, as the demo tests require.

`UV_OFFLINE=1 sh scripts/verify.sh` [passed](verification-final.log): **1,032 product tests, 149 demo tests and 55 standalone Node tests**. All five final PASS lines are present: offline Python/Node suites, figure rebuild/check, three byte-identical explorer/site outputs, Markdown links/anchors, and no model calls, SEC fetches or credentials. Tests and rebuilds ran in a disposable copy with network guards. The source tree was preserved.

## Visual review limits

The password field matches the existing paper/ink/green form. [Source lint](design-lint.json) has no failures and four warnings: two input outlines, existing time zero-padding and existing dashes. No redesign was requested. [The browser inspector](design-inspect.log) could not launch Chrome; the [fallback browser inventory](browser-limit.txt) reported an unavailable browser access host. No rendered screenshot or browser visual pass is claimed. Offline DOM behavior is covered in both languages.

## Commit handoff

The source checkout's Git metadata is read-only in this sandbox. Both earlier commits were imported from `live-check-budget.bundle` into a temporary local repository. Before changes, every parent-commit file matched the worktree byte for byte. The password commit is a direct child of `2064bbce5ed12b0c6bbf288359f802a74829e752`, with the requested `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` footer. `live-check-password.bundle` carries the three live-check commits relative to the original checkout head `f71d03aff75b29bf207ddd2ba16854621ab3e959` for Claude/owner import. The original bundles remain intact. No root-checkout branch update, push or deployment is claimed.
