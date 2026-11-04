# Live evidence binding integration repair

This is an offline regression on a previously observed production failure, not a new accuracy benchmark, model execution or OCR/ASR test. No model calls, SEC fetches or paid attempts were made for this repair. The original session and unsuccessful baseline verification remain retained.

## Frozen input and result

The [session fixture](../../../tests/fixtures/live-determinism/session-20261104T021100641318Z.json) was supplied from the video's `demo/cache/live-takes/v4/` directory. Its [provenance and SHA-256](../../../tests/fixtures/live-determinism/README.md) are checked by the regression tests. The public envelope records Baseten `meta-models/muse-spark-open-1026`, an original estimated cost of $0.02961845 and 23,496.586 ms latency. These remain historical observations.

The Apple value check cites both `E6` (AAPL/revenue/FY2025Q4, $102,466,000,000) and `E7` (AAPL/revenue/FY2025, $416,161,000,000). The old result has `actual_value: null`, reason `ambiguous_evidence`, claim verdict `unchecked` and overall verdict `insufficient_evidence`. The public capture contains checks rather than the model's raw final JSON; tests reconstruct proposals using those checks and the original number literals.

## Binding and request policy

For a numeric value claim with no usable binding, complete ticker/metric/period fields select an exact matching fact. Reports without those fields use the lookup arguments joined by evidence ID, filtered by the atomic claim's exact issuer, metric and explicit fiscal/calendar period when available; a remaining missing metric or period requires one candidate for the named ticker. No value similarity, lookup order or model-found number selects the fact.

Exactly one candidate is bound and sent through the existing numeric checker and correction builder. Zero or multiple candidates stay `unchecked` with reason `ambiguous_evidence`. Unknown/failed citations, opinions, change/history claims and explicit period interpretations retain their existing handling. Program binding events retain the source, matching fields, candidates and previous/selected evidence IDs in live envelopes and CLI traces.

Every verifier request in live and compare, including continuation and repair turns on Baseten, Fireworks and Meta, sends `temperature: 0` and `top_p: 1`. The 6,000-token live output limit is unchanged. These settings do not promise identical model responses across executions or providers.

## Recheck and integration findings

The frozen session now yields `contradicted`, binds only `E6` for Apple and produces the single `$416.2 billion` → `$102.5 billion` edit. The other three checked financial assertions remain supported and the opinion stays unchecked. Missing bindings and the original ambiguous pair are both tested; zero/two matching facts, mismatched issuer/metric/period, tool/result disagreement and unqualified periods cannot produce a binding.

The branch already imported `MAX_OUTPUT` in the hold test and stubbed 55 seconds in the server timeout test. W1's execution wrapper still used 28 seconds, outside the scope of that stub, so the provider's 22-second timeout returned 503. The execution wrapper now uses 55 seconds, preserving the pending reservation in its 504 envelope. The UI regression checks read text → receipt → verdict → corrected draft → SEC evidence → agent trace, including localized step counts, safe hostile text and collapse only when an edit exists.

Moving the site receipt before its verdict changed the site script hash. Two generated demo records, `hover-source.js` and `preview-data.js`, were refreshed with the offline compiler; each changed only its site-script provenance hash. Host data, timing, keyframes, beats and cues were checked unchanged, including optional outputs that are absent. No voice, browser or media output was generated.

## Validation records

- [Baseline full verifier](01-baseline-verify.log): 7 failed, 1,339 passed; one timeout regression and six localized trace-title regressions. The hold test passed at baseline.
- [Initial targeted run](02-targeted.log): 213 passed, with Python/Node network guards and provider credentials removed.
- [Expanded targeted run](03-targeted.log): 215 passed, adding missing fact metadata and bare-year scope cases under the same guards.
- [First full offline verifier after the repair](04-verify.log): all 1,367 product tests passed; 3 demo checks failed and 203 passed because the two generated demo records still referenced the previous site-script hash.
- [First demo refresh attempt](05-demo-refresh.log): the preservation guard stopped on an absent optional `beats.json` before changing any files; the following focused run retained the same 3 failures and 58 passes. The guard was corrected to preserve both existing files and absent optional outputs.
- [Demo provenance refresh and focused regressions](06-demo-refresh.log): only the two provenance hashes changed, all host outputs remained unchanged, and 61 tests passed with network access blocked.
- [Final full offline verifier](07-verify.log): `bash scripts/verify.sh` passed: 1,367 product tests, 206 demo tests, standalone Node tests, figure rebuild/check, byte-identical saved examples and data, Markdown links and network/credential guards. Complete stdout/stderr retained.

The targeted command ran `tests/test_live_determinism.py`, `tests/test_live_check.py`, `tests/test_live_server.py`, `tests/test_live_providers_history.py`, `tests/test_site_examples_runtime.py`, `tests/test_checks.py`, `tests/test_eval_fixes.py` and `tests/test_agent.py` in a temporary locked environment. Its launcher reused the Python/Node guards from [the verification runner](../../../scripts/verify.py). The full verifier independently installs locked dependencies, removes credentials, enforces its network guards and rebuilds data in a disposable copy.

## Delivery

`live-determinism.bundle` carries the fix commit on `refs/heads/feat/try-v3`, with prerequisite commit `bd1fe548e95cf7da61d709098983b736d4c1f998`. The worktree's Git metadata is outside the writable workspace, so the commit and bundle are created in a temporary shared clone. The commit includes the requested `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` footer. The original worktree keeps the changes for review; its pre-existing `w1-server.bundle` is excluded.
