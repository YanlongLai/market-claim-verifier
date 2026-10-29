# Credits and data attribution

## Code

Market Claim Verifier is copyright © 2026 Yanlong Lai and released under the [MIT License](LICENSE). Repository work was created during the Meta Global AI Developer Hackathon ([build disclosure](BUILD_LOG.md#build-log), [dated history](CHANGELOG.md)).

## SEC public data

Credit: **U.S. Securities and Exchange Commission, EDGAR** — public XBRL companyfacts, company ticker mappings and filed financial statements. These supply the verifier's financial evidence; they are not model-generated ground truth. Source definitions, access details and limitations are recorded in [DATA_SOURCES.md](docs/DATA_SOURCES.md) and the [source registry](sources/registry.yaml).

Evidence retains filing accessions, dates, source URLs and snapshot SHA-256 hashes ([EDGAR client](src/claimcheck/edgar.py), [run manifest](docs/evidence/eval-v2-2026-10-27/manifest.json)). Offline tests use [trimmed SEC fixtures](tests/fixtures/), including [23 snapshots with original/trimmed hashes](tests/fixtures/sec-offline/README.md); the site stores [filing excerpts and provenance](docs/site/data/site.json). XBRL tagging errors, restatements and derived facts are described in [DATA_QUALITY.md](docs/DATA_QUALITY.md). This repository's MIT code license does not replace source publishers' terms or imply SEC endorsement.

The animated cards use [11 complete first-filing iXBRL documents](tests/fixtures/sec-filings/README.md), downloaded from EDGAR on 2026-10-29 and stored with lossless compression and source hashes. The [generated chronology table](docs/site/BUILD_SUMMARY.md#on-screen-filing-chronology) records each displayed filing and its first-filed accession; recorded evaluation reports retain their original provenance.

## Evaluation claim sources

The [real-world claim list](eval/v2/real.yaml) credits source URLs, titles, publication dates and source tiers. Those claims are stored as paraphrases; [the source policy](docs/DATA_SOURCES.md#claim-source-tiers) explains the distinction between claim sources and SEC evidence. Generated/paraphrased claims and their inputs are listed in the [evaluation manifest](eval/v2/MANIFEST.json).

## Models used by the verifier

**Meta Muse Spark 1.3** via Meta Model API; **Meta Muse Spark Open (open weights)** via Baseten and Fireworks. Exact model IDs and recorded calls are in [provider code](src/claimcheck/providers.py), the [provider diagram](docs/diagrams/providers.mmd) and the [evaluation manifest](docs/evidence/eval-v2-2026-10-27/manifest.json). The OpenAI-compatible SDK is a transport client for these models ([project dependencies](pyproject.toml), [adapters](src/claimcheck/providers.py)).

## Media and dependencies

Offline production of demo media used Breeze-TTS-2 narration, ACE-Step music and Codex image_gen illustrations; this is separate from the claim-verification runtime. The existing [production tool/license record](docs/PROCESS-media.md#tools-and-licences), [demo provenance](demo/README.md#records-licences-and-host-completion), [image prompts](docs/prompts/) and [demo prompts](demo/prompts/) record those sources. In particular, Breeze-TTS-2 weights are research/non-commercial; narrator WAV files are excluded by [.gitignore](.gitignore). The video publication URL remains pending ([judge opening/handoff](demo/JUDGE_INTRO.md)).

Website paper textures, stationery, the fictional Banana News Flash masthead, finance illustrations and Hover spot illustrations were generated with built-in Codex `image_gen`. Their [exact reusable prompts](docs/prompts/site/polish.md), [export hashes and sizes](docs/site/img/polish/manifest.json), and [processing script](docs/site/img/polish/process-assets.py) record this decorative artwork separately from saved claims and SEC evidence. The footer reuses the existing Hover palm-out pose; personas and activity counts are labelled as examples.

Third-party packages remain under their own licenses. Exact Python dependencies are locked in [uv.lock](uv.lock) and [demo/uv.lock](demo/uv.lock); rendering/encoding tooling is documented in the [media process](docs/PROCESS-media.md#tools-and-licences).
