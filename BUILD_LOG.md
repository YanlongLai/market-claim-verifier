# Build Log

Dated record of what was built for the Meta Global AI Developer Hackathon (building period 2026-10-27 to 2026-11-04).
Everything in this repository was created during the hackathon. Times are America/Los_Angeles.

**Pre-hackathon:** none of this repository's code existed before 2026-10-27. The author runs an existing market-data
product (DappGo); its code is not in this repository and is not part of this submission. Before the event the author only
read the participant guide and noted that DappGo's own AI-written stock commentary on 2026-10-26 failed its internal
fact-assertion check — the problem this project addresses.

Live run traces kept as evidence are in [`docs/evidence/`](docs/evidence/) (raw model responses, tool calls, token usage,
cost, latency; no API keys).

## Day 1 — 2026-10-27 (Tue)

Goal: confirm the Meta Model API, create the repo, make the first tool call against SEC EDGAR.

- Read the Meta Model API docs and the account's model list. Picked `muse-spark-1.3` (Responses API, function calling,
  structured output; $1.25 / $4.25 per 1M input/output tokens). Reasoning tokens count against `max_output_tokens`.
- Confirmed SEC EDGAR XBRL `companyfacts` access (requires a contact User-Agent).
- Created the repo (Python 3.12, uv, MIT).
- Built the EDGAR fact tool: ticker → CIK, metric aliases (companies switch XBRL concepts over time), period selection by
  dates rather than filing labels, quarter vs year-to-date separation, preference for 10-K/10-Q over other forms,
  `period_type` labels, and derived values when filings do not report them directly (Q4 = annual − 9-month YTD;
  cash-flow quarters = YTD differences). Every derived value lists its source filings. EPS and share counts are never
  derived.
- Built the agent loop: Muse Spark decomposes a claim into sub-claims and calls `lookup_fact` / `list_periods`
  (parallel calls), then returns a structured verdict. Python re-checks every cited number against the tool output;
  when the model and the program disagree, the program wins.
- Built a hard budget ledger: worst-case cost is reserved before every model call and the call is refused if it would
  exceed the budget; actual usage is reconciled afterwards.
- Every run writes a trace: requests, raw responses, tool calls/results, usage, cost, latency.
- First live smoke test: Muse Spark issued `lookup_fact(META, revenue, 2025Q2)` correctly (2.1 s, ~$0.002).
- First live end-to-end verification: "Meta's Q4 2024 revenue was $48.4 billion, and its full-year 2024 net income was
  $70 billion." → revenue **supported** ($48.385B, derived), net income **contradicted** ($62.36B from the 10-K);
  overall `contradicted`; model and program agreed. 3 model calls, $0.0173, 27.7 s.
- Found from the live trace: one turn came back `incomplete` (`max_output_tokens`). Added status checks, one retry with
  a doubled limit (budget-reserved), and a fail-closed `insufficient_evidence` result if still incomplete.
- Second live run: "Tesla's Q3 2025 net income was about $1.4 billion and Alphabet's Q4 2024 revenue exceeded
  $100 billion." → overall `contradicted` (Alphabet $96.469B), $0.019, 34 s. Exposed a gap: the program check only
  knows "equals within 1.5%", so "about $1.4B" vs $1.373B was a program mismatch while the model said supported, and
  "exceeded" was treated as equality. → Day 2.
- Spot-checked tool values against published results: META Q4 2024 revenue $48.385B, GOOG Q4 2024 revenue $96.469B,
  TSLA Q3 2025 net income $1.373B, META FY2024 net income $62.36B.
- Tests: 26 offline tests passing (fake model client, trimmed SEC fixtures).
- Commits: `7c5670b`, `97b5365`, `f0acc85`. Model spend today ≈ $0.04.

## Second provider: Muse Spark Open on Baseten — 2026-10-27

- Baseten Model APIs are OpenAI-compatible at `https://inference.baseten.co/v1`.
- The hackathon key works only with model id `meta-models/muse-spark-open-1026`.
- Chat Completions tool definitions use the nested OpenAI chat format; the
  smoke-test tool call returned `finish_reason: "tool_calls"` and JSON-string
  function arguments, with tool results sent back as `role: "tool"` messages
  in the full stateless history.
