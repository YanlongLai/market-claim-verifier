# v010 source handoff

Five approved 480-square Wan B-roll clips now have deterministic PNG addressing in v3 motion.
[Proposed shot list and host commands](SHOTLIST-v4.md) cover all five placements, cached-voice retiming
and keyframes. Gate 1 remains pending. The proposed edit is **177.2611 s**, including an **11.3081 s**
unfilled DappGo News + Threads slot; narration changes: **none**. The implementation follows existing
scene/cue times; the proposed hold trims and unfilled thirteenth shot have not been applied to the film.

[Generation records](prompts/broll/README.md) preserve both complete prompt sets, unmodified clip receipts,
parameters, seeds, reference hashes and model revision. The extraction step conservatively discards four
tail frames (0.25 s) per clip, preserving 45 native 480×480 PNGs at 16 fps. Runtime holds only clean frame 44
until a beat-aligned exit. Panels are 600 px, with a 560 px opener for the full disclosure; subtitles retain
the bottom 200 px. The product is present on frame zero. Source/receipt hashes enter the runtime data and
therefore the existing motion-render cache identity.

## Verification

`UV_OFFLINE=1 sh scripts/verify.sh` passed in an isolated copy based on the committed preview data:
**929 product tests, 155 demo tests, 59 Node tests**; figure rebuild/check; all three site/explorer outputs
byte-identical; Markdown links/anchors; no model or SEC requests. New tests cover exact source-frame
boundaries, reverse seeks, every 30 fps film frame, product visibility, panel/text separation, subtitle
clearance, extraction/hash reuse and the proposed hold budget using retained voice measurements.

Local logs are retained under `demo/out/v010-*.log`. No paid attempt, synthesis, real B-roll extraction,
Chromium capture or film render was performed. Actual decoded appearance, DOM font geometry, stamp contact,
phone readability and narration perception still require Claude's host keyframes and Owner review.

The five pre-existing host outputs (`data.js`, `timing.json`, `keyframes.json`, `beats.json`, `cues.json`
under `demo/motion/v3/`) were preserved byte-for-byte and excluded from the source commit. Tests used the
committed versions of the first three and did not copy the two untracked host files.

## Local commit delivery

Direct staging was blocked when Git tried to create `index.lock` in the shared metadata outside the
writable workspace. The authorized fallback is `demo/out/v010-broll.bundle`, based on
`bd4aee434cd2c6bce6c6d1792bba2be91c18d3b8`,
with branch `demo/v010` and footer:

```text
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

To inspect/import that fallback on the host:

```sh
git bundle verify demo/out/v010-broll.bundle
git fetch demo/out/v010-broll.bundle refs/heads/demo/v010
git show --stat FETCH_HEAD
```

No push or upload occurred. Host rendering commands are in the [shot list](SHOTLIST-v4.md#host-commands-claude-not-executed-for-this-source-handoff).
