from __future__ import annotations

import json
import copy
import shutil
import wave
from pathlib import Path
from types import SimpleNamespace

import pytest

from claimcheck.agent import verify_claim
from claimcheck.budget import BudgetExceeded, Ledger
from claimcheck.ingest_media import decode, read_image, stitch_turns, transcribe
from claimcheck.period_context import missing_period_reason
from claimcheck.post import check_post, extract_claims, extraction_windows, screen_claims
from claimcheck.trace import TraceRecorder
from test_ingest import EVIDENCE, MEDIA, ROOT, ReplayMeta, offline_clients


class SequenceClient:
    def __init__(self, responses):
        self.queue = list(responses)
        self.requests = []
        self.responses = self
        self.chat = SimpleNamespace(completions=self)

    def create(self, **payload):
        self.requests.append(payload)
        result = self.queue.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class ProviderFailure(RuntimeError):
    def __init__(self, status):
        self.status_code = status
        super().__init__(f'HTTP {status} private-key')


def completed(text):
    return {'id': 'test', 'status': 'completed', 'output_text': text, 'usage': {'input_tokens': 10, 'output_tokens': 30}}


def test_recorded_period_loss_recovers_source_period_and_real_eps_calculation(tmp_path):
    saved = json.loads((EVIDENCE / 'video-captioned-baseten/ingest.json').read_text())
    channel = saved['channels'][0]
    old = channel['claims'][2]
    assert old['verdict'] == 'contradicted'  # original evidence stays intact
    claim = screen_claims(channel['normalized_text'], [old])[0]
    assert claim['extracted_claim'] == 'Apple reported EPS growth of 12%.'
    assert claim['claim'].endswith('for fiscal Q3 2025.')
    a, b = claim['period_context']['span']
    assert channel['normalized_text'][a:b] == claim['period_context']['text']
    # Reuse the actual successful FY2025Q3 tool responses from the other
    # recorded run. This checks deterministic math, not fresh extraction.
    other = json.loads((EVIDENCE / 'audio-baseten/ingest.json').read_text())['channels'][0]['claims'][2]
    trace = json.loads((EVIDENCE / 'audio-baseten/checks/audio' / other['trace_path']).read_text())
    client = SequenceClient([r['raw_response'] for r in trace['requests']])
    edgar, releases = offline_clients(tmp_path)
    result = verify_claim(claim['claim'], client, edgar, Ledger(tmp_path / 'ledger'),
                          'meta-models/muse-spark-open-1026', provider='baseten', release_client=releases, max_output_tokens=8000)
    assert result['verdict'] == 'supported'
    assert result['program_checks'][0]['actual_value'] == pytest.approx((1.57 / 1.40 - 1) * 100)
    assert claim['claim'] in str(client.requests[0])


@pytest.mark.parametrize('claim', ['Apple reported EPS growth of 12%.', 'Apple revenue was $94 billion.',
                                  'Apple EPS was $1.57 last quarter.', 'Apple revenue rose 10% in the June quarter.',
                                  'Apple revenue doubled.', 'Apple revenue was $2025.', 'Apple EPS grew twelve percent.'])
def test_periodless_numeric_claims_stop_before_model_or_sec(tmp_path, claim):
    recorder = TraceRecorder(claim, 'muse-spark-1.3')
    ledger = Ledger(tmp_path / 'ledger')
    result = verify_claim(claim, None, None, ledger, 'muse-spark-1.3', trace=recorder)
    assert result['verdict'] == 'insufficient_evidence'
    assert 'missing_period' in result['summary']
    assert result['program_checks'][0]['reason'] == result['summary']
    assert not recorder.requests and ledger.spent_total == 0


def test_recorded_rows_keep_date_guard_and_accept_exact_heading_context():
    saved = json.loads((EVIDENCE / 'video/ingest.json').read_text())
    channel = saved['channels'][1]
    old = channel['claims'][0]
    assert screen_claims(channel['normalized_text'], [old])[0]['status'] == 'rejected'
    post = channel['normalized_text']
    expanded = post[post.index('Release table:'):post.index('Net income:')].strip()
    accepted = screen_claims(post, [{**old, 'quote': expanded}])[0]
    assert accepted['status'] == 'to_verify' and '28' in accepted['quote']
    invented = screen_claims(post, [{**old, 'quote': expanded, 'claim': old['claim'].replace('94036', '99036')}])[0]
    assert invented['status'] == 'rejected'
    # Missing period in the second slide is inherited from that slide header.
    row = screen_claims(saved['channels'][2]['normalized_text'], saved['channels'][2]['claims'])[0]
    assert row['claim'].endswith('for fiscal Q3 2025.')


