# Providers, input support and cost

Checked 2026-10-30. Scope: the three providers currently integrated in this repository: Meta, Baseten and Fireworks. Account credit balances, expiration and quota were not queried; public availability does not establish account entitlement.

## Models & keys

Runtime settings checked against [config.py](../src/claimcheck/config.py),
[CLI flags](../src/claimcheck/cli.py), [provider adapters](../src/claimcheck/providers.py),
[cost ledger](../src/claimcheck/budget.py) and [ingest model allowlist](../src/claimcheck/ingest.py)
on 2026-11-04. The capability and published-price notes below retain their 2026-10-30 scope.

### Local provider credentials

| `--provider` | Key environment variable | Key-file environment variable | Default key file | File contents |
| --- | --- | --- | --- | --- |
| `baseten` | `BASETEN_API_KEY` | `BASETEN_API_KEY_FILE` | `~/secret/baseten_api_key.txt` | Raw key only; surrounding whitespace removed |
| `fireworks` | `FIREWORKS_API_KEY` | `FIREWORKS_API_KEY_FILE` | `~/secret/fireworks-api-key.txt` | Raw key only; surrounding whitespace removed |
| `meta` | `MODEL_API_KEY` | `MODEL_API_KEY_FILE` | `~/.config/dappgo/meta-model-api.env` | A `MODEL_API_KEY=your-key` line; blank/comment/unrelated lines ignored; matching quotes allowed |

A nonempty key environment variable wins. Otherwise the selected provider's key file is read;
`~` expands to your home directory. A missing file means no key; an unreadable configured file
is an error. Baseten and Fireworks files do not parse dotenv assignments. The Meta file is
parsed by Python, not sourced as shell code. The CLI does not use `META_MODEL_API_KEY`.

Keep these files outside the repository with private permissions. Create the parent directory,
write the value in your editor, then restrict it; do not paste secrets into shell arguments or film them:

```sh
mkdir -p ~/secret ~/.config/dappgo
# After creating the appropriate key file in your editor:
chmod 600 ~/secret/baseten_api_key.txt
# Point to a different existing file when needed:
export BASETEN_API_KEY_FILE="$HOME/secret/baseten_api_key.txt"
```

### Provider and model selection

Selection order is `--provider` > `CLAIMCHECK_PROVIDER` > `meta`.
Model order is `--model` > `CLAIMCHECK_MODEL` > the selected adapter's default.
`CLAIMCHECK_MODEL` is shared across providers: unset it or change it when switching hosts.
The integrated cost ledger recognizes exactly these Meta model pairs:

| Provider | Default model ID | Additional configured model ID |
| --- | --- | --- |
| Baseten | `meta-models/muse-spark-open-1026` | None |
| Fireworks | `accounts/fireworks/models/muse-spark-open` | None |
| Meta Model API | `muse-spark-1.3` | `muse-wonder-1.0` |

These are exact IDs, not aliases. An unknown pair is refused before a paid model call because
the ledger cannot reserve its cost. Ingest explicitly allows only these pairs. Ledger support
for Wonder does not establish current account entitlement or a measured quality comparison.
Keep Meta models for the hackathon runtime.

```sh
uv run python -m claimcheck verify 'META Q2 2025 revenue was $47.5B' \
  --provider baseten --model meta-models/muse-spark-open-1026 --budget 1
CLAIMCHECK_PROVIDER=meta CLAIMCHECK_MODEL=muse-wonder-1.0 \
  uv run python -m claimcheck post examples/posts/bigtech-thread.txt --budget 1 --dry-run
```

`--max-output-tokens` overrides `CLAIMCHECK_MAX_OUTPUT_TOKENS`; `--reasoning-effort` overrides
`CLAIMCHECK_REASONING_EFFORT`. For post checks these control verification turns; initial extraction
uses its own 4,000-token limit. They do not change OCR/ASR models. The adapters translate
Meta Responses and Baseten/Fireworks Chat Completions request shapes.

### OCR and ASR

All image OCR uses Meta `muse-spark-1.3`; all audio transcription uses Meta
`muse-voice-transcribe-1.0`. Video combines local decoding, three sampled frames and audio.
Provide `MODEL_API_KEY` or `MODEL_API_KEY_FILE` for these stages even when the text verifier
is Baseten or Fireworks. Their verifier keys cannot substitute for a Meta media key.
Native-text PDFs and text decode locally. Audio/video decoding requires FFmpeg/ffprobe.
Media model IDs are fixed in [ingest_media.py](../src/claimcheck/ingest_media.py).

### Budgets and previews

