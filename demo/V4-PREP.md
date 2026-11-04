The r3 v4 timeline is **178.000 seconds**. Beat 1 is **0:00–0:09 (9 s)** and beat 2 is **0:09–0:26 (17 s)**. All later cuts remain **26, 40, 56, 72, 122, 146, 162, 178 s**. Narration text, subtitles, voice parameters and music are unchanged. All nine host voice cues now exist and fit. Real site takes remain pending; v406/v409 are still explicit placeholders until the host recorder replaces them with validated assets.

The [storyboard](storyboard-v4.yaml) retains the `build.py` version-2 motion contract, the v3 Breeze clone/reference/seed and the seed-92 music settings. [Narration](NARRATION-v4.txt) follows DESIGN-final.md §4; subtitle cues are bounded by three lines of 42 characters. The old opening did not disclose DappGo's pre-existing status, so v4 uses the director's exact opening. Its October 27–November 4 line is locked director copy, not a new attestation that this preparation ran through November 4. The future live scene's price/speed language is also planned copy: a retained live receipt must support it when recorded. [Director source hashes and section](prep/v4/director-source.json).

Beat 7 uses **78 Baseten/post Threads items**, including unsuccessful and unchecked items. The measured median is **6.764814 s/post**, and the batch's first-start-to-last-finish time is **874.614749 s (14.5769 min)**. The narration rounds these to **6.8 seconds** and **1,000 posts ≈ 1.9 hours sequentially at that median**. This is a median-based projection, not measured throughput. News, Threads and eval-v2 timings, source hashes and formulas are in [scale-v4.json](data/scale-v4.json); [the compiler](scale_v4.py) rebuilds them. News and Threads had three concurrent provider comparison workers, with recorded envelopes of 85.19 and 211.18 minutes. Their workloads mix agent/post/media paths across models, so there is **no defensible same-model parallel figure for 1,000 posts**. Benchmark claim latency is kept separate from post latency. The eval manifest's resumed-invocation wall time is not presented as the whole evaluation.

Beat 4 has a real **16.000 s, 1920×1080, 30 fps** terminal recording: [MP4](assets/terminal-v4/beat4.mp4), [asciicast](assets/terminal-v4/beat4.cast), [receipt](assets/terminal-v4/beat4.json). A real `zsh` subprocess attached to a PTY reads the per-claim files and corrected gold: **74/357 (20.7%) → 323/357 (90.5%)**, then **240/266 (90.2%) held out**. The full-set development/corrected-gold disclosure and **recorded 2026-10-27 (America/Los_Angeles)** label stay visible. [Replay implementation](replay_v4.py).