- The model always reasons; reasoning text is returned in `reasoning_content`.
  `reasoning_effort=low` worked.
- Structured output and JSON mode are unavailable. Final verdicts must be
  requested as plain JSON, parsed, schema-validated, and repaired once on
  invalid output.
- Usage includes prompt/completion tokens, reasoning-token details, cached
  prompt-token details, and speculative accepted/rejected prediction-token
  details. Pricing is $1.25 input, $0.15 cached input, and $4.25 output per
  1M tokens.
- Rate-limit headers report 100 requests and 2,000,000 tokens; the Baseten
  credit pool is separate from the $150 Meta credit, with $100 Baseten credit.
- Live smoke test: tool call correct, 1.5 s, 666 input / 156 output tokens,
  52 reasoning tokens, ≈$0.0015.

## Day 2 scope — started 2026-10-27 (Tue) afternoon

Goal: make the program check understand how claims are phrased (approximate values, inequalities, growth rates).

- Added strict `compute_change` tool support with an optional prior-year base
  period, two underlying `lookup_fact` facts, absolute change, percentage
  change, and separate evidence IDs.
- Added pure number-phrase parsing with scale suffixes, percentage points, and
  precision derived from the last stated digit.
- Replaced expected/found program checks with claim-type and comparator-aware
  checks for values, inequalities, absolute changes, and percentage changes.
- Added model/program disagreement fields, program-derived overall verdict
  aggregation, offline parser/check tests, and replay coverage for the two
  live-trace claim shapes.
- Documented the tolerance rules in README.md.
- From the five 2026-10-27 live-run findings, accepted omitted, null, empty,
  `"null"`, and `"none"` `compute_change.base_period` values as the default
  prior-year period while retaining the required nullable strict-schema field.
- From the live change traces, resolved one `compute_change` citation together
  with its component fact IDs, deduplicated matching value evidence, and split
  `no_evidence` from `ambiguous_evidence`.
- Added direction-aware signed percentage/absolute-change checks, including
  `stated_sign_corrected`, and capped value tolerances at 10% of the stated
  magnitude.
- Built `history_rank` with quarter/annual windows, derived Q4 coverage,
  record-high/record-low and first-time-above sub-claims, plus `other` coverage
  sub-claims that remain unchecked.
- Resolved `first_time_above`, `record_high`, and `record_low` against one
  `history_rank` evidence window, using only periods through the claimed period
  and resolving phrase-only thresholds from matching sibling sub-claims.
- Added trimmed fixtures and fake-client replays for all five live traces,
  including the exact recorded `[E3, E4, E5]` citations, and expanded the
  offline suite to 90 passing tests.
- Lesson: replay tests now use recorded tool output verbatim.

## Evaluation set — 2026-10-27

- Built a 30-claim labeled evaluation set in `eval/claims.yaml` and generated
  `eval/claims.jsonl`, with 20 dev claims, 10 test claims, seven companies,
  value, rounding, inequality, growth, period, unit, multi-part, record/first,
  and SEC-insufficient-evidence categories.
- Added the independent raw-companyfacts gold builder
  `eval/build_gold.py`, which writes `eval/gold_facts.json` and
  `eval/GOLD_REVIEW.md`, including selected values, periods, accessions,
  concepts, and snapshot SHA-256 hashes.
- Added the sequential, resumable `single_shot` versus `agent` evaluation
  runner, shared budget accounting, pair result files, copied agent traces,
  budget-stop recording, and the `eval run` / `eval report` CLI commands.
- Completed the evaluation evidence ledger: single-shot traces now retain the
  rendered prompt and raw response, every pair records prompt hashes, timing,
  token buckets, model/tool calls and cost, and each run has a versioned
  manifest plus an auditable report. The first six-claim partial dev run was
  aborted by the author because its single-shot prompts/raw responses were not
  recorded; it is kept in `docs/evidence/eval-2026-10-27-aborted-partial/` as
  evidence and superseded by `eval-2026-10-27/`.
