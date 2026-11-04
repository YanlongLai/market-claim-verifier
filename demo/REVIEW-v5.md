# Demo v5 round 8 — opaque cards, centred numbers and provider credit

Base: `demo/v5` at `32d979b6` (round-7 host state, v023).
Only the owner's four visual/credit notes are applied. The 178-second cuts,
live recording, Baseten take receipt, terminal replay, evaluation evidence,
music and all earlier narration remain unchanged.

## Visual changes

Every visible repost is opaque paper with an 18 px corner radius and
`0 12px 32px rgba(0,0,0,.35)` shadow. The seven copies retain their scale,
offset and rotation animation. Their explicit depth order sits below the original
card. This is the film's only stack of duplicated cards.

The title and number line on each numeric live card form one vertically centred
block. The corrected-draft card has 26.96 px above and below that block at the
1920×1080 source size. The green rule is drawn inside the card, so its thickness
does not shift the content centre. The SEC equation has a separate label row and
one shared number/operator baseline. Equal-width terms, centred labels/numbers,
and equal gaps either side of each operator keep the three filing terms aligned.
[Font geometry](prep/v5/r8/font-geometry.json) is a source measurement, not a
browser-frame or encoded-picture audit.

## Credit and speech

On screen: **Built with Meta Muse Spark · Baseten · Fireworks · Meta Model API**.
The existing 56 px Arial credit fits the 1760 px available width. The live take's
Baseten-specific receipt text and source files remain byte-identical.

The full requested sentence synthesized to 5.44 s, but the closing stamp would
finish after the fade starts. That audio, engine receipt and failed compile are
retained. The owner-authorized shorter sentence is used:
**Built with Meta Muse Spark on Baseten, Fireworks and Meta.**
Its measured speech is **170.200–173.735 s**. The existing DappGo WAV is reused at
**174.015–174.570 s**; the stamp starts at **173.815 s**, completes at **175.415 s**,
and clears the **176.800 s** fade. No speech is cut or accelerated. All **47 other
voice units** reuse their original hashes. The pinned Breeze clone, reference,
seed and inference parameters are unchanged. Local audio stays in the ignored
cache. Comma-separated provider names are treated as one independently measured
sentence; the compiler still rejects multiple sentences in one unit.

## Host completion

[Round-8 records](prep/v5/r8/README.md) retain original sources, both synthesis
attempts, timing, receipt hashes and validation logs. The prepared review plan has
370 frames. Headless Chromium cannot launch in this sandbox. Native Chrome review
was also rejected by computer-use approval. No new encoded film, frame approval
or listening approval is claimed.

Run the remaining picture review/export on the host, from this worktree with its
new local credit cache. No recorder or new live check is needed:

```sh
export PLAYWRIGHT_MODULE=/Users/yan/ml-engines/playwright/node_modules/playwright
uv run --project demo python demo/motion_v5.py --measured --check
uv run --project demo python demo/build.py review-frames --storyboard demo/storyboard-v5.yaml --out demo/out/review-v5-r8
uv run --project demo python demo/build.py render --storyboard demo/storyboard-v5.yaml
uv run --project demo python demo/sync_v5.py --frames demo/out/review-v5-r8
```

Use the new r8 directories to preserve earlier reviews and ledgers. Inspect the
cascade entrance/hold, every numeric card and the outro in the encoded film, then
listen through the new credit and sign-off before signing the new ledger.
The offline verification command is `UV_OFFLINE=1 sh scripts/verify.sh`.
Round 8 passes **1,269 product, 333 demo Python and 140 Node tests**, with
figure/data rebuilds and links green.

## Historical encoded export

The following receipt describes the previous host export and does not certify r8.

<!-- actual-encode:start -->
Actual r6 encode: **demo-v024**, 178.000 s; **-14.16 LUFS integrated**, **-1.08 dBTP**.
Measured from `demo-v024.mp4`; SHA-256 `a6d91a5d7d3394f2f53b736708c76bb416cad029a6cd384baea7ec80223ed045`.
[Export and measurement receipt](runs/20261104T193434706232Z-v024.json).
<!-- actual-encode:end -->
