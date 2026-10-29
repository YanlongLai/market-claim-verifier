# Reproducible demo video

The default `storyboard.yaml` is now v2. Start with [v2 motion workflow](#v2-motion-workflow) below.
The following original pipeline notes and commands describe **v1**, preserved in `storyboard-v1.yaml`.
The old v002 capture-fix proposal is historical and was superseded by the approved v2 motion plan.

`storyboard-v1.yaml` is the original director's source of truth for narration, visuals, captions, and scene budgets.
Edit it, run the build from the repository root, review `demo/out/`, and iterate:

```sh
uv run --project demo python demo/build.py all --storyboard demo/storyboard-v1.yaml
# Draft voice only if Breeze is missing:
uv run --project demo python demo/build.py all --storyboard demo/storyboard-v1.yaml --voice-fallback say
```

Every successful assemble exports the next `demo/out/demo-vNNN.mp4` and matching `.srt`, writes a complete
`demo/runs/<UTC timestamp>-vNNN.json`, and appends to `BUILD_LOG.md`. Nothing commits or pushes automatically.
The first successful export is v001. Failed `all`/`assemble` attempts get `runs/attempt-<UTC>.json` and do not
consume a version number. An unchanged assemble reuses its master but records a new export version.

The deliverable is **1920×1080, 30 fps, H.264 + AAC, at most 180 seconds**. The storyboard's 170 seconds is a
soft target. Each scene lasts measured narration + 0.6 seconds, rounded up to a video frame; adjacent scenes
overlap by 0.4 seconds. Consequently total length is the sum of scene lengths minus 0.4 × (scene count − 1).
The overlap consumes silent padding, never speech. A scene more than 25% over its target gets a warning.
An export over three minutes is rejected; narration is never automatically rewritten or accelerated.

## Local tools and offline dependencies

Python dependencies are exact pins in `pyproject.toml` and `uv.lock`. Python 3.14 is selected by `.python-version`
(the project supports 3.12–3.14). FFmpeg and ffprobe are `/opt/homebrew/bin/ffmpeg` and `/opt/homebrew/bin/ffprobe`.
Use Node with an already-installed Playwright **1.64.x** and its Chromium. The scripts look in normal Node
resolution, `/opt/homebrew/lib/node_modules`, and existing `~/.npm/_npx/*/node_modules/playwright` directories.
For another existing installation, set `PLAYWRIGHT_MODULE` to the absolute Playwright package directory.
The builder never runs npm/npx installation or downloads Chromium.

This working copy has a self-contained dependency cache populated from local wheels. To keep uv entirely
offline and its writes inside the demo scope:

```sh
export UV_CACHE_DIR="$PWD/demo/cache/uv"
export UV_OFFLINE=1
uv sync --project demo --locked
node demo/capture/browser.mjs --version
uv run --project demo pytest demo/tests --basetemp=demo/cache/pytest -q
```

Prepare any missing tools/dependencies on the host before building in a restricted environment. Browser
contexts allow only `https://yanlonglai.github.io/market-claim-verifier/…`, block service workers and WebSockets,
and abort other requests. Filing links are displayed but never followed to sec.gov. The card uses local HTML
and system fonts. This run made no package/model downloads.

## Stages and iteration

```sh
uv run --project demo python demo/build.py voice --storyboard demo/storyboard-v1.yaml
uv run --project demo python demo/build.py capture --storyboard demo/storyboard-v1.yaml
uv run --project demo python demo/build.py images --storyboard demo/storyboard-v1.yaml
uv run --project demo python demo/build.py card --storyboard demo/storyboard-v1.yaml
uv run --project demo python demo/build.py assemble --storyboard demo/storyboard-v1.yaml

# Rebuild the changed scene, reusing the other nine, then export the full video:
uv run --project demo python demo/build.py all --storyboard demo/storyboard-v1.yaml --only s05-verdicts
# Re-record after the public page changes even if the storyboard did not:
uv run --project demo python demo/build.py capture --storyboard demo/storyboard-v1.yaml --only s05-verdicts --force
uv run --project demo python demo/build.py assemble --storyboard demo/storyboard-v1.yaml
```

### Apply the v002 director's fixes on the host

The reviewed v001 export and run record are already present. From this worktree, run only capture and
assemble; narration, music, generated stills, and the rendered end card reuse their existing caches:

```sh
cd /Users/yan/git/market-claim-verifier-demo
export UV_CACHE_DIR="$PWD/demo/cache/uv"
export UV_OFFLINE=1
uv run --project demo python demo/build.py capture --storyboard demo/storyboard-v1.yaml && uv run --project demo python demo/build.py assemble --storyboard demo/storyboard-v1.yaml
```

No `--force`, `voice`, or `card` run is needed. Capture settings and script changes invalidate all seven
capture keys; the caption layout change invalidates the rendered scene clips during assemble. With v001
as the latest successful export, this writes `demo/out/demo-v002.mp4`, its SRT, and a new run record.
Chromium must run on the host. Review all seven captures there, particularly the three cards in s05 and the
highlighted table row in s06. The framing checks fail if the chart, cards, or filing table extend into the
caption bands. The full scene changes are listed below.

`all` executes voice → capture → card → assemble; assembly validates the externally supplied stills.
Every command accepts `--force`, `--only SCENE` (repeat or comma-separate), `--voice-fallback say`, and
`--storyboard PATH`. `--only` limits generation/rendering. Assembly always includes the entire storyboard and
requires current caches for unselected scenes; make an initial full build first. Keep the same voice settings
between stage commands. `--force all --only …` refreshes that scene and the final mix. A process lock prevents
two CLI builds from writing the same caches or export number concurrently.

Cache directories are `cache/<stage>/<scene-id>/<content hash>/`. Receipts hash the actual artifacts as well
as their inputs, so damaged files are regenerated. Voice keys are SHA-256 of a canonical JSON tuple containing
the actual engine, instruction, seed, and narration with whitespace collapsed. Each scene has independent
voice, visual, and rendered-scene keys. Music has its own global key. Editing one scene leaves other scenes'
voice/capture/render caches reusable; only the final joined master must change. Previous hash directories
remain available if an edit is reverted. Use `--force capture` after a live site update: live page contents are
not fetched merely to check cache validity.

## Where each asset comes from

| Scene | Visual source | Target |
| --- | --- | ---: |
| s01-hook | Existing image_gen still and 1.00→1.06 zoom; label moves to top-left | 14 s |
| s02-problem | English site chart; all providers framed together; subtle boxes on the without-tools bars (44% / 21% / 20%) | 15 s |
| s03-what | Dark, enlarged live hero; title framed below the top label | 10 s |
| s04-extract | Dark, enlarged English post, highlighted claims, skipped opinions | 22 s |
| s05-verdicts | Amazon, NVIDIA, Tesla cards fill the content width together; emphasis follows narration, ending on false Tesla | 20 s |
| s06-filing | Wider Amazon filing modal; larger table text; full table row and highlighted value, then original-filing links | 20 s |
| s07-how | Existing image_gen diagram and 1.00→1.06 zoom; label moves to top-left | 24 s |
| s08-results | English site's same chart; subtle boxes on green SEC lookup + checks bars (83% / 90% / 90%); hold for 68% of the scene, then ease to the post-hoc rerun block | 24 s |
| s09-chinese | Dark, enlarged capture; click 中文, select Chinese example, show Chinese units | 9 s |
| s10-close | Existing end-card HTML, cached PNG, and 1.00→1.06 zoom; label moves to top-left | 14 s |

The seven capture scripts share `capture/common.mjs`. The storyboard is the only source for CSS viewport,
device scale, and colour scheme:

```yaml
capture:
  viewport: [1280, 720]
  scale: 1.5
  color_scheme: dark
```

These values flow into capture cache keys, job JSON, Playwright context options, and browser receipts.
`recordVideo.size` follows the storyboard's delivery `resolution: [1920, 1080]`; the smaller CSS viewport
gives approximately 1.5× text. Capture-only CSS fits the chart and three verdict cards between caption bands
and enlarges the filing modal; live claims, values, and chart data are preserved. Both chart scenes start in
English. Browser contexts use fresh English storage, network-idle waits, cubic eased scrolling, and a visible
mint cursor/click pulse. Page setup frames are excluded from the scene, then real
WebM footage is normalized to frame-exact WebM and H.264 MP4. Convenient copies are
`cache/capture/<id>.webm` and `<id>.mp4`. Receipts retain capture time, URL, focus, bar emphasis, viewport,
scale, colour scheme, video resolution, blocked requests, and tools.
Missing data/selectors or an unexpected Tesla verdict fail explicitly. Local source was used to prepare the
selectors; **live DOM and composition verification still require the host** as directed by the v002 brief.
No screenshots, local site copies, or synthetic frames are substituted for live captures.

## Regenerate the two stills

Use the built-in image_gen tool with `prompts/img/s01-hook.md` and `prompts/img/s07-how.md`, one request per
still. Preserve the exact visual intent and quoted words. Inspect every word; regenerate at most three total
attempts per scene if spelling is wrong. Save PNGs as `assets/img/<scene-id>.png`, exactly 1920×1080. The
`images` stage validates these assets; it never calls a generative model. Run `all --only SCENE` or `assemble`
after replacing an asset.

Both supplied stills were generated with the built-in tool, accepted on attempt one, and checked visually.
The tool returned 1672×941; FFmpeg's Lanczos scaler normalized them to the required 1920×1080. No text or
composition was redrawn. `assets/img/provenance.json` records prompt hashes, final image hashes, dimensions,
source output names, exact generation prompts, and the resolution normalization. The original prompt files
and storyboard narration/visual intent were not edited.

## Narration, music, and captions

Breeze is invoked once for the pending clips, reusing its loaded model:

```text
/Users/yan/ml-engines/breeze-tts/run.sh --device auto --jobs <jobs.json> --instruction <storyboard.voice.instruction> --seed <storyboard.voice.seed>
```

Jobs are `{id,text,out}` with absolute output paths under `cache/voice/`. Each `<out>.json` engine receipt is
read and preserved. Audio is validated, converted to 24 kHz mono WAV, and measured with ffprobe. Breeze's
installed `INSTALL.md` and `tts.py` define the batch interface. Its per-clip seed reset makes cached single-scene
regeneration independent of batch order. Missing Breeze fails unless `--voice-fallback say` was explicitly
provided. A runtime synthesis failure is reported; the fallback is not silently selected for such failures.

The draft fallback invokes macOS `say -v Samantha`, converts its AIFF output to 24 kHz mono WAV, and records
engine `macos-say`, `draft_only: true`. macOS say cannot honor Breeze's male voice instruction or seed; the
receipt says so. If the sandbox produces a zero-frame AIFF, the builder rejects it. For a deliberate Samantha
draft while Breeze is installed, explicitly set `voice.engine: say` in a separate storyboard and pass
`--storyboard demo/<draft-storyboard>.yaml`.

The music prompt is `prompts/music/bed.md`. Music is generated separately by Claude on the host, never by this
builder. The current host-generated `cache/music/bed-seed92.wav` is available. The exact ACE-Step regeneration
command, from the repository root, uses a fresh output name because the engine refuses to overwrite:

```sh
/Users/yan/git/number-rpg/audio/engines/ace-step/run.sh \
  --prompt 'minimal modern tech documentary underscore, soft electric piano, warm analog synth pad, light muted plucks, gentle kick on half-time, 92 bpm, D major, calm and confident, no drops, no vocals, instrumental' \
  --lyrics '[instrumental]' \
  --duration 190 --seed 92 --infer-steps 60 --guidance-scale 15 \
  --out "$PWD/demo/cache/music/bed-seed92-rerender.wav"
```

The wrapper pins its local checkpoint and uses MPS, float32, Euler/APG, with BF16 disabled. Follow the prompt's
notes when reviewing the result: it must sit under speech, without a lead melody in the voice band or sudden
swells. Set `music.path: demo/cache/music/bed-seed92.wav` in the storyboard to pin a bed; otherwise the newest
`cache/music/bed-*.wav` by modification time is selected and its SHA-256 is recorded. With no bed, the builder
announces that it is exporting narration only. It loops/trims music to length, applies `music.gain_db`, ducks
it with narration sidechain compression, and fades the bed out over the last two seconds. Two-pass loudnorm
targets −14 LUFS; the encoded AAC is then measured again and must be within 0.5 LU of that target with true
peak ≤ −1 dBTP. A true-peak margin accounts for AAC overshoot.

Subtitles preserve narration and are split into at most two lines of at most 42 characters. Their timing is
word-weighted within each measured voice clip; this is an estimate, so listen during review. Scene offsets
account for crossfades. Identical cues are burned in and exported as SRT. Pillow renders readable system-font
PNG panels because the supplied ffmpeg has no libass/drawtext filters; FFmpeg composites them. The scene
label (lower third) fades in/out at the top-left, 64 px from both edges. Subtitles stay bottom-centre,
66 px from the bottom, with white type, navy panels, and mint accents.

## Records, licences, and host completion

Run records include storyboard SHA-256; every scene's target, measured voice duration, frame-rounded final
duration, start, over-budget percentage, actual engine, and cache keys; all image/music/capture/audio hashes;
Python, ffmpeg/ffprobe, Playwright, Node and library versions; measured output format/loudness; output/SRT
paths and hashes; and cache changes against the previous successful run. `BUILD_LOG.md` summarizes the same
changes for humans. Keep runs, logs, assets, prompts, and scripts in source control. Cache/output media is
ignored, and `.gitignore` explicitly unignores `demo/runs/*.json` from the repository's general `runs/` rule.

Breeze-TTS-2 **weights are research / non-commercial**, under the BreezeBlue Research and Non-Commercial
License Agreement v1.1. Its source code is Apache-2.0; that does not grant commercial rights to its weights.
See `/Users/yan/ml-engines/breeze-tts/INSTALL.md` and `weights/LICENSE`. ACE-Step code and the installed
ACE-Step-v1-3.5B checkpoint are Apache-2.0. macOS Samantha is a system voice for draft review; its use remains
subject to the applicable Apple terms. The image files are outputs of the built-in image_gen tool; retain
their generation provenance.

The reviewed v001 is `out/demo-v001.mp4` (130.6 s), with run record
`runs/20261029T005234558907Z-v001.json`. The v002 source fixes are tested without launching Chromium here;
live capture, framing review, and the v002 export remain host work. Run the two-stage host command above,
listen for timing, and review the exported SRT. `VERIFICATION.md` records the current checks and host handoff.

## v2 motion workflow

Current revision: **demo v004**, implementing the three fixes in `brief-demo-v004.md`.
[REVISION-v004.md](REVISION-v004.md) records the proof-table geometry, shared subtitle timing,
headline spacing, passing checks and exact host commands. [REVISION-v003.md](REVISION-v003.md) is historical.
`SHOTLIST-v2.md` and `storyboard.yaml` contain the revised visuals and the unchanged ten narration lines.
All edits stay in `demo/**` on `demo/pipeline`; no commit or push. Claude renders and re-reviews on the host.
The v1 notes above are historical; `all` and `assemble` refuse the motion storyboard.

### Prepare and review

The existing `demo/.venv` contains the pinned Python dependencies. From this worktree's repository root:

```sh
demo/.venv/bin/python demo/build.py review-frames --prepare-only
```

This uses the ten cached clone-B clips, writes offline `motion/data.js`, timing, beats, cues,
`out/review-v4/plan.json` and a full-length `out/review-v4/subtitles.srt`. It never launches Chromium or TTS.
It invalidates completed index/evidence receipts so an older picture cannot appear current.

On the host, render the **49 review times**, including both exact Apple correction onsets:

```sh
demo/.venv/bin/python demo/build.py review-frames --out demo/out/review-v4
demo/.venv/bin/python demo/build.py keyframes --t 3 --t 65 --t 155 --out demo/out/keyframes-v4
```

After host rendering, `review-v4/` contains raw PNGs, matching `captioned/` PNGs, `subtitles.srt`, `plan.json`, `render.json`,
`index.json`, and a hashed `evidence.json`. Index rows record shot, time, cue, source file, captioned file
and active subtitle. Both stills and film use `motion_media.caption_canvas` and the same 30 fps caption
boundaries. The renderer measures real cell/text bounds, gutters, highlight coverage and headline spaces
before saving any frame; `render.json` includes the layout results. The index is written only after every
frame's time, shot and image validate. SRT and burn-in share `cues.json` sentence timings; long sentences
use character offsets, and wrapping never separates a motion cue phrase into different subtitle entries.

The original v002 already has subtitle evidence in ignored local outputs: full SRT (`out/demo-v002.srt`) and
45 actual captioned frames (`out/review-v2-captioned/index.json`), extracted from its MP4 rather than rebuilt
picture. These historical v002 outputs are not included in a clean clone; see the committed
[build record](BUILD_LOG.md). `review-v4/plan.json` is the current picture review request.

After the host reviews the revised frames, its motion-test/full-render commands remain:

```sh
demo/.venv/bin/python demo/build.py motiontest --shot m05 --len 2
demo/.venv/bin/python demo/build.py render
```

Full render creates the next versioned `out/demo-vNNN.mp4` / `.srt`, run record and build log. It keeps
1920×1080 / 30 fps / H.264 / AAC, hard cuts, ducked music, two-pass −14 LUFS mastering and a two-second fade.
The maximum remains 170 seconds. This source revision does not claim a new rendered film or visual approval.

### Narration, timing and motion

No voice regeneration is needed. The locked clone uses Breeze-TTS-2, seed 2026, `assets/voice/narrator-ref.wav`
and its exact transcript, with no instruction prompt. All ten current voice keys match the v002 run.
`voicecheck --threshold 0.85` remains available as an MFCC timbre screen; listening is part of host review.

The prepared timeline remains **160.4266 s**. Presentation holds preserve absolute keyframes 3 / 65 / 155;
m04 yields time for the eight-second Apple push. No speech is accelerated or overlapped. The first detected
music beat is **9.4041 s**; its subtraction makes video time zero. All cuts/events use measured beats from
`assets/beats-seed92.json`, without extrapolation, music looping or substituting fitted BPM metadata.

`motion_cues.py` analyses each cached clip with FFmpeg silence detection (−35 dB, 0.12 s). Sentence boundaries
use pauses only when their counts match; otherwise they use proportional character timing. Within-sentence
phrases use character offsets, so this is estimated alignment rather than forced word alignment. Each event
uses the first detected beat at or after cue start −0.10 s. `motion/cue-summary.md` records every event.

m02 shows coral $416B during “some are quietly wrong”. m05 changes to a fully populated Apple comparison
at FALSE, retaining both TRUE cards in a separate left column throughout the restrained eight-second push.
m08 reveals both 90.5% rows during “90.5 percent”. m09 converts 500 億 on “Chinese”, then shows the filed
amount and FALSE on “too”. Review times include event +0.3 s and exact Apple correction cue starts.

Open `motion/index.html` offline; `window.seek(t)` synchronously draws any second without a playback loop,
wall clock, random state, external fonts or network requests. Text is never scaled down during reveals;
bar growth and highlight sweeps carry motion while displayed data values remain accurate.

### Readability and evidence

Meaningful labels are at least **56 px**, body defaults to **64 px**, extraction/Chinese claims and result
providers use **72 px**, and financial values/highlighted numbers are at least **96 px**. Scene content
stays within x=64..1856 and above y=880. Captions are 56 px, at most two lines / 42 characters per line,
inside the bottom 200 px. The baseline note ends at y=866. Program/results boards occupy more than 60% of
the safe area. Nonessential copy/share decorations were removed instead of shrinking text.

Source text is HTML-decoded exactly once when product data loads, then tokenised before HTML escaping.
Quarter/year tokens remain together with real spaces; remaining literal entities are excluded from
numeric highlighting. No source report is edited.

| Shot | Values and pinned evidence |
| --- | --- |
| m01 / m02 / m04 | `data/demo-thread.json`, copied from `docs/evidence/posts-2026-10-28/demo-thread-baseten/report.json`: exact Amazon, NVIDIA, Apple quotes and an unjudged opinion. $416B abbreviates the incorrect $416.2B quarter claim. |
| m03 / m08 | `docs/evidence/eval-v2-2026-10-27/summary.json`, dev+test / 357 claims per system, cross-checked against `docs/site/data/site.json`. Meta 44→83%, Baseten 21→90.5%, Fireworks 20→90.5%. The badge “Up to +70.5 points” is the maximum difference between displayed scores (39 / 69.5 / 70.5), not an unqualified rounded +70. |
| m05 | Apple fiscal Q4 2025 $102.466B → $102.5B; full FY2025 $416.161B → $416.2B. Bars use the exact ratio 102.466 / 416.161. Only FALSE and the filed-quarter bar/value are coral. Amazon $143.083B supports $143.1B. NVIDIA $60.922B vs $26.974B supports more than double. |
| m06 | Three-month close-up: 2023 **143,083**, 2024 **158,877** USD millions, in fixed columns with 48 px gutters and 128 px right-aligned tabular values. Amber fills the complete 2023 cell. Nine-month values **404,824 / 450,167** remain in source data and the original `amzn-20240930.htm#f-212` filing link. |
| m07 | ±0.05B is the English report's actual number precision. E9 is the deliberately fake illustrative evidence ID; its rejection is visible at “rejects”. |
| m09 | Chinese report `docs/evidence/posts-2026-10-28/tw-social-post-meta/report.json`, claim **3**, KO: 「可口可樂 2024 年營收突破 500 億美元。」 500 億 = $50.0B; filed $47.061B = 470.6 億, displayed coral $47.1B. The filed amount is below the threshold, independently of rounding. |
| m10 | Visible live-demo URL and original QR both lead to `https://yanlonglai.github.io/market-claim-verifier/site/`. Explicit “Built during the Meta Global AI Developer Hackathon” line, Muse Spark / Meta open weights credits, and GitHub star CTA. |

`motion_data.py` hashes the pinned sources. The unchanged local QR matrix has a four-module quiet zone;
a separate Node test decodes its format/mask/data stream to verify the exact destination.

### Verification

```sh
demo/.venv/bin/python -m pytest demo/tests --basetemp=demo/cache/pytest-v004 -q
node --test demo/tests/motion.test.mjs demo/tests/layout.test.mjs demo/tests/capture.test.mjs
```

Tests cover exact shot-list/storyboard agreement, unchanged voice keys and full subtitle coverage,
entity-safe highlighting and period spacing, every Apple card position at 30 fps, complete correction
content at both spoken cues, readable type constants, safe-area/board geometry, cue visibility,
Coca-Cola source data, fixed proof-table gutters/highlight, single headline spaces, all 37 phrases in the
exported SRT, QR decoding, captioned review receipts, and synthetic FFmpeg caption/audio/mastering checks.
Current results: **83 Python tests and 41 standalone Node tests pass**. Actual DOM geometry checks run
inside the host renderer; phone readability and final visual approval remain host review.
