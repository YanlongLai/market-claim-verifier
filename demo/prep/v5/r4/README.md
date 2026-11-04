# V5 round 4 validation records

Source base: `2d20f823` on `demo/v5`. Fixes commit: `99c0e878`.
This source round addresses only v018 blockers B1–B3. No paid request, voice
synthesis, SEC fetch, new native recording, full render or OCR/ASR test was run.
Host capture v9 and independent film acceptance remain pending; see
[the host sequence](../../../REVIEW-v5.md).

Final command outcomes and source/log hashes are in [validation.json](validation.json).
[unchanged-timing.json](unchanged-timing.json) checks narration, storyboard, timing,
cues, SRT and the cut plan against the source base, byte for byte.

- `node-initial.log` and `python-initial.log` retain the initial failing regression
  runs. Fixtures needed the new line audits and verdict/filing referents. Existing
  tests also still expected the inspector removed by the r3 host, a placeholder on
  the now-wired scene, or unmeasured data where the host had supplied measurements.
  Those fixtures now state their intended conditions explicitly.
- `node-regressions.log` and `python-regressions.log` retain the passing focused
  checks. `demo-python.log` and `demo-node.log` retain the full local demo suites.
- `offline-verifier-initial.log` retains the first verifier run: all Python/Node
  suites, figures and data rebuilds passed; the final Markdown check rejected a
  link to the ignored review output, absent from its disposable copy. The handoff
  now gives that local report as a plain path. `offline-verifier.log` is the separate
  final run, including dependency setup with `UV_OFFLINE=1` and runtime network guards.
- `ending-v018-baseline-initial.json` and its log retain the first encoded-frame
  check. `ending-v018-baseline.json` and its log retain the repeated check after
  clarifying expected versus observed page presence in the report. Both detect the
  known failure at frame 4620; frames 4621 and 4622 pass. This is a recheck of the
  retained film and native take, not a new film or an OCR/ASR product measurement.
  Inputs and decoded PNG hashes are in the reports. The checker reconstructs the
  images from those retained MP4s; PNGs remain in the two named temporary folders.
- `browser-preflight.log` retains the worker preflight (exit 1, no error detail).
  `browser-launch.log` retains the separate launch diagnosis: macOS Mach-port
  bootstrap permission denied under the workspace sandbox. Neither opened a page
  or made a live check.
- `compile-initial.log`, `compile.log`, `compiled-check.log` and
  `compiled-check-final.log` retain generation and freshness checks. `clone.log`
  records the writable delivery clone; existing untracked assets were not imported.
- `links-with-ignored-output.log` retains an additional source-workspace link scan:
  pre-existing reviews under ignored `demo/out` link to external local scratch files.
  Those historical reviews were preserved. The verifier excludes ignored output;
  `links-final.log` checks the delivery clone, including this final handoff and records.

The failing v018 cut check is expected retained evidence. It does not count as a
passing round-4 film. The final host render must pass the new encoded-frame gate,
and the fresh ledger must pass human listening and full-sentence visual review.
