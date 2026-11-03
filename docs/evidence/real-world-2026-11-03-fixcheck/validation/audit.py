"""Read-only audit of retained fixcheck attempts and their one shared ledger."""
import hashlib
import json
import io
import subprocess
import tarfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / 'docs/evidence/real-world-2026-11-02'
MODELS = {'baseten': 'meta-models/muse-spark-open-1026',
          'fireworks': 'accounts/fireworks/models/muse-spark-open', 'meta': 'muse-spark-1.3'}

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def audit():
    events = [json.loads(line) for line in (OUT / 'ledger.jsonl').read_text().splitlines()]
    reserved = {e['reservation_id']: e for e in events if e['event'] == 'reserve'}
    reconciled = {e['reservation_id']: e for e in events if e['event'] == 'reconcile'}
    assert set(reconciled) <= set(reserved)
    assert len(reserved) == sum(e['event'] == 'reserve' for e in events)
    assert all(e['model'] == MODELS[e['provider']] for e in reserved.values())
    effective = {i: reconciled.get(i, e)['amount'] for i, e in reserved.items()}
    costs = {p: sum(effective[i] for i, e in reserved.items() if e['provider'] == p) for p in MODELS}
    assert all(v <= 5 for v in costs.values())
    seen, attempts, row_costs = Counter(), {}, Counter()
    for target in sorted((OUT / 'sets').iterdir()):
        if not (target / 'RUN_START.json').exists():
            continue
        assert (target / 'RUN_END.json').exists(), 'unfinished attempt: ' + target.name
        registration = json.loads((target / 'RUN_START.json').read_text())['freeze']
        assert digest(target / 'FREEZE.json') == registration['freeze_sha256']
        frozen = json.loads((target / 'FREEZE.json').read_text())['sha256']
        git_dir = Path('/private/tmp/real-world-fixes-local.git')
        git = ['git', *([f'--git-dir={git_dir}'] if git_dir.exists() else [])]
        archive = subprocess.check_output([*git, 'archive', registration['revision'], 'src/claimcheck',
            'prompts', 'scripts/real_world', 'tests/test_real_world_fixes.py', 'sources/registry.yaml'], cwd=ROOT)
        committed_runtime = 0
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            for member in tar:
                if member.isfile() and member.name in frozen:
                    assert hashlib.sha256(tar.extractfile(member).read()).hexdigest() == frozen[member.name]
                    committed_runtime += 1
        cases = [json.loads(l) for l in (target / 'claims.jsonl').read_text().splitlines()]
        ids = {c['id'] for c in cases}
        if target.name.startswith('news'):
            assert all(digest(target / f) == digest(BASELINE / f) for f in ('claims.jsonl', 'gold.jsonl'))
        blocks = {}
        for provider in MODELS:
            for path in ('agent', 'post'):
                records = [json.loads(p.read_text()) for p in (target / provider / path).glob('*/result.json')]
                assert len(records) == len(ids) and {r['id'] for r in records} == ids
                row_costs[provider] += sum(r['cost_usd'] for r in records)
                blocks[provider + '/' + path] = dict(Counter(r['status'] for r in records))
                if target.name.startswith('news'):
                    hon = next(r for r in records if r['id'] == 'RW046')
                    assert hon.get('verdict') not in {'supported', 'contradicted'} and not hon.get('any_supported')
        traces = [*target.glob('*/agent/*/trace.json'), *target.glob('*/post/*/traces/*.json')]
        for f in traces:
            t = json.loads(f.read_text())
            for request in t.get('requests', []):
                reservation = request.get('reservation') or {}
                i = reservation.get('reservation_id')
                if i:
                    assert i in reserved, 'trace request absent from ledger'
                    seen[i] += 1
        attempts[target.name] = {'items': len(ids), 'systems': blocks, 'trace_files': len(traces),
                                'registered_revision': registration['revision'],
                                'committed_runtime_files_verified': committed_runtime}
    assert set(seen) == set(reserved), 'ledger/trace reservation mismatch'
    assert all(n == 1 for n in seen.values()), 'duplicate retained request reservation'
    assert all(abs(row_costs[p] - costs[p]) < 1e-8 for p in MODELS), 'row/ledger cost mismatch'
    freeze = json.loads((OUT / 'sets/news/FREEZE.json').read_text())['sha256']
    original = {p: h for p, h in freeze.items() if p.startswith('docs/evidence/real-world-2026-11-02/')}
    assert all(digest(ROOT / p) == h for p, h in original.items()), 'original evidence changed'
    return {'passed': True, 'attempts': attempts, 'original_files_unchanged': len(original),
            'reservation_count': len(reserved), 'reconciled_count': len(reconciled),
            'unreconciled_reservations': len(set(reserved) - set(reconciled)),
            'ledger_usd': costs, 'row_cost_usd': dict(row_costs), 'models': MODELS,
            'cap_usd_per_provider': 5, 'no_best_of_selection': True, 'held_out': False}

if __name__ == '__main__':
    result = audit()
    target = OUT / 'validation/audit.json'
    if target.exists():
        raise RuntimeError('audit result exists; retain it and choose a new receipt name')
    target.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
