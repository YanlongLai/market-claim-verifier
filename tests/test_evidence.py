import copy
import json
import pytest
from claimcheck.evidence import SecReleaseConnector, export_bundle
from claimcheck.release_text import parse_html
from test_release import CLAIMS, selected


def example():
    runner, _, sub = selected(CLAIMS[0])
    quote = runner.evidence[sub['evidence_ids'][0]]
    raw, metadata = runner.release_service.client.read(quote['exhibit_url'])
    text = parse_html(raw).text
    return quote, raw, text, metadata


def test_real_meta_release_export_and_bundle(tmp_path):
    quote, raw, text, metadata = example()
    record = SecReleaseConnector().export(quote=quote, raw=raw, text=text, metadata=metadata)
    assert record.to_dict() == quote['evidence_record']
    assert record.to_dict()['fact']['low'] == 47.5e9
    assert record.to_dict()['authority']['audited'] is False
    mutable = record.to_dict()
    mutable['fact']['low'] = 1
    assert record.to_dict()['fact']['low'] == 47.5e9
    target = export_bundle(record, raw, text, tmp_path)
    assert json.loads(target.read_text()) == record.to_dict()
    assert export_bundle(record, raw, text, tmp_path) == target
    target.write_text('tampered')
    with pytest.raises(ValueError, match='modified'):
        export_bundle(record, raw, text, tmp_path)


@pytest.mark.parametrize('field,value', [('exhibit_url', 'https://example.com/release.html'),
    ('low', 1), ('value', 777), ('span_verified', False), ('start', 1), ('quote', 'invented'), ('sha256', '0' * 64)])
def test_reject_unadmitted_or_mutated_evidence(field, value):
    quote, raw, text, metadata = example()
    quote = copy.deepcopy(quote)
    quote[field] = value
    with pytest.raises(ValueError):
        SecReleaseConnector().export(quote=quote, raw=raw, text=text, metadata=metadata)


def test_changed_raw_bytes_fail():
    quote, raw, text, metadata = example()
    with pytest.raises(ValueError, match='integrity'):
        SecReleaseConnector().export(quote=quote, raw=raw+b' ', text=text, metadata=metadata)
