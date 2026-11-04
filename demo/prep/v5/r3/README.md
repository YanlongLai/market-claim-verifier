# Round 3 verification records

Source round based on `a3440e73`, with AI001 disabled. No paid live check, synthesis,
SEC request, product OCR/ASR test or final film render was performed.

| Check | Result | Record |
| --- | --- | --- |
| Full disconnected verification | PASS: 1,269 product tests, 294 demo tests, 128 Node tests; deterministic builders, figures and links | [verify-clock-final.log](verify-clock-final.log) |
| Demo suite after clock/cover gates | PASS: 294 | [pytest-demo-clock-final.log](pytest-demo-clock-final.log) |
| Standalone Node suites after clock/cover gates | PASS: 128 | [node-all-clock-final.log](node-all-clock-final.log) |
| Generated motion preview + check | PASS, explicitly unmeasured; 43 independent units / 43 SRT entries / zero inferred internal rows | [compiler-final.log](compiler-final.log) |
| Source-only Markdown links | PASS in disposable delivery clone (ignored output reviews excluded) | [links-source-final.log](links-source-final.log) |
| Actual local Chromium frames | BLOCKED: Chromium could not launch inside the sandbox; no PNG acceptance claimed | [browser-first.log](browser-first.log) |
| Linked worktree Git write | BLOCKED: Git metadata outside writable sandbox; delivery commits built in a temporary clone | [git-worktree-write.log](git-worktree-write.log) |

The initial focused test failures and subsequent successful checks remain alongside these
logs. They include the old seven-cue assertions and missing measured-onset fixtures; the new
suite also tests missing/short native holds, incomplete frame audits, multi-sentence aliases,
PCM silence/click bounds, cover framing, decoded start and page/video clock calibration.

The direct whole-worktree link scan in [links-final.log](links-final.log) also traversed
ignored `demo/out` reviews, whose existing absolute scratch links leave the repository.
Those independent review files were preserved. The official verifier's disposable source
copy and the source-only delivery clone both pass link checks.

[inputs-before.json](inputs-before.json) retains the exact committed v017 measured metadata.
New committed motion artifacts are labelled unmeasured previews until the host sequence in
[REVIEW-v5.md](../../../REVIEW-v5.md) replaces them with measured per-sentence sources.
None of these offline records certifies the next native take, narrator pronunciation or
continuous film picture. The fresh ledger requires actual measured units and actual onset/end
frame audit evidence, and retains human listening/full-duration picture acceptance as pending.
