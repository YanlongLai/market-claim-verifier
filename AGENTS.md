# Verification guide for AI agents

Start with [JUDGES.md](JUDGES.md) and [llms.txt](llms.txt). Treat saved results as evidence of recorded runs; the limits and post-hoc labels in those files are part of each claim.

## Offline verification

Prerequisites: a POSIX shell, **Python 3.12–3.14**, **uv**, and **Node 22+**. Python requirements and locked dependencies are in [pyproject.toml](pyproject.toml), [uv.lock](uv.lock), [demo/pyproject.toml](demo/pyproject.toml) and [demo/uv.lock](demo/uv.lock). Node is required for the [site lifecycle tests](tests/test_site_stamps_runtime.py) and [standalone demo tests](demo/tests/motion.test.mjs). No npm install, model keys, SEC cache or media files are required by the [verification entry point](scripts/verify.sh).

From the repository root, run:

```sh
sh scripts/verify.sh
```

The first invocation downloads locked Python dependencies and the build backend. Verification itself runs without network access: [the runner](scripts/verify.py) removes provider credentials, points key-file settings to a nonexistent file, and installs Python/Node network guards before tests/builders run. Everything runs in a disposable copy and temporary virtual environments; `.venv` and `.cache` symlinks are neither followed nor changed. The uv download cache defaults to the system temporary directory and can be overridden with `UV_CACHE_DIR` ([shell script](scripts/verify.sh)).

After one successful invocation has populated that cache, the **entire command, including dependency setup**, can run disconnected:

```sh
UV_OFFLINE=1 sh scripts/verify.sh
```

Expected final lines ([runner](scripts/verify.py); recorded results: [verification receipt](docs/VERIFICATION.md)):

```text
PASS offline Python and Node suites
PASS figure rebuild + --check
PASS explorer, site data and build summary: 3 byte-identical outputs
PASS Markdown links and anchors
PASS no model calls, SEC fetches or credentials; source tree unchanged
```

Both Python suites and all standalone Node tests run. [Media-test skip markers](demo/tests/test_media.py) skip optional Homebrew FFmpeg/ffprobe integrations when those binaries are absent; the command does not render a full video or launch Chromium. The [figure builder](docs/scripts/make_figures.py) first checks committed source hashes/embeds with `--check`, regenerates charts with `--all`, then checks again. AI-generated stills remain the committed assets. SVG timestamps/IDs are not byte-stable; figure checks cover inputs, embeds and successful regeneration. The [explorer builder](docs/scripts/build_explorer_data.py) and [site builder](docs/scripts/build_site.py) must reproduce **all three** committed data outputs byte for byte; `--offline` reuses stored filing excerpts. CI runs the same entry point on [push/PR](.github/workflows/verify.yml).

Tests use [committed, hash-checked SEC fixtures](tests/fixtures/sec-offline/README.md), [frozen subtitle text](demo/tests/fixtures/README.md) and synthetic WAV references. They do not depend on the author's ignored cache, licensed narrator audio, generated media or Git executable. The [manifest test](tests/test_eval_recording.py) injects known Git metadata to verify its recording without needing local history.

## Inspect the key numbers without dependencies

This command reads the [explorer snapshot](docs/explorer/data.json), which the full verifier independently rebuilds from per-claim results and raw traces ([builder](docs/scripts/build_explorer_data.py)). It counts incomplete/provider-error results as wrong:

```sh
python3 - <<'PY'
import json
from pathlib import Path
data = json.loads(Path('docs/explorer/data.json').read_text())
for system in ('agent@baseten', 'agent@fireworks', 'agent@meta',
               'single_shot@baseten', 'single_shot@fireworks', 'single_shot@meta'):
    correct = sum(c['results'][system].get('status') == 'completed'
                  and c['results'][system].get('verdict') == c['gold']
                  for c in data['claims'])
    print(f'{system}: {correct}/{len(data["claims"])}')
manifest = json.loads(Path('docs/evidence/eval-v2-2026-10-27/manifest.json').read_text())
for model in sorted(set(manifest['models'].values())):
    print(model)
PY
```

Expected output ([v2 report](docs/evidence/eval-v2-2026-10-27/REPORT.md), [model manifest](docs/evidence/eval-v2-2026-10-27/manifest.json)):

