# Real-world shot input contract

[realworld.py](../realworld.py) is an offline compiler. It reads retained News and Threads results under
`docs/evidence/real-world-*/`, writes [realworld.json](realworld.json), and refuses missing or inconsistent
records. The committed snapshot indexes the retained baseten/post attempts; synthetic test cases are
confined to temporary test directories and never enter this snapshot. A pending snapshot contains **no
measurements or narration** and supports source preview only; host voice/timing/render preparation refuses it.

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
  "provider": "baseten",
  "path": "post",
  "selection_note": "One fixed open-weight product route for all items, including failures.",
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
A frozen `claims.jsonl` input is also accepted: exactly one row must match the item's `id`, and the
whole input file is hashed. This selects the existing reviewed source row without rewriting it.
Reports use the saved post-check shape: `claims` (with `index`, `status`, `verdict`, `program_checks`),
`cost_usd` and `wall_clock_s`. An absent report status means the legacy completed post-report format;
otherwise status is `completed`, `partial`, `failed`, `error` or `provider_error`. Failed/partial reports
must retain their measured cost and wall time, even with no claims. Missing spend is never treated as zero.
The recorded total must include all attempts/retries for that item. Provider spend/latency receipts remain
auditable evidence, not an inference by this compiler.

For the retained real-world runner format, each item additionally indexes `result`, its `result.json`
receipt. The descriptor's `provider` and `path`, the item's `id`, and the report's provider/model must
match that receipt. Its ledger-based `cost_usd`, end-to-end `wall_seconds` and `status` are authoritative,
including on failure; missing receipt spend fails even when a report has a cost. `report` may be omitted
only for a non-completed receipt with no post report. Receipt-adjacent `traces/*.json` are hashed too,
including extraction-only traces from failed CLI attempts. The legacy report-only format remains valid.

The original [index](../../docs/evidence/real-world-2026-11-02/demo-shot.json) selects **baseten / post**
for all **80 News + 78 Threads** text attempts (30 own, 48 external). All six failed Threads attempts
remain in the denominators and accounting. The [recheck index](../../docs/evidence/real-world-2026-11-03-fixcheck/demo-shot.json)
selects the **80 news-r2 / baseten / post** adaptive attempts separately. Both descriptors retain the
route choice in `selection_note`. The two examples reuse retained T03 claim 2 and T09 claim 1 wording;
T33 failed before a program-checked post report on this route and remains in the totals.

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
uv run --project demo python demo/motion_v3.py --preview-only --check
```

These commands compile retained evidence and source preview without generating media.
[Host commands and remaining review](../REVISION-v010.md) describe
the source handoff.
