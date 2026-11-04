# Round-6 retained records

Base: `4f65cf54`, `demo/v5`. [Host preflight](host-preflight.json) records the
Chromium sandbox failure and denied Computer Use access. No paid request, synthesis
or r6 render occurred. [Source scope](source-scope.json) records the modified source
hashes; product code, prompts, recorded evaluation results and prior media remain.

The logs retain initial failures, the missing offline cache attempt and later
passing runs. [The previous review](review-before.txt) is retained verbatim.
[The v021 encode measurement](v021-actual-loudness.json) comes from a fresh FFmpeg
measurement of the existing encoded film; it does not describe an r6 render.

`compile-without-log.log` and `record-check-old-take.log` are **expected failures**:
the previous take has no real server JSONL and cannot pass the new gate. Tests use
an explicitly synthetic online log under `demo/tests/fixtures/`; it is never wired
to the film. Local terminal tests use the actual copied CLI session and its hashes.
The literal-chunk tests cover its partial lines, JSON output and final receipt.

The final full guarded verifier and bundle verification are retained alongside
these records. Capture, changed run-cue voice, measured timing, actual frames,
continuous-picture review, r6 render and listening remain host work; follow
[REVIEW-v5.md](../../../REVIEW-v5.md).
