# Demo subtitle regression fixture

[review-v4-subtitles.srt](review-v4-subtitles.srt) is the existing review-v4 subtitle export copied byte for byte from the ignored local output. It freezes the caption text/timing checked by [test_motion_cues.py](../test_motion_cues.py), so those tests no longer require `demo/out/`. The [committed cue document](../../motion/cues.json), [timing](../../motion/timing.json), [storyboard](../../storyboard.yaml) and [historical review](../../reviews-v004-ai2.md) provide the corresponding provenance.

Only subtitle text/timing is supplied; narrator audio and video remain local outputs under the [existing media policy](../../README.md#records-licences-and-host-completion).

The frozen SRT retains its final blank cue separator; [.gitattributes](../../../.gitattributes) permits that format-specific end-of-file whitespace for this file only.

[storyboard-v007.yaml](storyboard-v007.yaml) freezes the twelve-scene v007 storyboard before the approved
v010 hold trims and new reserved scene. Historical cue/audio regressions and the original v010 trim planner
use it, together with the retained speech lengths in [test_review_v007.py](../test_review_v007.py).
The active [v010 storyboard](../../storyboard-v3.yaml), committed [preview](../../motion/v3/preview-data.js),
and compiler/trace/zone tests in [test_v010.py](../test_v010.py) and
[motion-v3.test.mjs](../motion-v3.test.mjs) cover the revised thirteen-scene film without relying on local
host timing outputs. Temporary News/Threads compiler fixtures are synthetic and are never film evidence.
