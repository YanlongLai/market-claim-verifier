"""Narration alignment and phrase-addressed events, independent of a browser."""
from __future__ import annotations

import math
import re
from pathlib import Path

import media
from motion_timing import next_beat
from pipeline import BuildError, Subtitle, subtitle_chunks

NOISE_DB = -35
MIN_SILENCE_S = .12


def split_phrases(text: str) -> list[str]:
    """Split sentences/colons and comma + capitalised names; keep decimals intact."""
    boundaries = [0]
    for i, char in enumerate(text):
        decimal = char == '.' and i > 0 and i + 1 < len(text) and text[i-1].isdigit() and text[i+1].isdigit()
        if (char in '.:?!' and not decimal) or (char == ',' and re.match(r',\s+[A-Z]', text[i:])):
            boundaries.append(i + 1)
    boundaries.append(len(text))
    phrases = [text[a:b].strip() for a, b in zip(boundaries, boundaries[1:]) if text[a:b].strip()]
    if not phrases:
        raise BuildError('Narration must contain text to align.')
    return phrases


def parse_silences(log: str, duration: float) -> list[tuple[float, float]]:
    """Read ffmpeg intervals, including leading/trailing and an unclosed final pause."""
    intervals, start = [], None
    for match in re.finditer(r'silence_(start|end):\s*(-?[\d.]+)', log):
        kind, value = match[1], min(duration, max(0., float(match[2])))
        if kind == 'start':
            start = value
        elif start is not None:
            if value > start:
                intervals.append((start, value))
            start = None
    if start is not None and start < duration:
        intervals.append((start, duration))
    return intervals


def detect_silences(audio: Path, duration: float, log: Path) -> list[tuple[float, float]]:
    result = media.ffmpeg(['-i', audio, '-af', f'silencedetect=noise={NOISE_DB}dB:d={MIN_SILENCE_S}',
                           '-f', 'null', '-'], log, verbose=True)
    return parse_silences(result.stderr, duration)


def map_sentences(text: str, duration: float, silences: list[tuple[float, float]],
                  offset: float = 0.) -> tuple[list[dict], str]:
    """Match speech runs one-to-one, otherwise use character-weighted clip timing."""
    if not math.isfinite(duration) or duration <= 0 or not math.isfinite(offset):
        raise BuildError('Cue duration must be positive and finite; offset must be finite.')
    phrases = split_phrases(text)
    speech, cursor = [], 0.
    for start, end in silences:
        if not all(math.isfinite(v) for v in (start, end)) or start < cursor or end <= start or end > duration:
            raise BuildError('Silence intervals must be ordered, nonoverlapping and inside the clip.')
        if start > cursor + 1e-6:
            speech.append((cursor, start))
        cursor = end
    if cursor < duration - 1e-6:
        speech.append((cursor, duration))
    if not speech:
        raise BuildError('Narration clip contains no detected speech.')
    method = 'silence' if len(speech) == len(phrases) else 'proportional'
    if method == 'proportional':
        total, cursor, speech = sum(map(len, phrases)), 0, []
        for phrase in phrases:
            speech.append((duration * cursor / total, duration * (cursor + len(phrase)) / total))
            cursor += len(phrase)
    return [dict(text=p, start=round(offset+a, 9), end=round(offset+b, 9))
            for p, (a, b) in zip(phrases, speech)], method


def phrase_cue(cues: list[dict], phrase: str) -> dict:
    """Locate a word/phrase inside its sentence using a documented character offset."""
    if not phrase.strip():
        raise BuildError('Event cue phrase must contain text.')
    matches = []
    for cue in cues:
        for match in re.finditer(r'(?<!\w)' + re.escape(phrase) + r'(?!\w)', cue['text'], re.IGNORECASE):
            length = len(cue['text'])
            span = cue['end'] - cue['start']
            matches.append(dict(text=phrase,
                                start=round(cue['start'] + span * match.start() / length, 9),
                                end=round(cue['start'] + span * match.end() / length, 9),
                                sentence=cue['text'],
                                alignment='sentence' if match.start() == 0 else 'character-offset'))
    if len(matches) != 1:
        raise BuildError(f'Cue phrase {phrase!r} must identify exactly one narration phrase; found {len(matches)}.')
    return matches[0]


def snap_event(cue_start: float, beats: list[float], shot_start: float, shot_end: float) -> float:
    event = next_beat(beats, max(shot_start, cue_start - .10))
    if event >= shot_end - 1e-9:
        raise BuildError('Cue event falls beyond its shot; extend the presentation hold.')
    return event


