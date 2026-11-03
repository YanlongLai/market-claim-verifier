# Demo v010 implementation verification

Source-only update: approved hold trims, data-driven real-world reserve, real Apple trace ribbon.
No model, SEC, narration synthesis, browser capture or film render was used. There are no real-world-* result
records in this checkout; [the committed snapshot](../../../demo/data/realworld.json) is explicitly pending.
[The missing-evidence compiler run](compiler-missing-evidence.log) exits 1 as required and does not write numbers.

Retained attempts, in order (later runs do not replace earlier evidence):

- [Preparation attempts](preparation-attempts.txt): session-output excerpts for the initial sandbox uv cache
  failure and initial nullable tool_calls parser failure. A temporary uv environment/cache and explicit
  nullable-call handling resolved these. These excerpts are not retroactive test-pass records.
- [Targeted Python suite 1](targeted-01.log): 66 passed before the later keyframe/receipt additions.
- [Node suite 1](node-01.log): 21 passed before the later receipt/keyframe changes.
- [Demo Python suite 1](demo-suite-01.log): 171 passed.
- [Final demo Python suite](demo-suite-02.log): 172 passed, including the unindexed-recheck guard.
- [Final standalone Node suites](node-02.log): 83 passed, including all 21 v3 scene/ribbon tests.
- [Committed preview check](preview-check-01.log): reproducible 13-scene, 177.2611-second target preview.
- [Link check](links-01.log): local Markdown links/anchors passed at that revision.
- [Offline dependency setup attempt](verify-01.log): exited before tests because a locked `pyparsing`
  wheel was missing from the download cache. No verification pass is claimed for this attempt.
- [Standard verifier](verify-02.log): bootstrap may download locked dependencies; all verification
  subprocesses run in the disposable copy under Python/Node network guards. Passed 929 product tests,
  171 demo tests, 83 Node tests, figures, three byte-identical data outputs and links before the final
  unindexed-recheck guard was added.
- [Final disconnected source-copy verifier](verify-03-committed-preview.log): runs against the isolated
  delivery copy with committed base timing files; local host data/timing/keyframe/beat/cue files were
  never copied. `UV_OFFLINE=1` passed: **929 product tests, 172 demo tests, 83 Node tests**, figure
  rebuild/check, all three data outputs byte-identical, Markdown links/anchors and no model/SEC calls.
  The locked download cache was populated by the preceding standard invocation.
- [Local link check](links-03.log), [delivery link check](links-04-final.log) and
  [preview check](preview-check-02.log) passed after handoff
  documentation updates. No additional implementation changes followed the final source-copy run.
- [Host output hashes](host-output-hashes.json): all five local outputs match their pre-task hashes.

The active storyboard targets 177.2611 seconds, with an 11.3081-second reserve. Tests replay the twelve
retained host voice lengths with a synthetic ten-second new line to verify the approved cuts, original
voice/music identity, unchanged original narration and no speech speed changes. Synthetic News/Threads
records live only in temporary test directories and test arithmetic/failure handling, not accuracy.
The pending preview has no new spoken captions, and host voice/film preparation refuses pending evidence.

Five pre-existing host output files remain local and are excluded from delivery. Offline Node tests use
[preview-data.js](../../../demo/motion/v3/preview-data.js). The verifier now also runs the v3 Node suite.
Host keyframe/physical DOM review and locked-voice measurement remain necessary after real evidence arrives;
this record does not assert that those visual or audio checks passed.

Direct staging was rejected when Git could not create the shared worktree `index.lock` outside the
writable workspace. The authorized fallback is a local commit/bundle from an isolated temporary Git
directory; host timing outputs are excluded. This is a filesystem restriction, not a failed test.

[Host commands](../../../demo/REVISION-v010.md#host-commands) cover the one new voice line, timing,
keyframes and eventual render. The source task did not execute those media commands.
