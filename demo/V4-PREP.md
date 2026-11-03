The v4 source timeline is **178.000 seconds** in the director's nine-beat order. It is preparation, with no live site recording and no completed v4 narration. The director records **v406: 50.000 s** and **v409: 16.000 s** later. Both scenes visibly identify themselves as placeholders.

The [storyboard](storyboard-v4.yaml) retains the `build.py` version-2 motion contract, the v3 Breeze clone/reference/seed and the seed-92 music settings. [Narration](NARRATION-v4.txt) follows DESIGN-final.md §4; subtitle cues are bounded by three lines of 42 characters. The old opening did not disclose DappGo's pre-existing status, so v4 uses the director's exact opening. Its October 27–November 4 line is locked director copy, not a new attestation that this preparation ran through November 4. The future live scene's price/speed language is also planned copy: a retained live receipt must support it when recorded. [Director source hashes and section](prep/v4/director-source.json).

Beat 7 uses **78 Baseten/post Threads items**, including unsuccessful and unchecked items. The measured median is **6.764814 s/post**, and the batch's first-start-to-last-finish time is **874.614749 s (14.5769 min)**. The narration rounds these to **6.8 seconds** and **1,000 posts ≈ 1.9 hours sequentially at that median**. This is a median-based projection, not measured throughput. News, Threads and eval-v2 timings, source hashes and formulas are in [scale-v4.json](data/scale-v4.json); [the compiler](scale_v4.py) rebuilds them. News and Threads had three concurrent provider comparison workers, with recorded envelopes of 85.19 and 211.18 minutes. Their workloads mix agent/post/media paths across models, so there is **no defensible same-model parallel figure for 1,000 posts**. Benchmark claim latency is kept separate from post latency. The eval manifest's resumed-invocation wall time is not presented as the whole evaluation.

Beat 4 has a real **16.000 s, 1920×1080, 30 fps** terminal recording: [MP4](assets/terminal-v4/beat4.mp4), [asciicast](assets/terminal-v4/beat4.cast), [receipt](assets/terminal-v4/beat4.json). A real `zsh` subprocess attached to a PTY reads the per-claim files and corrected gold: **74/357 (20.7%) → 323/357 (90.5%)**, then **240/266 (90.2%) held out**. The full-set development/corrected-gold disclosure and **recorded 2026-10-27 (America/Los_Angeles)** label stay visible. [Replay implementation](replay_v4.py).