def cue_document(scenes: list[dict], timing: dict, local: dict, analysis: dict,
                 beats: list[float]) -> dict:
    """Shot IDs map directly to absolute-time cues; underscore keys hold provenance."""
    doc = dict(_version=1, _methods={}, _analysis=analysis, _events={})
    for scene, shot in zip(scenes, timing['shots']):
        cues, method = local[scene['id']]
        voice_start = shot.get('voice_start', shot['start'])
        absolute = [dict(text=c['text'], start=round(voice_start+c['start'], 9),
                         end=round(voice_start+c['end'], 9)) for c in cues]
        doc[shot['id']] = absolute
        doc['_methods'][shot['id']] = method
        events = []
        for spec in scene.get('cue_events', []):
            cue = phrase_cue(absolute, spec['cue'])
            event = dict(event=spec['event'], cue=spec['cue'], cue_start=cue['start'],
                         cue_end=cue['end'], alignment=cue['alignment'],
                         t=snap_event(cue['start'], beats, voice_start, shot['end']))
            if spec.get('review_at_start'):
                event['review_at_start'] = True
            events.append(event)
        doc['_events'][shot['id']] = events
    return doc


def caption_segments(text: str, phrases: list[str]) -> list[tuple[int, str]]:
    """Wrap a sentence without splitting a motion cue between subtitle entries."""
    words = list(re.finditer(r'\S+', text))
    protected = [match.span() for phrase in phrases
                 for match in re.finditer(r'(?<!\w)' + re.escape(phrase) + r'(?!\w)', text, re.IGNORECASE)]
    result, first = [], 0
    while first < len(words):
        choice = None
        for last in range(first, len(words)):
            end = words[last].end()
            chunks = subtitle_chunks(text[words[first].start():end])
            if len(chunks) != 1:
                break
            if not any(a < end < b for a, b in protected):
                choice = last, chunks[0]
        if choice is None:
            raise BuildError('A motion cue phrase cannot fit a two-line subtitle.')
        last, wrapped = choice
        result.append((words[first].start(), wrapped))
        first = last + 1
    return result


def sentence_subtitles(scenes: list[dict], timing: dict, document: dict) -> list[Subtitle]:
    """Use cues.json sentence times, including character offsets for long sentences.

    Start on the video frame containing the spoken onset. Millisecond timestamps
    sit just before that frame so SRT export and the 30 fps burn-in agree. A final
    caption stays through its settled motion cue, including m09's post-speech beat.
    """
    raw = []
    for scene, shot in zip(scenes, timing['shots']):
        sentences = document[scene['id']]
        events = document['_events'][scene['id']]
        for sentence in sentences:
            span = sentence['end'] - sentence['start']
            if span <= 0:
                raise BuildError('Subtitle sentence duration must be positive.')
            segments = caption_segments(sentence['text'], [e['cue'] for e in events])
            starts = [sentence['start'] + span * offset / len(sentence['text']) for offset, _ in segments]
            end = sentence['end']
            if sentence is sentences[-1]:
                end = min(shot['end'], max(end, shot['voice_end'],
                          max((e['t'] + .3 + 1 / media.FPS for e in events), default=end)))
            raw.extend(Subtitle(a, b, segment[1])
                       for a, b, segment in zip(starts, starts[1:] + [end], segments))

    def boundary(time: float, *, end: bool = False) -> float:
        frame = math.ceil(time * media.FPS - 1e-8) if end else math.floor(time * media.FPS + 1e-8)
        return math.floor(frame * 1000 / media.FPS + 1e-8) / 1000

    starts = [boundary(c.start) for c in raw]
    return [Subtitle(start, min(boundary(c.end, end=True), starts[i+1] if i+1 < len(raw) else math.inf), c.text)
            for i, (c, start) in enumerate(zip(raw, starts))]


def review_frame_plan(timing: dict, events: dict) -> list[dict]:
    plan = []
    for shot in timing['shots']:
        plan.append(dict(shot=shot['id'], t=round((shot['start']+shot['end'])/2, 9), cue='midpoint'))
        for event in events[shot['id']]:
            if event.get('review_at_start'):
                plan.append(dict(shot=shot['id'], t=event['cue_start'], cue=event['cue'],
                                 event=event['event'], sample='spoken-cue-start'))
            t = round(event['t'] + .3, 9)
            if t >= shot['end']:
                raise BuildError(f"{shot['id']}: event + 0.3 s crosses a shot cut.")
            plan.append(dict(shot=shot['id'], t=t, cue=event['cue'], event=event['event']))
    return plan
