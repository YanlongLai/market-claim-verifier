"""Rebuild the recall-fix comparison using saved evidence only; no inference."""
from __future__ import annotations

import json
import hashlib
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))

from claimcheck.budget import Ledger
from claimcheck.ingest import render_html
from claimcheck.ingest_media import write_json
from claimcheck.post import parse_extraction
from build_hardening_report import claim_recall, counts, number_score

OUT = ROOT / 'docs/evidence/multimodal-2026-10-30b'
BEFORE = ROOT / 'docs/evidence/multimodal-2026-10-30'


def measure(folder: Path, expected_input: str | None = None) -> dict:
    report = json.loads((folder / 'ingest.json').read_text())
    protocol = json.loads((folder / 'protocol.json').read_text())
    drift = [name for name, digest in protocol.get('source_hashes', {}).items()
             if (ROOT / name).exists() and hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest]
    channels = {}
    for channel in report['channels']:
        score = number_score(expected_input or report['input']['file'], channel)
        if channel.get('extraction_trace'):
            extraction = json.loads((folder / channel['extraction_trace']).read_text())
        else:
            traces = [json.loads(p.read_text()) for p in (folder / 'checks' / channel['id'] / 'traces').glob('*.json')]
            extraction = next((t for t in traces if t.get('claim', '').startswith('[extraction]')), {'requests': []})
        requests = []
        for request in extraction['requests']:
            # Recorded response shapes differ between Meta Responses and the
            # Baseten chat adapter; read the saved answer, never call a model.
            raw = request['raw_response']
            text = raw.get('output_text') or ''.join(
                part.get('text', '') for item in raw.get('output', []) for part in (item.get('content') or [])
                if part.get('type') == 'output_text')
            if raw.get('choices'):
                text = raw['choices'][0]['message'].get('content') or ''
            requests.append(dict(proposals=len(parse_extraction(text)) if request['status'] == 'completed' else 0, usage=request.get('usage'),
                                 finish_reason=request.get('finish_reason'), status=request['status']))
        claims = channel.get('claims', [])
        channels[channel['id']] = dict(
            number_recovery=score,
            financial_mentions_recovered=score['matched'], expected=len(score['expected']), extras=score['extra'],
            recall=claim_recall(channel, score), proposals_per_request=requests,
            accepted_claim_rows=sum(c['status'] != 'rejected' for c in claims),
            statuses=dict(Counter(c['status'] for c in claims)), verdicts=dict(Counter(c.get('verdict') for c in claims)),
            unique_verification_traces=len({c['trace_path'] for c in claims if c.get('trace_path')}),
            reused_checks=sum('verification_reused_from' in c for c in claims),
            claim_limit=channel.get('claim_limit'),
            rejected=[dict(quote=c['quote'], reason=c['screen_reason']) for c in claims if c['status'] == 'rejected'])
    return dict(channels=channels, verdicts=counts(report), status=report['status'], cost_usd=report['cost_usd'],
                source_files_different_from_final=drift,
                wall_clock_s=report['wall_clock_s'])


