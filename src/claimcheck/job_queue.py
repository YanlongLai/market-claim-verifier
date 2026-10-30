"""Serial, resumable local ingestion queue with conservative budget admission."""
import fcntl
import hashlib
import json
import math
from pathlib import Path
import shutil
from typing import Callable


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root: Path) -> dict:
    result = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError('queue snapshots and outputs cannot contain symlinks')
        if path.is_file() and not path.name.endswith('.lock'):
            result[str(path.relative_to(root))] = sha(path)
    return result


def engine_identity() -> dict:
    package = Path(__file__).parent
    files = {p.name: sha(p) for p in sorted(package.glob('*.py'))}
    root = package.parent.parent
    for p in sorted((root / 'prompts').glob('*.md')):
        files['prompts/' + p.name] = sha(p)
    if (root / 'uv.lock').exists():
        files['uv.lock'] = sha(root / 'uv.lock')
    return files


def evidence_files(cache: Path) -> dict:
    paths = [cache / 'company_tickers.json', *cache.glob('companyfacts-*.json')]
    if (cache / 'releases').is_symlink():
        raise ValueError('release cache symlinks are not accepted')
    if (cache / 'releases').exists():
        paths.extend((cache / 'releases').rglob('*'))
    result = {}
    for p in sorted(set(paths)):
        if p.is_symlink():
            raise ValueError('evidence cache symlinks are not accepted')
        if p.is_file() and not p.name.endswith('.lock'):
            result[str(p.relative_to(cache))] = sha(p)
    if not result:
        raise ValueError('provide a populated SEC evidence cache')
    return result


def save(path: Path, state: dict) -> None:
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True) + '\n')
    tmp.replace(path)


def run_queue(files: list[Path], cache: Path, out: Path, config: dict,
              worker: Callable, *, max_jobs: int = 10) -> dict:
    """Worker must enforce the supplied per-job cap via the reservation ledger.

    Unknown outcomes never retry automatically. Entire successful jobs are reused;
    interrupted/partial channels are not silently repeated.
    """
    total, cap = config['budget_usd'], config['per_job_budget_usd']
    if any(not math.isfinite(v) or v <= 0 for v in (total, cap)) or max_jobs < 1:
        raise ValueError('budgets and max_jobs must be positive and finite')
    if not files or len(files) > 100:
        raise ValueError('queue accepts 1–100 local inputs')
    from .ingest_media import input_kind, MAX_BYTES
    for p in files:
        input_kind(p)
        if not p.is_file() or not 0 < p.stat().st_size <= MAX_BYTES:
            raise ValueError('each queue input must be a nonempty supported file up to 128 MiB')
    identity = {'config': config, 'engine_and_prompts': engine_identity(),
                'inputs': [{'name': p.name, 'sha256': sha(p)} for p in files],
                'evidence': evidence_files(cache)}
    keys = [(p.suffix.lower(), item['sha256']) for p, item in zip(files, identity['inputs'])]
    if len(set(keys)) != len(keys):
        raise ValueError('duplicate input content; submit each input once')
    out.mkdir(parents=True, exist_ok=True)
    with (out / 'queue.lock').open('a+') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError('queue already has an active worker') from exc
        state_path = out / 'queue.json'
        if state_path.exists():
            state = json.loads(state_path.read_text())
            if state['identity'] != identity:
                raise ValueError('input, evidence, model, prompt, policy, price/code or budget changed; use a new queue')
            if inventory(out / 'evidence-cache') != identity['evidence']:
                raise ValueError('frozen evidence cache changed')
            for job in state['jobs']:
                if sha(out / job['input']) != job['sha256']:
                    raise ValueError('frozen input changed')
                if job['status'] == 'completed' and inventory(out / job['out']) != job['artifacts']:
                    raise ValueError('completed job artifacts changed; refusing reuse')
                if job['status'] == 'running':
                    job['status'] = 'needs_review'
                    job['reason'] = 'Previous process stopped with unknown API outcome; no automatic retry.'
            save(state_path, state)
        else:
            if any(p.name != 'queue.lock' for p in out.iterdir()):
                raise ValueError('new queue requires an empty output directory')
            frozen = out / 'evidence-cache'
            for name, expected in identity['evidence'].items():
                dest = frozen / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(cache / name, dest)
                if sha(dest) != expected:
                    raise ValueError('source cache changed during snapshot')
            jobs = []
            for i, (path, item) in enumerate(zip(files, identity['inputs'])):
                dest = out / 'inputs' / f'{i:04d}{path.suffix.lower()}'
                dest.parent.mkdir(exist_ok=True)
                shutil.copyfile(path, dest)
                if sha(dest) != item['sha256']:
                    raise ValueError('source input changed during snapshot')
                jobs.append({'id': i, 'input': str(dest.relative_to(out)), 'sha256': item['sha256'],
                             'out': f'jobs/{i:04d}', 'status': 'pending'})
            state = {'schema_version': 1, 'identity': identity, 'jobs': jobs,
                     'budget_basis': 'Sum of full admitted job caps; unused allowance is not recycled.',
                     'billed_usd': None}
            save(state_path, state)
        if state.get('budget_review_required'):
            return state
        admitted = sum(cap for j in state['jobs'] if j['status'] != 'pending')
        processed = 0
        for job in state['jobs']:
            if job['status'] != 'pending':
                continue
            if processed >= max_jobs or admitted + cap > total + 1e-12:
                break
            if inventory(out / 'evidence-cache') != identity['evidence']:
                raise ValueError('frozen evidence cache changed')
            job['status'] = 'running'
            admitted += cap
            save(state_path, state)
            try:
                report = worker(out / job['input'], out / job['out'], out / 'evidence-cache', cap)
                target = out / job['out']
                target.mkdir(parents=True, exist_ok=True)
                save(target / 'queue-result.json', report)
                amount = report.get('cost_usd')
                if type(amount) not in (float, int) or not math.isfinite(amount) or not 0 <= amount <= cap + 1e-8:
                    state['budget_review_required'] = True
                    raise ValueError('worker cost is unknown or exceeds allocated budget; inspect ledger')
                job['status'] = 'completed' if report.get('status') == 'completed' else 'needs_review'
                job['estimated_or_reserved_usd'] = report.get('cost_usd')
                job['artifacts'] = inventory(target)
            except Exception as exc:
                job['status'] = 'needs_review'
                job['reason'] = f'Worker failed ({type(exc).__name__}); inspect local traces, no automatic retry.'
            save(state_path, state)
            processed += 1
            if state.get('budget_review_required'):
                break
        state['admitted_budget_usd'] = admitted
        state['status'] = ('needs_review' if any(j['status'] == 'needs_review' for j in state['jobs']) else
                           'pending' if any(j['status'] == 'pending' for j in state['jobs']) else 'completed')
        save(state_path, state)
        return state