`--budget` overrides `CLAIMCHECK_BUDGET_USD` (default $0.50) in USD. The ledger reserves before
each call, reconciles recorded usage and retains holds on failures or missing usage. Extraction,
all verifier turns and retries count. This is a ceiling, not a fixed charge or a provider invoice.
`verify` and `post` share `runs/ledger.jsonl`; existing spend for the selected provider counts
toward its ceiling. `ingest` uses `runs/ingest-ledger.jsonl`, splitting a mixed-provider cap
equally between Meta preprocessing and the selected verifier. A Meta-only ingest uses the full
cap for both stages. `CLAIMCHECK_RUNS_DIR` changes the `runs` root; `CLAIMCHECK_CACHE_DIR`
changes the local SEC cache (default `.cache`). Preserve previous runs and ledgers.

```sh
uv run python -m claimcheck verify 'META Q2 2025 revenue was $47.5B' --provider baseten --dry-run
uv run python -m claimcheck post examples/posts/bigtech-thread.txt --provider fireworks --budget 1 --dry-run
```

Both previews skip key-file reads, model calls and SEC fetches. `verify` previews its initial
request/reservation against the existing ledger. `post` previews only initial extraction against
the requested cap and existing provider spend without writing a ledger or report; it cannot predict subsequent tool turns
or the final cost. Its request includes the supplied text. `ingest` has no `--dry-run` flag.

### Online (site) vs Local (CLI)

| Provider | Online (site) | Local (CLI) |
| --- | --- | --- |
| Baseten | Server `BASETEN_API_KEY`; adapter default fixed | Your `BASETEN_API_KEY` or raw-key file; `--provider baseten` |
| Fireworks | Server `FIREWORKS_API_KEY`; adapter default fixed | Your `FIREWORKS_API_KEY` or raw-key file; `--provider fireworks` |
| Meta Model API | Server `META_MODEL_API_KEY`; fixed verifier and media models | Your `MODEL_API_KEY` or Meta env file; `--provider meta`, optional `--model` |

