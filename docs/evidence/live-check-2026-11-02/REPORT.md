# Live check implementation verification

2026-11-02, branch `site/live-check-trace`. No push, deployment, Cloudflare secret access, paid model call, or live SEC fetch was performed. The [implementation and handoff](../../LIVE_CHECK.md) describe the optional production setup.

This work reuses the original Apple R06 Baseten responses and the committed SEC fixtures. Its 357-transcript recheck tests program identity; it is not a new held-out evaluation or OCR/ASR retest. Original evaluation files, failures, prompt files and numbers are unchanged.

## Final validation

[`UV_OFFLINE=1 sh scripts/verify.sh`](verification-final.log) **passed** with 962 product/replay/provider/site tests, 149 demo tests and 55 standalone Node tests. It also rebuilt/checked figures, reproduced all three explorer/site/build-summary outputs byte for byte, and passed Markdown links/anchors with network guards active. The full verifier needed no key, live SEC data, Wrangler or npm install.

[Focused tests](focused-tests.log) include source identity, all 357 v2 Baseten tool transcripts, real Apple raw-response replay, three outcomes, missing-period abstention, failed-call accounting, concurrent reservations, idempotent settlement, integer money, cross-midnight rate windows, safe DOM rendering, both languages, and the Pages boundary. [Input/source hashes](inputs.json) identify the implementation, reused trace and SEC fixtures. These tests compare the live finish path to the same Python CLI checker; they do not port or substitute verdict logic.

[The Python Worker dry run](worker-dry-run.log) bundled successfully with Wrangler 4.156.2; the final Pages Function bundle also compiled successfully. No deployment occurred. Local `wrangler pages dev` returned HTTP 200 / `mode=mock` for the exact saved Apple input, with `Cache-Control: no-store`.

[The isolated Python/WASM smoke](worker-smoke.json) used the production runner and real SQLite Durable Object, replacing **only** model and SEC transports with recorded responses/fixtures. It returned `supported`, seven public trace events and replayed usage cost $0.01221725. **New paid cost: $0.** A missing-period sentence returned `insufficient_evidence` with zero model cost. Five requests from one test IP succeeded; the sixth returned 429 / `rate_limited`. Setting the isolated Worker's budget to zero returned 429 / `budget_exhausted` before model transport. The smoke JSON wraps the normal `mode=live` service response in an explicit `offline_runtime_replay` label; it is not a fresh live-model run.

The frontend skill's source lint passed with zero failures/warnings. DOM/runtime checks cover phone/tablet/desktop widths and English/Traditional Chinese; the new form/trace has no animation and uses the existing light/dark variables. **Real-browser screenshots and visual approval were not completed:** the inspector's Chrome process exited in the sandbox, browser-host access was unavailable, and native computer-use access to Google Chrome was denied. Claude/owner should do the browser checks in the deployment handoff. Production model latency, SEC egress and cold-start behavior remain unmeasured; the 30-second target is bounded by timeout behavior, not a production SLA claim.

## Retained failures and partial checks

All attempts below were offline or local; none used paid model calls. Historical console logs are retained where captured, with local home paths redacted and terminal coloring/trailing whitespace removed. The early unit/runtime failures are summarized from their actual tool output; no missing historical console transcript has been invented.

| Attempt | Observed result and resolution |
| --- | --- |
| Initial scene runtime check | Existing harness ran the newly added `setupLive` outside its substituted boot block and failed with `fetch is not defined`. Updated the harness boot boundary; all 290 scene/asset checks subsequently passed |
| Initial raw-response unit replay | Fixture adapter looked for `CIK0000320193.json` instead of the committed `companyfacts-CIK0000320193.json`. Corrected only the adapter path; recorded fixtures were unchanged |
| [Full verifier 1](verification-01-nav-failed.log) | 959 passed, 1 failed: the pre-live section/navigation order assertion. Updated the expected order for the new live section |
| [Full verifier 2](verification-02-demo-hash-failed.log) | Product suite passed (961 tests at that stage); demo suite had 147 passed, 2 failed because its generated hover adapter recorded the old whole-site script hash. Regenerated only that adapter: its code is unchanged; one hash-comment line changed. Narration, host timing, data, media and original evidence remain untouched |
| [Interrupted setup/run](verification-03-interrupted.log) | Refresh attempted with the product environment, which lacks demo-only PyYAML; interrupted the just-started verifier, then used the locked demo environment to regenerate the adapter |
| Local Cloudflare toolchain setup | Initial launch used the root Pages config, then encountered an older uv version, restricted home cache/registry/log directories and watcher limits. Used temporary tool/cache/registry paths, the pinned toolchain with uv 0.13.7, and polling. No system tool upgrade or account change |
| Initial WASM smoke fixture | JSON files were not bundled as runtime assets. Bundled test fixtures as a Python module in the isolated temporary smoke Worker; production transport code was unchanged |
| Browser inspection | Chrome launch/access blocked as described above. Source lint and DOM tests passed; no visual sign-off claimed |

The final [verification log](verification-final.log) contains all five expected PASS lines. The local worktree's Git index is outside the writable sandbox (`index.lock`: operation not permitted), so the authorized commit is delivered as a Git bundle built in a temporary local repository. Its commit includes the requested `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` footer. No push or deployment was attempted.