def cli_worker(settings, config: dict):
    """Build an ingestion worker with a job-local ledger and frozen SEC sources."""
    import httpx
    from .budget import Ledger
    from .config import load_settings
    from .edgar import EdgarClient
    from .ingest import ingest_file
    from .providers import create_client
    from .release_fetch import ReleaseClient

    def no_network(url):
        raise RuntimeError('source absent from frozen queue cache; source fetching disabled')

    def work(source: Path, target: Path, cache: Path, cap: float):
        meta = settings if settings.provider == 'meta' else load_settings(provider='meta')
        budgets = {'meta': cap} if settings.provider == 'meta' else {'meta': cap / 2, settings.provider: cap / 2}
        ledger = Ledger(target / 'ledger.jsonl', budget_usd=cap, provider=settings.provider, provider_budgets=budgets)
        client = create_client(settings.provider, settings.model_api_key).with_options(max_retries=0) if settings.model_api_key else None
        vision = client if settings.provider == 'meta' else create_client('meta', meta.model_api_key).with_options(max_retries=0) if meta.model_api_key else None
        with httpx.Client(timeout=120) as http:
            return ingest_file(source, client=client, vision_client=vision, asr_http=http,
                meta_api_key=meta.model_api_key, edgar=EdgarClient(cache, fetcher=no_network, as_of=config['as_of']),
                release_client=ReleaseClient(cache, fetcher=no_network), ledger=ledger,
                model=config['model'], provider=settings.provider, out_dir=target,
                max_claims=config['max_claims'], max_output_tokens=config['max_output_tokens'],
                reasoning_effort=config['reasoning_effort'],
                secrets=[k for k in (settings.model_api_key, meta.model_api_key) if k])
    return work