- Added offline fake-client tests for the independent gold builder, report
  metric math, no-tool single-shot requests, resume behavior, budget stops,
  dataset validation, and report generation.
- Live evaluation results will be added after the Claude Code live run.

### Live verification results (Muse Spark 1.3, 2026-10-27, traces in `docs/evidence/2026-10-27/`)

Five claims were run live before and after the Day 2 fixes. Program verdicts:

| Claim | Before fixes | After fixes | Actual (SEC) |
|---|---|---|---|
| Meta Q2 2025 revenue was $47.5B, up 22% YoY | insufficient (growth unchecked) | **supported** | $47.516B, +21.6% |
| Tesla Q3 2025 net income about $1.4B; Alphabet Q4 2024 revenue exceeded $100B | contradicted | **contradicted** (Tesla part supported) | $1.373B; $96.469B |
| Alphabet Q3 2025 revenue topped $100B for the first time | supported ("first time" silently ignored) | **supported**, both parts checked | $102.346B; no earlier quarter above $100B |
| Tesla revenue fell 10% YoY in Q3 2025 | insufficient (growth unchecked) | **contradicted** | +11.6% |
| Meta Q4 2026 revenue was $60B | insufficient | **insufficient_evidence** (not yet filed) | — |

Each run: 3–4 model calls, $0.015–0.029, 25–52 s. Two bugs were found only by live runs and fixed: the model passing
`"null"` as a string argument, and real `lookup_fact` output lacking the `period` field that a hand-trimmed test fixture
had. Offline suite: 98 tests. Model spend so far ≈ $0.29 (ledger in `runs/`, not committed).

## Documentation & visuals — 2026-10-27

- Added four Mermaid diagrams under `docs/diagrams/` and embedded them in `README.md`: the checking flow, a committed
  Alphabet real-run sequence, the model-versus-program decision, and the two provider paths.
- Added `docs/scripts/make_figures.py`, which rebuilds the before/after, verdict-card, and live cost/latency figures from
  this build log and the committed live traces without model calls or network access.
- Added SVG and PNG figures under `docs/figures/`; the optional evaluation figure is generated only when a complete
  `docs/evidence/eval-*/summary.json` exists.
- Added `docs/figures/hero.png`, an AI-generated illustration, and recorded its prompt in
  `docs/prompts/hero-image.md` (with a pointer left at `docs/figures/hero-prompt.md`).
- Restructured `README.md` for a short judge-facing read while retaining the run, EDGAR, provider, verdict, and
  evaluation details below the overview.
- Made every visual reproducible and reusable: added the evidence-hashed figure registry, offline `--all`/`--check` builder, `.mmd` diagram sources, README/VISUALS markers, and the prompt library with the exact hero prompt and variants.

## Evaluation runs, third provider, provenance and data checks — 2026-10-27 (Tue) evening

All runs below are committed under `docs/evidence/` with manifest, per-call traces (prompt, raw response, tokens incl.
reasoning, cost, latency) and `REPORT.md`. Gold labels for the 30 claims were committed before the first run
(`f54f5d6`).

- **Recording first.** A first dev run was stopped after 6 claims because single-shot prompts and raw responses were not
  being saved; it is kept as `eval-2026-10-27-aborted-partial/`. Added per-call traces for every system, a run manifest
  (commit, versions, prompt SHA-256s, data snapshot hashes, time window, ledger spend) and a `prompts/` registry that a
  test keeps in sync with the code.
- **Run 1 (dev, Meta API + Baseten).** Agents beat single-shot on accuracy (0.75 vs 0.60 / 0.40) but said "supported"
  for 3 false claims: the model chose `approx` for un-hedged numbers such as "$1.3 billion" (actual $1.373B). Also
  found: "Microsoft Q4 2025 $281.7B" is false under both fiscal and calendar readings but agents answered
  "insufficient"; one Meta API call failed with an expired `previous_response_id`.
  Fixes: the program infers the comparator from the claim's wording; both period readings are checked; the Meta path
  resends full history when a referenced response or reasoning item has expired.
