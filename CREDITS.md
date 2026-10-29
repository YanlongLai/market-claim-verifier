# Credits and data attribution

## Code

Market Claim Verifier is copyright © 2026 Yanlong Lai and released under the [MIT License](LICENSE). Repository work was created during the Meta Global AI Developer Hackathon ([build disclosure](BUILD_LOG.md#build-log), [dated history](CHANGELOG.md)).

## SEC public data

Credit: **U.S. Securities and Exchange Commission, EDGAR** — public XBRL companyfacts, company ticker mappings and filed financial statements. These supply the verifier's financial evidence; they are not model-generated ground truth. Source definitions, access details and limitations are recorded in [DATA_SOURCES.md](docs/DATA_SOURCES.md) and the [source registry](sources/registry.yaml).

Evidence retains filing accessions, dates, source URLs and snapshot SHA-256 hashes ([EDGAR client](src/claimcheck/edgar.py), [run manifest](docs/evidence/eval-v2-2026-10-27/manifest.json)). Offline tests use [trimmed SEC fixtures](tests/fixtures/), including [23 snapshots with original/trimmed hashes](tests/fixtures/sec-offline/README.md); the site stores [filing excerpts and provenance](docs/site/data/site.json). XBRL tagging errors, restatements and derived facts are described in [DATA_QUALITY.md](docs/DATA_QUALITY.md). This repository's MIT code license does not replace source publishers' terms or imply SEC endorsement.

## Evaluation claim sources

The [real-world claim list](eval/v2/real.yaml) credits source URLs, titles, publication dates and source tiers. Those claims are stored as paraphrases; [the source policy](docs/DATA_SOURCES.md#claim-source-tiers) explains the distinction between claim sources and SEC evidence. Generated/paraphrased claims and their inputs are listed in the [evaluation manifest](eval/v2/MANIFEST.json).

## Models used by the verifier

**Meta Muse Spark 1.3** via Meta Model API; **Meta Muse Spark Open (open weights)** via Baseten and Fireworks. Exact model IDs and recorded calls are in [provider code](src/claimcheck/providers.py), the [provider diagram](docs/diagrams/providers.mmd) and the [evaluation manifest](docs/evidence/eval-v2-2026-10-27/manifest.json). The OpenAI-compatible SDK is a transport client for these models ([project dependencies](pyproject.toml), [adapters](src/claimcheck/providers.py)).

The [local-input probe](docs/evidence/multimodal-2026-10-29/REPORT.md) also uses Meta **Muse Voice Transcribe 1.0** for speech-to-text ([API documentation](https://dev.meta.ai/docs/speech-to-text)). OCR uses Muse Spark 1.3; transcripts and OCR are claim inputs, not financial evidence.

## Media and dependencies

Offline production of demo media used Breeze-TTS-2 narration, ACE-Step music and Codex image_gen illustrations; this is separate from the claim-verification runtime. The existing [production tool/license record](docs/PROCESS-media.md#tools-and-licences), [demo provenance](demo/README.md#records-licences-and-host-completion), [image prompts](docs/prompts/) and [demo prompts](demo/prompts/) record those sources. In particular, Breeze-TTS-2 weights are research/non-commercial; narrator WAV files are excluded by [.gitignore](.gitignore). The video publication URL remains pending ([judge opening/handoff](demo/JUDGE_INTRO.md)).

Third-party packages remain under their own licenses. Exact Python dependencies are locked in [uv.lock](uv.lock) and [demo/uv.lock](demo/uv.lock); rendering/encoding tooling is documented in the [media process](docs/PROCESS-media.md#tools-and-licences).

The small [multimodal test fixtures](tests/fixtures/multimodal/manifest.json) are self-made Pillow images and synthesized release readings encoded with ffmpeg. macOS `say` failed under the managed sandbox; the recorded fallback is [eSpeak NG](https://github.com/espeak-ng/espeak-ng), version 1.53.0, an offline formant synthesizer distributed under GPLv3 or later. No eSpeak program/voice package is bundled. [Generation provenance](tests/fixtures/multimodal/generation.json) records its exact source revision and the failed `say` attempts. The narration excerpts Apple's credited SEC release, with one disclosed number perturbation; it is not executive audio or a voice clone. This fixture-production tooling is separate from Meta-only verifier inference.
