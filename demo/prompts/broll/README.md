# v010 approved Wan B-roll records

The Owner selected five local 480×480 trials. [manifest.json](manifest.json) retains the complete
per-clip parameters, positive/negative prompts, seeds, reference image hashes, source/receipt hashes,
first/last-frame conditioning and model revision. The original prompt sets are copied verbatim:
[round 2](prompts-r2.json), [round 3](prompts-r3.json), including unselected shot prompts.
The original MP4s and unmodified generation receipts live in [assets/broll-480](../../assets/broll-480/).
These are decorative robot actions; they are not financial evidence or verifier model calls.

All five: Wan-AI/Wan2.2-TI2V-5B-Diffusers, revision `b8fff7315c768468a5333511427288870b2e9635`,
Apache-2.0 weights per the generation receipts; 20 steps, guidance 5, 49 frames at 16 fps,
480×480, background `#111a20`, subject scale 0.85. Seeds: arrive 11, point-glow 29,
turn-point 11, think-approve 11, stamp-press 29. The final three use first/last-frame conditioning.
Receipts retain the original host paths; replay uses repository-relative source/reference paths.
The selected first/last WebPs are already committed under `docs/site/img/auditor/H/`.

The Owner reported tail ghosting. [broll.py](../../broll.py) keeps source indices **0–44** of every clip:
45 frames / 16 = **2.8125 s**, discarding four complete frames (**0.25 s**, conservatively ≥0.2 s).
It never rescales or resamples the decoded frames. PNGs and extraction receipts are reproducible local
outputs under ignored `demo/cache/broll-480/`; each receipt records source/manifest hashes, FFmpeg version,
command, exact frame count, discarded tail and every decoded PNG hash. The film may hold frame 44 until
a detected beat permits the layout cut; frames 45–48 are never displayed. The opening keeps the clean
still through the disclosure shot. This uses no MP4 playback, timer, loop or random state.

From the repository root, using the demo environment:

```sh
uv run --project demo python demo/broll.py check
uv run --project demo python demo/broll.py extract --ffmpeg /opt/homebrew/bin/ffmpeg
```

`check` hashes sources/prompts/references and checks the committed runtime addresses without decoding media.
`extract` reuses an extraction only when all recorded PNG hashes still match. Missing/damaged PNGs or
mismatched bytes are decoded again. For an intentional record change, run
`uv run --project demo python demo/broll.py data` and review the resulting runtime-data diff.
Do not overwrite original generation receipts or regenerate the clips as part of verification.

[Proposed shot list and host handoff](../../SHOTLIST-v4.md). No frames or film were rendered for this source revision.
