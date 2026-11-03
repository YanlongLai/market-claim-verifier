"""Approved sources, extraction and hold-budget contracts; no real media decode/render."""
from copy import deepcopy
import json
from pathlib import Path
import shutil

from PIL import Image
import pytest
import yaml

import broll
import motion_v3
from pipeline import BuildError, read_json


def test_broll_sources_prompts_and_runtime_addresses_match():
    data = broll.records(broll.ROOT)
    assert (broll.ROOT/broll.DATA).read_text() == broll.runtime_data(data)
    assert {c['id'] for c in data['clips']} == {
        'hover-arrive-s11', 'point-glow-s29', 'stamp-press-s29', 'turn-point-s11', 'think-approve-s11'}
    assert data['retained_frames'] == 45
    assert data['retained_frames']/data['fps'] == 2.8125
    assert (data['source_frames']-data['retained_frames'])/data['fps'] >= .2
    for clip in data['clips']:
        assert clip['model']['repo_id'] == 'Wan-AI/Wan2.2-TI2V-5B-Diffusers'
        assert clip['model']['revision'] == 'b8fff7315c768468a5333511427288870b2e9635'
        assert clip['model']['license'] == 'apache-2.0'
        assert clip['params']['seed'] == int(clip['id'].rsplit('-s', 1)[1])
        assert clip['params']['steps'] == 20
        if 'last_image' in clip['params'] and clip['params']['last_image']:
            assert set(clip['inputs']) == {'first', 'last'}


def test_changed_source_fails_before_ffmpeg(tmp_path):
    data = broll.records(broll.ROOT)
    for clip in data['clips']:
        for key in ('receipt', 'source'):
            path = tmp_path/clip[key]
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(broll.ROOT/clip[key], path)
    shutil.copytree(broll.ROOT/'demo/prompts/broll', tmp_path/'demo/prompts/broll')
    (tmp_path/data['clips'][0]['source']).write_bytes(b'changed source')
    with pytest.raises(BuildError, match='source, receipt or saved prompt changed'):
        broll.records(tmp_path)


def test_extraction_uses_native_source_indices_and_reuses_hash_checked_pngs(tmp_path, monkeypatch):
    data = broll.records(broll.ROOT)
    data['clips'] = data['clips'][:1]
    record = tmp_path/broll.RECORD
    record.parent.mkdir(parents=True)
    record.write_text(json.dumps(data))
    calls = []
    def decode(command, check):
        assert check is True
        calls.append(command)
        assert 'trim=start_frame=0:end_frame=45,setpts=PTS-STARTPTS' in command
        assert command[command.index('-fps_mode')+1] == 'passthrough'
        assert '-r' not in command and not any('scale=' in value for value in command)
        folder = Path(command[-1]).parent
        for path in broll.frame_files(folder, 45):
            Image.new('RGB', (480, 480)).save(path)
    monkeypatch.setattr(broll.subprocess, 'run', decode)
    monkeypatch.setattr(broll.subprocess, 'check_output', lambda *a, **k:'ffmpeg test version\n')
    broll.extract(tmp_path, data, 'fake-ffmpeg')
    broll.extract(tmp_path, data, 'fake-ffmpeg')
    assert len(calls) == 1
    folder = tmp_path/'demo/cache/broll-480'/data['clips'][0]['id']
    receipt = read_json(folder/'extraction.json')
    assert receipt['discarded_tail_s'] == .25
    assert len(receipt['frames']) == 45
    assert not (folder/'frame-0045.png').exists()
    (folder/'frame-0044.png').unlink()
    with pytest.raises(BuildError, match='exactly 45 PNGs'):
        broll.validate_frames(folder, data)
    broll.extract(tmp_path, data, 'fake-ffmpeg')
    assert len(calls) == 2
    assert len(broll.validate_frames(folder, data)) == 45
    (folder/'frame-0002.png').write_bytes(b'damaged derived PNG')
    broll.extract(tmp_path, data, 'fake-ffmpeg')
    assert len(calls) == 3
    assert len(broll.validate_frames(folder, data)) == 45


