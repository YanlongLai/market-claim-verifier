# Demo v4 round 2 validation

Final runs: `demo-checks.log` (compiler/still/replay checks plus 213 demo Python tests), `demo-node.log` (100 standalone Node tests), `verify-01.log` (full offline verifier: 1,010 product tests, 213 demo tests, 100 Node tests, figures, data rebuilds and links), and `links.log` (working-tree Markdown links, including new handoff records). All passed.

`terminal-review.log` lists the 40 exact whole-second PNGs and confirms both locked MP4 durations/frame counts. `artifact-audit.json` records hashes/protected paths and the source base. The final media are 16.000 s / 480 frames and 24.000 s / 720 frames, at 1920×1080 and 30 fps.

Retained initial checks: `v4-tests-01.log` passed seven structural tests before the encoding duration issue was corrected. Cast-end timestamp assertions were added afterward and pass in the final demo suites. Initial concise recordings (`beat4-record.log`, `beat7-record.log`, `beat4-record-02.log`) are retained under `demo/assets/terminal-v4/takes/`; measured short durations are in that folder’s index. Final recording logs are `beat4-record-03.log` and `beat7-record-02.log`.

`phone-render.log` records the successful local AppKit SVG rasterization; the PNG was visually inspected. Earlier tool probes found no installed Playwright 1.64, no FFmpeg SVG decoder, and a sips decoding error. These were renderer-availability probes, not model/media-extraction tests. No dependency installation, model call, SEC fetch, narration synthesis, paid run, or push was performed.
