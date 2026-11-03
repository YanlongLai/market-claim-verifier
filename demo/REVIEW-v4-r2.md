# Demo v4 — director review round 2

Prepared from `fbd657b9831a9fe7069bb4c0d44c28212c002894` on 2026-11-03.

[Terminal replay](replay_v4.py) now clears between ideas, uses 40 px Menlo,
and shows at most eight nonempty lines including the headline and footer.
Each block types its highlighted final line last. The six-row batch table
is the requested exception to three supporting items; its sixth row is the
retained N02 CLI failure. T03 is explicitly a three-of-five-claims excerpt.
Dollar amounts use compact B/M units with quoted precision, including
`$2.29B → $229M`. Receipts retain the source hashes and limits.

The single dim bottom line is exactly:

```text
Replay of saved run · recorded 2026-10-27 · no live calls
```

That director-requested date identifies the original evaluation. Beat 7's
Threads and media examples retain their own dates in the referenced source
records. Frozen synthetic OCR/ASR examples reuse saved preprocessing and text
verification; this work does not retest OCR or ASR. The thousand-post figure
is a one-worker projection at the saved median, not a measured batch.

| Clip | Encoded duration / frames | Final highlighted line |
| --- | --- | --- |
| [Beat 4](assets/terminal-v4/beat4.mp4) | 16.000 s / 480 | `240/266 held-out · 90.2%` |
| [Beat 7](assets/terminal-v4/beat7.mp4) | 24.000 s / 720 | `median 6.8 s/post · 1,000 posts ≈ 2 h, one worker` |

Both clips are 1920×1080, 30 fps. The full set of 40 review PNGs is listed in
`demo/out/v4-terminal-review/README.md`, with hashes and exact sample timestamps
in `demo/out/v4-terminal-review/manifest.json`:

- `beat4-00s.png` through `beat4-15s.png` (16 frames).
- `beat7-00s.png` through `beat7-23s.png` (24 frames).

Regenerate these at exact whole-second source frames with
`python3 demo/terminal_review_v4.py`. Extraction rejects incorrect MP4 durations
or frame counts. [Prior takes](assets/terminal-v4/takes/README.md) are retained,
including the short intermediate encodes that exposed agg dropping idle time.

The [narration](NARRATION-v4.txt) and [storyboard cues](storyboard-v4.yaml) change
only these spoken passages; all cues remain within three lines of 42 characters:

- Beat 6: “About a cent. Under ten seconds.”
- Beat 7: “On saved Threads posts, the median was 6.8 seconds. At that median,
  a thousand posts take about two hours on one worker.”

Beat 2 uses the full verbatim saved post inside a phone outline:
[SVG](assets/saved-post-v4.svg) and [PNG](assets/saved-post-v4.png), both 1080×1920,
with 56 px text and “saved post · 28 Oct 2026”. [The builder](phone_v4.py)
reads the retained post report and embeds its source/text hashes in the SVG.
`python3 demo/phone_v4.py --png` optionally rasterizes through installed macOS
AppKit/Swift. The motion scene loads the SVG; its illustrative repost counter
remains a motion-system element. No Wan output was generated or changed here.

The accepted scale JSON, architecture SVG, timing JSON, keyframes and beat grid
remain byte-identical to the base commit. Host voice/Wan caches, broll-480 and
motion/v3 were not edited. No model or SEC calls, synthesis or push was performed.

Validation commands and logs are retained in `demo/out/v4-r2-validation/`:

Passed: 213 demo Python tests and 100 standalone Node tests. The full offline
verifier also passed 1,010 product tests, both demo suites, figure regeneration
and checks, byte-identical explorer/site/wild data rebuilds, and Markdown links.
The source tree was unchanged by the verifier; its guards blocked network access.

```sh
demo/.venv/bin/python demo/motion_v4.py --check
python3 demo/phone_v4.py --check
python3 demo/replay_v4.py check beat4
python3 demo/replay_v4.py check beat7
demo/.venv/bin/python -m pytest demo/tests -q -ra -p no:cacheprovider
node --test demo/tests/motion.test.mjs demo/tests/motion-v3.test.mjs demo/tests/motion-v4.test.mjs demo/tests/layout.test.mjs demo/tests/capture.test.mjs
bash scripts/verify.sh
```
