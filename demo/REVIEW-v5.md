# Demo v5 round 5 — fill the live wait

Source base: `demo/v5` at `ef980294`. Reuse the wired **capture v9** take,
`demo/cache/live-takes/v5/beat6-20261104T144805450235Z.json` (SHA-256
`9a1ff164348c73bb71c335e945f964cf811ec22597df9ca807cdc35976512e1f`).
**No re-record, paid request or voice synthesis was performed in this source round.**
AI001 remains disabled. The ten cuts, 178-second duration, other scenes' measured
cues, voice identities, assets, chapter labels and the round-4 export gates remain.

## Receipt-bound terminal

The checking card becomes an opaque HTML/CSS/JS terminal at **x=80–1840,
y=558–790**. It has three dots, the title **claimcheck · this live request**,
30 px monospace rows, at most five visible lines, and the footer
**recorded trace of this request**. It keeps the native in-progress SEC status
clear above it, with the existing v9 native rectangles and card-edge audit.

The check starts at scene-local **7.831466834 s**, film **65.831466834 s**.
Typing starts 0.6 seconds earlier and finishes at that onset:

```text
$ claimcheck post post.txt --provider baseten --budget 1
```

Each call's time, name and arguments come from `result.events`. Its evidence ID
comes from the matching subsequent `tool_result`. The portable inputs retain these
fields so media-free verification rebuilds the same terminal.

| From check onset | Recorded row / state |
| --- | --- |
| +2.129651 s | `lookup_fact AMZN revenue 2023Q3 → E1` |
| +2.400641 s | `lookup_fact NVDA revenue FY2024 → E2` |
| +2.701321 s | `lookup_fact AAPL revenue FY2025Q4 → E3` |
| +6.844600 s | `compute_change NVDA revenue FY2024 vs FY2023 → E6` |
| +7.334576 s | Last result received; `… model reasoning (Muse Spark)` and a film-clock cursor |
| +16.412355 s | `verdict contradicted 16.4 s $0.02`; clock freezes at `16.4 s` |
| Scene +25.304457834 s | Terminal yields to the existing verdict card and both E3 filing citations |

The fourth call's actual result is **E6**, not the E4 in the direction's example:
`compute_change` creates intermediate evidence internally. No ID is relabelled.
The displayed cost rounds the recorded `$0.0215182` to `$0.02`. The stopwatch
stops at the **verdict event**, independently of `latency_ms` or browser wall time.
Typing, rows, blink and clock all support deterministic backward/nonsequential seeks.

## Narration and sync

There are **48 independent sentence/phrase units** (43 existing + 5 new). The
three requested additions contain five sentences, each with its own cached WAV,
PCM measurement, SRT cue, named proof and ledger row:

| Cue unit | Phase-local earliest speech onset | Narration |
| --- | --- | --- |
| `claims` | +0.8 s | Four claims. |
| `lookups` | +1.8 s, after the preceding unit | Four SEC lookups. |
| `evidence_ids` | +4.2 s | Each filed number comes back with its evidence ID. |
| `thinking` | +9.0 s | The clock is the model's thinking time. |
| `decide` | +13.0 s, after the preceding unit | Then the program decides. |

**Timing conflict resolved by retaining the existing cue:** “Muse Spark calls the
SEC tools.” already speaks from check +0.2 to +2.435 s in the retained measured
source. A new +0.8 s sentence would overlap it. The new offsets therefore specify
earliest starts; same-phase sentences queue after the whole preceding PCM unit.
The original cue stays in place. The final actual onsets come from the host's new
PCM measurements; no sentence is truncated, accelerated or silently overlapped.

Each sentence's terminal focus arrives **0.2 s before its measured onset** and
holds through the last word. Focus changes the command, title, call rows, reasoning
line or clock while trace rows retain their recorded arrival times. Each new
sentence is bound to `check_against_sec` with `offset_s`. The compiler refuses
any checking-phase unit whose complete audio would leave **less than 0.4 s before
`verdict_reveal`**, and still requires the native status to remain visible through
the last spoken word. A shorter future take must pass both limits.

The delivered v505 SRT/timing is explicitly an **unmeasured preview** pending host
voice generation. The other nine scenes retain their existing measured timing and
metadata. Preview timing cannot produce an accepted sync ledger or export.

