# market-claim-verifier

`market-claim-verifier` is a small agent that decomposes a financial claim, retrieves the relevant SEC EDGAR XBRL facts, and asks Meta Muse Spark to produce a cited verdict; deterministic checks in Python verify the model's numbers before returning `supported`, `contradicted`, or `insufficient_evidence`. Built during the Meta Global AI Developer Hackathon starting 2026-10-27.

## Setup

```bash
uv sync
```

Keep the model key outside this repository, either as `MODEL_API_KEY` or in the default file `~/.config/dappgo/meta-model-api.env`:

```dotenv
MODEL_API_KEY=your-key-here
```

The SEC EDGAR data source is public. The checked-in code uses the local `.cache/` files when available and sends the configured contact User-Agent for a cache miss.

## CLI

```bash
python -m claimcheck edgar META revenue 2025Q2
python -m claimcheck verify 'Meta Q2 2025 revenue was $47.5B, up 22% YoY'
python -m claimcheck verify --dry-run 'Meta Q2 2025 revenue was $47.5B'
```

Use `--model muse-wonder-1.0`, `--budget 0.10`, or
`--max-output-tokens 5000` on `verify` when needed. Tool turns default to
4,000 output tokens and the final verdict to 3,000; the CLI flag or
`CLAIMCHECK_MAX_OUTPUT_TOKENS` overrides both. Set
`--reasoning-effort` or `CLAIMCHECK_REASONING_EFFORT` to pass a reasoning
effort through to the model. A run trace and append-only budget ledger are
written under `runs/`; keys are never written to either file. This tool is not
investment advice.

## EDGAR result fields

Successful `lookup_fact` results include `duration_days` and `period_type`:
`quarter`, `ytd`, `annual`, or `instant`. Additive flows can be returned with
`derived: true`, a human-readable `derivation`, and the source `components`
used in the subtraction; `form_fallback` identifies a non-statement-form
fallback. EPS and share counts are not derived.

`YYYYQn` uses the fact's SEC `frame` when present. If there is no frame, it
uses the calendar quarter containing the fact's `end` date; fiscal `fp` names
are not used as calendar quarter labels. This keeps date-based YTD derivation
working for non-calendar fiscal years.

## How verdicts are decided

The model labels each atomic claim, but the program verdict is computed from
the cited evidence. A value claim must cite one numeric `lookup_fact`; a
matching lookup fact plus the same fact nested in a cited `compute_change` is
treated as one. A growth claim must cite exactly one numeric `compute_change`
result; its two component fact IDs may also be cited. Ambiguous evidence is
`unchecked`. If no numeric evidence is cited, or every cited tool result is an
error, the reason is `no_evidence`; otherwise unresolved competing citations
are `ambiguous_evidence`.

| Comparator | Program rule |
| --- | --- |
| `eq` | Difference is at most the precision implied by the stated number |
| `approx` (value or absolute change) | Difference is at most `max(2 × precision, 2.5% of abs(stated))` |
| `approx` (percent change) | Difference is at most `max(2 × precision, 1.0 percentage point)` |
| `gt`, `lt` | Strict comparison; no tolerance |
| `gte`, `lte` | Comparison accepts equality within the stated precision |
| value-claim cap | Every value tolerance is additionally capped at `10% × abs(stated value)` |

The cap applies after the comparator-specific rule. For example, an approximate
`$2 trillion` value cannot receive more than `$200 billion` of tolerance even
though its displayed-number precision would otherwise allow a larger window.

`history_rank` compares quarters only with quarters (including derived Q4) and
annual periods only with annual periods. It supplies record-high/record-low
checks and the chronological comparison window used by `first_time_above`.
Every factual assertion must be represented as a sub-claim; assertions outside
the available EDGAR checks use `claim_type=other` and remain unchecked.

Overall, any contradicted sub-claim makes the claim `contradicted`; all
supported sub-claims make it `supported`; otherwise it is
`insufficient_evidence`. The result retains the model verdict and flags any
model/program disagreement.

## Evaluation

The checked-in evaluation set has 30 natural-language claims in
[`eval/claims.yaml`](eval/claims.yaml), with a stratified 20-claim `dev` split
and 10-claim `test` split; the split assignments are recorded per claim.
The JSON-compatible YAML is converted to [`eval/claims.jsonl`](eval/claims.jsonl)
by the independent gold builder. It reads raw `.cache/companyfacts-*.json`
files directly, records the selected SEC values, dates, accession numbers,
concepts, and snapshot SHA-256 values, and writes
[`eval/gold_facts.json`](eval/gold_facts.json) plus the human-review table
[`eval/GOLD_REVIEW.md`](eval/GOLD_REVIEW.md). It never imports `claimcheck`.

Rebuild the labels offline and check the hand-written verdicts:

```bash
.venv/bin/python eval/build_gold.py
```

Run the same model as either a no-tools single-shot judge or the existing
tool-using agent. The default evaluation budget is $2.00 and is shared by all
pairs through one append-only ledger. The run is sequential and resumable;
each pair gets a JSON result, and agent traces are copied under the output
directory:

```bash
.venv/bin/python -m claimcheck eval run \
  --split all \
  --systems single_shot,agent \
  --budget 2 \
  --out docs/evidence/eval-2026-10-27/
```

Before a live run, inspect the plan without a key, model call, or network:

```bash
.venv/bin/python -m claimcheck eval run --dry-run --split dev
```

Generate the metrics and report after a run:

```bash
.venv/bin/python -m claimcheck eval report \
  --out docs/evidence/eval-2026-10-27/
```

The report includes accuracy, per-gold-class precision/recall,
false-supported rate, insufficient rate, latency percentiles, cost, a
per-claim comparison, and agent error categories. A failed or budget-stopped
pair is recorded and counts as missing for scoring; it is not silently
retried. `single_shot` receives no tools and is asked to judge from its own
knowledge, while `agent` uses the SEC cache and the existing deterministic
checks. The gold rules accept reader-style rounding, treat any false part of
a multi-part claim as contradicted, and reserve insufficient evidence for
facts outside the SEC snapshot. The sample is small, so the report makes no
significance claims; live results are intentionally not part of the checked-in
evaluation artifacts.

Each evaluation records the complete audit trail: every rendered request
(instructions, input, and structured-output format), raw response, reservation,
usage and cost in a trace; per-pair prompt hashes, input/cached/output/reasoning
tokens, model/tool-call counts, start/finish timestamps, verdict and scoring
fields; and a run manifest with the run window, wall clock, code/runtime
versions, git state, CLI arguments, budget and ledger spend, claims and SEC
snapshot hashes, and the full prompt registry. Prompt source files are exported
and checked for drift with `python -m claimcheck prompts export`.
