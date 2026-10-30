"""Pure v2 timing: use measured onsets, never the requested BPM or fitted beat."""
from __future__ import annotations

import math
from bisect import bisect_left

from pipeline import BuildError


def video_beats(grid: dict) -> tuple[float, list[float]]:
    raw = grid.get('beats_s', [])
    if (not raw or any(type(b) not in (float, int) or not math.isfinite(b) or b < 0 for b in raw)
            or any(b <= a for a, b in zip(raw, raw[1:]))):
        raise BuildError('beats_s must be finite, nonnegative, strictly increasing detected beats.')
    offset = raw[0]
    return offset, [round(b - offset, 9) for b in raw]


def next_beat(beats: list[float], t: float) -> float:
    if not math.isfinite(t):
        raise BuildError('Beat time must be finite.')
    index = bisect_left(beats, t - 1e-9)
    if index == len(beats):
        raise BuildError('Narration exceeds the detected beat grid. Review the voice/music on the host; no beats are invented.')
    return beats[index]


def narration_lead(scene: dict) -> float:
    lead = scene.get('narration_lead_s', 0)
    if type(lead) not in (int, float) or not math.isfinite(lead) or lead < 0:
        raise BuildError(f"{scene['id']}: narration_lead_s must be a nonnegative, finite number.")
    return float(lead)


def narration_start(scene: dict, start: float, beats: list[float]) -> float:
    lead = narration_lead(scene)
    return next_beat(beats, start + lead) if lead else start


def target_timing(scenes: list[dict]) -> dict:
    shots, start = [], 0.0
    for scene in scenes:
        length = float(scene['target_s'])
        if not math.isfinite(length) or length <= 0:
            raise BuildError('Shot targets must be positive and finite.')
        shots.append(dict(id=scene['id'], start=round(start, 9), end=round(start + length, 9)))
        start += length
    return dict(source='targets', duration=round(start, 9), shots=shots)


def narration_timing(scenes: list[dict], durations: dict[str, float], beats: list[float], pad: float = .3) -> dict:
    if not math.isfinite(pad) or pad < .3:
        raise BuildError('v2 cuts require at least 0.3 s after narration.')
    shots, start = [], 0.0
    for scene in scenes:
        length = float(durations[scene['id']])
        if not math.isfinite(length) or length <= 0:
            raise BuildError(f"{scene['id']}: narration duration must be positive and finite.")
        voice_end = round(start + length, 9)
        end = next_beat(beats, voice_end + pad)
        shots.append(dict(id=scene['id'], start=start, end=end, voice_s=length, voice_end=voice_end))
        start = end
    return dict(source='narration', duration=start, shots=shots)


def presentation_timing(scenes: list[dict], durations: dict[str, float], beats: list[float],
                        focus: dict | None = None, pad: float = .3) -> dict:
    """Hold approved compositions; borrow time from the preceding shot for a focus cue.

    Speech always plays at its original speed. The Apple focus must finish by the
    approved absolute still, so its shot may start earlier than the target layout.
    """
    measured = narration_timing(scenes, durations, beats, pad)
    targets = target_timing(scenes)
    shots, start = [], 0.
    for i, (scene, target) in enumerate(zip(scenes, targets['shots'])):
        voice_s = durations[scene['id']]
        voice_start = narration_start(scene, start, beats)
        voice_end = round(voice_start + voice_s, 9)
        earliest = next_beat(beats, voice_end + pad)
        end = next_beat(beats, max(voice_end + pad, target['end']))
        if focus and i + 1 < len(scenes) and scenes[i+1]['id'] == focus['shot']:
            candidates = [b for b in beats if earliest-1e-9 <= b <= end+1e-9]
            for candidate in reversed(candidates):
                false_at = next_beat(beats, candidate + focus['cue_start'] - .1)
                if false_at + focus['settle_s'] + focus['push_s'] <= focus['t'] + 1e-9:
                    end = candidate
                    break
            else:
                raise BuildError('Narration and the half-speed push cannot fit before the approved Apple frame.')
        shots.append(dict(id=scene['id'], start=start, end=end, voice_s=voice_s, voice_end=voice_end,
                          hold_s=round(end-voice_end, 9)))
        if voice_start != start:
            shots[-1]['voice_start'] = voice_start
        start = end
    measured.update(shots=shots, duration=start, presentation_holds=True)
    return measured


def keyframe_times(timing: dict, scenes: list[dict]) -> list[float]:
    """v2c preserves absolute stills; legacy timing retains fractional shot progress."""
    if timing.get('presentation_holds'):
        return [3., 65., 155.]
    targets = target_timing(scenes)
    result = []
    for t in [3., 65., 155.]:
        i = next(i for i, shot in enumerate(targets['shots']) if shot['start'] <= t < shot['end'])
        old, new = targets['shots'][i], timing['shots'][i]
        fraction = (t - old['start']) / (old['end'] - old['start'])
        result.append(round(new['start'] + fraction * (new['end'] - new['start']), 9))
    return result


def motiontest_window(timing: dict, beats: list[float], prefix: str = 'm05', length: float = 2, fps: int = 30,
                      cue_events: dict | None = None) -> dict:
    matches = [s for s in timing['shots'] if s['id'] == prefix or s['id'].startswith(prefix+'-')]
    if len(matches) != 1:
        raise BuildError('Choose one motiontest shot id or unique prefix.')
    shot = matches[0]
    if not math.isfinite(length) or not 0 < length <= shot['end']-shot['start']:
        raise BuildError('Motiontest length must be positive, finite, and fit inside the shot.')
    local = [b for b in beats if b >= shot['start']-1e-9 and b < shot['end']-1e-9]
    event = local[min(4, len(local)-1)]
    if cue_events:
        event = next((e['t'] for e in cue_events[shot['id']] if e['event'] in ('flips.0', 'strike')), event)
    start = max(shot['start'], math.floor(min(event-.2, shot['end']-length)*fps)/fps)
    return dict(shot=shot['id'], event=event, **{'from':start, 'to':start+length})