- **Run 2 (dev agents + the held-out test split, first and only pre-registered test run).** False-supported fell to 0.
  Test accuracy: agent 7/10 (Meta API), 10/10 (Baseten); single-shot 5/10 and 3/10. Dev run exposed the Meta model
  writing free text into the `interpretations` field → only real evidence IDs are accepted.
- **Run 3 (post-hoc, agents on all 30).** Meta API agent 0.90 dev / 0.80 test, Baseten 0.95 / 1.00, still 0
  false-supported.
- **Third provider.** Added Muse Spark Open on Fireworks (`accounts/fireworks/models/muse-spark-open`) through a shared
  OpenAI-compatible chat adapter with its own budget pool. Its first live run cited the same Tesla fact twice under
  calendar and fiscal labels → identical evidence is now collapsed, and facts carry `fiscal_equals_calendar`.
- **Run 4 (all 30 claims, six systems, one code version).** Agent accuracy 30/30 on Baseten and Fireworks, 26/30 on the
  Meta API; single-shot 18/30 (Meta API), 10/30 (Fireworks), 6/30 (Baseten); 0 false-supported for every system.
  Paired agent − single-shot accuracy: +27 pts on Meta API (bootstrap 95% CI +7 to +47, McNemar p = 0.039), +79 on
  Baseten, +67 on Fireworks. Mean cost per claim $0.011–0.021; mean latency 10 s (Baseten agent) to 48 s (Fireworks
  agent). Two Baseten single-shot calls ended `incomplete` (reasoning used the whole output limit) and count as wrong.
- **Statistics in reports.** Wilson 95% intervals for accuracy, false-supported and insufficient rates (overall, per
  split, per category); paired bootstrap (10,000 resamples, seeded) and exact McNemar tests between systems.
- **Provenance.** Every fact now carries a tier (L1 audited 10-K, L2 reviewed 10-Q, L3 derived), confirming filings,
  revision status and a strength level; sub-claims and verdicts report the weakest evidence used. Added
  `sources/registry.yaml` and `docs/DATA_SOURCES.md` (what SEC XBRL covers and does not, claim-source tiers, and the rule
  that per-site reliability is only published with n ≥ 20 and a confidence interval).
- **Fiscal-label bug found while collecting real-world claims.** SEC companyfacts `fy`/`fp` describe the filing, not
  the period: Oracle's quarter ended 2026-08-31 is tagged `fy=2026` but is fiscal 2027 Q1. Both the verifier and the
  independent gold builder had relied on these fields, so they agreed with each other and were wrong together. Each now
  derives fiscal year and quarter from period dates and the issuer's fiscal year-end, with two separate
  implementations; they agree on all 159,368 quarterly, year-to-date and annual facts since 2019 for 23 issuers, and
  match the issuers' own quarter names (Oracle, NVIDIA, Microsoft, Apple, Meta, Tesla). The 30 v1 gold verdicts were
  unchanged.
- **SEC tagging errors.** A data-quality checker over 24 issuers (`docs/DATA_QUALITY.md`) found that Oracle's 10-Ks filed
  in 2020–2022 tag full-year revenue for fiscal 2018, 2019, 2021 and 2022 on the fourth-quarter period. The verifier
  now drops a quarter whose value equals its covering annual value, derives the quarter instead (Oracle FY2018 Q4:
  $11.0B rather than $39.4B) and lists the excluded row. A first version flagged any quarter above 60% of the year; it
  produced 154 false alarms (e.g. Tesla's Q4 2012 revenue really was 74% of that year) and was replaced by the exact-match
  rule, which flags only the 6 Oracle rows. The checker reports 21 consistency anomalies and 603 revised periods (289
  above 0.5%); revisions are listed separately because later filings routinely reclassify earlier periods.
- **Eval v2 in progress.** A seeded generator (`eval/v2/`) builds 260 claims across 23 companies and 10 families,
  including 26 deliberately ambiguous fiscal/calendar claims whose gold is computed under both readings. Review of the
  first draft found wrong month names, missing years and an "at least" claim worded as an equality; these were fixed
  before freezing.
- **Figures.** The evaluation chart now shows all six systems with Wilson intervals; added a data-quality chart and
  Fireworks to the provider diagram.
