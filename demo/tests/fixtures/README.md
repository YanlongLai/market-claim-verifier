# Demo subtitle regression fixture

[review-v4-subtitles.srt](review-v4-subtitles.srt) is the existing review-v4 subtitle export copied byte for byte from the ignored local output. It freezes the caption text/timing checked by [test_motion_cues.py](../test_motion_cues.py), so those tests no longer require `demo/out/`. The [committed cue document](../../motion/cues.json), [timing](../../motion/timing.json), [storyboard](../../storyboard.yaml) and [historical review](../../reviews-v004-ai2.md) provide the corresponding provenance.

Only subtitle text/timing is supplied; narrator audio and video remain local outputs under the [existing media policy](../../README.md#records-licences-and-host-completion).

The frozen SRT retains its final blank cue separator; [.gitattributes](../../../.gitattributes) permits that format-specific end-of-file whitespace for this file only.
