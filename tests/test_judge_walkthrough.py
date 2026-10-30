import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / 'examples/evidence'
COMMITTED = ROOT / 'docs/evidence/judge-walkthrough'


def builder(monkeypatch):
    monkeypatch.syspath_prepend(str(EXAMPLES))
    spec = importlib.util.spec_from_file_location('judge_walkthrough', EXAMPLES / 'judge_walkthrough.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build


def test_three_actual_program_verdicts_and_reproducible_artifacts(tmp_path, monkeypatch):
    result = builder(monkeypatch)(tmp_path)
    checks = [row['program_check'] for row in result['results']]
    assert [c['program_verdict'] for c in checks] == ['supported', 'contradicted', 'insufficient_evidence']
    assert checks[0]['actual_range'] == [47.5e9, 50.5e9]
    assert checks[1]['stated_range'] == [48.5e9, 51.5e9]
    assert not checks[2]['evidence_valid']
    assert result['cost']['incremental_api_total'] == 0
    assert result['cost']['api_requests'] == 0
    assert 'Not measured' in result['cost']['live_cost']
    expected = {p.relative_to(COMMITTED) for p in COMMITTED.rglob('*') if p.is_file()}
    actual = {p.relative_to(tmp_path) for p in tmp_path.rglob('*') if p.is_file()}
    assert actual == expected
    for path in expected:
        assert (tmp_path / path).read_bytes() == (COMMITTED / path).read_bytes(), path


def test_modified_evidence_bundle_is_not_silently_replaced(tmp_path, monkeypatch):
    build = builder(monkeypatch)
    build(tmp_path)
    source = next((tmp_path / 'evidence').glob('*.html'))
    source.write_bytes(b'changed')
    with pytest.raises(ValueError, match='modified'):
        build(tmp_path)
