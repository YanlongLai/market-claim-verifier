# Demo v010 — approved shot list v4

Owner approval for this placement/hold-trim plan is recorded in the v010 implementation brief.
The [v3 storyboard](storyboard-v3.yaml) now applies these targets and the five approved local Wan trials.
The [v3 shot list](SHOTLIST-v3.md), [narration](NARRATION-v007.txt), voice identity, music offset,
program verdicts, evidence and result qualifiers remain the baseline. No film, keyframes, TTS, push or upload
was produced here. Claude performs host preparation and rendering after the applicable Owner gates.

**Approved target total: 177.2611 s (2:57.2611)** including an **11.3081 s real-world-test placeholder**.
Baseline v009: 178.1899 s. These are beat-snapped proposal times calculated from the retained v009
voice lengths, not newly measured media. The original [broll.py planner](broll.py) is replayed against
the [historical storyboard fixture](tests/fixtures/storyboard-v007.yaml); active host preparation now uses
the approved targets directly. Changing measured narration may invalidate the budget; preparation refuses
an overrun or a changed real-world reserve.

## Approved target timeline

All times are absolute seconds. The existing twelve spoken paragraphs remain verbatim.
The hold column is silence **after** narration; Hover also keeps its nine-second narration lead.
The real-world scene occupies the reserve below. Until its evidence is committed, the data-driven preview
carries no metrics or narration; the compiler and host film preparation fail clearly.

| Scene | Proposed in–out (s) | Duration | Silent tail | Picture and reason |
| --- | --- | --- | --- | --- |
| Disclosure / product | 0.0000–6.1533 | 6.1533 | 1.9933 | **hover-arrive-s11** plays at 0.0000–2.8125, then holds its last clean frame. A 560 px left panel leaves the complete disclosure readable at 64 px on the right. The real product identity, Apple $416.2B claim and saved-check link are visible on frame zero, including at 3 s. Arrival introduces Hover beside the hook without delaying the product. |
| Apple post | 6.1533–17.6704 | 11.5171 | 3.8371 | Same real post and unresolved quarter trap; remove 2.7631 s of the old tail. |
| Extract | 17.6704–27.3531 | 9.6827 | 2.5627 | Same exact quotes and unjudged opinion; remove 1.9505 s of the tail. |
| Hover audit | 27.3531–53.5452 | 26.1921 | 5.8409 | **point-glow-s29** plays at 27.3531–30.1656 beside the Apple claim, then exits on the next detected beat. It points toward the right-hand product pane and hands off to the site's original spotlight audit inside the nine-second lead; narration starts 36.6643. The source/quarter search, comparison, strike and ≈4× conclusion retain their own cues. Remove 1.9505 s of the final hold. |
| Original filing | 53.5452–66.7341 | 13.1889 | 3.1889 | Keep the original Amazon two-column proof table and amber cell sweep; remove 1.9041 s of tail. |
| Program verdict | 66.7341–76.6955 | 9.9614 | 3.3214 | **stamp-press-s29** starts on the detected beat at/before the final-verdict cue minus 1.5 s (about 70–74 s in this proposal). Its press reinforces Python's recorded verdict; number, period and neutral E1 citation remain to the right, with FALSE gated to its existing cue. Exact visual contact needs host frame review; no contact alignment is claimed. Remove 1.7879 s of tail. |
| L4 releases | 76.6955–101.0300 | 24.3345 | 4.8945 | **turn-point-s11** plays at 76.6955–79.5080, then exits on a beat. Turning toward the right-hand release passage motivates this source-class transition. The actual Meta guidance value/period and regression/furnished/unaudited labels remain visible; Adobe and the future-performance caveat retain their cues. Remove 0.8127 s of tail. |
| Screenshot input | 101.0300–113.5920 | 12.5620 | 2.7220 | Same self-made source crop, OCR quote and $1.67 → $1.57 check; remove 0.3947 s of tail. |
| Synthetic audio input | 113.5920–126.5487 | 12.9567 | 3.1167 | Same measured waveform, ASR quote, fiscal quarter and unverified-speaker label; remove 0.0697 s of tail. |
| Original v2 results | 126.5487–142.8259 | 16.2772 | 4.2772 | **think-approve-s11** starts on the open-weights results cue (about 133–137 s here). Thinking → approval accompanies already revealed recorded results; the three provider rows, 357 claims and includes-dev/corrected-gold qualifiers remain in HTML beside it. It conveys completion of this saved check, not universal reliability. Remove 0.7895 s of tail. |
| Limits | 142.8259–155.7130 | 12.8871 | 0.8871 | Keep every limitation and coverage qualifier. Beat rounding adds 0.1161 s; no narration is shortened. |
| **Real-world saved runs · evidence pending** | **155.7130–167.0211** | **11.3081** | ≥1.3081 | **Data-driven News + Threads pages:** tested items, program-check coverage, claim verdict counts, cost/item and p50; up to three retained paraphrases with @handle only. Separate frozen-text post-hoc rechecks. No metrics or narration until the compiler validates the evidence. New locked-voice line ≤10 s. |
| CTA / QR | 167.0211–177.2611 | 10.2400 | 2.0800 | Keep the URL, matching QR, hackathon line and Meta credits through the last frame. Beat rounding adds 0.0697 s. |

