# Real-world shot input contract

[realworld.py](../realworld.py) is an offline compiler. It reads retained News and Threads results under
`docs/evidence/real-world-*/`, writes [realworld.json](realworld.json), and refuses missing or inconsistent
records. The committed pending JSON contains **no measurements or narration**. It supports source preview
only; host voice/timing/render preparation refuses it. Synthetic test cases are confined to temporary test
directories and never enter this snapshot.

Each selected run supplies `demo-shot.json` beside its raw reports. This is an explicit selection/index
contract for the evidence producer, not a replacement for the run manifest, raw requests, ledgers or failed
attempts required by the [test-record guide](../../docs/TEST_RECORDS.md). Include every attempted item in
the run, including partial/provider-error results; do not select only successes. Exactly one original run
must expose both sources. Rechecks have their own descriptor and are never merged into the original counts.
Every `real-world-*` run directory must have an index; an unindexed recheck fails compilation rather than
silently disappearing. Original pages appear first, followed by the separately labeled rechecks.

```json
{
  "schema_version": 1,
  "run_id": "use-the-recorded-run-id",
  "phase": "original",
  "sources": [
    {"id": "news", "items": [
      {"id": "recorded-item-id", "input": "news/input.json", "report": "news/report.json"}
    ]},
    {"id": "threads", "items": [
      {"id": "recorded-post-id", "input": "threads/input.json", "report": "threads/report.json",
       "examples": [{"claim_index": 1, "paraphrase": "Short evidence-reviewed paraphrase."}]}
    ]}
  ]
}
```

Paths resolve relative to the descriptor and must remain under `docs/evidence/real-world-*/`.
Inputs are JSON containing the retained source text and, for Threads examples, the public `url`.
Reports use the saved post-check shape: `claims` (with `index`, `status`, `verdict`, `program_checks`),
`cost_usd` and `wall_clock_s`. An absent report status means the legacy completed post-report format;
otherwise status is `completed`, `partial`, `failed`, `error` or `provider_error`. Failed/partial reports
must retain their measured cost and wall time, even with no claims. Missing spend is never treated as zero.
The recorded total must include all attempts/retries for that item. Provider spend/latency receipts remain
auditable evidence, not an inference by this compiler.

For a post-hoc fix recheck use `phase: "posthoc_frozen_text_recheck"` and `rechecks_run` naming the original
run. It may cover a subset of sources/items; each receives its own statistics/page. This label means a
frozen-text check, **not a new OCR/ASR test or fresh held-out evaluation**. Other recheck types fail rather
than being mislabeled. The renderer labels these pages explicitly.

The compiler hashes descriptors, inputs and reports. It derives tested-item counts, items with at least
one program-checked claim, that coverage fraction/percentage, claim verdict counts, cost per attempted
item and median item wall time. Partial/failed items remain in cost, latency and coverage denominators.
Coverage is not recall or verdict accuracy; no gold-based accuracy is calculated here.

At most three examples are selected explicitly in the descriptors. Their claim indices must point to
recorded program checks. Paraphrases are short, human-reviewed text, not generated summaries. Numeric
tokens must occur in that example's input/check evidence; a changed decimal magnitude fails. The original
URL stays in evidence, while only its `@handle` is compiled/displayed. No full post URL is shown on screen.

The narration template is:

> Saved real-world runs: {news} news items, {threads} Threads posts. Coverage is not accuracy.

The compiler fills both counts from the original run. It caps the template at 22 words; the host must
measure the locked-voice WAV at **≤10 seconds**. Timing rejects a longer clip rather than accelerating it.
The shot remains in its approved **11.3081-second** reserve. The twelve original paragraphs are unchanged.

```sh
uv run --project demo python demo/realworld.py
uv run --project demo python demo/realworld.py --check
uv run --project demo python demo/motion_v3.py --preview-only
```

The first two commands intentionally fail until real evidence exists. Committing a pending preview does
not assert that the real-world test ran. [Host commands and remaining review](../REVISION-v010.md) describe
the source handoff.
