# v010 source handoff

The Owner-approved [shot list v4](SHOTLIST-v4.md) is applied to the [storyboard](storyboard-v3.yaml):
**13 scenes, 177.2611 seconds**, including `v311b-realworld` at **155.7130–167.0211 s**. The twelve original
paragraphs, locked clone voice, music offset and evidence qualifiers remain unchanged. Retained original
voice lengths plus a synthetic ten-second new line fit these targets without speed changes.

The new shot reads [realworld.json](data/realworld.json), produced by the offline
[compiler](realworld.py). It supports per-source tested items, program-check coverage, claim verdict
counts, cost per item, p50 item latency, and up to three retained paraphrases. Threads URLs display only
`@handle`. Original results and post-hoc frozen-text rechecks receive separate pages/counts.
[The input contract](data/REALWORLD.md) specifies the evidence index and narration template.

**No `docs/evidence/real-world-*` run exists in this checkout.** The committed snapshot is an explicit
pending state with no measurements or narration. The compiler fails clearly; voice synthesis and film
preparation refuse pending evidence. Populating it requires retained results, not guesses. This source
handoff does not claim that a real-world test ran.

Hover now includes a compact animated ribbon during its existing narration lead, after point-glow exits.
[The trace compiler](agent_trace.py) reads the same Apple post-check trace as the product: `lookup_fact`
→ `E1`, `sub_claims`, `final_verdict`, with recorded per-request costs/latencies and run totals. Playback
compresses model-request time into the lead; no tool execution duration is invented. Seeks rebuild each
state synchronously. Host keyframes include every recorded step and every compiled real-world page.

[The committed preview](motion/v3/preview-data.js) is separate from host `data.js`, `timing.json`,
`keyframes.json`, `beats.json` and `cues.json`. Tests use the preview, and the page uses it when host
revision/source hashes are stale. The five existing host outputs remain uncommitted and byte-identical
to their pre-task copies. The preview generator never requires audio, a browser, or a film render.

The five [approved B-roll records](prompts/broll/README.md), frame addressing, clean-tail trims, product
visibility and bottom 200-pixel subtitle zone remain in force. Physical text geometry, decoded PNGs,
stamp contact, phone readability and the new voice line require host review. No synthesis, keyframe
capture, B-roll extraction, film render, push or upload was performed during this implementation.

## Host commands

Run from the repository root. First preserve the host outputs in a new directory:

```sh
mkdir -p demo/out
v010_backup_dir=$(mktemp -d demo/out/v010-before-realworld.XXXXXX)
cp demo/motion/v3/data.js demo/motion/v3/timing.json demo/motion/v3/keyframes.json \
  demo/motion/v3/beats.json demo/motion/v3/cues.json "$v010_backup_dir/"
```

After retaining the real-world run records and their `demo-shot.json` indices, compile/check the snapshot
and refresh the committed target preview. These commands fail until the evidence is available:

```sh
uv run --project demo python demo/realworld.py
uv run --project demo python demo/realworld.py --check
uv run --project demo python demo/motion_v3.py --preview-only
uv run --project demo python demo/motion_v3.py --preview-only --check
```

Synthesize **only the new line**, using the storyboard's locked Breeze clone/reference/seed. Do not use
`--force`, a fallback voice, or an all-scenes synthesis. The compiler fills the narration template; the
host must measure its WAV at ≤10 s. The following timing preparation uses all twelve cached original
clips plus that new clip and never synthesizes missing clips:

```sh
uv run --project demo python demo/build.py --storyboard demo/storyboard-v3.yaml \
  voice --only v311b-realworld
uv run --project demo python demo/build.py --storyboard demo/storyboard-v3.yaml \
  review-frames --prepare-only --out demo/out/review-v010-plan
```

Review the refreshed local timing/cues/SRT and keep the five host outputs uncommitted. Preparation rejects
an over-ten-second new line, an altered reserve or total >180 s. It never speeds up speech. Generate the
approved B-roll cache if needed, then keyframes (including all trace steps and real-world pages):

```sh
uv run --project demo python demo/broll.py check
uv run --project demo python demo/broll.py extract --ffmpeg /opt/homebrew/bin/ffmpeg
uv run --project demo python demo/build.py --storyboard demo/storyboard-v3.yaml \
  keyframes --out demo/out/keyframes-v010-scenes
uv run --project demo python demo/build.py --storyboard demo/storyboard-v3.yaml \
  review-frames --out demo/out/review-v010-captioned
```

Use `BrollLayer.windows(MOTION_DATA)` in the v3 page to recompute insert samples after retiming; review
start, start+1.4, play_end−0.01 and exit boundaries. Old v009 absolute samples are stale. After the applicable
Owner keyframe/motion review gates, the host commands for two-second motion checks and eventual film are:

```sh
uv run --project demo python demo/build.py --storyboard demo/storyboard-v3.yaml \
  motiontest --shot v304-hover --len 2 --out demo/out/motiontest-v010-hover.mp4
uv run --project demo python demo/build.py --storyboard demo/storyboard-v3.yaml \
  motiontest --shot v311b-realworld --len 2 --out demo/out/motiontest-v010-realworld.mp4
uv run --project demo python demo/build.py --storyboard demo/storyboard-v3.yaml render
```

The full render uses the next versioned `demo/out/demo-vNNN.mp4`; no `--out` or overwrite is used.
Independent review and publication remain later steps. These are handoff commands, not actions executed here.

## Verification and delivery

Test records, including failed/partial preparation attempts, are retained in
[the v010 verification record](../docs/evidence/demo-v010/README.md). The verifier now explicitly includes
the v3 Node suite alongside the other standalone suites. It runs in a disposable copy with network guards.
The final disconnected verification passed **929 product tests, 172 demo tests and 83 Node tests**,
figure rebuild/check, three byte-identical data outputs and local links, using committed base timing
files rather than the host's uncommitted outputs.
The [historical storyboard fixture](tests/fixtures/storyboard-v007.yaml) preserves existing v007 audio/cue
regressions; active v010 timing, provenance, error paths, page zones and deterministic ribbon tests are separate.

Local commit footer: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. If shared Git metadata is
unwritable, delivery uses `demo/out/v010-realworld-trace.bundle`; its base and commit are reported with
the result. The host can inspect and import it without changing the local timing files:

```sh
git bundle verify demo/out/v010-realworld-trace.bundle
git fetch demo/out/v010-realworld-trace.bundle refs/heads/demo/v010
git show --stat FETCH_HEAD
git merge --ff-only FETCH_HEAD
```