```text
agent@baseten: 323/357
agent@fireworks: 323/357
agent@meta: 297/357
single_shot@baseten: 74/357
single_shot@fireworks: 71/357
single_shot@meta: 158/357
accounts/fireworks/models/muse-spark-open
meta-models/muse-spark-open-1026
muse-spark-1.3
```

The [original frozen claims](eval/v2/claims-v2.jsonl) were committed before v2 execution. The displayed results use [two corrected gold answers](eval/v2/claims-v2-corrected.jsonl); [registered-gold scores](docs/evidence/eval-v2-2026-10-27/REPORT-registered-gold.md) remain available. The run manifest explicitly records a dirty working tree. Do not call the [later agent rerun](docs/evidence/eval-v2-2026-10-28-r2-posthoc/REPORT.md) a fresh held-out evaluation. Its empty single-shot summary rows are not results ([status-aware builder](docs/scripts/build_explorer_data.py)).

## Verify the build window

In a Git clone with history, use:

```sh
git log --reverse --format='%h %aI %s'
git show --no-patch --format='%H%n%aI%n%s' 7c5670b
```

The first commit is `7c5670b84e6052db9fa67fd86606fb2ee11ee42c`, authored **2026-10-27T14:20:17-07:00** ([changelog](CHANGELOG.md#day-1--2026-10-27)). The [build log's opening disclosure](BUILD_LOG.md#build-log) states that no repository code pre-existed. Dates in [CHANGELOG.md](CHANGELOG.md) use America/Los_Angeles; some build-log “Day 2/Day 3” headings describe iterations, and [demo records](demo/BUILD_LOG.md) use UTC. History inspection is optional and is not needed by the offline verifier.

## File map

| Read this | To verify |
| --- | --- |
| [agent.py](src/claimcheck/agent.py), [tools.py](src/claimcheck/tools.py), [checks.py](src/claimcheck/checks.py) | Tool loop, evidence IDs and final program verdict |
| [providers.py](src/claimcheck/providers.py), [config.py](src/claimcheck/config.py) | Meta defaults, provider adapters and configurable model IDs; preserve Meta models for hackathon runtime |
| [budget.py](src/claimcheck/budget.py), [budget tests](tests/test_budget.py) | Reservation before calls and usage reconciliation |
| [prompts/](prompts/), [prompt registry](src/claimcheck/prompts.py), [recording tests](tests/test_eval_recording.py) | Prompt text/version hashes and recording |
| [eval/v2/](eval/v2/), [independent gold builder](eval/build_gold.py) | Frozen claim set, corrections and reference calculations |
| [v2 evidence](docs/evidence/eval-v2-2026-10-27/), [post-hoc evidence](docs/evidence/eval-v2-2026-10-28-r2-posthoc/) | Reports, manifests, per-claim results and traces |
| [replay tests](tests/test_live_replay.py), [trimmed SEC fixtures](tests/fixtures/) | Offline numeric/evidence regressions without API calls |
| [source policy](docs/DATA_SOURCES.md), [source registry](sources/registry.yaml), [data quality](docs/DATA_QUALITY.md) | Evidence tiers L1–L3 and source limitations |
| [figure registry](docs/figures/figures.json), [site data](docs/site/data/site.json) | Figure inputs and saved filing excerpts |
| [demo opening](demo/JUDGE_INTRO.md), [demo build log](demo/BUILD_LOG.md), [media credits](CREDITS.md#media-and-dependencies) | Disclosure, approval records and production-model provenance |
| [planned work](ROADMAP.md), [license](LICENSE), [credits](CREDITS.md) | Public product plans, MIT code license and SEC attribution |

Check local Markdown links with `python3 scripts/check_links.py`; `--external` additionally fetches HTTP links and separately reports blocked/unverifiable responses ([checker](scripts/check_links.py)). Do not use live evaluation, SEC fetches, synthesis or media-render commands to verify offline claims. Preserve recorded evidence, numbers, prompt files and product code when maintaining this documentation.

## Retain test records for reuse

Owner preference, 2026-10-30: retain all test-run evidence, including failed/partial paid attempts, so future work can reuse it. Follow [the test-record guide](docs/TEST_RECORDS.md): freeze cases and budgets before paid execution; retain input/source hashes, parameters, raw redacted responses, traces, verdicts, coverage, ledger costs and validation logs. Do not overwrite previous runs or select only successes. Prefer offline replay or frozen-transcript rechecks when they answer the question. Explicitly label rechecks that do not retest OCR/ASR. Never commit credentials or private account balances.