def test_conflicting_context_does_not_choose_a_period():
    quote = 'Apple EPS grew 12%.'
    post = 'Fiscal Q3 2025 versus fiscal Q3 2024.\n' + quote
    result = screen_claims(post, [{'quote': quote, 'claim': quote, 'kind': 'reported_fact'}])[0]
    assert missing_period_reason(result['claim'])
    assert 'period_context' not in result


@pytest.mark.parametrize('introduction,label', [('calendar Q3 2025', 'calendar Q3 2025'),
                                               ('Q3 2025', 'Q3 2025')])
def test_adjacent_period_keeps_the_stated_calendar_basis(introduction, label):
    quote = 'Apple revenue grew 10%.'
    post = quote + ' The reported period is ' + introduction + '.'
    result = screen_claims(post, [{'quote': quote, 'claim': quote, 'kind': 'reported_fact'}])[0]
    assert result['claim'] == 'Apple revenue grew 10% for ' + label + '.'


@pytest.mark.parametrize('stage', ['extraction', 'agent', 'ocr', 'asr'])
def test_transient_5xx_retries_are_bounded_traced_and_charged(monkeypatch, tmp_path, stage):
    delays = []
    monkeypatch.setattr('claimcheck.retries.time.sleep', delays.append)
    ledger = Ledger(tmp_path / 'ledger', budget_usd=5)
    record = tmp_path / 'call.json'
    client = SequenceClient([ProviderFailure(503), ProviderFailure(502), ProviderFailure(500)])
    recorder = TraceRecorder('test', 'muse-spark-1.3', secrets=['private-key'])
    if stage == 'asr':
        class HTTP:
            def post(self, *args, **kwargs):
                assert kwargs['files']['audio'][1].read(4) == b'RIFF'  # reopened on retry
                return SimpleNamespace(status_code=503)
        with pytest.raises(Exception, match='503'):
            transcribe({'audio': str(MEDIA / 'release-reading.wav'), 'duration_s': 47.29},
                       http=HTTP(), api_key='private-key', ledger=ledger, record=record)
        calls = json.loads(record.read_text())['attempts']
    elif stage == 'ocr':
        with pytest.raises(Exception, match='vision failed'):
            read_image({'id': 'image', 'image': str(MEDIA / 'example-post.png')}, client=client,
                       ledger=ledger, record=record, secrets=['private-key'])
        calls = json.loads(record.read_text())['attempts']
    else:
        with pytest.raises(ProviderFailure):
            if stage == 'extraction':
                extract_claims('Apple revenue $1 in FY2025.', client=client, ledger=ledger,
                               model='muse-spark-1.3', provider='meta', recorder=recorder)
            else:
                verify_claim('Apple revenue $1 in FY2025.', client, None, ledger,
                             'muse-spark-1.3', trace=recorder)
        calls = recorder.as_dict()['requests']
    assert len(calls) == 3 and delays == [1, 2]
    assert calls[-1]['retry']['exhausted']
    assert ledger.spent_total > 0
    assert 'private-key' not in json.dumps(calls)


def test_retry_success_and_nontransient_failure_and_budget_stop(monkeypatch, tmp_path):
    monkeypatch.setattr('claimcheck.retries.time.sleep', lambda _: None)
    client = SequenceClient([ProviderFailure(503), completed('{"claims": []}')])
    recorder = TraceRecorder('test', 'muse-spark-1.3')
    ledger = Ledger(tmp_path / 'ledger')
    assert extract_claims('post', client=client, ledger=ledger, model='muse-spark-1.3', provider='meta', recorder=recorder) == []
    assert len(recorder.requests) == 2 and recorder.requests[-1]['status'] == 'completed'
    client = SequenceClient([ProviderFailure(400)])
    with pytest.raises(ProviderFailure):
        extract_claims('post', client=client, ledger=ledger, model='muse-spark-1.3', provider='meta', recorder=recorder)
    assert len(client.requests) == 1
    client = SequenceClient([ProviderFailure(503), completed('{"claims": []}')])
    with pytest.raises(BudgetExceeded):
        extract_claims('post', client=client, ledger=Ledger(tmp_path / 'cap', budget_usd=.02), model='muse-spark-1.3', provider='meta', recorder=recorder)
    assert len(client.requests) == 1


