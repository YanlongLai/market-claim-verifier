# Demo verification and host handoff

**Current status: v003 source fixes and subtitle evidence are complete; see
[REVISION-v003.md](REVISION-v003.md) for all ten AI2 fixes, A–G, checks and host commands.**
The original v002 capture-fix
checks below are historical; that method was superseded by SHOTLIST-v2.md. Use storyboard-v1.yaml to
reproduce legacy captures, and the v2 README workflow for the current task.

The director's brief is `/Users/yan/note/dappgo/flow-atlas/hackathon-briefs/brief-demo-v002.md`.
Changes are confined to `demo/**` on `demo/pipeline`. No commit or push was made, and the existing
`.gitignore` modification was preserved. Chromium was not launched, as the brief requires host captures.

## Completed checks

```sh
UV_CACHE_DIR="$PWD/demo/cache/uv" UV_OFFLINE=1 uv run --project demo pytest demo/tests --basetemp=demo/cache/pytest-v002 -q
```

Result: **30 passed**. This includes four Node shot-contract tests, invoked by pytest without a browser.

- The storyboard's single `capture:` block specifies `viewport: [1280, 720]`, `scale: 1.5`, and
  `color_scheme: dark`. Tests pass that configuration through capture cache identity, job JSON, and the
  actual JavaScript Playwright options factory. Changing each setting updates the capture key and browser
  options while preserving the voice key. Invalid dimensions, scale, and colour scheme fail early.
- Chart scene tests check the English site routes, opposite bar emphasis, s02's static hold, and s08's
  68% hold followed by the post-hoc rerun scroll. Missing bars and framing that reaches the subtitle band fail.
- A real FFmpeg integration test encodes H.264/AAC at 1920×1080, 30 fps, with transitions, looped/ducked
  music, and loudness verification. Pixel checks on the encoded result confirm the mint label at the
  top-left 64 px margin, bottom-centred subtitles, and a clear former lower-third position.
  The frame at `cache/pytest-v002/test_real_h264_aac_1080p_cross0/burned-captions.png` was also visually
  inspected. This isolated synthetic fixture is test evidence.
- The existing normalization, cache corruption, timing/subtitle, versioning, full-export, audio, and 180 s
  guard tests continue to pass.
- Python compilation and Node syntax checks pass for the demo sources and tests.

## Cache and preservation checks against v001

The baseline is `runs/20261029T005234558907Z-v001.json` and `out/demo-v001.mp4` (130.566667 s).

- All ten narration strings and the voice configuration match the pre-edit baseline exactly.
- All ten voice keys match v001, and their current hashed cache receipts validate.
- The two stills and the rendered end card retain their v001 visual cache keys; those caches validate.
- All seven capture keys change, so the host command below re-records each site scene without `--force`.
- The `media.py` renderer hash changes, so assemble re-renders the scene overlays.
- The still image files, end-card HTML/renderer, browser launcher, original v001 MP4, and `.gitignore`
  match their pre-edit hashes. All tracked repository files match their pre-edit contents.
- NVIDIA continues to be selected by the existing `$60.9 billion` text fix.
- Narration timing, the Ken Burns effect, and the end-card design are preserved.

## Host continuation

Run exactly this from the host:

```sh
cd /Users/yan/git/market-claim-verifier-demo
export UV_CACHE_DIR="$PWD/demo/cache/uv"
export UV_OFFLINE=1
uv run --project demo python demo/build.py capture --storyboard demo/storyboard-v1.yaml && uv run --project demo python demo/build.py assemble --storyboard demo/storyboard-v1.yaml
```

Only capture and assemble are needed. Existing narration, music, stills, and the rendered end card are
reused. With v001 still the latest export, the next successful assemble produces `out/demo-v002.mp4`,
the matching SRT, and a new run record.

