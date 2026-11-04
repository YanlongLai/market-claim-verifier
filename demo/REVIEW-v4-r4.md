# v4 round 4 — director fixes

The delivery bundle includes a merge of main `788605d862ef2f8a39b4ae052645ebde8e9a2236`
into the video branch, followed by the round 4 fixes. Shared Git metadata is read-only
in this session; the merged files and fixes are also present in this working tree.

- **D1:** Beat 1 embeds only `#top` from this worktree's current simplified site.
  The compiler retains its exact hero markup and CSS with source hashes. The iframe
  receives a script-free document containing one section, with scrolling disabled;
  site navigation is absent from its first frame. The five v3 host files were backed
  up under `demo/out/v4-r4-backup/`, then restored byte for byte after the merge.
- **D2:** Five copies of the saved phone card spread outward and fade. The only
  scene text is “A real number.” / “The wrong period.” The numeric counter and its
  illustrative-metric caption are removed.
- **D3:** The live closing take carries `hackathon.dappgo.com` at 48 px in the
  bottom-right corner throughout beat 9. It is the scene's only added overlay.
- **D4:** Both retained live takes receive a uniform 1.4× presentation transform,
  clipped to 1920×1080. The horizontal crop centres on the form/result column and
  clamps to the source edge. Beat 6 keeps the top of the source visible to retain
  the cost/time receipt through the original draft scroll; beat 9 uses a vertically
  centred crop. Source videos, narration, voice, scale JSON and terminals are unchanged.

Cuts remain **0, 9, 22, 34, 50, 66, 124, 148, 164, 178**. Keyframe plans now also
cover the opening frame, cascade, live verdict/receipt/draft, and first/last closing
frames. The classic-script bundle is rebuilt by `motion_v4.py` and measured preparation.
V4 browser layout assertions run before every captured frame on the host.

## Commands

Run from the repository root on this host, using its installed Playwright 1.64.1:

```sh
export PLAYWRIGHT_MODULE=/Users/yan/ml-engines/playwright/node_modules/playwright
export UV_CACHE_DIR=/private/tmp/mcv-v4-r4-uv-cache
uv run --project demo python demo/motion_v4.py
uv run --project demo python demo/build.py review-frames --storyboard demo/storyboard-v4.yaml --prepare-only --out demo/out/review-v4-r4
uv run --project demo python demo/build.py keyframes --storyboard demo/storyboard-v4.yaml --out demo/out/keyframes-v4-r4
uv run --project demo python demo/build.py render --storyboard demo/storyboard-v4.yaml
```

The compiler and measured review-plan preparation passed. Keyframes and render
were attempted, but Chromium could not launch in the execution sandbox. Computer
Use separately rejected Terminal access for safety reasons. No new full render or
passing browser-frame review is claimed. Existing takes and exports remain retained.

## Validation records

- Focused v4 tests: **22 Python tests and 9 Node tests passed**.
- Preservation: **240/240 files unchanged**, including all five protected v3 files,
  narration/storyboard, voice cache/reference, live takes/receipts and terminal clips.
- Full offline verification: **PASS — 1,269 product tests, 228 demo tests and
  106 Node tests**, figure regeneration/checks, byte-identical data rebuilds and
  Markdown links. Dependency setup also ran with `UV_OFFLINE=1` on the final run.
- [Four inspected 480 px crop previews](prep/v4/r4/crop-previews.json) retain the
  source/filter hashes. These are crop-only footage checks, separate from browser QA.

[All run commands and statuses](prep/v4/r4/commands.json),
[initial snapshot](prep/v4/r4/baseline.json),
[preservation hashes](prep/v4/r4/preservation.json),
[Python tests](prep/v4/r4/17-python-final.log),
[Node tests](prep/v4/r4/13-node-final.log),
[keyframe failure](prep/v4/r4/10-keyframes.log),
[render failure](prep/v4/r4/11-render.log),
[passing offline verification](prep/v4/r4/19-offline-verification-final.log),
[earlier failed verification](prep/v4/r4/12-offline-verification.log).
Failed and partial attempts are retained alongside later checks.

Both new delivery commits carry:

```text
Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
```