def test_overlap_stitch_offsets_and_chunk_scoped_speakers():
    first = [{'id': 'turn-1', 'text': 'The company reported EPS growth of twelve percent.', 'start_ms': 585000, 'end_ms': 599000, 'speaker': 'A'}]
    second = [{'id': 'turn-1', 'text': 'EPS growth of twelve percent. Next topic.', 'start_ms': 0, 'end_ms': 15000, 'speaker': 'A'}]
    turns, edits = stitch_turns([({'start_ms': 0}, first), ({'start_ms': 590000}, second)])
    assert turns[1]['text'] == 'Next topic.'
    assert (turns[1]['start_ms'], turns[1]['end_ms']) == (590000, 605000)
    assert [t['speaker'] for t in turns] == ['chunk-1:A', 'chunk-2:A']
    assert edits[0]['removed_prefix'] == 'EPS growth of twelve percent. '
    second[0]['text'] = 'A different transcription.'
    turns, edits = stitch_turns([({'start_ms': 0}, first), ({'start_ms': 590000}, second)])
    assert edits[0]['unresolved'] and turns[1]['text'] == second[0]['text']


@pytest.mark.skipif(not shutil.which('ffmpeg') or not shutil.which('ffprobe'), reason='optional local codec integration')
def test_real_twelve_minute_clip_chunks_absolute_tail_and_upload_limits(tmp_path):
    _, channels = decode(MEDIA / 'long-call.flac', tmp_path / 'media')
    channel = channels[0]
    assert channel['duration_s'] == 720
    assert [(c['start_ms'], c['end_ms']) for c in channel['audio_chunks']] == [(0, 600000), (590000, 720000)]
    class HTTP:
        def post(self, *args, **kwargs):
            audio = kwargs['files']['audio'][1]
            with wave.open(audio) as wav:
                seconds = wav.getnframes() / wav.getframerate()
                assert 0 < seconds <= 600 and wav.getnchannels() == 1
            return SimpleNamespace(status_code=200, json=lambda: {'turns': [
                {'transcript': 'Apple EPS was 1.67 for fiscal Q3 2025.', 'speaker': 'A',
                 'startMs': int((seconds - 10) * 1000), 'endMs': int((seconds - 2) * 1000)}]})
    turns, record = transcribe(channel, http=HTTP(), api_key='fake-key', ledger=Ledger(tmp_path / 'ledger'), record=tmp_path / 'asr.json')
    assert turns[-1]['end_ms'] == 718000 and record['status'] == 'completed'
    assert len(record['chunks']) == 2


def test_long_extraction_windows_cover_all_text_and_preserve_tail(tmp_path):
    post = ('Nonfinancial source text. ' * 500) + '\nApple reported revenue of $94 billion for fiscal Q3 2025.'
    windows = extraction_windows(post)
    assert windows[0][0] == 0 and windows[-1][1] == len(post)
    assert all(b - a <= 6000 for a, b in windows)
    assert all(windows[i+1][0] < b for i, (a, b) in enumerate(windows[:-1]))
    client = SequenceClient([completed('{"claims": []}')] * len(windows))
    result = check_post(post, client=client, edgar=None, ledger=Ledger(tmp_path / 'ledger'), model='muse-spark-1.3',
                        provider='meta', out_dir=tmp_path / 'out', allow_long_input=True)
    assert len(client.requests) == len(windows) and 'revenue of $94 billion' in str(client.requests[-1])
    assert result['proposed_count'] == 0


