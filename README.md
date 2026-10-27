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

Use `--model muse-wonder-1.0` or `--budget 0.10` on `verify` when needed. A run trace and append-only budget ledger are written under `runs/`; keys are never written to either file. This tool is not investment advice.

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
