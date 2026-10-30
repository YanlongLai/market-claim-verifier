# Reuse and inspect this study

## No-credit verification

After installing the repository's locked dependencies, run from its root:

```sh
.venv/bin/python scripts/report_multimodal_benchmark.py
.venv/bin/python scripts/audit_multimodal_benchmark.py
```

These commands read retained files only. They recompute verdict scores and descriptive reading metrics, check all planned result cells, input/source-code/media hashes, local HTML links and the authorization cap, then rebuild the derived report/index. They do **not** repeat OCR, speech recognition, extraction or verification model calls. `summary.json`, `error-analysis.json`, `REPORT.md`, `inventory.json` and `audit.json` are derived outputs; the underlying paid records stay unchanged.

Use the Git revision containing the completed published results. The audit checks the source hashes recorded in `freeze.json`; later product edits can intentionally differ. For changed product modules it verifies the exact bytes in [the frozen source archive](frozen-source.zip), or the frozen Git revision, and lists those historical sources explicitly. The archive also supports repository ZIP downloads without Git history. Evaluation data/scorer hashes must still match the files used for replay. The original pre-call source revision is recorded there and remains in Git history. SEC snapshot restoration is needed for a new live verification run, not for this report replay.

## Where the evidence lives

| Artifact | Content |
| --- | --- |
| [Input manifest](../../../eval/multimodal-v1/manifest.json) | Exact input paths, bytes, SHA-256, split, issuer, format and source snapshot |
| [Original inputs](../../../eval/multimodal-v1/inputs/) | All 72 controlled files, including synthetic audio/video |
| [Gold](../../../eval/multimodal-v1/gold.json) | Labels and raw SEC rows; source coordinates were not sent to the model |
| [Frozen source proof](freeze.json) | Code, prompt, manifest and lockfile identities before paid execution |
| [Prepared text/media](prepared/) | Decode output, exact OCR/ASR results, source locations and redacted call records |
| [Text jobs](text-cache/) | Full text, extraction results, agent requests/responses, tool calls, verdicts and cost per unique job |
| [Development settings](selected-profiles.json) | Both profile results and the choice recorded before the test split |
| [Development ledger snapshot](development-ledger.jsonl) | Read-only copy through profile-selection time; not an additional charge |
| [Test reports](test/) | Same-file/provider HTML and JSON results, including errors and cache references |
| [Native image calls](native-images/) | Original-image request parameters, raw response, acceptance status and costs |
| [Real issuer diagnostics](diagnostic/) | Unscored Tesla page pipeline outputs, kept separate from control accuracy |
| [Full ledger](ledger.jsonl) | All phases; count this once, not again alongside the development snapshot |
| [Machine index](summary.json) | Per-format scores, native reading metrics, costs, latency and links to every test cell |

Requests refer to image/audio bytes by path/hash rather than duplicating base64 payloads. Original and derived media are both retained. [Environment](environment.json) records the authoring versions; original bytes, rather than cross-version encoder output, define the paired inputs.

## Reuse a stock report

`stock-summary` combines selected retained `ingest.json` files without reading API credentials or adding model fees; see the [stock-review guide](../../STOCK_REVIEW.md). It preserves repeated occurrences and uncertain results. It does not make uploaded documents authoritative evidence.

## New paid experiments

Do not run the archived `bench.py all` command merely to inspect results. It is an execution harness, can write selection timestamps, and requires a separately reviewed run directory/version and spending authority for new calls. Reuse the committed files for a fair comparison; register new inputs, prompts or settings as a new version. Do not overwrite this study or replace failures with better attempts.

Nine failed text jobs did not produce the standard post HTML. `scripts/render_failed_benchmark_jobs.py` creates explicitly labeled failure views from their unchanged records/traces; the first audit failure and the offline presentation repair remain recorded. This fixes navigation only, without retrying calls or changing scores.
