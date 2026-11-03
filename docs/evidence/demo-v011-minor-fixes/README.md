# v011 AI2 N4/N5 source verification

Offline source fixes on `demo/v010`, base `6ca4544d`. The local review is
`demo/out/review-v011/AI2-REVIEW.md`.
[Change details and host commands](../../../demo/REVISION-v011-minors.md).

## Retained attempts

Each numbered JSON records the command, UTC start, elapsed time, exit code and
matching log. Earlier attempts are retained, including failures.

- [01 real-world check](01-realworld.log): passed; compiled evidence unchanged.
- [02 preview regeneration](02-preview.log) and [03 preview check](03-preview-check.log):
  passed; 13 scenes and 177.2611 s.
- [04 Python regressions](04-python-regressions.log): 104 passed.
- [05 first Node attempt](05-node-regressions.log): failed on the synthetic fixture's
  stale `1 run failures` expectation; updated to the allowed `1 failed runs` wording.
- [06 Node regressions](06-node-regressions.log): all 28 passed, including every
  frame's safe box/font checks, aggregate semantics, 56 px floor and the exact
  75/77/138-frame extraction holds.
- [07 browser still attempt](07-browser-stills.log): could not run; Playwright 1.64
  is absent. No package/browser download was attempted. Computer Use subsequently
  reported browser access unavailable and rejected Google Chrome access with
  `Computer Use was not approved to use Google Chrome`.
- [08 repository verification](08-offline-verification.log): `bash scripts/verify.sh`;
  1,010 product tests, 206 demo tests and 97 Node tests passed, along with figure
  rebuild/check, three byte-identical explorer/site outputs, the byte-identical
  wild findings rebuild, local links and the unchanged-source/no-network gate.
- [09 offline font/box audit](09-font-layout.log): 74 checks on the actual motion.js
  boxes at 157 s and 165 s, using local SFNS/Arial font advances and CSS line height.
  Labels are at least 14 px at 480 px playback width, no measured text exceeds its
  box, and boxes stay within x=64..1856 and y=64..816. The reproducible audit scripts
  and [measured rows](layout-audit.json) are retained. This is not a browser screenshot
  or certification of encoded glyphs/caption placement; that visual check stays pending.
- [10 Markdown links](10-markdown-links.log): passed after adding this handoff.
- [11 final preview check](11-final-preview-check.log): passed after verification;
  the committed preview remains reproducible without touching host outputs.
- [12 isolated Python](12-isolated-regressions.log) and [13 isolated Node](13-isolated-node.log):
  104 and 28 passed in a separate checkout of the delivered source. It has the
  committed base host data/timing/keyframes, no untracked beats/cues, and no voice
  or media cache. Raw failed-attempt logs retain their original TAP whitespace;
  the source whitespace check excludes those logs.

The Python timing regression replays the retained clip lengths. The original
7.12 s extraction clip is placed 1.05 s later without changing its cache identity
or duration. Its opinion sentence clock becomes 22.770308257 s and its SRT start
22.766 s, against a 22.766667 s encoded reveal. It asserts the cue starts no earlier
than reveal minus 0.1 s, checks the real mixer delay/filter plan without invoking
FFmpeg, preserves every scene cut, and requires the 177.2611 s total duration.
No licensed audio was decoded or newly synthesized for these checks; this does
not claim a fresh listening, ASR or word-alignment test.

[Task-entry state](source-before.json) and [host preservation](host-preservation.json)
record all five original host-file hashes, including the three pre-existing local
modifications. All five match after the checks. No model calls, SEC fetches, voice
synthesis, film render, push or upload occurred.
