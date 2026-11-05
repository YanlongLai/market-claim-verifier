# GitHub verify on Linux: example PNG bytes (2026-11-04)

GitHub's `Offline verification` job failed on most pushes with `Stale example: a.png`, while the same suite passed
on macOS. In a local Linux container (Python 3.12, Node 22, the same `scripts/verify.sh`), a fresh render of the
example post image had **0 differing pixels** but different PNG bytes: Linux zlib 1.2.13 compresses differently.

Fix (commit history has details):
- `build_examples.put`: a PNG is current when its size, mode and every decoded pixel match; build mode keeps the
  committed bytes, because saved recordings hash them. One changed pixel is still stale (tests).
- The clean-rebuild test compares PNGs by pixels and requires each manifest PNG row to hash the PNG on disk;
  every other file stays byte-exact.
- Job limit 15 to 25 minutes (green runs already took up to 12).

| Log | Result |
| --- | --- |
| [linux-verify-1-failed-clean-rebuild.log](linux-verify-1-failed-clean-rebuild.log) | Linux, after the first fix: 1 failure (clean rebuild compared PNG bytes) |
| [linux-verify-2-pass.log](linux-verify-2-pass.log) | Linux, final: pass |
| [macos-verify-pass.log](macos-verify-pass.log) | macOS, final: pass |
