# README v3, language audit and screenshot handoff — 2026-11-04

This is an offline documentation and reading-layer update from `site/r3-polish` at `48a86e1b`. No model calls, SEC fetches, audio synthesis or new paid evaluation were made. The README follows the owner's final design section 12; its headline precision follows the section 6 one-number set. Historical observations remain labelled with their original scope.

## Cost and speed

| Figure | Provenance | Interpretation |
| --- | --- | --- |
| Live $0.01 / 6 s | [Production receipt](../live-prod-2026-11-03/REPORT.md): $0.00988 and 6.34 s | Rounded one-claim observation supplied by the owner; not an SLA. The older saved Apple trace is a different run. |
| Text $0.01–0.04 / 6–25 s | Owner's binding README-v3 planning band | Guidance by input size, not a measured minimum/maximum. No new run was performed to validate its endpoints. |
| Multi-assertion saved post | [Original report](../posts-2026-10-28/demo-thread-baseten/report.json), [saved envelope](../../site/data/examples/text.json): $0.062084 and 38.4 s | Historical receipt exceeds the planning band. It is preserved, rather than relabelled with the live headline. |
| Benchmark $0.02 per claim / 10 s median / p95 21 s | [Original report](../eval-v2-2026-10-27/REPORT.md#metrics), Baseten test row: mean $0.019880, p50 10012.8 ms, p95 20758.0 ms | Rounded completed-case summaries of the original held-out text run. Failures still count as wrong in accuracy. |
| Media overhead | [Media examples](../media-examples-2026-11-03/REPORT.md), [provider accounting](../../PROVIDERS.md#price-comparison) | OCR/ASR adds preprocessing cost and duration. The receipt separates preprocessing from verification; there is no measured fixed surcharge. |

The production receipt's historical $3/day setting is not today's live limit. It remains unchanged as a dated record. Ledger estimates/reservations are not invoices; retries, extraction and each model/tool-loop call contribute to cost.

## Accuracy and coverage

The README table is computed from [the original per-claim explorer snapshot](../../explorer/data.json), which the offline verifier independently rebuilds from saved results/traces. Count a result correct only when its status is completed and its verdict matches corrected gold. The all-claim denominator is 357; the held-out test split is 266. [Original metrics](../eval-v2-2026-10-27/REPORT.md#metrics) · [Registered gold](../eval-v2-2026-10-27/REPORT-registered-gold.md).

| System | All correct | Held-out correct |
| --- | --- | --- |
| agent@baseten | 323/357 | 240/266 |
| single_shot@baseten | 74/357 | 56/266 |
| agent@fireworks | 323/357 | 237/266 |
| single_shot@fireworks | 71/357 | 51/266 |
| agent@meta | 297/357 | 218/266 |
| single_shot@meta | 158/357 | 111/266 |

The headline 90.2% (240/266) and false support 1/139 describe Baseten's original corrected-gold held-out split. Historical all-claim percentages and later post-hoc reruns are separate. [78 Threads / 80 news](../real-world-2026-11-02/REPORT.md) describe corpus scope and coverage, not a new accuracy estimate. Frozen-transcript rechecks do not retest OCR/ASR.

## Scope and limits

[Current live contract](../../LIVE_CHECK.md#limits-and-failure-behavior) and [deployment configuration](../../../deploy/k8s/live-check.yaml) define the shared limits: $10 per UTC day, $60 lifetime, five accepted checks per IP per ten minutes. Public authenticated history retains inputs/results for 14 days. Pasted text is limited to 600 Unicode characters; arbitrary browser file uploads remain planned. The SEC cache TTL is six hours; saved demonstrations retain their original source dates. [Scope and company-count provenance](../REVIEW_GUIDE.md#facts-in-detail) records ≈8,000 companies, 23 tested, and SEC XBRL periods generally 2009 onward.

These are implementation/configuration facts, not a new production deployment or runtime audit. Provider stops and budget limits may halt a comparison. Original manifests, corrected-gold disclosure, failed attempts and raw traces remain available.

## Language audit

The initial scan found CJK in 109 default-language Markdown/HTML/TXT files, plus mixed Latin prose in existing Chinese mirrors. All eligible Markdown, HTML, TXT and SRT files are now covered by [the repository test](../../../tests/test_language_purity.py), including evidence, build logs, prompts, captions and both llms files. JSON/YAML may retain language fields and original sources. No directories containing repository evidence are exempted. The [final audit receipt](language-audit.json) lists 2,083 files: 2,007 English and 76 Chinese, with zero language violations.

- English prose uses English labels, unit explanations and translated quotations. Chinese prose lives in separate `.zh-TW.*` files or Chinese routes. Stray duplicated language labels were removed.
- [Exact pre-edit sources](original-language-sources.json) retain each original path, SHA-256 and complete UTF-8 text. Re-encoding a `text` field recovers the exact original bytes, including failed/partial diagnostic logs. This archive also retains the original extraction-prompt source and its hash.
- Chinese TXT inputs remain byte-identical in `.zh-TW.txt` mirrors. [Display translation mapping](input-translations.json) identifies the English reading files and exact original paths. Historical hashes refer to original bytes, not the display translations. The English files must not be substituted for original paid inputs in a replay.
- Recorded result/traces JSON, prompt hashes within those records, verdicts and financial values are unchanged. HTML reading copies explicitly identify translations and link original JSON plus a Chinese reading copy. Chinese report layers link English source quotations/errors instead of mixing prose languages.
- The demo compiler now reads the original `.zh-TW.txt` input. Its unmeasured preview and adapted website-source hash were refreshed offline; [locked-demo-outputs.json](locked-demo-outputs.json) confirms measured data, timing, keyframes, beats and cues are unchanged. The approval-lock test reads the exact archived pre-translation shot list, keeping the original storyboard/voice lock intact. [Preview refresh](demo-preview-refresh.log).
- Embedded CJK in archived TXT diagnostic code strings is represented with Unicode escapes; exact original logs are retained in the archive. This is a representation change, not a rerun or a corrected test outcome.
- The prompt Markdown export spells source-language unit literals with reversible Unicode escapes and explicitly identifies that representation. Runtime prompt text and hashes remain unchanged; the prompt registry still records the exact unescaped text. No paid call is authorized by this documentation update.

[Changed-file list](FILES_CHANGED.txt) covers the complete delivery. The [language policy](../../LANGUAGE.md) defines future updates. AI001 remains disabled and its files were not loaded or changed.

## Screenshots

[Capture script](../../../scripts/capture_readme_shots.py) renders the local Pages overlay in English at 1600 px viewport width. It selects story A, captures the Try section, opens the committed saved text result and requires its strike/insert correction plus SEC citations. External requests are blocked and API routes return 503; no simulated live result or budget is used. It writes `docs/site/img/readme/try-story-a.png` and `corrected-draft.png`, each at most 400,000 bytes, then inserts them at the markers in both READMEs.

The local launch failed before rendering because the OS sandbox denied Chromium's Mach-port rendezvous. [Failure receipt](screenshots/failure.json) and [browser log](screenshots/capture.log) retain that attempt. No screenshot or browser visual QA is claimed. The READMEs show explicit host-capture notices until real PNGs exist. The existing robot GIF remains at its original path and is unchanged.

Host commands from the repository root:

```sh
npm install --prefix /tmp/mcv-readme-browser --cache /tmp/mcv-readme-npm playwright
/tmp/mcv-readme-browser/node_modules/.bin/playwright install chromium
PLAYWRIGHT_MODULE=/tmp/mcv-readme-browser/node_modules/playwright/index.mjs \
  uv run python scripts/capture_readme_shots.py
bash scripts/verify.sh
```

Set `CHROME_PATH` if using an existing Chromium executable. A successful capture retains a browser receipt, dimensions, file sizes, image/source hashes and a capture log. Keep the failed launch record as well.

## Verification

Validation output is retained alongside this report. [First full run](verify-r1.log) caught stale static copy and the prompt export; [second full run](verify-r2.log) passed the product suite and caught the demo preview/input references. [Focused checks](targeted-final.log) and [demo checks](demo-r1.log) retain the corrections. [Figure refresh](figure-refresh.log) records regeneration of the two charts whose build-log prose source changed; the PNGs remained byte-identical. The final full run is recorded separately, without rewriting failures. No browser or screenshot success is implied by offline suites passing.

Final `bash scripts/verify.sh`: **PASS**. [Complete final run](verify-r3.log) passed the offline suites, figure regeneration, saved envelopes/assets, all three data outputs, wild-data reproducibility and Markdown/llms links. The [final link check](links-final.log) and [screenshot-driver syntax check](screenshot-script-final-check.log) are retained separately. Screenshot capture still requires the host; no browser success is inferred from these checks.
