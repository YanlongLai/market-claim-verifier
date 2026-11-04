# Public live-check budget and durable stops — 2026-11-02

Follow-up to commit `7bf3272c16be1d4bcc350241d71b84f7d19e1ab4`. This is offline implementation validation, not a deployed endpoint or a fresh model evaluation. No Baseten calls, SEC requests, paid execution, credentials, push or deployment are part of this work.

The [input record](inputs.json) freezes the parent implementation hashes, $3 daily / $20 lifetime configuration and test cases. Existing saved evaluations and all earlier live-check records remain unchanged. The first [focused run](focused-01.log) passed 68 tests; the [completed focused run](focused-02.log) passed 70 after adding default lifetime-cap and admin-reset cases. [Preparation notes](preparation-01.log) retain the failed system-Python adapter import and its locked-environment recovery.

Implementation and Cloudflare setup are in [LIVE_CHECK.md](../../LIVE_CHECK.md). Budget and provider tests use offline transport doubles and SQLite; the original Apple checks reuse frozen responses and SEC fixtures. No OCR/ASR or fresh model quality is retested.

## Verification

`UV_OFFLINE=1 sh scripts/verify.sh` [passed](verification-01.log): **1,001 product tests, 149 demo tests and 55 standalone Node tests**. Figure input checks, regeneration and rechecks passed. The explorer, site JSON and build summary reproduced all three committed outputs byte for byte. Local Markdown links/anchors passed. The verifier stripped provider credentials and installed Python/Node network guards; no model or SEC request occurred.

Focused tests cover public remaining amounts before/after reconciliation, UTC midnight and late settlement, default $20 lifetime accounting across pruned days, invalid configurations, refusal before model I/O, and 50 simultaneous reservations against the actual synchronous SQLite adapter for each cap. Mocked 402 and quota-worded 403/429 persist a provider pause through an alarm and object restart; normal authentication/rate errors remain distinct. An admin deployment reset is consumed once, preserves pending holds and daily spend, and cannot be supplied through public request data. Browser-script tests exercise English/Chinese at 390/768/1440 widths, progress values, the exact $0.10 threshold, daily/lifetime/provider stops, disabled inputs, midnight refresh and unavailable budget reads. These DOM geometry checks do not measure browser fonts or approve rendered appearance.

## Visual scope and limitation

This changes one component in the existing paper/ink/green design: the subject-specific element is the public $3 allowance beside the live SEC-check form. No new direction, imagery, fonts or palette were introduced. [Source lint](design-lint.log) reports **0 failures / 3 warnings**: the existing textarea outline is an input affordance; zero-padding formats trace elapsed time; dashes occur in existing numeric/trace placeholders and the owner's required exhausted-budget wording. These do not justify redesigning the surrounding page.

The [real-browser inspector](design-inspect.log) could not launch Chrome. The [fallback record](browser-limit.txt) retains the unavailable browser host and rejected native Chrome access. No browser screenshot, visual score or browser inspection pass is claimed. The new component still needs an owner visual check in both color schemes after import/deployment. Offline DOM behavior and all repository verification gates passed.

## Local commit handoff

The original worktree's Git metadata points outside its writable sandbox; importing the existing live-check bundle failed with `FETCH_HEAD: Operation not permitted`. The existing bundle was imported into a temporary local clone instead, and every unchanged parent file was compared with the working copy before this follow-up. The new local commit is a direct child of `7bf3272`, with the same requested coauthor footer. A separate `live-check-budget.bundle` carries both live-check commits relative to the worktree's original `f71d03a` head for owner/Claude import. The original bundle remains intact. No root-worktree branch update, push or deploy is claimed.
