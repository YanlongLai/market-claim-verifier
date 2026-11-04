# Provider budgets — offline implementation record

This change adds independent daily and lifetime spend gates for Baseten, Fireworks and Meta Model API, while retaining the original aggregate counter as an additional sum guard. No provider account balance was queried and no paid model, OCR/ASR, synthesis or live SEC call was made. Tests replay committed responses and use synthetic usage through fake transports. This is regression evidence, not a new accuracy or media-extraction evaluation. The operator supplies real cap values and rolls the image.

## Accounting and migration

Every new paid reservation binds its billing provider. Verifier calls charge the chosen provider; OCR/ASR charges Meta. Both provider and aggregate checks succeed before any reservation is committed. Reconciliation updates the original UTC day and lifetime counters, rejects cross-provider settlement, and retains missing-usage holds. A provider daily shortfall pauses that provider until UTC midnight without changing actual spend. Lifetime and credit stops persist; compare retains an exhausted member's error envelope and continues to later providers. The shared IP rate stop still ends a comparison.

V1 stored only aggregate totals and untagged holds. An exact historical provider split cannot be recovered from its expiring public history. Migration conservatively carries legacy spend and stop flags against **every** provider, keeps the original aggregate unchanged, retains existing history rows, and records its carryover privately in `provider_migration`. Legacy hold refunds reconcile each inherited copy once. New spending is attributed to one provider. This can stop a provider early; it must not be described as audited historical provider spend. [Operator cap calculation and migration](../../../deploy/README.md#setting-provider-caps).

The API exposes each provider's daily/lifetime counters and status, a separate `global` guard, and provider sums in the old top-level `*_usd` fields for one release. Pages allowlists these nested fields on budget reads and failure envelopes, drops private fields, and permits compare to continue after an exhausted member. The English and Traditional Chinese chooser show three meters; available providers and compare remain runnable while another provider is paused. Media inputs also need Meta preprocessing budget.

## Validation and retained attempts

The [source hashes](source-hashes.json) identify the final changed implementation, configuration and test inputs against base `165c0620`. They do not reconstruct intermediate source states. [Run metadata](runs.json) records commands, outcomes and checksums of the compressed complete stdout/stderr logs. Failed attempts remain available alongside passing attempts. The [initial summary](initial-run-summary.json) retains the first tool-transcript counts; its full stdout was not saved, and no full historical console log is claimed.

The focused server suite passed **153 tests**. The combined provider, budget, site and language suite passed **199 tests**. Pages boundary tests passed **26 tests**. After refreshing two generated source-checksum lines, the demo suite passed **206 tests**. The refresh changes only `demo/motion/v3/hover-source.js`'s source checksum and `preview-data.js`'s site provenance checksum. The hover implementation body is byte-identical; measured host timing, narration, media and paid records remain untouched.

The broad runs caught and corrected an HTTP-status variable shadow, missing handling for historical pages without a live chooser, a test that accidentally tried verify's nonexistent credential-file guard, stale asset cache stamps, and stale offline demo provenance. Other failed assertions reflected the replaced shared-budget contract, an object-identity comparison in a new test, or README length. The saved logs distinguish those failures from later passing checks.

**Final verification passed:** [complete verifier log](verify-05.log.gz): **1,525 product Python tests, 206 demo Python tests and 97 standalone Node tests**. The final lines confirm both suites, byte-identical data rebuilds, figure rebuild/checks, Markdown links and network/credential guards. The run metadata retains all earlier failures. Both Python suites, standalone Node tests, figure checks/rebuild, byte-identical data rebuilds, Markdown links and offline guards use `bash scripts/verify.sh`. No paid smoke check or deployment is part of this record.

## Visual review limit

The design-taste-frontend source lint returned **0 failures and 2 warnings** on the existing page. The automated screenshot inspector could not launch Chrome (`Chrome exited early, code null`). The browser access host was unavailable, and a computer-use request was rejected with “Computer Use was not approved to use Google Chrome.” No screenshots or real-browser visual approval are claimed. Shipped JavaScript runtime checks cover both languages at phone, tablet and desktop dimensions, including independent pauses, switching providers, compare, UTC rollover and unavailable budgets.

## Delivery

The worktree's Git metadata is outside the writable workspace; staging there failed with `index.lock: Operation not permitted`. Commits are created in an isolated temporary Git directory on `feat/provider-budgets` from `165c0620` and packaged in the owner-requested `provider-budgets.bundle`. The original worktree branch ref is unchanged. Import the bundle in a writable checkout; the operator sets the six real provider caps and two aggregate ceilings before rolling the image. [Deployment handoff](../../../deploy/README.md).
