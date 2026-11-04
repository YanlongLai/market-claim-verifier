# Demo build log

Successful assembles are appended automatically. See runs/ for complete records.

## 2026-10-29 UTC — initial pipeline verification

The first real demo export is pending host execution. The attempted
`all --voice-fallback say` is recorded in `runs/attempt-20261029T001528328317Z.json`.
Breeze failed on its external Numba cache in this sandbox. Chromium also cannot launch here;
live browser access was denied. No export version has been consumed.

The two image_gen stills are complete at 1920×1080. The host-generated 190 s music bed is available.
The isolated synthetic media test passed at 1920×1080, 30 fps, H.264/AAC, 4.800 s,
−13.99 LUFS integrated and −10.56 dBTP. It is test evidence, not a demo export or capture.

## v001 — 2026-10-29T00:52:34.551585+00:00

Length: 130.567 s. Scenes >25% over budget: none.

Changed scene cache keys: s01-hook: render, visual, voice; s02-problem: render, visual, voice; s03-what: render, visual, voice; s04-extract: render, visual, voice; s05-verdicts: render, visual, voice; s06-filing: render, visual, voice; s07-how: render, visual, voice; s08-results: render, visual, voice; s09-chinese: render, visual, voice; s10-close: render, visual, voice.

Changed global cache keys: assembly_cache_key, music_cache_key.

Output: `/Users/yan/git/market-claim-verifier-demo/demo/out/demo-v001.mp4`; SHA-256 `8ea3f1c41fa9e31008dbadb47885670e9c878199bfee4b8941d5f8b5810ea1d4`.

## 2026-10-29 UTC — v001 review and method change (Claude, director)

v001 (130.6 s) built end to end on the host: Breeze-TTS-2 voice on MPS (~10× slower than real time), live-site
Playwright recordings, ACE-Step music bed, subtitles, −14 LUFS. Director's review: site recordings too small to
read; light site vs dark stills; s08 recorded the Chinese explorer under English narration; lower third collides
with subtitles. Owner review: the narrator sounds like a different person in each scene (voice design per clip).

Decision (Owner): switch to an HTML/CSS/JS frame-addressable motion timeline rendered by Playwright and assembled
by ffmpeg, cut to the music's beat; lock one narrator voice via voice-clone from one approved reference clip;
staged approval: shot list → voice → 3 key frames → 2 s motion test → full render → second-AI review.
Shot list: demo/SHOTLIST-v2.md. The v002 capture-fix run was stopped as superseded.

## 2026-10-29 UTC — voice locked (Owner)

Owner picked candidate B (Breeze-TTS-2 voice design, seed 2026) from three candidates (seeds 1234, 2026, 7) on the
same line and instruction. Locked as demo/assets/voice/narrator-ref.wav + narrator-ref.txt (+ receipt). Every scene
is now synthesized in voice-clone mode from this reference. Music beat grid measured: ~129 BPM (ACE-Step ignored
the 92 BPM prompt), uneven (drift up to 0.24 s), first beat at 9.45 s → motion snaps to detected beats
(demo/assets/beats-seed92.json).

## 2026-10-29 UTC — v2 gate 3 implementation (code + tests only)

