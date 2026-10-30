"""Build a deterministic three-outcome judge walkthrough without model/network calls."""
from pathlib import Path
import argparse
import json

from export_sec_release import RecordedMeta, FIXTURES, offline_only
from claimcheck.checks import evaluate_sub_claim
from claimcheck.evidence import SecReleaseConnector, export_bundle
from claimcheck.release_fetch import ReleaseClient
from claimcheck.release_text import parse_html
from claimcheck.tools import ToolRunner

CASES = [
    ('matching-range', 'META expects revenue of $47.5 billion to $50.5 billion for FY2025Q3.'),
    ('changed-range', 'META expects revenue of $48.5 billion to $51.5 billion for FY2025Q3.'),
    ('wrong-period', 'META expects revenue of $47.5 billion to $50.5 billion for FY2025Q4.'),
]


def build(out: Path) -> dict:
    client = ReleaseClient(FIXTURES, fetcher=offline_only)
    runner = ToolRunner(RecordedMeta(), release_client=client)
    found = runner.dispatch('find_earnings_release', {
        'ticker': 'META', 'metric': 'revenue', 'period': 'FY2025Q3', 'claim_kind': 'guidance'})
    candidate = found['candidates'][0]
    quote = runner.dispatch('quote_release', {key: candidate[key] for key in ('candidate_id', 'start', 'end')})
    if quote.get('error'):
        raise ValueError(quote['error'])
    raw, metadata = client.read(quote['exhibit_url'])
    text = parse_html(raw).text
    record = SecReleaseConnector().export(quote=quote, raw=raw, text=text, metadata=metadata)
    record_path = export_bundle(record, raw, text, out / 'evidence')
    results = []
    for identity, claim in CASES:
        # These atomic inputs and their evidence selection are predefined, not model extractions.
        sub = {'text': claim, 'original_claim': claim, 'stated_text': claim,
               'claim_type': 'guidance', 'comparator': 'eq', 'evidence_ids': [quote['evidence_id']]}
        check = evaluate_sub_claim(sub, runner)
        results.append({'id': identity, 'claim': claim, 'program_check': check,
                        'selected_evidence_id': quote['evidence_id']})
    result = {
        'schema_version': '1.0', 'mode': 'offline deterministic walkthrough',
        'input_selection': 'Three predefined atomic claims; no extraction or model output is simulated.',
        'scope': 'Only the selected FY2025Q3 outlook quote; not an exhaustive search for FY2025Q4.',
        'source_record': str(record_path.relative_to(out)), 'record_id': record.record_id,
        'source_sha256': record.to_dict()['source']['sha256'],
        'cost': {'currency': 'USD', 'incremental_api_total': 0,
                 'stages': {'source_network': 0, 'ocr': 0, 'asr': 0, 'model_extraction': 0, 'model_verification': 0},
                 'api_requests': 0, 'basis': 'No API requests; local cached source and deterministic program checks.',
                 'excluded': ['Local CPU/storage costs are not metered.', 'Historical source acquisition costs are not reconstructed.'],
                 'live_cost': 'Not measured by this example; do not use zero as the price of live verification.'},
        'results': results,
    }
    (out / 'results.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    locator = record.to_dict()['locator']
    source = record.to_dict()['source']
    (out / 'SOURCE.md').write_text(f'''# Official source and exact quote

Publisher: {source['publisher']}. Filed {source['filed_on']}; retrieved {source['retrieved_at']}.

[Original SEC exhibit]({source['url']}) · [Raw snapshot](evidence/{source['sha256']}.html) · [Full normalized text](evidence/{locator['text_sha256']}.txt) · [Evidence record]({result['source_record']})

## Verified excerpt

Normalized-text character offsets: **[{locator['start']}, {locator['end']})**. These are not raw HTML byte offsets.

```text
{locator['quote']}
```

Source SHA-256: `{source['sha256']}`.
Text SHA-256: `{locator['text_sha256']}`.

L4: issuer-furnished, unaudited, medium maximum evidence strength. The quote establishes what the issuer forecast, not whether the future result occurred. The normalized text is produced by `claimcheck.release_text.parse_html/v1`.
''')
    explanations = {
        'matching-range': 'Both stated endpoints match the issuer outlook for the same quarter.',
        'changed-range': 'Both endpoints are $1 billion above the selected issuer outlook.',
        'wrong-period': 'The selected quote concerns Q3, not Q4. Matching numbers cannot repair a period mismatch. This example does not establish that no Q4 disclosure exists elsewhere.',
    }
    rows = []
    for item in results:
        check = item['program_check']
        rows.append(f"| {item['claim']} | **{check['program_verdict']}** | {explanations[item['id']]} |")
    (out / 'REPORT.md').write_text('''# One official source, three different outcomes

**Offline deterministic walkthrough.** Three predefined atomic claims use one recorded Meta Platforms SEC earnings-release quote. No live model, OCR, ASR, network retrieval or extraction is run. This is an illustrative regression example, not an accuracy benchmark or a saved model conversation.

## Inspect the result

| Claim | Program verdict | Why |
|---|---|---|
''' + '\n'.join(rows) + f'''

[Open the exact official-source excerpt](SOURCE.md#verified-excerpt) · [Complete source provenance](SOURCE.md) · [Machine-readable checks and costs](results.json)

All three cases select the same quote. The third check rejects its applicability: evidence selection is not evidence acceptance. No model-proposed verdict is needed; the existing financial checker produces the outcome. Read each `program_check.reason`, `actual_range` and `stated_range` in the JSON for the program output.

## What this costs

| Stage | Incremental API cost USD | Reason |
|---|---:|---|
| Source retrieval | 0 | Committed local snapshot; network fallback disabled |
| OCR / ASR | 0 | Existing HTML text |
| Claim extraction | 0 | Three predefined inputs |
| Verification model | 0 | Deterministic Python rules |
| Total | **0** | **0 API requests** |

Local CPU/storage is not metered; historical acquisition cost is not reconstructed. This is not a quote for live agent verification. See the [provider comparison](https://github.com/YanlongLai/market-claim-verifier/blob/main/docs/PROVIDERS.md) for dated model rates and recorded live costs.

## Reproduce

From the repository root:

```sh
uv run python examples/evidence/judge_walkthrough.py --out /tmp/claimcheck-judge
```

Open the generated `REPORT.md`. The output retains original bytes, normalized text, a versioned evidence record and full deterministic checks. Source and quote integrity are rechecked; a changed existing evidence artifact is rejected instead of overwritten.

## Limits

US issuer guidance only, from one chosen recorded document. No arbitrary uploaded document becomes authoritative. No current/live source freshness, exhaustive retrieval, extraction recall or general accuracy is claimed. All outcomes concern the issuer's statement, not the truth of future financial performance.

Record ID: `{record.record_id}`.
''')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.out)
    print(json.dumps({'report': str(args.out / 'REPORT.md'), 'verdicts': [r['program_check']['program_verdict'] for r in result['results']], 'api_cost_usd': 0}, indent=2))


if __name__ == '__main__':
    main()