def main() -> None:
    selection = json.loads((OUT / 'probe-set.json').read_text())
    comparisons = {}
    cases = {**selection['cases'], **selection.get('adaptive_runs', {})}
    for name, case in cases.items():
        baseline = (OUT / case['baseline']).resolve()
        comparisons[name] = dict(baseline=baseline.name, before=measure(baseline),
                                 after=measure(OUT / name, case.get('expected_input')))
        if comparisons[name]['after']['status'] == 'running':
            raise RuntimeError(f'{name} is still running; wait before rebuilding the report')
        if case.get('same_transcript_comparator'):
            comparisons[name]['same_transcript_before'] = measure(OUT / case['same_transcript_comparator'], case.get('expected_input'))
        report = json.loads((OUT / name / 'ingest.json').read_text())
        (OUT / name / 'ingest.html').write_text(render_html(report))
    total = Ledger(OUT / 'ledger.jsonl').spent_total
    write_json(OUT / 'before-after.json', dict(
        policy='Numeric-assertion coverage, not semantic accuracy. A rewritten value and its guarded source quote must cover each expected financial mention. Source-window bounds apply when recorded. Repeated exact rewrites can share one verification; unmatched/failed assertions count as missed.',
        new_spend_usd=total, combined_spend_usd=total + selection['prior_spend_usd'], runs=comparisons))
    lines = [
        '# Recall fixes — 2026-10-30b', '',
        f'**Two planned post-hoc development probes, one adaptive long-call repeat and one frozen-transcript recheck; new estimated spend ${total:.8f} / $8; '
        f'combined multimodal spend ${total + selection["prior_spend_usd"]:.8f} / $20.** '
        'Known self-made fixtures, not a held-out evaluation. No other media probes were rerun. '
        '[Frozen selection and budget](probe-set.json), [machine comparison](before-after.json).', '',
        '## Before / after', '',
        'Coverage counts expected financial numeric assertions whose values occur in an accepted rewrite and its exact source quote. '
        'Dates and period labels are excluded. The deliberate $1.67 EPS error counts as recovered input and must be contradicted. '
        'Each repeated source occurrence counts separately; reused verification is disclosed below. Coverage is not verdict accuracy.', '',
        '| Input | Recovered mentions before → after | Guarded coverage before → after | Program-checked before → after | EPS error before → after |',
        '|---|---:|---:|---:|---|']
    for name, comparison in comparisons.items():
        before = next(iter(comparison['before']['channels'].values()))
        after = next(iter(comparison['after']['channels'].values()))
        def ratio(side, field):
            value = side['recall'][field] if field in {'accepted', 'program_checked'} else side[field]
            return f'{value}/{side["expected"]}'
        def eps_verdict(folder):
            report = json.loads((folder / 'ingest.json').read_text())
            return ', '.join(sorted({c.get('verdict', c['status']) for ch in report['channels'] for c in ch.get('claims', [])
                                     if '1.67' in c['claim']})) or 'missed'
        lines.append(f'| [{name}]({name}/ingest.html) | {ratio(before, "financial_mentions_recovered")} → {ratio(after, "financial_mentions_recovered")} | '
                     f'{ratio(before, "accepted")} → {ratio(after, "accepted")} | '
                     f'{ratio(before, "program_checked")} → {ratio(after, "program_checked")} | '
                     f'{eps_verdict(BEFORE / comparison["baseline"])} → {eps_verdict(OUT / name)} |')
    lines += ['', '## Diagnosis and changes', '',
        '- **Extraction, not ASR truncation, dominated the recorded long-call loss.** Its 6,606 normalized characters used two extraction requests, each returning only three surface rewrites of repeated facts. '
        'Both responses completed below the 8,000-token ceiling; most output tokens were reasoning. All six surviving proposals were checked, so the old eight-claim cap did not bind this run. '
        'The 0–600s / 590–720s audio uploads and absolute tail times were already intact. One non-exact ASR boundary overlap remained unresolved.',
        '- **Long extraction is now local.** Inputs above 6,000 characters use at most 1,400-character windows, prefer individual paragraph/turn boundaries, and retain 200 characters of overlap plus unique nearby stated period context. '
        'The default eight-check allowance applies per extraction window; the shared reservation ledger still refuses calls over budget. '
        'Quote variants survive screening, duplicate overlap spans merge, and identical final rewrites with the same ticker/kind reuse one verification. '
        'Explicit quote spans limit source credit to the extraction window. Semantic paraphrases are not consolidated.',
        '- **The first new long-call run failed visibly.** Fresh ASR recovered 59/60 expected financial mentions, but the first extraction used all 8,000 output tokens (7,997 reasoning) and returned no JSON. '
        'It remains a partial failure with zero checked assertions in the table. The adaptive `long-call-r2` requests low reasoning effort for long-input extraction, '
        'retains the 8,000-token ceiling and shared dollar cap, and reruns the same affected clip. The changed reasoning setting is a comparison confound; no attempt was discarded.',
        '- **Context and punctuation follow-up.** The adaptive media run exposed two synthetic-context-prefix quotes rejected as non-contiguous, plus a legitimate `2025,` rejected as a new number. '
        'Nearby period context now goes in instructions outside the quotable post; fiscal and calendar context must agree before propagation. '
        'A trailing comma no longer makes a stated context year fail the period-number exception. Date days and financial quantities still require the quote. '
        'The final `long-call-frozen` run rechecks the exact raw ASR text from `long-call-r2` with fresh extraction/verification and no new ASR. '
        '[Frozen text and source hashes](frozen-transcript.json). This text projection makes no new timing or speaker-attribution claim.',
        '- **The text EPS miss was evidence routing.** Its exact claim already said fiscal Q3 2025. The model labeled it `reported_in_release` and cited both a failed release search and a valid L2 $1.57 XBRL fact. '
        'The release-only path ignored that fact. An ordinary GAAP level claim can now use cited L1/L2 XBRL only when issuer, metric, unit and explicit period match and there is no cited release quote. '
        'Guidance/non-GAAP still require release evidence. The saved output stream now deterministically contradicts $1.67. This does not relax missing-period handling.',
        '- **Regression coverage.** Tests retain the original lost-period 12% growth case (1.57 / 1.40 − 1 = 12.14%, supported), undated claims stopping before model/SEC access, date/number invention rejection, '
        'overlap deduplication, distinct quote variants, scoped periods, per-window claim limits, tail/context retention and verification reuse. Wrong issuer/metric/calendar-period fallback is rejected.', '',
        '## Observed limits and protocol', '']
    for name, comparison in comparisons.items():
        after = next(iter(comparison['after']['channels'].values()))
        lines.append(f'- **{name}:** status `{comparison["after"]["status"]}`; {after["accepted_claim_rows"]} accepted claim rows, '
                     f'{after["unique_verification_traces"]} unique verification traces, {after["reused_checks"]} reused checks; '
                     f'{after["recall"]["program_checked"]}/{after["expected"]} expected numeric assertions program-checked; '
                     f'{after["extras"]} extra input financial mentions. Verdicts: `{json.dumps(comparison["after"]["verdicts"], sort_keys=True)}`. '
                     f'[Protocol]({name}/protocol.json), [raw ingest]({name}/ingest.json).')
        if after['rejected']:
            lines.append(f'  Rejected proposals remain in the raw report: {len(after["rejected"])}; no rejected rewrite earns coverage.')
        if comparison.get('same_transcript_before'):
            previous = next(iter(comparison['same_transcript_before']['channels'].values()))
            lines.append(f'  On identical heard text: guarded/program-checked coverage '
                         f'{previous["recall"]["accepted"]}/{previous["expected"]} → '
                         f'{after["recall"]["accepted"]}/{after["expected"]}. Fresh extraction is still stochastic.')
    lines += ['',
        'Fresh ASR can change number recovery, wording and speaker labels, so the live long-call comparison also reflects ASR variability. '
        'The synthetic 720-second clip repeats one short eSpeak NG narrator with silence. Whole-turn times and chunk-scoped labels do not prove speaker identity or diarization. '
        'Exact-quote coverage can remain incomplete; eight unique checks per window, output limits and the dollar cap still bound recall. '
        'No real-call or exhaustive-video benchmark is claimed. The earlier seven-run evidence and all failures remain unchanged.', '',
        'Some date-bearing revenue rows remain `insufficient_evidence`: their numeric revenue/growth checks pass, but a separate period-end-date `other` subclaim is unchecked. '
        'Model summaries can disagree with program results (including whole-percent rounding); only program verdicts are counted. '
        'All 39 growth checks in the final frozen report are supported (including reused checks); its numeric contradictions are the deliberate EPS error. '
        'The final frozen text still misses expected numeric assertions despite retaining all accepted quotes. '
        'A frozen text recheck is not a successful fresh media or attribution run.', '',
        'Runtime models are Meta Muse Spark 1.3 (text control), Meta Muse Spark Open via Baseten (long-call text) and Muse Voice Transcribe 1.0 (ASR). '
        'Keys load only through `claimcheck.config` and are redacted; SEC access uses committed snapshots only. '
        'Text retains 4,000 output tokens and long-call retains 8,000, matching their baselines. '
        'The adaptive media repeat and frozen-text recheck explicitly request low reasoning effort for extraction. '
        'Protocols record actual UTC times, hashes and model IDs. HTTP 5xx retries retain separate reservations/traces. '
        'The shared new ledger has an $8 total cap and $4 provider partitions.', '',
        'Each live protocol preserves the hashes actually used. The final source hashes are in the validation receipt; '
        'the comparison JSON lists source drift for each run. The XBRL fallback was tightened to require the exact source level literal after the frozen probe launched; '
        'the saved final text/frozen output streams replay through that final guard with unchanged verdicts. '
        'Legacy long extraction replay retains its archived windows/context transport; the intermediate media repeat is kept as a historical run, not relabeled as final-code inference.', '',
        '## Reproduce offline', '',
        '```sh', 'python3 scripts/multimodal/build_recall_report.py', 'UV_OFFLINE=1 sh scripts/verify.sh', '```', '',
        'The builder reads saved evidence only. Paid probes are separate and refuse to overwrite runs. '
        'Full-suite and disconnected-verifier results are recorded in [validation.json](validation.json).', '']
    (OUT / 'REPORT.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    main()
