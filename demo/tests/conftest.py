"""Explicit synthetic trace inputs for a source round pending host recording.

Never wire these fixtures into the film. Production compilation refuses an absent
real JSONL. Tests use a separate receipt so offline CI never needs SSH or credits.
"""
import copy,json
from pathlib import Path
import pytest,yaml
from pipeline import file_hash

ROOT=Path(__file__).resolve().parents[2]

@pytest.fixture(scope='module')
def v5_story(tmp_path_factory):
    story=yaml.safe_load((ROOT/'demo/storyboard-v5.yaml').read_text())
    saved=json.loads((ROOT/'demo/prep/v5/r5/inputs-before.json').read_text())
    receipt=copy.deepcopy(saved['recordings']['v505']['receipt'])
    # The early portable summary deliberately pruned public event fields. Native
    # citation data comes from the retained response, independent of our log.
    current=json.loads((ROOT/'demo/motion/v5/inputs.json').read_text())
    receipt['result']=copy.deepcopy(current['recordings']['v505']['receipt']['result'])
    receipt['result'].update(cost_usd=.0215182,cost_is_bound=False,verdict='contradicted')
    log=ROOT/'demo/tests/fixtures/v5-serverlog-synthetic.jsonl'
    receipt['server_log']=dict(path=log.relative_to(ROOT).as_posix(),sha256=file_hash(log),request_id='0'*32)
    receipt['result'].pop('request_id',None)
    receipt['mp4']={'sha256':saved['recordings']['v505']['asset_sha256']}
    path=tmp_path_factory.mktemp('synthetic-v5')/'receipt.json'
    path.write_text(json.dumps(receipt))
    story['scenes'][5]['recording'].update(receipt=str(path),receipt_sha256=file_hash(path),timings=receipt['timings'])
    from record_v5 import live_cue_events
    story['scenes'][5]['cue_events']=live_cue_events(story['scenes'][5],receipt)
    return story