Scope: demo/** on demo/pipeline; no commit/push. The Git remote is market-claim-verifier, absent from the
DappGo developer registry and repository catalog; workspace governance discovery is degraded/excluded for
this independent hackathon repository. No shared registry or other worktree files were changed.

Preserved storyboard-v1.yaml and its capture/assemble path. Rebuilt storyboard.yaml as the ten approved v2
shots with exact narration/direction. Added locked voice cloning (reference bytes + transcript + seed + text
in the cache identity), MFCC-mean voicecheck with optional librosa and a stdlib fallback, deterministic HTML
motion shots, file:// data inlining, host PNG renderer, three-keyframe / 2 s test / full-render commands, and
Python/Node plus synthetic-audio/media tests. `all`/`assemble` cannot accidentally render v2.

Timing decisions: first actual detected beat is 9.4041 s; do not use fitted first_beat_s=9.4549 or a 92 BPM
grid. Targets remain the initial layout; after voice, cuts use the detailed brief's first detected beat
>= narration end + 0.3 s, superseding the earlier shot-list bar-line wording. Default key frames retain
shot-relative progress after measured timing. No speech is shortened. The Chinese Meta compound claim
retains its actual FALSE verdict; only its claim amount converts to $62.3B. Its prose summary disagrees
with the program checks (amount contradicted, growth unchecked), so the screen makes no component-verification claim. The QR is precomputed locally and
independently decoded in tests. Number provenance and exact host commands are in README's v2 motion workflow.

No Chromium launch, real TTS synthesis, v2 PNG capture, motion-test video, or full v2 film was attempted.
Only tiny synthetic TEST media is encoded for verification. Owner gate 3 remains the next host review;
gates 4 and 5 must follow Owner approval of the preceding artifact. Existing v001 media/records are preserved.

## 2026-10-29 UTC — motion v2c preparation and tests

Implemented the Owner's brief-demo-motion-v2c.md within demo/** on demo/pipeline; no commit/push or full
video render. All ten cached clone-B clips are analysed with FFmpeg silencedetect (−35 dB, 0.12 s).
Pause-count mismatches use proportional character timing; generated motion/cues.json includes per-shot
methods, absolute cues and 35 phrase-addressed beat events. motion/cue-summary.md lists every event time.

Enlarged the equal m05 cards to 576×500 with 56 px companies / 80 px verdicts / 104 px values / 44 px periods;
broadened m03's bars/counters. Restored presentation holds instead of the 89.838 s narration-only timeline,
while allowing m04 to yield time for the narration-led Apple focus. The prepared presentation is 160.4266 s.
The eight-second push completes at 64.6877, so absolute t=65 still shows the approved Apple bars. The three
existing approved PNGs were inspected and preserved; fresh browser comparison is host work.

Added build.py review-frames: shot midpoints plus every cue event +0.3 s, with a validated completed index.
Ran its --prepare-only mode against the real caches: out/review-v2/plan.json contains 45 stills. No Chromium
or new review PNGs were produced here. Host commands and complete verification are in VERIFICATION.md.

Final checks: 72 Python tests passed (including 19 Node motion tests), plus 4 standalone Node capture tests.
Pytest log: demo/cache/pytest-v2c-verified-ElKR47/pytest.log. Tests use small synthetic media where needed;
those files are fixtures rather than demo exports. Separate host visual review remains pending.

## v002 — 2026-10-29T03:49:26.027927+00:00

Length: 160.433 s. Scenes >25% over budget: m05-verdicts (+39.1%).

Changed scene cache keys: m01-open: render, voice; m02-spread: render, voice; m03-baseline: render, voice; m04-extract: render, voice; m05-verdicts: render, voice; m06-proof: render, voice; m07-program: render, voice; m08-results: render, voice; m09-chinese: render, voice; m10-cta: render, voice; s08-results: removed; s05-verdicts: removed; s04-extract: removed; s09-chinese: removed; s10-close: removed; s01-hook: removed; s03-what: removed; s02-problem: removed; s07-how: removed; s06-filing: removed.

Changed global cache keys: assembly_cache_key.

Output: `/Users/yan/git/market-claim-verifier-demo/demo/out/demo-v002.mp4`; SHA-256 `0ab4a81dffcb0ec3f941b8f39d7bf5fc374b09873436731cb810ac916ceefb96`.

## 2026-10-29 UTC — v003 source revision, tests and subtitle evidence

Applied brief-demo-v003.md within demo/** on demo/pipeline. Full change mapping for AI2 #1–10 and
A–G, cue times and host commands: REVISION-v003.md. No new narration, commit/push or Chromium run.
All ten voice keys and scene starts still match v002; duration remains 160.4266 s.

Local verification: 76 Python tests and 25 standalone Node tests pass. Review preparation writes 49
current still times plus the full SRT under out/review-v3/. The host command will render raw and captioned
pairs and publish validated, hashed evidence only on completion. Existing v002 now has its matching
full SRT and 45 real captioned PNGs extracted from the unchanged MP4 under out/review-v2-captioned/.
These historical frames are subtitle evidence; the new v003 picture awaits Claude's host render/review.

Workspace discovery: the Git remote is YanlongLai/market-claim-verifier; it is absent from the DappGo
repository registry/catalog. AI001 governance is therefore not applied to this unrelated repository;
discovery is degraded to the supplied brief and workspace defaults. The pre-existing .gitignore edit
was preserved. No files outside demo/** were edited for this task.

## v003 — 2026-10-29T04:32:59.353111+00:00

Length: 160.433 s. Scenes >25% over budget: m05-verdicts (+39.1%).

Changed scene cache keys: m01-open: render; m02-spread: render; m03-baseline: render; m04-extract: render; m05-verdicts: render; m06-proof: render; m07-program: render; m08-results: render; m09-chinese: render; m10-cta: render.

Changed global cache keys: assembly_cache_key.

Output: `/Users/yan/git/market-claim-verifier-demo/demo/out/demo-v003.mp4`; SHA-256 `260ca9f951e3c7eee11d25844bfd6921335d63525f69dd8fa0cbf77df96f1a7b`.

## v004 — 2026-10-29T05:08:25.502588+00:00

Length: 160.433 s. Scenes >25% over budget: m05-verdicts (+39.1%).

Changed scene cache keys: m01-open: render; m02-spread: render; m03-baseline: render; m04-extract: render; m05-verdicts: render; m06-proof: render; m07-program: render; m08-results: render; m09-chinese: render; m10-cta: render.

Changed global cache keys: assembly_cache_key.

Output: `/Users/yan/git/market-claim-verifier-demo/demo/out/demo-v004.mp4`; SHA-256 `3c8c45b13aeda817f9992c061070255da71418c8042b2602d1a8586402d96c0f`.

## v005 — 2026-10-29T05:24:46.403109+00:00

Length: 160.433 s. Scenes >25% over budget: m05-verdicts (+39.1%).

Changed scene cache keys: m01-open: render; m02-spread: render; m03-baseline: render; m04-extract: render; m05-verdicts: render; m06-proof: render; m07-program: render; m08-results: render; m09-chinese: render; m10-cta: render.

Changed global cache keys: assembly_cache_key.

Output: `/Users/yan/git/market-claim-verifier-demo/demo/out/demo-v005.mp4`; SHA-256 `30bbf4335952960fcb1c2db918ef351d733c70f99205bf5c7534c65ebac2149a`.

## v006 — 2026-10-29T05:43:49.017526+00:00

Length: 160.433 s. Scenes >25% over budget: m05-verdicts (+39.1%).

Changed scene cache keys: m01-open: render; m02-spread: render; m03-baseline: render; m04-extract: render; m05-verdicts: render; m06-proof: render; m07-program: render; m08-results: render; m09-chinese: render; m10-cta: render.

Changed global cache keys: assembly_cache_key.

Output: `/Users/yan/git/market-claim-verifier/demo/out/demo-v006.mp4`; SHA-256 `30bbf4335952960fcb1c2db918ef351d733c70f99205bf5c7534c65ebac2149a`.

## 2026-10-29 UTC — media lost and rebuilt (incident)

Claude removed the demo worktree with `git worktree remove --force` after merging, which deleted the git-ignored
local media (demo/cache, demo/out, narrator-ref.wav). No backup existed. Everything was regenerated from the
recorded parameters: narrator reference (Breeze-TTS-2 voice design, seed 2026), music (ACE-Step seed 92), ten clone
narration clips, then render. Result v006 is byte-identical to v005 (SHA-256 30bbf433…2149a); voicecheck 0.8977
as before. Lesson: move or check ignored outputs before removing a worktree; never `--force` remove after builds.

## 2026-10-29 UTC — Owner approved the final demo video

demo-v006.mp4 (= v005, SHA-256 30bbf433…2149a, 160.4 s) approved by the Owner as the final hackathon demo video.
Not uploaded or posted anywhere yet; the Breeze-TTS-2 non-commercial licence note was given to the Owner before approval.

## 2026-10-29 — v007 gate 1 source proposal

Prepared SHOTLIST-v3.md, storyboard-v3.yaml and NARRATION-v007.txt on demo/v007. Target 178 s;
beat-snapped preview 178.1899 s. Kept the approved v006 entry, data and narration; the new timeline lives in
motion/v3/. Added the complete spoken opening disclosure over the visible product, the site's Hover H poses
and adapted pose/spotlight expressions, META guidance / Adobe non-GAAP release checks, the recorded self-made
screenshot and synthetic-audio EPS error, original v2 results with corrected-gold/development labels, honest
limits, and the new https://hackathon.dappgo.com/ URL/QR. Previous QR preserved as motion/qr-v006.json.

REVISION-v007.md lists three key-frame times per scene, evidence contracts and host commands. The locked Breeze
clone reference and measured music bed are reused. No TTS, Chromium, MPS, v007 frames, video render, upload or
post was run. This is a source proposal awaiting Owner shot-list approval, not a new video export or approval.
The explicit v007 brief authorizes a local source commit (or a bundle if Git metadata is read-only); no push.
The worktree's shared Git metadata rejected `index.lock` creation, so the local commit is delivered as
`demo/out/v007-source.bundle`, with the exact requested Claude Opus 5.5 co-author footer.

Validation: `UV_OFFLINE=1 sh scripts/verify.sh` passed: 817 product tests, 94 demo tests and 52 standalone
Node tests, figure rebuild/check, three byte-identical explorer/site outputs and Markdown links/anchors.
The final scene and documentation checks also pass. Actual host font geometry, voice/cue listening, final
duration/loudness and visual approval remain unclaimed; no v007 export version was consumed.

## v007 — 2026-10-30T04:11:52.349441+00:00

Length: 178.200 s. Scenes >25% over budget: none.

Changed scene cache keys: v301-disclosure: render, voice; v302-apple: render, voice; v303-extract: render, voice; v304-hover: render, voice; v305-proof: render, voice; v306-program: render, voice; v307-l4: render, voice; v308-screenshot: render, voice; v309-audio: render, voice; v310-results: render, voice; v311-limits: render, voice; v312-cta: render, voice; m08-results: removed; m02-spread: removed; m05-verdicts: removed; m03-baseline: removed; m04-extract: removed; m01-open: removed; m07-program: removed; m06-proof: removed; m10-cta: removed; m09-chinese: removed.

Changed global cache keys: assembly_cache_key, audio_master_cache_key.

Output: `/Users/yan/git/market-claim-verifier-video/demo/out/demo-v007.mp4`; SHA-256 `ccf1e25f17a946d32957e17254177fb00d16280427b1dc6d27087e0416bd33e3`.

## v008 — 2026-10-30T04:50:02.022385+00:00

Length: 178.200 s. Scenes >25% over budget: none.

Changed scene cache keys: v301-disclosure: render; v302-apple: render; v303-extract: render; v304-hover: render; v305-proof: render; v306-program: render; v307-l4: render; v308-screenshot: render; v309-audio: render; v310-results: render; v311-limits: render; v312-cta: render.

Changed global cache keys: assembly_cache_key.

Output: `/Users/yan/git/market-claim-verifier-video/demo/out/demo-v008.mp4`; SHA-256 `52b2a3fc211e1b00e33605e4c4ee5a342a0fb1ce37c7a5dbccd89f8ac78f862e`.

## v009 — 2026-10-30T05:14:05.061783+00:00

Length: 178.200 s. Scenes >25% over budget: none.

Changed scene cache keys: v301-disclosure: render; v302-apple: render; v303-extract: render; v304-hover: render; v305-proof: render; v306-program: render; v307-l4: render; v308-screenshot: render; v309-audio: render; v310-results: render; v311-limits: render; v312-cta: render.

Changed global cache keys: assembly_cache_key.

Output: `/Users/yan/git/market-claim-verifier-video/demo/out/demo-v009.mp4`; SHA-256 `5ef16ffdfc7ec5f4297485c3013690dd326465087d5e2d98fa1108331e4f551f`.

## 2026-10-30 UTC — Owner approved v009 as the current candidate (not final)

`demo/out/demo-v009.mp4` (v007 shot list after both independent AI2 review rounds): 178.200 s, 1920×1080 30 fps,
integrated −14.17 LUFS, true peak −1.27 dBTP, SHA-256 prefix `5ef16ffdfc7ec5f4`. Round 1 (overall FAIL, six fixes)
and round 2 (five fixed; limits-card border collision) reports are in the local review folders; the remaining
collision was fixed in `2f0bbf2` and checked on the v009 review frame. The narrator audio is Breeze-TTS-2 output
(research/non-commercial licence) and the film is not committed; host-measured timing files remain local outputs.

The Owner later said v009 is not the final version and asked not to upload yet; further improvements are planned before the 2026-11-04 deadline.

## 2026-11-02 — v010 real-world reserve and Apple trace source handoff

Applied the Owner-approved SHOTLIST-v4 hold targets to storyboard-v3.yaml: 13 scenes, 177.2611 s,
including v311b-realworld at 155.7130–167.0211 s. Original narration, locked voice/music and result
qualifiers remain unchanged. Added an offline real-world compiler and committed pending snapshot,
per-source renderer, separately labeled frozen-text recheck pages, numeric/provenance checks, and a
real Apple request/tool/E1 cost/latency ribbon inside Hover's existing narration lead. No real-world-*
records exist here yet; compilation fails clearly, and host voice/film preparation refuses pending data.

A separate committed preview lets offline tests exercise the new scene without changing the five local
host timing outputs. Source tests preserve the historical v007 storyboard and replay retained voice
lengths plus a synthetic ten-second new line. Keyframe plans include all recorded ribbon steps and
compiled real-world pages. The full verifier now includes the v3 Node suite explicitly.

Test attempts/logs and host-file hash receipt are retained under docs/evidence/demo-v010/. Standard
verification passed 929 product tests, 171 demo tests and 83 Node tests, figure rebuild/check, three
byte-identical data outputs and Markdown links. A subsequent unindexed-recheck regression brought the
final demo suite to 172 passing tests; final source-copy verification is recorded separately there.
An initial disconnected dependency bootstrap failed on a missing locked wheel; that attempt is retained.

Direct staging could not create the shared Git index.lock outside the writable workspace. The authorized
fallback is an isolated local commit/bundle with the requested Claude Opus 5.5 co-author footer. No host
voice synthesis, frame capture, film render, push or upload was performed. REVISION-v010.md has the
one-line voice, timing, keyframe and eventual render commands; actual evidence/voice/visual review remains
pending. This is source work, not a new film export or publication approval.

Final source-copy verification: `UV_OFFLINE=1 sh scripts/verify.sh` passed 929 product tests,
172 demo tests, all 83 Node tests and every rebuild/link gate. The isolated copy used committed base
v3 timing/data/keyframes and had no untracked host beats/cues or narration cache. All five original
host output hashes still matched at delivery. Full log: docs/evidence/demo-v010/verify-03-committed-preview.log.

## v011 — 2026-11-03T10:37:39.707288+00:00

Length: 177.267 s. Scenes >25% over budget: none.

Changed scene cache keys: v301-disclosure: render; v302-apple: render; v303-extract: render; v304-hover: render; v305-proof: render; v306-program: render; v307-l4: render; v308-screenshot: render; v309-audio: render; v310-results: render; v311-limits: render; v311b-realworld: render; v312-cta: render.

Changed global cache keys: assembly_cache_key.

Output: `/Users/yan/git/market-claim-verifier-video/demo/out/demo-v011.mp4`; SHA-256 `0d4c5d3365c311c9ae4897aa49a0cd6b04beaa55ce81a41535c8325d53fdf0a2`.

Review: v010 (177.267 s, SHA-256 prefix `f018f2514d48684e`, entry lost when the working tree was reset to an imported commit) received AI2 verdict NOT a ship-candidate (0 blockers, 2 majors, 3 minors; review kept locally in `demo/out/review-v010/`). All five were fixed in `1c1210a7`. v011 AI2 re-review: **ship-candidate, 0 blockers, 0 majors, 2 minors** (N4 aggregate label size 48 → 56 px; N5 opinion narration starts ~1.05 s before its card). Loudness −14.1 LUFS, true peak −1.1 dBTP. **Current candidate (not final); not uploaded; awaiting Owner review.**

## v012 — 2026-11-03T16:07:20.794643+00:00

Length: 177.267 s. Scenes >25% over budget: none.

Changed scene cache keys: v301-disclosure: render; v302-apple: render; v303-extract: render; v304-hover: render; v305-proof: render; v306-program: render; v307-l4: render; v308-screenshot: render; v309-audio: render; v310-results: render; v311-limits: render; v311b-realworld: render; v312-cta: render.

Changed global cache keys: assembly_cache_key, audio_master_cache_key.

Output: `/Users/yan/git/market-claim-verifier-video/demo/out/demo-v012.mp4`; SHA-256 `b4b0296a362f26cd19c388e3bf7a247b5f9128aa78f875e83081450f0e6affd5`.

Review: v012 AI2 re-review (`1677f61a` fixes): **ship-candidate, 0 blockers, 0 majors, 0 minors**; N4 labels now 56 px, N5 opinion clause starts on the opinion reveal (22.766 s). Loudness −14.1 LUFS, true peak −1.1 dBTP. **Current candidate (not final, 480 B-roll); not uploaded; awaiting Owner review.**

## v014 — 2026-11-04T03:25:41.097141+00:00

Length: 178.000 s. Scenes >25% over budget: none.

Changed scene cache keys: v401: render; v402: render; v403: render; v404: render; v405: render; v406: render; v407: render; v408: render; v409: render.

Changed global cache keys: assembly_cache_key.

Output: `/Users/yan/git/market-claim-verifier-video/demo/out/demo-v014.mp4`; SHA-256 `25e1a816208f8cf5b718c9a788c7e5ec3d2d6c1b859e4fbbbfc3d36e780b6c79`.

## v015 — 2026-11-04T07:36:33.451155+00:00

Length: 178.000 s. Scenes >25% over budget: none.

Changed scene cache keys: v401: render; v402: render; v403: render; v404: render; v405: render; v406: render, voice; v407: render; v408: render; v409: render.

Changed global cache keys: assembly_cache_key, audio_master_cache_key.

Output: `/Users/yan/git/market-claim-verifier-video/demo/out/demo-v015.mp4`; SHA-256 `720c20848cdbc16d0e39866ed977cfb3ba761da6f884c5edee829852f80fa9c5`.

## v017 — 2026-11-04T10:30:13.831902+00:00

Length: 178.000 s. Scenes >25% over budget: none.

Changed scene cache keys: v500: render; v501: render; v502: render; v503: render; v504: render; v505: render; v506: render; v507: render; v508: render; v509: render.

Changed global cache keys: assembly_cache_key, audio_master_cache_key.

Output: `/Users/yan/git/market-claim-verifier-video/demo/out/demo-v017.mp4`; SHA-256 `cac073dfdfbc08b3ccd6bd30e643e5a0d479af8ff4486e2a5cedee4053a7b4f3`.

## v018 — 2026-11-04T12:38:41.740366+00:00

Length: 178.000 s. Scenes >25% over budget: none.

Changed scene cache keys: v500: render, voice; v501: render, voice; v502: render, voice; v503: render, voice; v504: render, voice; v505: render, voice; v506: render, voice; v507: render, voice; v508: render, voice; v509: render, voice.

Changed global cache keys: assembly_cache_key, audio_master_cache_key.

Output: `/Users/yan/git/market-claim-verifier-video/demo/out/demo-v018.mp4`; SHA-256 `e55c4e148d9992a5971e93e1873cee0c1b6e28e5baeaf342327d5710a3122a49`.

## v019 — 2026-11-04T14:59:52.408547+00:00

Length: 178.000 s. Scenes >25% over budget: none.

Changed scene cache keys: v500: render; v501: render; v502: render; v503: render; v504: render; v505: render; v506: render; v507: render; v508: render; v509: render.

Changed global cache keys: assembly_cache_key, audio_master_cache_key.

Output: `/Users/yan/git/market-claim-verifier-video/demo/out/demo-v019.mp4`; SHA-256 `3056f8233df40f8869ed424f49b76423d020a37870ce55316adc78cae498f401`.

## v020 — 2026-11-04T16:18:15.089943+00:00

Length: 178.000 s. Scenes >25% over budget: none.

Changed scene cache keys: v500: render; v501: render; v502: render; v503: render; v504: render; v505: render, voice; v506: render; v507: render; v508: render; v509: render.

Changed global cache keys: assembly_cache_key, audio_master_cache_key.

Output: `/Users/yan/git/market-claim-verifier-video/demo/out/demo-v020.mp4`; SHA-256 `16166f167f7b6ece0f1a34d2373c31e1bdb9bca91f13a29366c0f0fb245a9c15`.

## v021 — 2026-11-04T16:26:45.207840+00:00

Length: 178.000 s. Scenes >25% over budget: none.

Changed scene cache keys: v500: render; v501: render; v502: render; v503: render; v504: render; v505: render; v506: render; v507: render; v508: render; v509: render.

Changed global cache keys: assembly_cache_key.

Output: `/Users/yan/git/market-claim-verifier-video/demo/out/demo-v021.mp4`; SHA-256 `163972485d8157083948833b35e833d259368a26fef9f36114c78c6a224eec81`.

## v022 — 2026-11-04T17:49:36.920531+00:00

Length: 178.000 s. Scenes >25% over budget: none.

Changed scene cache keys: v500: render; v501: render; v502: render; v503: render; v504: render; v505: render; v506: render, voice; v507: render; v508: render; v509: render.

Changed global cache keys: assembly_cache_key, audio_master_cache_key.

Output: `/Users/yan/git/market-claim-verifier-video/demo/out/demo-v022.mp4`; SHA-256 `1dc5a48a33704eeb48f339f3436b9e7a0676ca33bda5b5edfe3a86e6bcc1fba8`.

## 2026-11-04 — v5 round 7: readable, source-bound terminal replays

Retained the host v022 take and every underlying source. Both terminal windows now
use five 30 px monospace rows at 36 px pitch, with 30 px source/replay labels inside
the header. The online replay starts with the recorded request event, retains the
whole-request stopwatch, and groups the six actual program checks. Its cue clock
reads the first real tool call and verdict directly from the captured log.

The local recording has twelve selected event rows, including all five condensed
tool call/result pairs and each claim verdict. It plays at 3x above the separately
labelled saved OCR/ASR and scale evidence throughout the batch block. The final
receipt summary holds from 129.433 s to the 138 s block boundary. The opening local
ledger row requires command typing and timestamped progress; the later receipt is
recorded separately. The full command remains in metadata and the omitted --out
path is explicitly disclosed in the picture.

Synthesized only the whole-request clock explanation and "Four tool calls" with
the locked local Breeze voice; all other voice units are reused. The clock cue
keeps its original start. Count annotations, focused source rows, a declared hold
of the original verdict frame, a larger illustrative-scenario label, helper-text
spacing and the SEC-to-trace handoff address the supplied AI2 findings. Actual
browser audits and offline regressions now verify the named log events as well as
geometry. The supplied review, source hashes, failed attempts and measurements
are retained in [round-7 records](prep/v5/r7/README.md).

Headless Chromium could not launch in this workspace. The v022 MP4 and earlier
review remain historical; no r7 encoded-picture or listening pass is claimed.
The [host completion commands](REVIEW-v5.md#host-completion) render from the same
take and sources without recording another request.

## v023 — 2026-11-04T19:05:15.287301+00:00

Length: 178.000 s. Scenes >25% over budget: none.

Changed scene cache keys: v500: render; v501: render; v502: render; v503: render; v504: render; v505: render, voice; v506: render; v507: render; v508: render; v509: render.

Changed global cache keys: assembly_cache_key, audio_master_cache_key.

Output: `/Users/yan/git/market-claim-verifier-video/demo/out/demo-v023.mp4`; SHA-256 `4490351abb290f782a7ed5e5b997e49dff86efc27f068ba0724acd556c6ec902`.

## v024 — 2026-11-04T19:34:34.701549+00:00

Length: 178.000 s. Scenes >25% over budget: none.

Changed scene cache keys: v500: render; v501: render; v502: render; v503: render; v504: render; v505: render; v506: render; v507: render; v508: render; v509: render, voice.

Changed global cache keys: assembly_cache_key, audio_master_cache_key.

Output: `/Users/yan/git/market-claim-verifier-video/demo/out/demo-v024.mp4`; SHA-256 `a6d91a5d7d3394f2f53b736708c76bb416cad029a6cd384baea7ec80223ed045`.

## v025 — 2026-11-04T20:09:59.956381+00:00

Length: 178.000 s. Scenes >25% over budget: none.

Changed scene cache keys: v500: render; v501: render; v502: render; v503: render; v504: render; v505: render; v506: render; v507: render; v508: render; v509: render.

Changed global cache keys: assembly_cache_key.

Output: `/Users/yan/git/market-claim-verifier-video/demo/out/demo-v025.mp4`; SHA-256 `e8119e30520edb5d6983e417f8bbfdce1eb179e657090bc3d9bc3a13a579c3cc`.