The [README scene table](README.md#where-each-asset-comes-from) lists every scene's change. On the host,
review all seven dark captures at the larger text scale; verify that s05 frames all three claim cards and
s06 shows the full filing table row and highlighted value. Confirm s02 boxes the memory-only bars and s08
boxes the green English bars before reaching the post-hoc rerun. Check the top-left labels and bottom
subtitles through transitions.

Live DOM/composition verification and the v002 export remain host work. No v002 footage or export was
created in this sandbox.

## v2 motion — gate 3 code verification

Brief: `/Users/yan/note/dappgo/flow-atlas/hackathon-briefs/brief-demo-motion-v2.md`.
Scope remains `demo/**`, branch `demo/pipeline`; no commit or push. The pre-existing root `.gitignore`
change and v001 media/run records are preserved. No Chromium launch, new real narration, v2 keyframe,
motion test, or full v2 video was attempted. Frame rendering remains host work at the Owner's gate 3.

```sh
demo/.venv/bin/python -m pytest demo/tests --basetemp=demo/cache/pytest-v2-final -q
node --test demo/tests/motion.test.mjs demo/tests/capture.test.mjs
```

Result: **49 Python tests passed; 13 Node tests passed** (the Node contracts are also invoked by pytest).
No skipped tests. The isolated synthetic media test really burns captions, checks subtitle glyphs in the
bottom band, trims/mixes narration and music from an absolute window, and verifies 1080p 30 fps H.264/AAC
and −14 LUFS. Those fixture videos are test evidence only.

The source checks cover all ten exact narration strings/director notes; clone reference-sensitive cache
keys and actual Breeze CLI flags; first-eligible-detected-beat timing in Python and Node; default keyframe
retiming; the first-flip 2 s motiontest range and matching audio/music offsets; deterministic seeks in
arbitrary order; easing and beat events; type sizes and palette contrast constants; original AMZN table
cells; evaluation aggregates; and independent decoding of the precomputed QR. The Chinese card retains the
report's FALSE verdict without trusting its prose summary's inconsistent component-verification claim.

`motion/timing.json` currently records the **160 s target layout**, because v2 clone narration has not
been synthesized. `motion/beats.json` and `data.js` are prepared for offline file:// viewing. The locked
music offset is the first actual detected beat, 9.4041 s. After voice, the builder replaces targets with
measured narration cuts on the first detected beat >= voice end + 0.3 s, and remaps default keyframes to
m01/m05/m10. The earlier bar-line wording is superseded by the detailed motion brief's explicit cut rule.

On the host, run `uv run --project demo python demo/build.py keyframes` for the initial three PNGs.
Review actual layout, legibility, and source framing there; code/font constants cannot prove browser
layout. Voicecheck and audio listening happen after clone synthesis. Motiontest and full render remain
later approval gates. Exact commands and the per-shot number/source map are in README's
[v2 motion workflow](README.md#v2-motion-workflow).

## Motion v2c — narration cues and review frames

Source: `/Users/yan/note/dappgo/flow-atlas/hackathon-briefs/brief-demo-motion-v2c.md`.
Scope: `demo/**` on the existing `demo/pipeline` worktree, revision `aa606c6` plus local demo files.
No commit, push, full film render, Chromium launch, voice synthesis or edit outside `demo/` was performed.
The pre-existing `.gitignore` change is preserved. Registry discovery still excludes this independent
hackathon repository, as recorded in the gate-3 entry in BUILD_LOG.md; no shared claim/knowledge files
were changed. This entry supersedes earlier timing and pending-voice status above.

The brief supplies the goal, scope and acceptance criteria without further intake. The implementation
uses measured cached audio, deterministic character fallback, phrase-addressed events and presentation
holds. The disproof checks are missing/ambiguous phrases, an event on the wrong beat, speech truncated by
a cut, failure to finish Apple's push by 65, and an incomplete review index. Those cases fail explicitly.

Verified commands:

```sh
demo/.venv/bin/python demo/build.py review-frames --prepare-only
demo/.venv/bin/python -m pytest demo/tests --basetemp=demo/cache/pytest-v2c-verified-ElKR47/work -q
node --test demo/tests/capture.test.mjs
```

Result: **72 Python tests passed**, including the **19-test Node motion suite**; the separate capture
suite passed **4 tests**. No skips. The saved pytest output is
`demo/cache/pytest-v2c-verified-ElKR47/pytest.log`. Integration tests invoke real FFmpeg for silence detection,
caption/audio/mastering checks on synthetic fixtures; they do not render a demo film or launch a browser.

| Acceptance | Status and evidence |
| --- | --- |
| Per-clip pause analysis and fallback | Implemented and tested in `motion_cues.py` / `tests/test_motion_cues.py`; all ten real cached clips analysed with −35 dB / 0.12 s. `motion/cues.json` records absolute sentence cues, method, audio hash, detector settings and event phrase timing. Eight clips require proportional fallback; m01/m09 use silence. |
| Beat snapping follows narration | All 35 declared events are tested against the first detected beat at or after cue start − 0.10 s. Browser logic consumes those exact events. Rejection follows “rejects”; provider rows follow “Meta Model API” / “Baseten and Fireworks”. See `motion/cue-summary.md` for every shot's method and event times. |
| Large m05 cards | Equal 576×500 cards at x=64/672/1280, y=338, gaps=32. Names 56 px, verdicts 80 px, values 104 px, periods 44 px. Initial cards cover about 68% of the main safe area (x=64..1856, y=174..880), before the headline. Geometry/type and visibility are checked by the Node suite. |
| Other shot density | Reviewed the specified content regions: m01 and m10 retain their approved broad compositions; m02 fills a 1456×470 post plus share icons; m04 spans 1792×484 in two panels; m06 spans a 1792×410 table plus links; m07 spans two full-width lanes; m08 spans three full-width result rows; m09 pairs a 1000×480 post with a 726 px conversion column. m03 was the sparse chart: bars grow from 320 to 432 px wide and counters from 80 to 104 px. Its maximum-zoom geometry test verifies 64 px side margins, headline clearance, ≥4 px counter/bar gaps, ≥12 px before its footnote and no subtitle-band intrusion. Browser/font QA remains host work. |
| Approved looks at 3/65/155 | Inspected the three existing approved PNGs. Opening and CTA drawing functions retain their composition. The m05 completed focus retains x=240, y=350, 1440×520, exact labels, coral quarter and grey full-year bars in the real 102.466/416.161 ratio. Actual prepared-timeline seek checks at 3/65/155 pass. Fresh pixel comparison remains host work. |
| Half-speed focus and fixed 65-second Apple frame | m04 yields its target hold so m05 starts at 44.1876 s. Company flips: Amazon 47.9027, NVIDIA 50.7124, Apple 53.0808. Spoken FALSE event 56.4477; push 56.6877–64.6877. The completed bars remain visible through the cut at 73.3983. All speech plays unaccelerated. The full presentation is 160.4266 s and all cuts remain detected beats with ≥0.3 s narration padding. |
| Review stills command | `build.py review-frames` requests only stills, every shot midpoint plus every cue event +0.3 s. Real-cache preparation produced `out/review-v2/plan.json`: **45 frames**. Unit tests verify PNG/time/shot receipt checks, index rows and failures; stale completed indices are invalidated. `index.json` is written only after real PNGs validate. |

Within-sentence word timing uses character offsets inside the mapped sentence, not forced alignment.
m02's values, m03's 21% and m09's 億 are not literally spoken; their semantic cue choices are documented
in README. Narration, clone-B cache keys, reference voice, music/beat grid, source numbers and original
approved PNGs are preserved.

Host continuation (no full render is requested by this task):

```sh
uv run --project demo python demo/build.py keyframes --out demo/out/keyframes-v2c
uv run --project demo python demo/build.py review-frames
```

The first command redraws exactly 3/65/155 into a new directory for comparison with the approved looks
in `out/keyframes-v2/`. The second writes the
45 PNGs and `out/review-v2/index.json` for the separate second-AI reviewer. The current sandbox output
contains the plan and cue analysis, not fresh review PNGs or a completed index. Producer checks above
are not independent visual approval.

## Demo v003 — source verification and subtitle handoff

`REVISION-v003.md` is the current full mapping of the v003 brief. Tests pass: 76 Python tests,
plus 25 standalone Node tests. All ten cached narrator keys and scene starts match v002.
No narration was changed or regenerated; the prepared duration stays 160.4266 s.

Current browser-free preparation:

```sh
demo/.venv/bin/python demo/build.py review-frames --prepare-only
```

Prepared `out/review-v3/plan.json` has 49 still times, including exact Apple correction onsets
56.887282540 / 58.926647619 and settled cue samples. Its `subtitles.srt` covers all narration.
No completed v003 index/evidence receipt is published before the host renders actual PNGs.
The host review command also generates captioned PNGs using the film's 56 px caption compositor.

The missing historical subtitle evidence is now available: `out/demo-v002.srt` and
`out/review-v2-captioned/` with 45 frames extracted from the existing v002 MP4, index and hashed receipt.
These are actual v002 picture/captions, not v003 fixes. Current picture/phone checks and the v003 render
remain Claude's host work under the supplied brief. No commit or push was made.
