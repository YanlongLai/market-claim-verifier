# Real traces and provider setup: implementation receipt

2026-11-04. Base: `e7058155`. This is offline implementation validation and a local
dry-run capture. It is not a new financial accuracy evaluation, OCR/ASR test, online
paid capture or production deployment. No paid model calls or production SSH were made.

## Delivered behavior

- Live runs emit single-line INFO summaries with a generated request ID, elapsed time,
  safe tool/evidence fields, model activity and verdict/cost or error. Envelopes and retained
  history carry the matching ID. Spend-gate transitions and history retention are unchanged.
- The SSH helper streams cp-1 pod logs, supplies sudo's password only through stdin,
  retains the full live-line spool and can filter by an ID learned after the verdict.
- The PTY helper records actual CLI output chunks, timing, command, working directory,
  source hash, exit status and available receipt fields. It retains failed attempts and
  redacts keys spanning reads. CLI progress reports tool calls before dispatch and actual
  per-claim verdicts, followed by a total receipt. `post --dry-run` previews extraction offline.
- Both READMEs explain all three providers, key variables/files, exact model overrides,
  OCR/ASR keys, budgets and online/local differences. The detailed provider guide distinguishes
  local Meta dotenv credentials from the server's raw `META_MODEL_API_KEY` secret.

[Capture commands and on-screen labels](../../REAL_TRACES.md) ·
[Models and keys](../../PROVIDERS.md#models--keys) ·
[Source and artifact hashes](manifest.json).

## Validation and retained attempts

| Record | Result |
| --- | --- |
| [Full verifier, final](verify-r2-passed.log) | Exit 0: 1,493 product/site tests, 206 demo tests and 97 standalone Node tests. All saved-data rebuilds, figure checks, language checks and Markdown checks passed. |
| [Full verifier, first](verify-r1-failed.log) | 1 failed, 1,492 passed. The new README section exceeded the existing 320-line limit. Condensed the section and removed duplicate setup prose; the length test was preserved. |
| [Targeted run 1](targeted-r1.log) | 72 passed: runner, HTTP adapter, CLI, post and new capture/privacy tests. |
| [Targeted run 2](targeted-r2.log) | 69 passed: language purity, provider/history behavior and new capture/privacy tests. |
| [Targeted run 3](targeted-r3.log) | 57 passed after the README condensation, including the existing length and mirror checks. |
| [Initial command error](targeted-command-error.log) | Exit 4: a nonexistent test filename; no tests ran. |
| [Early partial output](targeted-early-partial.log) | Completion was not retained; not counted as a pass. |
| [First actual PTY rehearsal](local-dry-run.json), [terminal](local-dry-run.log) | Exit 2: uv's default cache was outside the sandbox's writable roots. Retained without a final receipt; no paid call. |
| [Second actual PTY rehearsal](local-dry-run-r2.json), [terminal](local-dry-run-r2.log) | Exit 0 with a writable, populated uv cache and `UV_OFFLINE=1`; actual `post --dry-run`, six PTY reads, receipt cost $0.00. This is an extraction preview, not a verification result. |

The log/capture tests use fake SSH and CLI executables plus retained model/SEC fixtures.
They exercise late response IDs, terminal-event detection, request/envelope correlation,
private provider bodies, malformed fields, no-key previews, PTY chunk timestamps,
split-key redaction, nonzero exits and output-file preservation. They do not retest OCR/ASR.
The owner still performs the server rollout and paid online/local captures.

## Commit and bundle handoff

The worktree's shared Git metadata is outside the sandbox's writable roots; staging there
was rejected with `Operation not permitted`. The commit is created on `feat/real-trace` in a
temporary checkout, with the requested co-author footer, and exported to `real-trace.bundle`
at the original worktree root. The original worktree contains the source changes; its branch
metadata remains at the base commit. The bundle requires the existing `e7058155` base.

From the original worktree, the owner can import and advance the branch while preserving files:

```sh
git fetch ./real-trace.bundle feat/real-trace
git reset --mixed FETCH_HEAD
```
