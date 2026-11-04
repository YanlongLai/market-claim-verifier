# Corrected draft — offline implementation validation

2026-11-03. Based on `f54856f6b60477db15ee5a6a680a77d4be6e0ae1`, worktree `feat/corrected-draft`. No model calls, SEC fetches, deployment or push. No new quality/accuracy estimate or OCR/ASR test. The existing gate, budgets, authentication and self-hosted HTTP adapter are unchanged.

The [live runner](../../../workers/live/src/live.py) passes program checks and retained evidence into the pure Python [correction builder](../../../src/claimcheck/correction.py). Pages passes its new `corrections` field, and the English/Traditional Chinese site renders original spans as strike/insert text plus cited changes and explicit reasons for unedited assertions. See the [contract and limits](../../LIVE_CHECK.md#corrected-draft).

## Retained Apple example

Round 2, based on `08953e9f`: the [generated envelope](apple-corrections.json) now reuses the **full four-assertion** [saved post](../posts-2026-10-28/demo-thread-baseten/report.json), all its recorded program checks and their raw traces, including the [Apple trace](../posts-2026-10-28/demo-thread-baseten/traces/20261029T023240Z-12ac28b8.json). The [offline builder](../../../scripts/build_corrected_draft_example.py) preserves the original text and verdicts. It namespaces copies of each claim's local evidence IDs (`C1:E1`, `C2:E1`, `C2:E4`, `C3:E1`) to avoid collisions and represents the report's screened opinion as unchecked; this does not turn screening into a financial verdict. Rebuild with `python3 scripts/build_corrected_draft_example.py`; `--check` checks the committed envelope.

There is **one edit** (Apple), and four `not_corrected` entries: Amazon's revenue check (`supported`), NVIDIA's revenue check (`supported`), NVIDIA's more-than-double check (`supported`), and the valuation opinion (`not_judged`). NVIDIA has two recorded checks, so the four source assertions produce five envelope records. The source contains no insufficient-evidence result; tests separately cover `insufficient_evidence`, with an explicit “not corrected” reason, without changing the saved verdicts.

**Corrected draft — only listed assertions checked**

> Apple pulled in ~~$416.2 billion~~ → **$102.5 billion** of revenue in fiscal Q4 2025 alone.

The saved program value is `102466000000 USD`, `FY2025Q4`, evidence `C3:E1` (originally `E1` in the Apple trace). Its two components are $416.161B annual revenue and $313.695B nine-month revenue. The builder cites both recorded component filings, including when the top-level `filing_url` is empty: [annual component](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/), [nine-month component](https://www.sec.gov/Archives/edgar/data/320193/000032019326000020/). These references come from the historical trace and were not revalidated against current SEC data.

The [site's saved demo](../../site/data/live-demo.json) is a different, single-claim Apple check (fiscal Q3 2026), so its [builder](../../../scripts/build_live_demo.py) adds the envelope for that input: no edits, one `supported` reason. “See a saved check” renders this section without a live call. Both languages place the explicit scope sentence directly beneath the draft; deletion/insertion text uses the theme's contradicted/supported ink colours, with AA contrast checked in both themes. The live runner also returns an envelope for the single supported input “Apple revenue was $391 billion in fiscal 2024.”; a fixture-backed regression runs the complete live loop without network access.

## Validation records

Every attempt is retained. Focused tests load Python/Node network guards and remove provider credentials. The full verifier installs locked dependencies, then runs in its own guarded disposable copy.

| Receipt | Result / scope |
| --- | --- |
| [01 dependencies](01-dependencies.log) | Locked dependency setup into a temporary environment; no model/SEC requests |
| [02 targeted](02-targeted.log), [metadata](02-targeted.json) | 99 passed, 2 failed: canonical labels adjacent to Chinese text; a cyclic nested-citation test fixture |
| [03 targeted](03-targeted.log), [metadata](03-targeted.json) | 101 passed after both fixes |
| [04 targeted](04-targeted.log), [metadata](04-targeted.json) | 106 passed, including directional growth and absolute-change formatting |
| [05 full verifier](05-verify.log), [metadata](05-verify.json) | 1 failed, 1,203 passed: existing server test prohibited returning the original post to its caller; updated to permit the requested response while retaining no-post-storage and no-secret-exposure assertions |
| [06 targeted](06-targeted.log), [metadata](06-targeted.json) | 117 passed, including issuer/metric context binding and unsupported currencies |
| [07 targeted](07-targeted.log), [metadata](07-targeted.json) | 146 passed, including HTTP adapter privacy, range/compound guards and language switching after live submission |
| [08 full verifier](08-verify.log), [metadata](08-verify.json) | 1,218 product/site tests passed; demo tests: 203 passed, 3 failed because preview artifacts retained the previous site-script hash |
| [09 preview refresh and demo suite](09-demo-preview.log), [metadata and unchanged-host hashes](09-demo-preview.json) | Two preview artifacts refreshed; all 206 guarded demo tests passed |
| [10 full verifier](10-verify.log) | `UV_OFFLINE=1 bash scripts/verify.sh` after preview refresh; complete output retained |
| [11 round-2 targeted](11-r2-targeted.log), [metadata](11-r2-targeted.json) | 149 passed, 1 failed: the new annual-input test incorrectly supplied enriched program output to the strict model-response parser |
| [12 round-2 targeted](12-r2-targeted.log), [metadata](12-r2-targeted.json) | 150 passed after using the saved raw model JSON as the test-response template; includes the full post, supported single claim, saved-demo rendering and light/dark AA contrast |
| [13 round-2 visual checks](13-r2-visual-check.log), [metadata](13-r2-visual-check.json) | Frontend source lint: 0 failures, 4 existing warnings. Browser inspector unavailable: Chrome exited before connection; native Chrome computer-use access was denied. No browser screenshot or computed-style result is claimed. Offline CSS contrast checks and English/Traditional Chinese renderer checks passed |
| [14 round-2 full verifier](14-r2-verify.log), [metadata](14-r2-verify.json) | `UV_OFFLINE=1 bash scripts/verify.sh`; full output and exit status retained |

[Unit tests](../../../tests/test_correction.py) cover unique/missing/repeated/overlapping spans, emoji offsets, stated scales and grouping, half-up rounding, English/Traditional Chinese periods, explicit non-corrections, finite values, direct/derived/nested citations, growth directions and the no-model-number invariant. [Live tests](../../../tests/test_live_check.py) exercise the response envelope and malicious model-proposed replacements. [Pages tests](../../../tests/node/live-boundary.test.mjs) exercise its allowlist; [site runtime tests](../../../tests/test_site_live_runtime.py) pass the Python-generated envelope into shipped JavaScript and render hostile originals, replacements and URLs as inert text. Existing suites continue to cover budgets, authentication and server reuse.

The existing demo compiler regenerated [hover-source.js](../../../demo/motion/v3/hover-source.js) and [preview-data.js](../../../demo/motion/v3/preview-data.js). Their only changes are the current site-script SHA-256. Measured host data, timing, keyframes, beats, cues and all narration text remain byte-identical; the receipt records before/after hashes. No voice, browser capture or media rendering ran.

[Round-1 input and source hashes](inputs-and-sources.json) identify that round's recorded Apple source, implementation and targeted tests, with base/current hashes for unchanged gate, budgets, authentication and server sources. Round-2 targeted/full-verifier metadata above retain the current implementation, tests, builders, envelopes and source-report/trace hashes. The [operator handoff](../../../deploy/README.md#host-operator-commands) provides the existing immutable-image build/import/rollout commands; preserve its PVC, one replica and Recreate strategy.
