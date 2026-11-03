# Muse Spark Open extraction LoRA: feasibility

**Decision: stop before paid execution in this environment.** Fireworks supports
serverless LoRA training for `accounts/fireworks/models/muse-spark-open-nvfp4`,
and a small token-priced experiment could fit $15. The available environment
cannot obtain the matching tokenizer: upstream access is gated, the local Hugging
Face credential is expired, and the named official tokenizer caches are absent.
This is an access/prerequisite failure, not evidence that Muse Spark Open cannot
be fine-tuned or that LoRA fails to improve extraction.

Checked **2026-11-03 UTC** (Nov 2 in America/Los_Angeles). See the
[registered protocol](PROTOCOL.md), [source fingerprints and facts](sources.json),
[cost ledger](ledger.json), and [outcome report](REPORT.md).

## Training and dataset support

The [official model page](https://fireworks.ai/models/fireworks/muse-spark-open)
directs LoRA training to the Serverless Training API with the **NVFP4** model ID.
It says managed fine-tuning in the UI is unavailable for this model. The ordinary
`muse-spark-open` ID is the production serverless inference route.

Authenticated model GETs confirm the distinction:

| Recorded API field | `muse-spark-open` | `muse-spark-open-nvfp4` |
| --- | --- | --- |
| `state` | `READY` | `READY` |
| `supportsServerless` | true | false |
| `supportsServerlessTraining` | false | true |
| `supportsLora` | false | true |
| `supportsServerlessLora` | false | false |
| `supervisedLoraTunable` | false | true |
| `baseModelDetails.tunable` | false | false |

[Inference metadata](api-muse-spark-open.json) ·
[NVFP4 metadata](api-muse-spark-open-nvfp4.json) ·
[retrieval records](model-probes.jsonl). The newer supervised-LoRA flag is true
even though the legacy tunable field is false; neither the legacy field nor UI
availability alone establishes managed REST SFT eligibility. No managed job was
submitted, and no managed bypass for the missing local tokenizer was established.

The [managed SFT guide](https://docs.fireworks.ai/fine-tuning/fine-tuning-models)
documents JSONL examples containing a `messages` array, with 3–3,000,000 rows.
Its REST workflow creates a dataset, uploads the file through
`POST /v1/accounts/{account_id}/datasets/{dataset_id}:upload`, then creates a job
through `POST /v1/accounts/{account_id}/supervisedFineTuningJobs`.
[Upload reference](https://docs.fireworks.ai/api-reference/upload-dataset-files) ·
[job reference](https://docs.fireworks.ai/api-reference/create-supervised-fine-tuning-job).
These endpoints were researched, not executed.

The confirmed Muse route instead uses a local loop to submit tokenized batches
to shared GPUs. The [Serverless Training guide](https://docs.fireworks.ai/fine-tuning/training-api/serverless)
supports SFT and other objectives with LoRA, without provisioning a dedicated
trainer. Fireworks Python SDK **1.2.30** was installed only in a disposable
temporary environment; project dependencies and lockfiles were not changed.

## Account-level probe and tokenizer failure

The supplied Fireworks key was read with the repository's raw-key-file loader,
in memory. Request records omit authentication headers. Account lookup records
retain only account counts; private balances and account response bodies are
excluded. The separate existing Hugging Face credential was used only for an
access check and was never retained.

1. [First control probe](session-probes.jsonl): session creation and rank-8 model
   initialization submission returned HTTP 200. Initialization was asynchronous;
   this first probe did not await completion. Session deletion returned HTTP 200.
2. [Second control probe](session-info-probes.jsonl): awaited initialization,
   then `get_info` confirmed `is_lora: true`, `lora_rank: 8`. The returned
   `model_data.tokenizer_id` was null; `model_data.model_name` was the server-local
   `/llm-downloader-destination/base/fireworks/muse-spark-open-nvfp4` path.
   Session deletion returned HTTP 200.
3. The SDK's [tokenizer loader](https://github.com/fw-ai-external/python-sdk/blob/main/src/fireworks/training/sdk/_core/lib/public_interfaces/training_client.py)
   uses these model-info fields. The server-local path does not exist locally.
   [Local access check](tokenizer-access.json) found no complete tokenizer cache
   for the named official BF16, NVFP4, or legacy NVFP4 repositories.
4. The [official NVFP4 tokenizer](https://huggingface.co/meta-models/Muse-Spark-Open-816B-A42B-NVFP4/blob/main/tokenizer_config.json)
   returned HTTP 401 unauthenticated and HTTP 401 with the existing credential;
   the latter response identifies an expired OAuth token.
   [Both responses](nvfp4-tokenizer-probes.jsonl) and the separate
   [BF16 authenticated check](hf-authorized-probe.json) are retained.

No forward/backward pass, optimizer step, checkpoint save, generation request,
dataset upload, promoted model, or dedicated deployment was submitted. Both
temporary sessions were deleted. No training examples or evaluation splits were
constructed after this gate failed.

## Prices and budget

The live [pricing page](https://fireworks.ai/pricing) and
[serverless training documentation](https://docs.fireworks.ai/fine-tuning/training-api/serverless)
agreed on these standard USD rates at retrieval. Early search snippets omitted
Muse from the pricing table; the fetched current pages contain it.

| Route | Input/prefill per 1M | Cached per 1M | Output/sample per 1M | Train per 1M |
| --- | ---: | ---: | ---: | ---: |
| Production base serverless inference | $1.25 | $0.15 | $4.25 | N/A |
| Muse Spark Open Serverless Training API | $6.19 | $1.239 | $15.48 | $18.58 |

The generic managed-SFT rate for models over 300B is $10/1M training tokens;
that is a different product and was **not** used as the Muse serverless training
rate. No discount, cached-prefix saving, or private balance is assumed.

The [ledger](ledger.json) retains these **unexecuted planning calculations**:

- 256 examples × 1 epoch × at most 1,536 rendered tokens × $18.58/1M:
  **$7.30595328**. Masked prompt tokens are included.
- Same-sampler base and adapter evaluation: 32 posts per arm, each bounded to
  1,536 prefill + 1,536 sampled tokens: **$2.13024768** total.
- Optional production-base comparison on the same 32 posts: **$0.27033600**.
- Combined token-work estimate: **$9.70653696**. These are assumptions, not
  measured tokenizer counts, a reservation, or a completed experiment.

**Estimated incurred Fireworks charges: $0.00; outstanding reservations: $0.00;
task cap: $15.00.** Control operations submitted no billable tokens or dedicated
GPU workload. These estimates are not an invoice.

## Evaluation and serving

[Checkpoint evaluation](https://docs.fireworks.ai/fine-tuning/evaluating-fine-tuned-models)
can sample serverless training checkpoints without a dedicated deployment. This
is a Training SDK sampler, not a serverless chat-completions endpoint. A fair
adapter comparison would use an untrained NVFP4 checkpoint and the trained
checkpoint on the same sampler, recording a separate production-base comparison
if desired. Comparing BF16 production serving with NVFP4 checkpoint sampling
alone would confound LoRA, quantization, and endpoint changes.

[Deployment documentation](https://docs.fireworks.ai/fine-tuning/deploying-loras)
requires on-demand deployment for a promoted adapter's chat endpoint. The
account's [shape-match responses](shape-probes.jsonl) returned one validated
NVFP4 shape: **4 × B300**, FP4, with `MULTI_LORA`, both with and without
`enableAddons: true`. No deployment was created. Generic deployment documentation
says FP4 addons are unsupported, so the match result and generic guidance differ;
successful adapter loading and serving remain untested.

At the published $15/B300 GPU-hour, one four-GPU replica is **$60/hour, or
$1/minute** before any regional premium. Fifteen serving minutes alone consume
the entire cap. The illustrative token work above leaves about **5.29 minutes**
for such a deployment, if all other assumptions hold. Preemptible evaluation is
documented, but neither guaranteed capacity nor a lower price was established;
no free/preemptible discount is assumed. Budget is therefore a serving constraint,
not proof that the smaller checkpoint-sampling experiment is unaffordable.

## Conditions for a new attempt

Obtain working authorized access to the matching official tokenizer, verify its
renderer against the selected Fireworks base, and recheck current rates/support.
Resolve managed-REST eligibility separately if using that alternative. Register
a new immutable run directory, freeze development-only examples and a distinct
held-out extraction set with hashes, and count rendered tokens before reserving
any paid work. Preserve these failed-access records. No extraction-quality,
latency, cost-per-extraction, or open-weight fine-tuning prize result follows from
this feasibility probe.
