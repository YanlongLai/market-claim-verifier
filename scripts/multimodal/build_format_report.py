"""Rebuild the format smoke-test report from retained runs; no model calls."""
import json
import hashlib
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/evidence/input-formats-2026-10-30'


def main():
    manifest = json.loads((OUT / 'probe-set.json').read_text())
    lines = ['# Input-format smoke probes — 2026-10-30', '',
        'Six cases selected before paid execution; known synthetic Apple US-equity fixtures. One run per case, failures retained. These are integration smoke tests, not held-out accuracy or a controlled provider comparison.', '',
        'The [frozen probe set](probe-set.json) records input hashes, generation and the $3 shared cap ($1 per provider). SDK retries are disabled; existing bounded transient retries are reserved and traced. SEC data is replayed from committed fixtures, without live SEC requests.', '',
        '## Recorded results', '',
        '| Format | Text provider | Status | Proposed / accepted / checked | Verdict counts | Estimated USD | Seconds |',
        '|---|---|---|---|---|---:|---:|']
    reusable = []
    reported_total = 0.0
    for case in manifest['cases']:
        source = ROOT / 'tests/fixtures/multimodal' / case['file']
        if hashlib.sha256(source.read_bytes()).hexdigest() != case['sha256']:
            raise SystemExit(f"Input hash changed: {case['name']}")
        name = case['name']
        report = json.loads((OUT / name / 'ingest.json').read_text())
        if report['status'] == 'running':
            raise SystemExit(f'{name} is still running')
        reported_total += report['cost_usd']
        frozen = []
        for channel in report['channels']:
            folder = OUT / name / 'frozen-text'
            folder.mkdir(exist_ok=True)
            for field in ('raw_text', 'normalized_text'):
                if field not in channel:
                    continue
                target = folder / f"{channel['id']}-{field}.txt"
                target.write_text(channel[field])
                frozen.append({'channel': channel['id'], 'field': field,
                               'path': str(target.relative_to(OUT)),
                               'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
        reusable.append({'case': case, 'status': report['status'],
                         'cost_usd': report['cost_usd'], 'coverage': report['coverage'],
                         'protocol': f'{name}/protocol.json', 'report': f'{name}/ingest.json',
                         'frozen_text': frozen})
        coverage = report['coverage']
        verdicts = Counter(c.get('verdict', c.get('status', 'unknown')) for ch in report['channels'] for c in ch.get('claims', []))
        counts = ' / '.join(str(coverage[k]) for k in ('proposed_claims', 'accepted_claims', 'program_checked_claims'))
        summary = ', '.join(f'{k}: {v}' for k, v in sorted(verdicts.items())) or 'none'
        lines.append(f"| [{name}]({name}/ingest.html) | {case['provider']} | {report['status']} | {counts} | {summary} | ${report['cost_usd']:.6f} | {report['wall_clock_s']:.1f} |")
    reserves, reconciles = {}, {}
    for line in (OUT / 'ledger.jsonl').read_text().splitlines():
        e = json.loads(line)
        key = (e['provider'], e['reservation_id'])
        (reconciles if e['event'] == 'reconcile' else reserves)[key] = e['amount']
    totals = defaultdict(float)
    for key in reserves.keys() | reconciles.keys():
        totals[key[0]] += reconciles.get(key, reserves.get(key, 0))
    if abs(reported_total - sum(totals.values())) > 0.000001:
        raise SystemExit('Per-case costs do not reconcile to ledger')
    if sum(totals.values()) > manifest['budget_usd']:
        raise SystemExit('Recorded cost exceeds registered cap')
    lines += ['', '## Spend', '', '| Provider | Estimated USD |', '|---|---:|']
    lines += [f'| {p} | ${v:.8f} |' for p, v in sorted(totals.items())]
    lines += [f'| Total | ${sum(totals.values()):.8f} |', '',
        'Usage-based estimates use the repository price ledger, not provider invoices. Unreconciled reservations, if present, remain included. No private account balances are published.', '',
        '## Interpretation and boundaries', '',
        '- Markdown, JPEG, WebP and PDF contain the same two known assertions: revenue $94.036 billion (supported) and deliberately wrong diluted EPS $1.67 (contradicted; filed value $1.57), Apple fiscal Q3 2025. Inspect the exact quotes and program checks, not just run completion.',
        '- MP3 re-encodes the existing synthetic release reading, including deliberately incorrect EPS. Silent video reuses the existing table slides. Their assertion counts differ from the two-claim controls; no cross-format accuracy ranking is justified.',
        '- JPEG/WebP use Meta OCR; MP3 uses Meta ASR; silent video uses only three Meta OCR frames. The chosen provider performs text extraction and verification. This does not test Baseten/Fireworks native media endpoints.',
        '- The silent-video run is partial because the input has no audio track. All four extracted visual claims were program-checked (three supported, one contradicted); the missing audio channel is retained, not silently dropped. This does not establish coverage outside the three sampled frames.',
        '- PDF uses local page text extraction, not vendor-native PDF or OCR. Audio does not establish speaker identity; sampled video does not establish whole-video coverage.',
        '- Proposed/accepted/checked counts describe processing, not recall or truth accuracy. Insufficient evidence and missed/rejected assertions remain visible. Small synthetic probes do not validate other codecs, noisy recordings, complex PDFs, or two-hour inputs.',
        '- General URLs and scanned PDFs remain unsupported. No new integration status is inferred solely from a successful smoke probe.', '',
        '## Validation', '', '[Validation receipt](validation.json) and [full offline log](offline-verification.log) retain commands and results. Final report rebuild/hash/cost checks and final documentation links are checked after paid completion.', '', '## Reproduce and reuse', '', '[Machine-readable index](runs.json) lists each input hash, protocol, outcome, cost, coverage and frozen text. Each run retains calls/ (OCR or ASR requests/responses when applicable), checks/ traces (extraction and verifier requests/responses), ingest.json and ingest.html. Frozen raw/normalized text can be rechecked without paying for OCR/ASR again; that only tests downstream text verification and does not revalidate media extraction, timestamps or attribution.', '', 'Replay all registered cases in a fresh output root; the suite retains command arguments, exit codes and stdout/stderr logs:', '', '```sh', '.venv/bin/python scripts/multimodal/run_format_suite.py --out-root runs/formats-001', '```', '', 'For one case:', '', '```sh',
        '.venv/bin/python scripts/multimodal/run_probe.py markdown format-probes/post.md \\',
        '  --provider fireworks --out-root runs/format-recheck --budget 3 --max-output-tokens 4000', '```', '',
        'Use the remaining file/provider pairs in probe-set.json with the same output root to share the cap. This makes paid calls. Existing result directories are never overwritten. To rebuild this report offline: `python3 scripts/multimodal/build_format_report.py`.', '']
    (OUT / 'runs.json').write_text(json.dumps(reusable, indent=2) + '\n')
    (OUT / 'REPORT.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    main()
