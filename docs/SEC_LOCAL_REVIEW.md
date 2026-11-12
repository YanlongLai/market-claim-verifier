# Native Claude Code + model-free SEC review

The original Meta/Baseten/Fireworks model paths are unchanged. `check-json` does
not read model keys or invoke any model provider. Its default SEC mode is `on`;
`--sec off` returns omitted/verification_paused with no publishable statements.
Network is disabled unless `--allow-sec-network` is explicitly passed.

```sh
python scripts/claude-code-proposals.py public-input.txt --out runs/native-unique
python -m claimcheck check-json runs/native-unique/proposals.json \
  --issuers reviewed-issuers.json --cache-dir .cache --as-of 2025-10-30
```

Use the repository's locked Python environment. The first command uses the
unmodified native `claude -p` executable, the owner's existing Claude Max login,
no API key, no token extraction, no API SDK or proxy. It rejects provider/key
and OAuth-token overrides, disables hooks, skills, MCP, tools and project/user
settings, runs in an empty temporary directory and retains a bounded receipt.
It has a timeout and no API fallback. Native usage limits still apply; its
`total_cost_usd` output is not proof of a separate bill. Actual billing was not
observed. Never expose this helper as an end-user model-routing service.

The issuer registry is **separate trusted input**, reviewed by the owner or a
trusted data process. The model must not generate or edit it. Bind an issuer key
to the selected source's market/ticker/CIK; the SEC ticker map must independently
agree. The loaded companyfacts payload must also contain the same CIK; a
correctly named cache file alone is insufficient. A Taiwan issuer must not become Honeywell because a model guessed HON.
The helper's proposed CIK is not itself evidence.

Input schema: `sec-proposals-v1`, with up to 100 unique-id claims containing
`issuer_key`, `ticker`, `cik`, `metric`, `period`, `unit`, `value`. See the frozen
cases and registry under `docs/evidence/sec-switch-20261111`.

Output `sec-check-v1` retains input/registry hashes, verification policy,
per-claim status and SEC provenance. Only canonical statements generated from
resolved SEC metric/period/value/unit become publishable. Arbitrary original
model prose, causal claims and forecasts are not echoed as verified. Exact unit
and issuer agreement are mandatory; unsupported/ambiguous cases are omitted.
This initial bounded path conservatively omits derived facts lacking a direct
filing URL. It does not certify entire articles or ingest its results into the
DappGo production content service automatically.

## Comparison protocol and results

Run `PYTHONPATH=src python scripts/compare-sec-checks.py --out <new-directory>`.
Never overwrite previous runs. Six fixed adversarial cases yielded one verified,
one corrected and four omitted. Paused mode yielded zero publishable SEC facts.
Article and narration/subtitle excerpts share the same adjudicated statement.
These are historical trimmed fixtures, not representative production accuracy,
full article readability or rendered-video quality measurements. The issuer case
is inspired by the preserved RW046 failure; the original verdicts were not edited.

Native Max smoke execution on 2026-11-12 UTC extracted two public test claims.
Checking those against the existing cached SEC snapshot retained the correct
47,516,000,000 USD revenue and corrected 47,516 USD to that value. No new model
API key was created. Private execution receipt/proposals/check are under the
market-lab `experiments/openai-credit-20261111/sec-switch-20261111/claude-run-01`.

Official behavior references (checked 2026-11-12):
- https://code.claude.com/docs/en/headless
- https://code.claude.com/docs/en/legal-and-compliance

## Handoff

Keep full failed/partial logs. Run `sh scripts/verify.sh` for the canonical
offline gate and the new native-boundary tests without paid calls. Do not run
`verify` or `post` expecting Max inference: those retain their configured API
provider paths. AI001 coordination/skill remains disabled by the owner.
