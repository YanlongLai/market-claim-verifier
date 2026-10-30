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
