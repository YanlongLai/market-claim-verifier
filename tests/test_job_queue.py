import json
from pathlib import Path
import pytest
from claimcheck.job_queue import run_queue


def setup(tmp_path):
    cache = tmp_path / 'cache'
    cache.mkdir()
    (cache / 'company_tickers.json').write_text('{}')
    files = [tmp_path / 'a.txt', tmp_path / 'b.txt']
    for i, file in enumerate(files):
        file.write_text(str(i))
    return files, cache, tmp_path / 'queue', {'budget_usd': 2.0, 'per_job_budget_usd': 1.0}


def test_resume_skips_success_and_respects_per_invocation_limit(tmp_path):
    files, cache, out, config = setup(tmp_path)
    calls = []
    def worker(source, target, frozen, cap):
        calls.append(source.read_text())
        assert (frozen / 'company_tickers.json').read_text() == '{}'
        assert cap == 1
        return {'status': 'completed', 'cost_usd': 0.1}
    first = run_queue(files, cache, out, config, worker, max_jobs=1)
    assert first['status'] == 'pending'
    assert calls == ['0']
    second = run_queue(files, cache, out, config, worker)
    assert second['status'] == 'completed'
    run_queue(files, cache, out, config, worker)
    assert calls == ['0', '1']
    assert second['admitted_budget_usd'] == 2


def test_budget_admission_does_not_recycle_unspent_allowance(tmp_path):
    files, cache, out, config = setup(tmp_path)
    config['budget_usd'] = 1.5
    result = run_queue(files, cache, out, config, lambda *a: {'status': 'completed', 'cost_usd': 0.01})
    assert [j['status'] for j in result['jobs']] == ['completed', 'pending']
    assert result['admitted_budget_usd'] == 1


def test_crash_outcome_never_retries(tmp_path):
    files, cache, out, config = setup(tmp_path)
    calls = []
    def crash(*args):
        calls.append(1)
        raise KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt):
        run_queue(files, cache, out, config, crash)
    result = run_queue(files, cache, out, config, lambda *a: {'status': 'completed', 'cost_usd': 0.1})
    assert calls == [1]
    assert [j['status'] for j in result['jobs']] == ['needs_review', 'completed']


@pytest.mark.parametrize('changed', ['input', 'source', 'model', 'artifact'])
def test_changed_identity_or_artifacts_refuses_reuse(tmp_path, changed):
    files, cache, out, config = setup(tmp_path)
    worker = lambda *a: {'status': 'completed', 'cost_usd': 0.1}
    run_queue(files, cache, out, config, worker)
    if changed == 'input': files[0].write_text('different')
    if changed == 'source': (cache / 'company_tickers.json').write_text('{"new":1}')
    if changed == 'model': config['model'] = 'other'
    if changed == 'artifact': (out / 'jobs/0000/queue-result.json').write_text('{}')
    with pytest.raises(ValueError):
        run_queue(files, cache, out, config, worker)


def test_partial_report_is_not_automatically_retried(tmp_path):
    files, cache, out, config = setup(tmp_path)
    calls = []
    def worker(*a):
        calls.append(1)
        return {'status': 'partial', 'cost_usd': 0.2}
    run_queue(files, cache, out, config, worker)
    result = run_queue(files, cache, out, config, worker)
    assert len(calls) == 2
    assert result['status'] == 'needs_review'


def test_active_worker_lock(tmp_path):
    import fcntl
    files, cache, out, config = setup(tmp_path)
    out.mkdir()
    with (out / 'queue.lock').open('a+') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(ValueError, match='active worker'):
            run_queue(files, cache, out, config, lambda *a: None)


def test_duplicate_inputs_rejected(tmp_path):
    files, cache, out, config = setup(tmp_path)
    with pytest.raises(ValueError, match='duplicate'):
        run_queue([files[0], files[0]], cache, out, config, lambda *a: None)


def test_cost_overrun_stops_admission_and_resume(tmp_path):
    files, cache, out, config = setup(tmp_path)
    calls = []
    def worker(*a):
        calls.append(1)
        return {'status': 'completed', 'cost_usd': 2}
    result = run_queue(files, cache, out, config, worker)
    assert result['budget_review_required']
    assert [j['status'] for j in result['jobs']] == ['needs_review', 'pending']
    run_queue(files, cache, out, config, worker)
    assert len(calls) == 1