Beat 7 has a real **24.000 s, 1920×1080, 30 fps** terminal recording: [MP4](assets/terminal-v4/beat7.mp4), [asciicast](assets/terminal-v4/beat7.cast), [receipt](assets/terminal-v4/beat7.json). It streams recorded T03 extraction, model-selected SEC calls and all claim verdicts, a saved batch table, then `fair-multimodal-v1` **META-webp / Muse OCR** and **MSFT-wav / Muse Voice Transcribe** examples. The product CLI has no offline inference replay flag, so this uses the requested saved-trace fallback. Playback is editorial, with original timestamps shown; it is not a fresh execution or a runtime measurement. Frozen shared preprocessing, text reuse, synthetic fixture status and no OCR/ASR retest are explicit. A [source snapshot](assets/terminal-v4/source-snapshots.json) preserves the exact scale JSON used before later provenance-only additions. Both clips use **Menlo 32 px**, dark theme, with no scaling down. `agg` renders the real asciicast, and FFmpeg pads it to 1920×1080. [Renderer provenance](prep/v4/terminal-renderer.json) and [agg documentation](https://docs.asciinema.org/manual/agg/usage/).

Beat 5 has a [1920×1080 SVG](assets/architecture-v4.svg) with **56–72 px** text. The [v4 motion system](motion/v4/index.html) reveals its five nodes and four arrows over 14 seconds. [Compiler](motion_v4.py), [timing](motion/v4/timing.json), [preview subtitles](motion/v4/subtitles.srt). Source timing is fixed to the director's cuts. Caption rendering uses the existing two-line system, within the three-line maximum. Recorded videos are explicitly sought and awaited before screenshots. No file under `demo/motion/v3` was written. The pre-existing local changes there remain untouched.

The r2 preparation left the new Wan clips **pending host generation**. [Prompts, parameters and attempts](prompts/broll/prompts-r4.json) preserve the approved manifest's Wan2.2-TI2V-5B model/revision, 480×480, 49 frames / 16 fps, 20 steps, guidance 5, MPS bfloat16, model offload, native SDPA, float32 tiled VAE and 256 tokens. Both three-second accents have conditioning PNGs and seeds 11/29; these drawings are abstract shapes, not evidence. That preflight reported MPS built but unavailable and loaded no model. R3 does not generate or audit the pre-existing local v4 b-roll output. The approved five clips remain available and unchanged. [Host generator wrapper](broll_v4.py) retains raw engine receipts and every failed/partial attempt, skips already hash-verified successful outputs on a resumed run, and copies only three-second 480-test accents into the repo.

The earlier sandbox Breeze attempt failed in the read-only Numba/librosa cache. Its [jobs](prep/v4/breeze-jobs.json), [engine log](prep/v4/breeze-full-engine.log) and failure are retained in [voice status](prep/v4/voice-status.json). A later host synthesis produced all nine cues. The [r3 audit](prep/v4/voice-timing-r3.json) reads retained receipts and WAV frame counts, checks audio/receipt hashes and narration identity, and writes nothing under `demo/cache/voice`. With the **0.300 s** pad, all cues fit; **no further neighbouring-scene reallocation is needed**. The director's r3 decision supersedes the first cut in the original spec snapshot.

| Cue | Measured voice | Voice + pad | Scene |
| --- | ---: | ---: | ---: |
| v401 | 8.240 s | 8.540 s | 9.000 s |
| v402 | 10.640 s | 10.940 s | 17.000 s |
| v403 | 7.440 s | 7.740 s | 14.000 s |
| v404 | 12.240 s | 12.540 s | 16.000 s |
| v405 | 13.840 s | 14.140 s | 16.000 s |
| v406 | 20.640 s | 20.940 s | 50.000 s |
| v407 | 16.800 s | 17.100 s | 24.000 s |
| v408 | 12.800 s | 13.100 s | 16.000 s |
| v409 | 4.880 s | 5.180 s | 16.000 s |

The committed motion files remain a **target-duration preview**. Host preparation consumes measured voice receipts and keeps exact cuts; speech is never sped up or cut. No new synthesis is needed. [Protected-file baseline](prep/v4/r3-baseline.json) covers the pre-existing v3/voice/broll state.

The existing bed is **189.939229 s**; the offset plus film needs **187.4041 s**. It has **2.535129 s spare**, so no new music was generated. [Music receipt](prep/v4/music-v4.json).

The [recorder](record_v4.py) and [Playwright worker](record_v4.mjs) make **at most one live check per invocation**, with no automatic retry; both takes use that result. The server independently caps requests at one. It proxies only `/api/budget` and `/api/check` to `https://hackathon.dappgo.com`, with that Origin and JSON Content-Type, without redirects or browser cookies. Request bodies are never logged. The production $3/day gate remains authoritative.

`demo/v4` at r2 predates the simplified site, so the recorder serves a temporary snapshot of **committed main**, retaining the site commit, archive and page/script/style/example hashes. It never merges over local work. The native result heading shows the model ID, while the form names Baseten separately; the current site does **not** display the exact combined `meta-models/muse-spark-open-1026 · Baseten` line or a special receipt tooltip. Capture shows the actual ID/tool calls and hovers the native cost/seconds text without inserting product copy.

Capture uses **1920×1080, deviceScaleFactor 1, CSS zoom 125%**, cursor hidden except a click indicator, and small mouse-wheel steps (60 px every 50 ms; each tool call holds 0.8 s). Beat 6 holds 2.5 s on verdict, 4 s on corrected draft and 3 s on evidence, shows every tool call, then hovers the receipt. These actions must complete within the first 48 s, allowing startup variance in the scene's first 50 s. Its continuous WebM also retains the subsequent result scene. Beat 9 is a continuous tail: corrected draft and the SEC link together, then the page's native footer, with no new overlay; the footer must arrive by 11.5 s to fit both views in the first 16 s. WebMs are retained; `/opt/homebrew/bin/ffmpeg` creates **1920×1080, 30 fps** MP4s. Duration, dimensions, frame rate and hashes are checked before both placeholders are replaced atomically. The storyboard uses each asset's first exact scene-duration seconds. Missing/short/altered takes block host review/keyframes/render.

The password is read at runtime from `LIVE_CHECK_PASSWORD_FILE` and typed only into the local masked field. It is excluded from URLs, subprocess arguments and receipts. No screenshots, HARs, browser traces, storage exports or request-body logs are written. Result receipts recursively strip password/credential fields, secret echoes, budgets and balances. Failed/partial attempts and video remain available; timestamped attempts are not overwritten.

The live receipt must support the unchanged **“About a cent. Under ten seconds.”** narration. Main's historical saved viral-post result is **$0.062084 / 38.400 s**, not evidence of a new live check; the one-claim saved example cannot stand in for the viral post. A new result outside the locked price/speed copy is retained for director review and is not wired for export. Narration is never rewritten, and no second take is automatic.

**No real take was made in this session:** both required environment variables are unset, and no usable Playwright installation was found. Run on the host from `/Users/yan/git/market-claim-verifier-video`, using an existing package plus its Chromium installation and a private file containing only the password:

```sh
export PLAYWRIGHT_MODULE="/absolute/path/to/node_modules/playwright"
export LIVE_CHECK_PASSWORD_FILE="/absolute/path/to/existing-private-password-file"
export UV_CACHE_DIR="${TMPDIR:-/tmp}/claimcheck-verify-uv-cache"

uv run --project demo python demo/record_v4.py --preflight
uv run --project demo python demo/record_v4.py --port 8765 --site-ref main
uv run --project demo python demo/record_v4.py --check
uv run --project demo python demo/motion_v4.py
```

The recorder starts/stops its own server at **http://127.0.0.1:8765/**. Choose another `--port` if occupied. It uses the same handler as `scripts/serve_site.py --docs-root <temporary-main-docs> --port 8765 --proxy-api https://hackathon.dappgo.com --max-checks 1`; do not start a competing server. Outputs live under `demo/cache/live-takes/v4/`: `beat6-<UTC timestamp>.webm`, `beat9-<UTC timestamp>.webm`, matching `.mp4` and redacted `.json` receipts, run/config/session records and the pre-wiring storyboard snapshot. No password-file path is stored in receipts. `--check` is offline; `--preflight` opens no product page and makes no API request.

If Playwright is missing, install the existing isolated host version once:

```sh
# The renderer requires an existing Playwright 1.64.x + Chromium installation.
# If missing, install this isolated local copy once:
npm install --prefix demo/cache/playwright-v4 --no-audit --no-fund 'playwright@~1.64.0'
demo/cache/playwright-v4/node_modules/.bin/playwright install chromium
export PLAYWRIGHT_MODULE="$PWD/demo/cache/playwright-v4/node_modules/playwright"

```

These are **HOST steps, listed only; not run in this session**:

```sh
uv run --project demo python demo/build.py review-frames --storyboard demo/storyboard-v4.yaml --prepare-only --out demo/out/v4-r3-review-plan
uv run --project demo python demo/build.py keyframes --storyboard demo/storyboard-v4.yaml --out demo/out/v4-r3-keyframes
uv run --project demo python demo/build.py render --storyboard demo/storyboard-v4.yaml
```

Checks, with no inference, SEC fetching or full film render:

```sh
uv run --project demo python demo/realworld.py --check
uv run --project demo python demo/scale_v4.py --check
uv run --project demo python demo/motion_v4.py --check
bash scripts/verify.sh
```

`motion_v4.py --check` checks the committed target preview without changing host voice timing or requiring ignored live media. The strict media gate is `record_v4.py --check` and host review/keyframe/render preparation. Rebuild the preview before checking it if host preparation has written measured timing. [Earlier validation](prep/v4/VALIDATION.md), [r3 validation](prep/v4/R3-VALIDATION.md).

This session's Git metadata is read-only. R3 is committed from accepted r2 (`2e1d610d`) in a temporary repository with the requested `Co-Authored-By` footer, and delivered in **demo/out/v4-r3.bundle**. Nothing was pushed. Import without disturbing the current modified worktree:

```sh
git bundle verify demo/out/v4-r3.bundle
git fetch demo/out/v4-r3.bundle refs/heads/demo/v4:refs/heads/demo/v4-r3
git log --oneline demo/v4..demo/v4-r3
git diff demo/v4...demo/v4-r3
```

The current worktree already contains these edits, so do not check out or cherry-pick over them blindly. The imported branch is the committed, reviewable copy. [Initial branch/HEAD and protected v3 hashes](prep/v4/baseline.json).
