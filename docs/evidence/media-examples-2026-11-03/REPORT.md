# Packaged live examples — offline implementation receipt

Scope: five self-made inputs of the saved Big Tech post, a packaged-file API,
bilingual cards/read-text rendering, and host-only preparation/recording tools.
Base: `adc9406d24a22f1f6f732ae2670202a4197adbb6`, branch `feat/media-examples`.
The offline implementation and packaging made no deployment, push, verifier
model invocation, SEC fetch or new accuracy measurement. Host Breeze synthesis
is recorded below.

## Inputs and saved-result boundary

[The manifest](../../examples/manifest.json) records every file's hash and
size. All five input files are ready, including the host-generated MP3 and MP4
packaged in [round 3](#round-3--finished-media-package). During the initial offline
implementation, the installed Breeze environment's capability-only probe returned
`MPS available: False`; that pass invoked no synthesis or substitute voice.

[The text envelope](../../site/data/examples/text.json) reuses the original
recorded post run with unchanged claims, evidence, corrections, events, cost,
latency and source hashes. Native input-read time was not recorded and is null.
There are no invented saved image/PDF/audio/video runs. Offline tests inject
known OCR/ASR responses; they do not retest extraction accuracy. The host
recorder retains one attempt per selected ID, including failures, and declares
that its public API records exclude provider-private response bodies.

## Validation records

All retained failures below are offline development checks, not paid attempts.
Earlier console-only setup/preflight output is not recreated as historical logs.
A console-only preview snapshot guard initially assumed `beats.json` existed;
it stopped before any write. The corrected guard preserves missing files too.

| Record | Recorded result |
| --- | --- |
| [Initial site tests](site-initial.log) | 12 failed, 27 passed; new section order/index fetch required fixture updates |
| [Initial example tests](examples-initial.log) | 2 failed, 50 passed; PDF whitespace and timeout test coordination |
| [Focused revision 2](examples-focused-r2.log) | 9 failed, 51 passed; DOM adapter expectations and decoder-timeout coordination |
| [Focused revision 3](examples-focused-r3.log) | 2 failed, 24 passed; removed an unnecessary pasted-text read from card execution |
| [Combined focused checks](focused-final.log) | 1 failed, 90 passed; origin-auth assertion count needed the added route |
| [Record-builder checks](records-final.log) | 5 passed |
| [Pages boundary](pages-examples.log) | 16 passed; JSON/byte/origin/ID checks, nested allowlist, mock and 65 s abort |
| [Static route crawl](routes.log) | 44 local paths, zero missing; external link origins listed but never fetched |
| [First full verifier](verify-r1.log) | 1 failed, 1,276 passed; added `decoding="async"` to both new preview images |
| [Second full verifier](verify-r2.log) | Product: 1,278 passed. Demo: 3 failed, 203 passed; two generated source-hash references still pointed to the previous site script |
| [Preview metadata refresh](preview-refresh.log) | Refreshed only the two script-hash references; host timing, cues, keyframes and data unchanged |
| [Demo metadata checks](demo-metadata.log) | 3 passed |
| [Third full verifier](verify-r3.log) | Stopped during the passing product suite after review found the new grid rule also matched an older layout; scoped the rule to the Try gallery |
| [Final full verifier](verify-r4.log) | PASS: 1,278 product tests, 206 demo tests, standalone Node suites, figure/link checks and all byte-identical data/example rebuilds |

Full verifier command: `UV_OFFLINE=1 UV_CACHE_DIR=/private/tmp/claimcheck-verify-uv-cache bash scripts/verify.sh`.
It runs in a disposable copy with Python/Node network guards, provider secrets
removed (including the new Meta key), locked dependencies and no model/SEC calls.
It checks/rebuilds all example assets and selected saved envelopes byte for byte,
in addition to the original replay, figure, explorer, site and link checks.

The [PDF render](post-pdf-preview.png) was inspected after generation: one page,
Times serif, legible paragraphs, no clipping; native extraction matches the post
after whitespace normalization, including the thread emoji. EN/繁中 hostile-text
DOM tests cover 390/768/1280 px configurations. These adapter tests do not measure
browser fonts or replace visual browser approval.

Browser screenshot review was unavailable: computer use returned
`Computer Use was not approved to use Google Chrome`. No browser access was
forced. `DESIGN-final.md` was absent from this worktree and searches of the nearby
Git worktrees/temp directories; the implementation retains the established
paper/serif/green site style and the brief's five-card/result-order requirements.

## Round 3 — finished media package

Base: `c0e3c762`, branch `feat/media-examples`. All five manifest entries are
ready. The real MP3 is 32.96 s / 264,428 bytes. The H.264 1920×1080 + AAC MP4 is
33.46 s / 626,547 bytes, ending exactly 0.5 s after its unchanged 32.96 s audio
track and below the 2,000,000-byte limit. The manifest and site example index
record the measured durations, final sizes and SHA-256 hashes. Both cards now
contain native controls and real file links, including before JavaScript loads.
The two pending notices are removed; offline rebuilding no longer recreates them.
Unrecorded saved verification results remain explicitly pending.

Asset receipts live under `docs/evidence/example-assets/`:

- [First host synthesis receipt](../example-assets/20261104T005047.671530Z/source.wav.json),
  with jobs, input/reference hashes, source WAV and synthesis log retained in the
  same directory.
- [Second host synthesis receipt](../example-assets/20261104T010559.135205Z/source.wav.json),
  with the same full records retained; the published media came from this host
  preparation. Both receipts record Breeze-TTS-2, seed 2026 and the locked voice.
- [Offline packaging receipt](../example-assets/20261104T011425.576957Z-packaging/receipt.json),
  with the original 40.90 s MP4, exact FFmpeg command and encoding log retained.
  This trim copied the AAC stream without re-encoding. No new synthesis, Meta
  model, SEC request or OCR/ASR accuracy check was run during packaging.

[Media validation](../example-assets/20261104T011425.576957Z-packaging/validation.log)
decoded both complete files, confirmed the identical AAC bitstream before/after
trim and checked all manifest hashes, sizes and measured durations. Offline
encoding of the second retained source WAV reproduced the published MP3 byte for
byte; this was an encoding recheck, not new voice synthesis.

The two demo preview source-hash references were refreshed for removal of unused
pending-media translations. Existing narration timing, cues and keyframes were
preserved; historical run records were not rewritten.

Round-3 verification records:

- [First full verifier](verify-media-r3.log): 1,280 product tests passed;
  2 demo tests failed and 204 passed because the adapted hover-source hash stamp
  was stale in that snapshot. The stamp is now refreshed.
- [Static route crawl](routes-media-r3.log): 45 local paths, zero missing;
  external origins listed without requests.
- [Final full verifier](verify-media-r3-final.log): PASS, 1,280 product tests,
  206 demo tests and all standalone Node suites. Figure rebuild/check, Markdown
  links, all three core data outputs and all example asset/envelope byte-identical
  rebuilds passed. The same offline command documented above made no model or
  SEC calls, used no credentials and left the source tree unchanged.

## Host handoff

See [Examples](../../LIVE_CHECK.md#examples) for the exact Breeze command,
manifest/index rebuild, one-attempt recording, saved-envelope selection and
offline verification. See [deployment configuration](../../../deploy/README.md)
for `META_MODEL_API_KEY` / `META_MODEL_API_KEY_FILE`, FFmpeg and the read-only
`/app/examples` image directory. Existing SEC/claim code, prompts, historical
evidence and numbers are preserved.
