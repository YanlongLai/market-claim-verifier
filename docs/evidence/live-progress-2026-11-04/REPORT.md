# Live request progress and abuse guards

Offline implementation record, 2026-11-04, from `main` at `5f385d3c` on
`feat/live-progress-and-abuse`. No deployment, model calls, SEC requests, OCR/ASR
execution or account-balance queries. Saved financial results remain unchanged.

The origin adds a durable rolling password-failure window (fifth wrong password
locks for 30 minutes), a durable 20-member rolling site-run window, two concurrent
members with no queue, and a durable 30-request rolling API burst window with a
ten-minute block. The existing five-check IP gate and spend reservations remain.

The terminal uses the same allowlisted log events as the pod, an unguessable UUID
v4, a five-minute in-memory buffer capped at 200 lines, and a no-store Pages proxy.
Compare derives a distinct ID per member. Both reading layers open the terminal
before POST completion and retain collapsed logs afterward, with 15 px mono text.
The UI clock ticks at 700 ms; shared network polls are at least three seconds
apart because 700 ms network polls would exceed the required 30/IP/minute guard.
The existing 1 KiB streamed JSON limit already rejects bodies over 16 KiB.

History summaries now carry allowlisted saved errors, including legacy records;
refreshing 50 failed rows does not issue 50 additional detail requests. Pages
forwards the trusted client IP on budget, history and progress requests. No secret
configuration changes. The origin image copies the new progress module.

## Validation records

[Final full verification](verify-3.log), using [these source hashes](inputs-verify-3.json),
passed: 1,556 product tests, 206 demo tests, 97 standalone JavaScript tests,
figure rebuild/check, byte-identical saved/site/explorer/wild data and Markdown
links. No model calls, SEC fetches or credentials; the source tree was unchanged.


- [Focused regression pass](targeted-5.log): 167 passed before history fanout repair.
- [History repair and broader regression pass](targeted-6.log): 166 passed.
- [Progress and bilingual terminal pass](progress-3.log): 23 passed, including
  cancellation and legacy history errors.
- [Pages progress contract pass](pages-progress-3.log): 7 passed.
- [First full-verifier source hashes](inputs-verify-1.json) and
  [interrupted full run](verify-1.log): stopped to address the history fanout;
  two old assertions assumed no burst/site ledger keys and IP-free budget reads.
- [Second full verification](verify-2.log): all 1,556 product tests passed;
  three demo preview checks detected the stale site-script provenance hash.
  [Offline rebuild](preview-rebuild.log) updated only that SHA-256 in the generated
  hover adapter and preview. [Demo checks](demo-targeted.log): 61 passed.
  [Host data/timing/keyframe hashes](host-media-hashes.json) still match the base.
- [Terminal placement check](site-progress-4.log): 10 passed after moving the
  panels above both the compare table and the full result.
- Earlier `targeted-*`, `pages-*`, `progress-*` and `site-progress-*` logs retain
  all failed/partial setup and fixture attempts. Nothing was overwritten.

The tests use fake clocks/transports, frozen SEC/model fixtures and the shipped
JavaScript in the existing offline DOM adapter. They verify lifecycle/TTL,
bounded cursors, redaction, endpoint shapes, Pages field projection, authentication,
rolling windows, site admission, concurrency release, terminal stages, shared poll
cadence, collapse, error states and reading-language purity. They are not a fresh
financial benchmark, media-extraction retest, browser pixel review or live smoke
check. The operator builds, deploys and tests live.

## Delivery boundary

The managed filesystem permits edits in this worktree but rejects writes to its
shared Git metadata outside the workspace. Commits and the bundle are therefore
created in an isolated writable Git copy from the same base. The original
worktree retains all edited files; its branch ref is not advanced by this session.
The commit carries the owner-requested co-author footer. No deployment occurred.
