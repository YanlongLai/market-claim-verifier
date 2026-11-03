# Claim-extraction LoRA attempt — 2026-11-03 UTC

**Outcome: stopped at feasibility; no trained adapter or quality comparison.**
Fireworks accepted a rank-8 Muse Spark Open NVFP4 LoRA initialization, but this
workspace could not obtain its matching tokenizer. Upstream files are gated;
the existing Hugging Face credential is expired and the named tokenizer caches
are absent. Both temporary Fireworks sessions were deleted. Estimated incurred
Fireworks spend is **$0.00 of the authorized $15.00**.

[Feasibility findings and official sources](FEASIBILITY.md) ·
[registered protocol](PROTOCOL.md) · [ledger](ledger.json) ·
[source facts/fingerprints](sources.json) · [artifact manifest](manifest.json).
Dates use UTC; the account checks occurred on Nov 2 in America/Los_Angeles.

## What the attempt established

| Question | Recorded outcome |
| --- | --- |
| Correct training base | `accounts/fireworks/models/muse-spark-open-nvfp4` |
| Account can initialize LoRA | Yes; awaited rank-8 initialization and model info, no training batches |
| Serverless training rate | $18.58/1M train tokens; sampler $6.19/1M prefill, $15.48/1M output |
| Matching tokenizer usable locally | No; missing local artifact/cache and expired upstream credential |
| Dataset upload / managed SFT job | Documentation inspected; neither executed; managed REST eligibility unresolved |
| Adapter serverless chat endpoint | Not supported by the documented serving route |
| Dedicated serving shape | Shape match returned 4 × B300; deployment/adapter loading untested |
| Dedicated standard price estimate | $60/replica-hour before regional premiums |
| Training, evaluation, or serving charges incurred | $0 estimated; no token or dedicated GPU work submitted |

The budget could cover a small checkpoint-sampling experiment under the
[unexecuted estimates](ledger.json). The stop is specific to available tokenizer
access; it is not a claim that Fireworks lacks Muse LoRA support or that a $15
training experiment is inherently impossible. Model API flags, UI guidance, and
generic FP4 addon documentation differ in places; the feasibility report retains
those distinctions rather than claiming a tested managed or serving route.

## Data and measurement boundaries

No SFT examples, dataset upload, training/held-out extraction split, or paid
baseline were created. No held-out v2 claims or real-world evaluation items were
used for training or example construction. The prospective development-only
split policy is in the protocol; there are **no dataset hashes or extraction
scores to report**. Artifact hashes cover the feasibility evidence only.

| Requested measurement | Base | LoRA |
| --- | --- | --- |
| JSON validity | Not run | Not run |
| Exact quote-span match | Not run | Not run |
| Ticker / metric / period / number accuracy | Not run | Not run |
| Missing / extra claims | Not run | Not run |
| Extraction latency / cost | Not run | Not run |

Control-request timings in the raw records measure initialization/metadata HTTP
operations, not extraction latency. There is no measured win and no serving
validation. The conditional `--provider fireworks-lora` option was therefore not
added. Default providers, prompts, product code, previous evidence, and existing
accuracy numbers were not changed.

## Retained records and validation

- [Public-model GETs](model-probes.jsonl), with full
  [base](api-muse-spark-open.json) and [NVFP4](api-muse-spark-open-nvfp4.json) bodies.
- [Account-projected shape discovery](shape-probes.jsonl), both
  [initial control](session-probes.jsonl) and
  [awaited model-info](session-info-probes.jsonl) attempts, including deletion.
- [Tokenizer errors](nvfp4-tokenizer-probes.jsonl),
  [BF16 access error](hf-authorized-probe.json), and
  [local tokenizer/cache checks](tokenizer-access.json).
- [Ledger](ledger.json): all 18 retained HTTP events, zero charges/reservations,
  planning arithmetic, and preliminary local-script failures. Account lookup
  bodies are projected before retention; credentials and balances are omitted.
- [Offline evidence audit](validate.py) and [validation receipt](VALIDATION.md).

The repository's complete offline verifier runs both Python suites, standalone
Node tests, figure checks/rebuilds, deterministic data rebuilds, and local
Markdown links. It does not train a model or validate a live adapter. See the
receipt for actual commands and outcomes. A new training attempt must use a new
directory and retain this outcome.
