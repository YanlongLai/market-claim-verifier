# Judge-readiness verification receipt

Verified **2026-10-29**, branch `docs/judge-readiness`. Host: macOS arm64, Python **3.14.6**, Node **26.6.0**, uv **0.12.1**. Prerequisites and expected output: [AGENTS.md](../AGENTS.md#offline-verification).

## Offline command

```sh
sh scripts/verify.sh
# After the locked dependency cache is populated:
UV_OFFLINE=1 sh scripts/verify.sh
```

The disconnected invocation completed successfully in a fresh local clone containing the committed changes, with no `.venv`/`.cache` symlinks; Git status was clean before and after. [Raw verification output](evidence/judge-readiness-2026-10-29/offline-verify.txt) records:

| Check | Result |
| --- | --- |
| Product, providers, replay, evaluation and site lifecycle | **255 passed** |
| Demo Python pipeline, including local synthetic FFmpeg integrations | **83 passed** |
| Standalone Node motion/layout/capture contracts | **41 passed** |
| Figure source/README check → chart rebuild → check | **PASS** |
| Explorer JSON, site JSON and site build summary | **3 byte-identical outputs** |
| Markdown file links and anchors | **PASS** |

The [runner](../scripts/verify.py) uses a disposable source copy, temporary environments, no provider credentials, and tested Python/Node network guards. The original `.venv`/`.cache` symlinks are ignored and not followed. The independent [key-score inspection command](../AGENTS.md#inspect-the-key-numbers-without-dependencies) also produced exactly the six counts and three model IDs documented there.

## Portability and scope

With `media.FFMPEG` and `media.FFPROBE` set by a test-only plugin to nonexistent paths, the demo suite reports **78 passed, 5 skipped** ([output](evidence/judge-readiness-2026-10-29/without-native-media.txt)). Only the five marked native-media integrations skip. The normal full run above has no skipped tests. No Chromium launch, speech synthesis, full video render, model request or SEC download is needed.

The new [SEC fixture inventory](../tests/fixtures/sec-offline/README.md) removes tests' dependency on ignored cache files; its [hash checker](../scripts/build_offline_fixtures.py) validates all 23 committed snapshot hashes against [provenance](../tests/fixtures/sec-offline/provenance.json). [Subtitle text](../demo/tests/fixtures/README.md), synthetic reference WAVs and [injected Git metadata](../tests/test_eval_recording.py) remove the remaining local-output/history dependencies. Product code, prompts, benchmark claims/gold/results and site data were not modified. The original README body from “The problem” onward is preserved byte for byte.

## Link and secret checks

```sh
python3 scripts/check_links.py --external
gitleaks dir --redact --no-banner .
gitleaks git --redact --no-banner --log-opts=--all .
git diff --check
```

The [link checker](../scripts/check_links.py) checks all Markdown plus `llms.txt`, including relative destinations and heading/HTML anchors; HTTP URLs are fetched separately. All **77 documents** passed, with no broken local links and **3 HTTP successes, 0 broken, 0 unverified**. It also rejects file links outside the repository. Code-example paths are not treated as clickable links.

**Gitleaks 8.30.1** scanned the working tree and all Git refs; no secrets were detected with defaults plus the [narrow media-hash exceptions](../.gitleaks.toml) ([scan output](evidence/judge-readiness-2026-10-29/secret-scan.txt)). The fresh clone's scan includes **45 commits**. The nine unconfigured findings were exactly 64-character hexadecimal `input_key`, `assembly_cache_key` and `music_cache_key` values in recorded media files, produced by [cache hashing](../demo/pipeline.py) and [motion assembly](../demo/motion_build.py). Exceptions require the exact field/line shape **and** specific media-record paths; no whole directory or commit is excluded. A temporary `api_key` canary in the same media-record directory was still detected. Scans do not traverse `.venv`/`.cache` symlinks or redistribute credentials.

## Existing issues repaired

The initial figure check found stale `BUILD_LOG.md` input hashes for the before/after and development-latency figures. Only [registry hashes](figures/figures.json) and the [visual index](VISUALS.md) were refreshed; existing chart images/values are unchanged. Seven links to ignored or machine-local demo outputs were replaced with labeled local-output paths and the [committed build record](../demo/BUILD_LOG.md), preserving historical review findings.

The workflow is [configured for push/PR](../.github/workflows/verify.yml); it has not been run on GitHub by this local-only task. The demo publication URL remains pending, and the [opening disclosure](../demo/JUDGE_INTRO.md) has not been rendered into the existing video.

## Paired media and stock-context receipts

[Primary benchmark audit](evidence/fair-multimodal-v1/audit.json) validates the frozen experiment independently of subsequent product changes. [Post-hoc audit](evidence/stock-context-posthoc-2026-10-30/audit.json) verifies both retained repair attempts and their shared budget. [Final product verification log](evidence/stock-context-posthoc-2026-10-30/final-offline-verification.log) records 901 product, 149 demo Python and 55 Node tests plus presentation/output/link checks. Replay instructions are in [REUSE](evidence/fair-multimodal-v1/REUSE.md).