The named-element audit now requires **the terminal window plus the clear native
in-progress SEC status** for all six checking-phase voice units. It validates
terminal bounds, opacity, title, dots, 30 px type, five-line scrolling, exact rows,
clock and cursor. Every sentence still receives onset/end frame audits. Local OCR
selection includes every live sentence and every scene (at least 24 frames);
its report is named `ocr-N.json` for the actual sample count. The verdict sentence
continues to require both native verdict and the two receipt-bound E3 filings.

## Host sequence — reuse this take

Retain prior review directories before regenerating them. Run in order after
importing the bundle; existing sentence caches are reused and only new units need
synthesis. No recording command is needed.

```sh
export UV_CACHE_DIR=/private/tmp/mcv-v5-uv-cache
export PLAYWRIGHT_MODULE=/Users/yan/ml-engines/playwright/node_modules/playwright
v5_review_stamp=$(date -u +%Y%m%dT%H%M%SZ)
for v5_review_dir in demo/out/review-v5 demo/out/keyframes-v5; do
  if test -e "$v5_review_dir"; then
    mv "$v5_review_dir" "$v5_review_dir-before-r5-$v5_review_stamp"
  fi
done
uv run --project demo python demo/build.py voice --only v505 --storyboard demo/storyboard-v5.yaml
uv run --project demo python demo/motion_v5.py --measured
uv run --project demo python demo/motion_v5.py --measured --check
uv run --project demo python demo/build.py review-frames --storyboard demo/storyboard-v5.yaml --out demo/out/review-v5
uv run --project demo python demo/build.py keyframes --storyboard demo/storyboard-v5.yaml --out demo/out/keyframes-v5
CLANG_MODULE_CACHE_PATH=/private/tmp/mcv-v5-swift-cache uv run --project demo python demo/review_v5.py --frames demo/out/review-v5
uv run --project demo python demo/build.py render --storyboard demo/storyboard-v5.yaml
uv run --project demo python demo/sync_v5.py --frames demo/out/review-v5
```

If a measured unit exceeds the available interval, retain the failed attempt and
repair narration timing before continuing. The take must stay wired. Final
listening, continuous-picture acceptance, native-status clearance, terminal
readability, card-3 transition and the existing encoded-cut check remain host work.
The render retains the round-4 encoded-frame gate at frames 4619–4622 and the
178 s, −14±1 LUFS and ≤−1 dBTP gates.

## Offline evidence and bundle import

[Round-5 records](prep/v5/r5/) retain the baseline, initial failures and validation
logs. [Round-4 records](prep/v5/r4/) remain available. The guarded verifier runs in
a disposable copy without provider credentials, model calls, SEC fetches or media.
The exact validation results are in the retained round-5 logs. All new film text
is English. Host voice, frame review and full film acceptance remain pending.

Final guarded verification: **1,269 product tests, 328 demo Python tests and 136
Node tests pass**, with figure/data rebuilds and local links green
([full log](prep/v5/r5/offline-verify-final.log)). The media-free delivery clone also
reproduces the compiled files ([check](prep/v5/r5/portable-compiled-check-second.log)).
The direct working-tree link check's retained failure is limited to pre-existing
absolute links in ignored host review outputs; the isolated source check passes.

```sh
uv run --project demo python demo/motion_v5.py --check
UV_CACHE_DIR=/private/tmp/mcv-v5-verify-uv-cache UV_OFFLINE=1 sh scripts/verify.sh
```

The supplied linked worktree's Git metadata is outside the writable sandbox;
[the prior write failure](prep/v5/r3/git-worktree-write.log) records that constraint.
Delivery commits are on `demo/v5` in a writable temporary clone based on
`ef980294`, and the supplied worktree contains the same source changes. The bundle
excludes unrelated untracked media and host run records. On the host, on `demo/v5`:

```sh
git fetch demo/out/v5-r5.bundle demo/v5
git merge-base --is-ancestor HEAD FETCH_HEAD
git reset --mixed FETCH_HEAD
```

The ancestry check must pass before the mixed reset. This imports the commits
while preserving working files and any later host recording changes.
