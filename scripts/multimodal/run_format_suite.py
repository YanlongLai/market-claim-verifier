"""Replay the registered format probes with paid calls; retain commands and logs.

Example: .venv/bin/python scripts/multimodal/run_format_suite.py --out-root runs/formats-001
Never overwrites a previous suite. All cases share a $3 cap ($1/provider).
"""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / 'docs/evidence/input-formats-2026-10-30/probe-set.json'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-root', required=True, type=Path)
    args = parser.parse_args()
    output = args.out_root.resolve()
    if output.exists():
        parser.error('output already exists; choose a fresh directory')
    manifest = json.loads(MANIFEST.read_text())
    for case in manifest['cases']:
        source = ROOT / 'tests/fixtures/multimodal' / case['file']
        if hashlib.sha256(source.read_bytes()).hexdigest() != case['sha256']:
            parser.error(f"input hash mismatch: {case['name']}")
    output.mkdir(parents=True)
    (output / 'probe-set.json').write_text(MANIFEST.read_text())
    failures = 0
    for case in manifest['cases']:
        command = [sys.executable, str(ROOT / 'scripts/multimodal/run_probe.py'),
                   case['name'], case['file'], '--provider', case['provider'],
                   '--out-root', str(output), '--budget', str(manifest['budget_usd']),
                   '--max-output-tokens', '4000']
        record = {'case': case['name'], 'command': command,
                  'started_at': datetime.now(timezone.utc).isoformat()}
        with (output / f"{case['name']}.log").open('w') as log:
            process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, text=True)
            for line in process.stdout:
                print(line, end='', flush=True)
                log.write(line)
                log.flush()
            record['exit_code'] = process.wait()
        record['finished_at'] = datetime.now(timezone.utc).isoformat()
        with (output / 'execution.jsonl').open('a') as handle:
            handle.write(json.dumps(record) + '\n')
        failures += record['exit_code'] != 0
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
