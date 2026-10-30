"""Rebuild the 2026-10-30 hardening probe and comparison without model calls."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from claimcheck.budget import Ledger
from claimcheck.ingest import render_html
from claimcheck.ingest_media import write_json
from build_report import accuracy, cell, financial_numbers

OUT = ROOT / 'docs/evidence/multimodal-2026-10-30'
BEFORE = ROOT / 'docs/evidence/multimodal-2026-10-29'
CASES = {'text': 'text', 'screenshot': 'screenshot', 'audio': 'audio-baseten',
         'audio-two-voices': 'audio-two-voices', 'video': 'video',
         'video-captioned': 'video-captioned-baseten', 'long-call': None}


def number_score(filename: str, channel: dict) -> dict:
    if filename != 'long-call.flac':
        return accuracy(filename, channel)
    expected = json.loads((ROOT / 'tests/fixtures/multimodal/long-generation.json').read_text())['expected_financial_mentions']
    observed = financial_numbers(channel.get('raw_text', ''))
    keys = [n['canonical_value'] for n in observed]
    matched = sum(b.size for b in SequenceMatcher(a=expected, b=keys, autojunk=False).get_matching_blocks())
    return {'expected': expected, 'observed': observed, 'matched': matched, 'extra': len(observed) - matched,
            'available': bool(channel.get('raw_text'))}


def claim_recall(channel: dict, score: dict) -> dict:
    """Expected financial mentions represented by source-backed accepted claims.

    Require both the rewrite's value and a corresponding source quote span.
    Count repeated source mentions independently, never date/quarter numbers.
    This is numeric-assertion coverage, not semantic correctness or WER.
    """
    source = channel.get('normalized_text', '')
    observed = score['observed']
    covered: set[int] = set()
    checked: set[int] = set()
    for claim in channel.get('claims', []):
        if claim.get('status') == 'rejected' or claim.get('kind') not in {'reported_fact', 'issuer_guidance'}:
            continue
        quote = claim.get('quote', '')
        if not quote:
            continue
        pattern = r'\s+'.join(re.escape(w) for w in quote.split())
        spans = claim.get('quote_spans')
        if spans is None:
            spans = [list(m.span()) for m in re.finditer(pattern, source)]
        for start, end in spans:
            remaining = Counter(m['canonical_value'] for m in financial_numbers(claim['claim']))
            for i, number in enumerate(observed):
                a, b = number['normalized_span']
                key = number['canonical_value']
                if a < end and b > start and remaining[key]:
                    covered.add(i)
                    remaining[key] -= 1
                    if claim.get('program_checks'):
                        checked.add(i)
    keys = [n['canonical_value'] for n in observed]
    aligned = SequenceMatcher(a=score['expected'], b=keys, autojunk=False).get_matching_blocks()
    expected_observed = {b.b + i for b in aligned for i in range(b.size)}
    return {'accepted': len(covered & expected_observed), 'program_checked': len(checked & expected_observed),
            'expected': len(score['expected']), 'covered_observed_indices': sorted(covered & expected_observed)}


def counts(report: dict) -> dict:
    claims = [c for channel in report['channels'] for c in channel.get('claims', [])]
    return dict(Counter(c.get('verdict', c['status']) for c in claims))


def main() -> None:
    runs = {p.parent.name: json.loads(p.read_text()) for p in sorted(OUT.glob('*/ingest.json'))}
    if set(runs) != set(CASES) or any(r['status'] == 'running' for r in runs.values()):
        raise SystemExit('wait for exactly the seven planned probe cases to finish')
    ledger = Ledger(OUT / 'ledger.jsonl')
    total = ledger.spent_total
    if abs(total - sum(r['cost_usd'] for r in runs.values())) > .000001:
        raise SystemExit('per-run charges do not reconcile with the ledger')
    scores, comparisons = {}, {}
    for name, report in runs.items():
        scores[name] = {}
        for channel in report['channels']:
            score = number_score(report['input']['file'], channel)
            scores[name][channel['id']] = {**score, 'claim_recall': claim_recall(channel, score)}
        (OUT / name / 'ingest.html').write_text(render_html(report))
        old_name = CASES[name]
        if old_name:
            old = json.loads((BEFORE / old_name / 'ingest.json').read_text())
            previous = {c['id']: claim_recall(c, number_score(old['input']['file'], c)) for c in old['channels']}
            comparisons[name] = {'before_run': old_name, 'before': previous,
                                 'after': {k: v['claim_recall'] for k, v in scores[name].items()},
                                 'before_verdicts': counts(old), 'after_verdicts': counts(report)}
    write_json(OUT / 'number-accuracy.json', {'policy': 'Ordered financial mentions; unit scaling; dates and quarter/year labels excluded. Extras retained. Not WER.', 'runs': scores})
    write_json(OUT / 'before-after.json', {'policy': 'Numeric assertion recall: an expected mention must match both a guarded claim value and its exact source quote span. All recorded baseline stop states count as missed; repeats in long audio count separately. Not semantic accuracy. Baseline selection frozen in probe-set.json; no best-of rerun selection.', 'runs': comparisons})
    lines = ['# Multimodal input probe — 2026-10-30', '',
        f'**{len(runs)} exploratory hardening runs; estimated new spend ${total:.8f}; '
        f'combined with the recorded $1.30508830: ${total + 1.3050883:.8f}, below the $15 task cap.** '
        'This is a post-hoc development probe on known synthetic media, not a held-out evaluation. '
        'Every stop state, rejected rewrite and insufficient-evidence result remains in the records.', '',
        '## Protocol and media', '',
        'Runtime inference uses only Meta models: `muse-spark-1.3` for OCR/Meta text, '
        '`meta-models/muse-spark-open-1026` for Baseten text, and `muse-voice-transcribe-1.0` for ASR. '
        'Keys load through `claimcheck.config` and are redacted. SDK retries are zero. HTTP 500/502/503/504 '
        'gets at most three attempts with 1s/2s backoff; each attempt has its own reservation and trace. '
        'Other errors are not retried by this policy. Failed attempts retain conservative reservations. '
        'The new locked ledger is capped at $13.69 (Meta $8, Baseten $5.69), reserving $1.31 for prior spend. '
        'All SEC retrieval is restricted to committed hash-checked snapshots; no live SEC or external call media is used.', '',
        '[Probe set and baseline choices](probe-set.json) list the seven cases. The evidence directory uses the requested '
        '2026-10-30 label; actual UTC execution times are in each `protocol.json`. Text and screenshot retain the baseline '
        '4,000-token limit; remaining cases use 8,000 (the row-only baseline used 4,000, a comparison confound). '
        'Source hashes, provider IDs, input hashes, usage, failure attempts and post/tool traces are retained per run.', '',
        'The short media are unchanged from the [2026-10-29 report](../multimodal-2026-10-29/REPORT.md): '
        'Apple FY2025 Q3 release excerpts with EPS deliberately changed from $1.57 to $1.67; row slides retain both correct and wrong EPS. '
        'All voices are self-made eSpeak NG offline formant narration, not any executive. '
        'The new [720-second FLAC](../../../tests/fixtures/multimodal/long-call.flac) repeats the committed narration once per minute, '
        'with disclosed silence; it is not a real long earnings call. '
        '[Long generation record and speech windows](../../../tests/fixtures/multimodal/long-generation.json), '
        '[generator](../../../scripts/multimodal/make_long.py), [all fixture hashes](../../../tests/fixtures/multimodal/manifest.json).', '',
        'Period introductions and nearby headings now enter claim extraction. A source-backed program fallback carries a unique '
        'nearby fiscal period into otherwise undated claims and records the original rewrite plus context spans. '
        'Mixed context stays unresolved. A numeric financial claim with no dated period gets program `insufficient_evidence` '
        'with `missing_period`, before any verifier-model or SEC call. Date-day and financial-number inventions still fail the quote guard; '
        'the extractor must include a date heading in its exact contiguous quote or use the stated fiscal quarter. '
        'Long audio is decoded without truncation into <=600s WAVs with 10s overlap; turn timestamps are offset to absolute media time. '
        'Only exact intersecting suffix/prefix words are removed, with an edit record. Non-exact overlaps are retained and flagged. '
        'Speaker labels are chunk-scoped; no cross-chunk speaker identity is inferred. Long transcripts use bounded, overlapping extraction windows.', '',
        '## Capability matrix', '',
        '✓ means reached for all relevant channels; ✗ partial means some; ✗ means none; — means not applicable. '
        'Stage 4 needs cited numeric SEC evidence. Stage 5 includes program `insufficient_evidence`. '
        'Stage 6 means unverified labels and whole-turn times, never named-person attribution or successful diarization.', '',
        '| Input / run | 1 Decode | 2 Text + offsets | 3 Claims | 4 SEC | 5 Program | 6 Attribution | Reason / limit |',
        '|---|---|---|---|---|---|---|---|']
    for name, report in runs.items():
        reasons = [c['id'] + ': ' + c['error'] for c in report['channels'] if c.get('error')]
        reasons += [c['id'] + ': ' + v['screen_reason'] for c in report['channels'] for v in c.get('claims', []) if v['status'] == 'rejected']
        reasons += [f"{k}: {v}" for k, v in counts(report).items() if k in {'insufficient_evidence', 'failed', 'not_checked'}]
        reason = '; '.join(dict.fromkeys(reasons)) or 'Applicable stages reached; see verdicts and attribution limits below'
        lines.append('| ' + f'[{name}]({name}/ingest.html) ({report["provider"]}) | ' + ' | '.join(cell(s) for s in report['stages']) + ' | ' + reason.replace('|', '\\|') + ' |')
    lines += ['', '## Before / after on the recorded media', '',
        'Recall here means **expected financial numeric assertions covered by an accepted rewrite and its exact source quote**. '
        'The rewrite must contain the value; a broad quote alone cannot recover another row. '
        'Dates/quarter labels are excluded. Both level and growth mentions count; the two 12% assertions are separate source occurrences. '
        'Correctly recovering the deliberate $1.67 error counts toward recall, while verification must contradict it. '
        'Failed/absent extraction counts as missed. This metric is narrower than semantic claim recall and is not a correctness score. '
        '[Per-channel measurements and definitions](before-after.json). Baselines and new runs use matching text providers; '
        'there is one planned new run per case and no discarded repeats.', '',
        '| Input | Baseline run | Before accepted / expected | After accepted / expected | After program-checked / expected |',
        '|---|---|---:|---:|---:|']
    for name in CASES:
        after = [v['claim_recall'] for v in scores[name].values()]
        a, c, n = (sum(v[k] for v in after) for k in ('accepted', 'program_checked', 'expected'))
        before = comparisons.get(name)
        old = list(before['before'].values()) if before else []
        baseline = f'[{CASES[name]}](../multimodal-2026-10-29/{CASES[name]}/ingest.html)' if before else 'New 12-minute control'
        old_cell = f"{sum(v['accepted'] for v in old)}/{sum(v['expected'] for v in old)}" if old else '—'
        lines.append(f'| {name} | {baseline} | {old_cell} | {a}/{n} | {c}/{n} |')
    lines += ['', '## Number recovery, cost and latency', '',
        'Ordered financial mentions recovered from OCR/ASR are scored separately from extraction recall. '
        'No word error rate, OCR pixel boxes or real-call generalization is claimed. [All numbers and spans](number-accuracy.json).', '',
        '| Run | Financial mentions recovered / expected (extras) | Estimated USD | Wall seconds | Verdict / stop counts |',
        '|---|---|---:|---:|---|']
    for name, report in runs.items():
        recovery = '; '.join(f"{key}: {s['matched']}/{len(s['expected'])} (+{s['extra']})" for key, s in scores[name].items())
        summary = ', '.join(f'{k}: {v}' for k, v in sorted(counts(report).items()))
        lines.append(f'| {name} | {recovery} | ${report["cost_usd"]:.8f} | {report["wall_clock_s"]:.3f} | {summary} |')
    events = [json.loads(line) for line in (OUT / 'ledger.jsonl').read_text().splitlines()]
    attempts = sum(e['event'] == 'reserve' for e in events)
    lines += ['', f'**Total: ${total:.8f} across {attempts} reserved API attempts.** '
        'Token pricing: $1.25/M input, $0.15/M cached input, $4.25/M output; ASR `ceil(upload_seconds) × $0.18 / 3600`, '
        'including overlap on both uploads. Costs are ledger estimates, not a provider invoice. Failed/usage-less reservations stay charged.', '',
        '## ASR timing, labels and observed limits', '']
    for name, report in runs.items():
        for channel in report['channels']:
            if channel['kind'] == 'transcript':
                turns = channel.get('segments', [])
                labels = ', '.join(sorted({t['speaker'] for t in turns if t.get('speaker')})) or 'none'
                times = '; '.join(f"{t.get('speaker', '?')}: {t.get('start_ms', '?')}–{t.get('end_ms', '?')} ms" for t in turns)
                lines.append(f'- **{name}:** labels {labels}; {times}.')
    notes = OUT / 'observations.md'
    if not notes.is_file():
        raise SystemExit('write observations.md from the saved failures/verdicts before building the final report')
    lines += ['', notes.read_text().strip(), '', '## Reproduce offline', '', '```sh',
              'python3 scripts/multimodal/build_hardening_report.py', 'sh scripts/verify.sh',
              'UV_OFFLINE=1 sh scripts/verify.sh', '```', '',
              'Report rebuilding reads saved evidence only. The paid [probe runner](../../../scripts/multimodal/run_probe.py) '
              'refuses to overwrite runs and is separate from verification. '
              '[Runtime](../../../src/claimcheck/ingest.py), [hardening regressions](../../../tests/test_ingest_hardening.py). '
              'Codec integration is optional without ffmpeg/ffprobe; the full verifier does not render media or call models.', '']
    if (OUT / 'validation.json').is_file() and json.loads((OUT / 'validation.json').read_text()).get('status') == 'passed':
        validation = json.loads((OUT / 'validation.json').read_text())
        lines += [f"Validation: **{validation['product_tests_passed']} product, {validation['demo_tests_passed']} demo and "
                  f"{validation['standalone_node_tests_passed']} standalone Node tests passed**; full suite and "
                  '`UV_OFFLINE=1 sh scripts/verify.sh` passed. [Receipt](validation.json).', '']
    (OUT / 'REPORT.md').write_text('\n'.join(lines))
    print(f'Built {len(runs)}-run hardening report; new ${total:.8f}; combined ${total + 1.3050883:.8f}')


if __name__ == '__main__':
    main()
