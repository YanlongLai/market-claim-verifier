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
