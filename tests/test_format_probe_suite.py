"""The reuse runner must refuse mutation/spend on stale input or old output."""
import importlib.util
import json
from pathlib import Path
import pytest


def runner():
    path = Path(__file__).parents[1] / 'scripts/multimodal/run_format_suite.py'
    spec = importlib.util.spec_from_file_location('format_suite', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_existing_output_refused_before_paid_process(tmp_path, monkeypatch):
    module = runner()
    monkeypatch.setattr(module.sys, 'argv', ['suite', '--out-root', str(tmp_path)])
    monkeypatch.setattr(module.subprocess, 'Popen', lambda *a, **k: pytest.fail('must not call provider'))
    with pytest.raises(SystemExit) as exc:
        module.main()
    assert exc.value.code == 2
    assert not list(tmp_path.iterdir())


def test_input_hash_mismatch_refused_before_paid_process(tmp_path, monkeypatch):
    module = runner()
    source = tmp_path / 'tests/fixtures/multimodal'
    source.mkdir(parents=True)
    (source / 'input.txt').write_text('changed')
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'cases': [{'name': 'changed', 'file': 'input.txt', 'sha256': 'incorrect'}]}))
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    monkeypatch.setattr(module, 'MANIFEST', manifest)
    monkeypatch.setattr(module.sys, 'argv', ['suite', '--out-root', str(tmp_path / 'out')])
    monkeypatch.setattr(module.subprocess, 'Popen', lambda *a, **k: pytest.fail('must not call provider'))
    with pytest.raises(SystemExit) as exc:
        module.main()
    assert exc.value.code == 2
    assert not (tmp_path / 'out').exists()