The twelve original scenes recover **12.2369 s** through shorter silent tails and beat rounding;
the reserve consumes **11.3081 s**, leaving the film **0.9288 s shorter** than v009 and **2.7389 s below 3:00**.
No narration is accelerated or cut. **Exact narration changes: none.** The [new narration template](data/REALWORLD.md) is filled from retained run counts and must measure ≤10 s
inside the reserve. Original narration remains verbatim; the new line gets its own captions and locked-voice clip.

## Frame and layout contract

The committed storyboard now applies the approved hold edit and includes `v311b-realworld` as its
thirteenth scene at 155.7130–167.0211 s. [The committed preview](motion/v3/preview-data.js) is generated
without narration/media and shows an explicit pending state while [the snapshot](data/realworld.json)
has no results. [The evidence compiler](realworld.py) never fills missing numbers.

The Apple [trace compiler](agent_trace.py) binds the real post-check requests, tool name, E1 fact ID,
cost and latency. A frame-addressed ribbon replaces the Hover title after point-glow exits and before
narration starts; it adds no time and never presents request latency as measured tool execution time.

Existing measured `data.js`, `timing.json`, `keyframes.json`, `beats.json` and `cues.json` remain local and
uncommitted. Host preparation rebuilds them from cached voice plus the single new line after real-world
compilation. The page falls back to the committed preview when old host outputs have stale source hashes.

[Source records and prompts](prompts/broll/README.md) retain all five clips and the exact model revision,
seeds, steps, source dimensions and first/last references. Every clip drops source frames 45–48:
45/16 = **2.8125 s**, trimming **0.25 s** (whole-frame conservative rounding of ≥0.2 s).
The renderer selects `floor((t − clipStart) × 16)` clamped to 0–44, and holds only the clean frame 44
until the beat-aligned exit. There is no native video playback or wall-clock animation.

Panels are 600×600 at (64,256), except the 560×560 opener at (64,296). They have rounded corners,
a soft shadow and `#111a20` background. They contain images only; labels, evidence and numbers are separate HTML.
Images and shadows are clipped to x=64..1856 / y=64..880. The bottom **200 px** belong exclusively to subtitles.
Real DOM checks reject panel/text overlap, clipping, missing/wrong-size PNGs and subtitle incursions.
Offline tests cover source-frame boundaries, forward/reverse seeks and every 30 fps film frame.

## Host commands (Claude; not executed for this source handoff)

Use the [v010 handoff](REVISION-v010.md#host-commands) for the evidence compiler, the single new voice line,
measured timing, keyframes, motion checks and eventual full render. The first evidence command fails until
real-world records exist. The old v009 absolute insert samples must be recomputed after retiming.
No voice synthesis, keyframe capture, film render, push or upload was performed in this source task.