Beat 7 has a real **24.000 s, 1920×1080, 30 fps** terminal recording: [MP4](assets/terminal-v4/beat7.mp4), [asciicast](assets/terminal-v4/beat7.cast), [receipt](assets/terminal-v4/beat7.json). It streams recorded T03 extraction, model-selected SEC calls and all claim verdicts, a saved batch table, then `fair-multimodal-v1` **META-webp / Muse OCR** and **MSFT-wav / Muse Voice Transcribe** examples. The product CLI has no offline inference replay flag, so this uses the requested saved-trace fallback. Playback is editorial, with original timestamps shown; it is not a fresh execution or a runtime measurement. Frozen shared preprocessing, text reuse, synthetic fixture status and no OCR/ASR retest are explicit. A [source snapshot](assets/terminal-v4/source-snapshots.json) preserves the exact scale JSON used before later provenance-only additions. Both clips use **Menlo 32 px**, dark theme, with no scaling down. `agg` renders the real asciicast, and FFmpeg pads it to 1920×1080. [Renderer provenance](prep/v4/terminal-renderer.json) and [agg documentation](https://docs.asciinema.org/manual/agg/usage/).

Beat 5 has a [1920×1080 SVG](assets/architecture-v4.svg) with **56–72 px** text. The [v4 motion system](motion/v4/index.html) reveals its five nodes and four arrows over 14 seconds. [Compiler](motion_v4.py), [timing](motion/v4/timing.json), [preview subtitles](motion/v4/subtitles.srt). Source timing is fixed to the director's cuts. Caption rendering uses the existing two-line system, within the three-line maximum. Recorded videos are explicitly sought and awaited before screenshots. No file under `demo/motion/v3` was written. The pre-existing local changes there remain untouched.

The new Wan clips are **pending host generation**. [Prompts, parameters and attempts](prompts/broll/prompts-r4.json) preserve the approved manifest's Wan2.2-TI2V-5B model/revision, 480×480, 49 frames / 16 fps, 20 steps, guidance 5, MPS bfloat16, model offload, native SDPA, float32 tiled VAE and 256 tokens. Both three-second accents have conditioning PNGs and seeds 11/29; these drawings are abstract shapes, not evidence. MPS is built but unavailable in this sandbox; the retained preflight loaded no model. The approved five clips remain available and unchanged. [Host generator wrapper](broll_v4.py) retains raw engine receipts and every failed/partial attempt, skips already hash-verified successful outputs on a resumed run, and copies only three-second 480-test accents into the repo.

The locked Breeze `build.py voice` request included all nine cues. It failed before synthesis in the engine's read-only Numba/librosa cache; no v4 cue was synthesized. [Jobs](prep/v4/breeze-jobs.json), [full engine log](prep/v4/breeze-full-engine.log), [voice status](prep/v4/voice-status.json). Chromium's architecture-only probe also failed because Playwright 1.64 was unavailable. No site capture was attempted. Exact command/exit/log receipts are retained under `demo/prep/v4`. Further synthesis and capture attempts stopped as requested. Voice durations remain **unmeasured**: the builder rejects a cue that exceeds its locked scene, and never cuts or speeds up speech. The director must resolve any measured overrun before export.

The existing bed is **189.939229 s**; the offset plus film needs **187.4041 s**. It has **2.535129 s spare**, so no new music was generated. [Music receipt](prep/v4/music-v4.json).

Run these commands on the host from `/Users/yan/git/market-claim-verifier-video`. They generate local media and render the architecture only; they do not record the site or call a provider/SEC API:

```sh
# The renderer requires an existing Playwright 1.64.x + Chromium installation.
# If missing, install this isolated local copy once:
npm install --prefix demo/cache/playwright-v4 --no-audit --no-fund 'playwright@~1.64.0'
demo/cache/playwright-v4/node_modules/.bin/playwright install chromium
export PLAYWRIGHT_MODULE="$PWD/demo/cache/playwright-v4/node_modules/playwright"

# Use the existing engine environments/models; do not run --prepare again.
uv run --project demo python demo/broll_v4.py --generate
uv run --project demo python demo/motion_v4.py
node demo/motion/render.mjs --entry v4/index.html --t 70 --out demo/out/v4-architecture-review
uv run --project demo python demo/build.py voice --storyboard demo/storyboard-v4.yaml
uv run --project demo python demo/build.py review-frames --storyboard demo/storyboard-v4.yaml --prepare-only --out demo/out/v4-review-plan
```

If the host also lacks SoX (the failed import printed that warning), install it with `brew install sox`. If it already has the required Playwright package, set `PLAYWRIGHT_MODULE` to that directory and omit the two installation commands. Host Breeze must be able to write its own engine cache; no reference audio, voice parameters or model code should change. `build.py voice` retains all synthesized clips even if the final timing gate finds an overrun. Keep the director cuts and resolve that overrun explicitly.

Checks, with no inference, SEC fetching or full film render:

```sh
uv run --project demo python demo/realworld.py --check
uv run --project demo python demo/scale_v4.py --check
uv run --project demo python demo/motion_v4.py --check
bash scripts/verify.sh
```

`motion_v4.py --check` checks the committed **unmeasured target preview**, without changing host voice timing. Rebuild the preview with `motion_v4.py` before that check if host preparation has written measured timing. [Validation record](prep/v4/VALIDATION.md).

Git ref/index writes are blocked here. The source changes are committed in order in a temporary Git repository; each commit has the requested `Co-Authored-By` footer. The verified `demo/out/v4-prep.bundle` contains only the v4 commit chain relative to the recorded base. Nothing was pushed. Review/import it without changing an existing branch:

```sh
git bundle verify demo/out/v4-prep.bundle
git fetch demo/out/v4-prep.bundle refs/heads/demo/v4:refs/heads/demo/v4-prepared
git log --oneline demo/v4..demo/v4-prepared
git diff demo/v4...demo/v4-prepared
```

The current worktree already contains these edits, so do not check out or cherry-pick over them blindly. The imported branch is the committed, reviewable copy. [Initial branch/HEAD and protected v3 hashes](prep/v4/baseline.json).