The site's server reads Kubernetes Secret `live-check-secrets` in namespace `dappgo-hackathon`.
Its keys are `BASETEN_API_KEY`, `FIREWORKS_API_KEY`, `META_MODEL_API_KEY`,
`LIVE_CHECK_PASSWORD` and `LIVE_ORIGIN_TOKEN`. `META_MODEL_API_KEY` covers both online Meta
verification and media preprocessing. The HTTP adapter also accepts each name with `_FILE`;
these server files contain raw values, including the Meta key. Explicit server environment
values win even when empty, unlike the CLI's nonempty-key fallback. There are no default
server secret-file paths. [Deployment configuration](../deploy/README.md#configuration-and-persistence).

Site visitors supply the review password, never provider keys. The Pages proxy keeps the
matching `LIVE_ORIGIN_TOKEN` and its Access credentials `LIVE_ACCESS_CLIENT_ID` /
`LIVE_ACCESS_CLIENT_SECRET`; Pages receives no provider keys. The server fixes model IDs,
and ignores local CLI model environment settings. Its manifest sets shared limits of $10/day
and $60 lifetime; local `--budget` does not change them. [Real request logs and CLI capture](REAL_TRACES.md).

## Platform capability versus integration

| Provider / model | Vendor-declared inputs | Repository use today | Audio / video boundary |
|---|---|---|---|
| Meta / muse-spark-1.3 | Text; repository has a working image OCR path | Text extraction, tool-based verification, image OCR | Audio uses separate muse-voice-transcribe-1.0; video uses local decoding plus OCR/ASR, not a native video endpoint |
| Baseten / Muse Spark Open | Library lists text, image, video, audio | Text extraction and verification with meta-models/muse-spark-open-1026 | Library listing is not an endpoint contract for the pinned model; native audio/video request shapes remain unverified |
| Fireworks / accounts/fireworks/models/muse-spark-open | Text and images, text output | Text extraction and verification | Native audio/video is not established by this model page; image routing is not integrated here |
| Meta / muse-voice-transcribe-1.0 | Audio | File ASR, chunked with overlap | Turn timestamps and session speaker labels; no verified identity or word alignment |

Sources: [Baseten model library](https://www.baseten.co/library/muse-spark-open/), [Fireworks model card](https://fireworks.ai/models/fireworks/muse-spark-open), [Meta pricing and ASR](https://dev.meta.ai/docs/pricing-rate-limits). Meta OCR implementation: [media adapter](../src/claimcheck/ingest_media.py). Vendor modality labels need endpoint probes before enabling another adapter. No unsupported capability is inferred from a shared model family name.

## Current repository input contract

| Input | Support | Limit |
|---|---|---|
| Text | TXT, Markdown | Financial claims; not a universal fact checker |
| Image | PNG, JPEG, WebP through Meta OCR | Reading text is not evidence authentication |
| Audio | WAV, MP3, M4A, FLAC, AIFF, AAC, OGG | Up to 2 hours and 128 MiB; 10-minute ASR chunks; English language bias |
| Video | MP4, MOV, WebM, MKV | Same size/duration limits; only three sampled frames plus audio |
| PDF | Local native text, page-scoped | Up to 100 pages / 128 MiB; scanned/blank pages reported unchecked; no PDF OCR or cross-page context |
| URL | Deferred, direct readable documents only | No general HTML extraction, login or browser automation |

Accepted duration is a decoder limit, not a demonstrated accuracy guarantee. Media read/heard text remains a claim, not financial evidence.

## Recorded input-format probes

The [2026-10-30 format report](evidence/input-formats-2026-10-30/REPORT.md) adds six preselected paid smoke probes across all three text providers: Markdown, JPEG, WebP, MP3, silent MP4 and local native-text PDF. Per-case completion, claim counts, verdicts, latency and ledger costs are public. One example is evidence for that path, not exhaustive codec, language, provider or accuracy validation. Media still uses Meta OCR/ASR before text-provider routing; no native Baseten/Fireworks media endpoint was tested. Unsupported URLs and scanned PDFs remain deferred.

## Price comparison

USD per million tokens; published standard rates, not credit-adjusted prices.

| Provider / model | Input | Cached input | Output | Repo integration |
|---|---:|---:|---:|---|
| Meta Spark 1.3 Standard | 1.25 | 0.15 | 4.25 | Yes |
| Baseten Spark Open | 1.25 | 0.15 | 4.25 | Yes |
| Fireworks Spark Open | 1.25 | 0.15 | 4.25 | Yes |
| Meta Spark Contributor | 0.10 | 0.002 | 0.20 | Not configured in the price ledger; requires training-use consent |

Sources: [Meta rates](https://dev.meta.ai/docs/pricing-rate-limits), [Baseten rates](https://www.baseten.co/pricing/), [Fireworks model rates](https://fireworks.ai/models/fireworks/muse-spark-open).

Meta ASR is $0.18/audio hour ($0.003/minute), separate from downstream claim checks. Official documentation says whole seconds rounded down; the current ledger conservatively reserves rounded-up seconds and retains reservations on failures. Reported ledger estimates are not invoices. Overlapping chunks and retries add processed audio. OCR is token-priced, not a fixed price per image.

Total cost = decoding/storage + OCR/ASR + extraction + every tool-loop model call + retries. Search or licensed market-data charges must be added if introduced. A document may contain many chargeable claims.

## Batch and scale

[Fireworks Batch API](https://docs.fireworks.ai/guides/batch-inference) advertises 50% off serverless token rates, but requires model compatibility. Its model page offers on-demand deployment; exact pinned-model/account batch execution has not been tested here. No provider-native batch adapter is integrated. Meta/Baseten batch discounts for these routes are unverified. Concurrent requests and background responses are not automatically discounted batch inference.

An agent loop has sequential tool dependencies: batch extraction or independent evidence-ready checks first, then resume dependent stages. Shared SEC limits must be enforced across workers before scaling beyond the current process-wide gate. Cache immutable source bytes and successful OCR/ASR; key verification reuse by claim, source, policy and model versions.

## Measured quality and cost

Original 266-claim held-out split, corrected labels; recorded run, not a fresh benchmark of today's code:

| Agent | Accuracy | Reported mean cost USD | Mean latency seconds |
|---|---:|---:|---:|
| Baseten | 90.2% | 0.019880 | 11.307 |
| Fireworks | 89.1% | 0.019973 | 68.530 |
| Meta | 82.0% | 0.025880 | 38.372 |

[Full report and denominator details](evidence/eval-v2-2026-10-27/REPORT.md). Meta has one incomplete agent case; means follow the report's completion accounting. These numbers are not SLAs. Closed Spark and Open Spark are different model variants. Media has only [development probes](evidence/multimodal-2026-10-30b/REPORT.md), not comparable provider-wide accuracy scores. Measure extraction recall separately from verdict accuracy; 50/60 program-checked assertions on frozen ASR is coverage, not 83.3% truth accuracy.

## Paired format evidence (2026-10-30)

The [completed benchmark](evidence/fair-multimodal-v1/REPORT.md) compares identical nine-format inputs with shared frozen Meta preprocessing. Separate native PNG/JPEG/WebP probes completed six control images per format on every provider; native audio/video endpoints were not tested. Native image probes do not change the product adapter: all product image routes still require Meta OCR. [Official price cross-check](evidence/fair-multimodal-v1/RATE_CHECK.md) · [total task spend](evidence/fair-multimodal-v1/task-spend.json). No discounted provider Batch was used.

## Real webcast smoke test

[Real AV v1](evidence/real-av-v1/REPORT.md) exercises WAV and MP4 with all three verifier routes. Meta still provides ASR/OCR for all routes. Original slide webcast visuals are retained; three sampled frames cannot establish full video coverage. Period, quotation and accounting-basis gaps are reported separately from transcription numeric preservation.