@pytest.mark.parametrize('name', ['text', 'screenshot', 'audio', 'audio-two-voices', 'video', 'video-captioned', 'long-call'])
def test_new_probe_outputs_replay_through_final_runtime_without_network_or_codecs(monkeypatch, tmp_path, name):
    from claimcheck.ingest import ingest_file
    monkeypatch.setattr('claimcheck.retries.time.sleep', lambda _: None)
    folder = ROOT / 'docs/evidence/multimodal-2026-10-30' / name
    saved = json.loads((folder / 'ingest.json').read_text())
    protocol = json.loads((folder / 'protocol.json').read_text())
    requests, speech = [], []
    for channel in saved['channels']:
        if channel.get('media_call'):
            call = json.loads((folder / channel['media_call']).read_text())
            if channel['kind'] == 'transcript':
                if 'chunks' in call:
                    speech.extend(json.loads((folder / 'calls' / c['record']).read_text())['response'] for c in call['chunks'])
                else:
                    speech.append(call['response'])
            else:
                requests.append(call)
        if channel.get('extraction_trace'):
            requests.extend(json.loads((folder / channel['extraction_trace']).read_text())['requests'])
        for claim in channel.get('claims', []):
            if claim.get('trace_path'):
                requests.extend(json.loads((folder / 'checks' / channel['id'] / claim['trace_path']).read_text())['requests'])

    def recorded_decode(path, media_dir):
        media_dir.mkdir(parents=True)
        channels = []
        for old in saved['channels']:
            channel = {k: copy.deepcopy(v) for k, v in old.items() if k in {
                'id', 'kind', 'decoded', 'duration_s', 'sample_ms', 'image_info', 'audio_sha256', 'stitch_policy'}}
            if old['kind'] == 'text':
                channel['segments'] = [{k: s[k] for k in ('id', 'text')} for s in old['segments']]
            elif old['kind'] == 'transcript':
                # Bytes are not uploaded: fake ASR reads recorded responses.
                # Real decode/upload PCM limits are checked separately above.
                audio = media_dir / 'audio.wav'
                audio.write_bytes(b'RIFF offline replay placeholder')
                channel['audio'] = str(audio)
                if old.get('audio_chunks'):
                    channel['audio_chunks'] = [{**{k: c[k] for k in ('start_ms', 'end_ms', 'duration_s')}, 'audio': str(audio)} for c in old['audio_chunks']]
            else:
                image = media_dir / (old['id'] + '.png')
                source = MEDIA / 'example-post.png' if old['kind'] == 'ocr' else folder / old['image']
                shutil.copyfile(source, image)
                channel['image'] = str(image)
            channels.append(channel)
        return saved['input']['kind'], channels

    class HTTP:
        def post(self, *args, **kwargs):
            assert kwargs['files']['audio'][1].read(4) == b'RIFF'
            response = speech.pop(0)
            return SimpleNamespace(status_code=200, json=lambda: response)
    monkeypatch.setattr('claimcheck.ingest.decode', recorded_decode)
    replay = ReplayMeta(requests)
    edgar, releases = offline_clients(tmp_path)
    def outside_corpus(url):
        raise RuntimeError('SEC document is outside the committed probe corpus')
    edgar.fetcher = releases.fetcher = outside_corpus
    result = ingest_file(MEDIA / saved['input']['file'], client=replay, vision_client=replay,
        asr_http=HTTP(), meta_api_key='fake-key', edgar=edgar, release_client=releases,
        ledger=Ledger(tmp_path / 'ledger', budget_usd=5), model=saved['model'], provider=saved['provider'],
        out_dir=tmp_path / 'out', max_output_tokens=protocol['max_output_tokens'])
    assert result['status'] == saved['status'] and not replay.requests and not speech
    assert [s['status'] for s in result['stages']] == [s['status'] for s in saved['stages']]
    for actual, expected in zip(result['channels'], saved['channels']):
        assert actual['raw_text'] == expected['raw_text']
        assert [(c['status'], c.get('verdict')) for c in actual['claims']] == [(c['status'], c.get('verdict')) for c in expected['claims']]
        assert [c['source_locations'] for c in actual['claims']] == [c['source_locations'] for c in expected['claims']]


def test_report_recall_counts_values_and_quote_locations_without_credit_for_heading_rows(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / 'scripts/multimodal'))
    from build_hardening_report import claim_recall, number_score
    channel = {'normalized_text': 'Table: $94 billion revenue; $23 billion net income.',
               'raw_text': 'Table: $94 billion revenue; $23 billion net income.',
               'claims': [{'quote': 'Table: $94 billion revenue; $23 billion net income.',
                           'claim': 'Apple revenue was $94 billion in fiscal Q3 2025.',
                           'status': 'verified', 'kind': 'reported_fact', 'program_checks': [{}]}]}
    score = {'observed': [{'canonical_value': '94000000000', 'normalized_span': [7, 18]},
                          {'canonical_value': '23000000000', 'normalized_span': [28, 39]}],
             'expected': ['94000000000', '23000000000']}
    assert claim_recall(channel, score)['accepted'] == 1
    channel['claims'][0]['status'] = 'rejected'
    assert claim_recall(channel, score)['accepted'] == 0
    for folder, expected in [('multimodal-2026-10-29/audio-baseten', 1), ('multimodal-2026-10-30/audio', 5)]:
        report = json.loads((ROOT / 'docs/evidence' / folder / 'ingest.json').read_text())
        c = report['channels'][0]
        assert claim_recall(c, number_score(report['input']['file'], c))['accepted'] == expected