def test_frame_validation_rejects_wrong_dimensions(tmp_path):
    data = broll.records(broll.ROOT)
    for path in broll.frame_files(tmp_path, 45):
        Image.new('RGB', (480, 480)).save(path)
    Image.new('RGB', (960, 960)).save(tmp_path/'frame-0002.png')
    with pytest.raises(BuildError, match='native 480 square PNG'):
        broll.validate_frames(tmp_path, data)


def test_proposed_hold_trims_preserve_speech_and_fail_on_preview_or_overrun():
    story = yaml.safe_load((broll.ROOT/'demo/storyboard-v3.yaml').read_text())
    # Synthetic grid/measurements; never relies on the host's local narration outputs.
    beats = [i/2 for i in range(400)]
    lengths = [6, 14, 12, 28, 15, 12, 25, 13, 13, 17, 13, 10]
    voices = [4, 8, 7, 11, 10, 7, 19, 9, 9, 12, 12, 8]
    timing = dict(duration=178, shots=[])
    start = 0
    for scene, length, voice in zip(story['scenes'], lengths, voices):
        timing['shots'].append(dict(id=scene['id'], start=start, end=start+length, voice_s=voice))
        start += length
    original = deepcopy(timing)
    plan = broll.proposed_timeline(timing, story['scenes'], beats)
    assert timing == original
    assert plan['duration'] <= timing['duration'] <= 180
    assert plan['narration_changes'] == []
    reserve = next(s for s in plan['shots'] if s['id'] == 'v311b-real-world')
    assert 10 <= reserve['duration_s'] <= 12
    assert reserve['narration'] is None and 'PLACEHOLDER' in reserve['status']
    assert all(a['end'] == b['start'] for a,b in zip(plan['shots'], plan['shots'][1:]))
    for shot, old in zip((s for s in plan['shots'] if 'voice_s' in s), timing['shots']):
        assert shot['voice_s'] == old['voice_s']
        assert shot['hold_s'] >= .3
        assert shot['start'] in beats and shot['end'] in beats
    hover = next(s for s in plan['shots'] if s['id'] == 'v304-hover')
    assert hover['voice_start'] >= hover['start']+9
    del timing['shots'][0]['voice_s']
    with pytest.raises(BuildError, match='host-measured cached narration'):
        broll.proposed_timeline(timing, story['scenes'], beats)
    original['shots'][0]['voice_s'] = 90
    with pytest.raises(BuildError, match='film budget|beat grid'):
        broll.proposed_timeline(original, story['scenes'], beats)


def test_shotlist_budget_replays_retained_voice_measurements_without_host_outputs():
    from test_review_v007 import LENGTHS, pauses
    story = yaml.safe_load((broll.ROOT/'demo/storyboard-v3.yaml').read_text())
    voices = [dict(voice_s=n, key=s['id']) for s,n in zip(story['scenes'], LENGTHS)]
    data = motion_v3.compile_data(broll.ROOT, story, voices=voices,
                                 analyze=lambda scene, voice: pauses(scene['id'], voice['voice_s']))
    proposal = broll.proposed_timeline(data['timing'], story['scenes'], data['beats']['beats_s'])
    assert proposal['duration'] == pytest.approx(177.2611)
    reserve = proposal['shots'][-2]
    assert (reserve['start'], reserve['end'], reserve['duration_s']) == pytest.approx((155.713, 167.0211, 11.3081))
    document = (broll.ROOT/'demo/SHOTLIST-v4.md').read_text()
    assert 'Exact narration changes: none.' in document
    assert '177.2611 s' in document and '11.3081 s' in document
    for clip in broll.records(broll.ROOT)['clips']:
        assert clip['id'] in document
