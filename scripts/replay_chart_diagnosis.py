"""Offline Tesla chart case analysis; never reruns or changes paid records."""
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from claimcheck.coverage_diagnostics import coverage_diagnostics
from claimcheck.stock_review import build_stock_review
OUT=ROOT/'docs/evidence/chart-diagnosis-2026-10-30'
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    base=ROOT/'docs/evidence/stock-context-posthoc-2026-10-30/attempt-2'
    sources=[base/f'REAL-TSLA-{n}/ingest.json' for n in (4,5,23)]
    image=ROOT/'docs/evidence/real-media-2026-10-30/images/tesla-q3-2026-23.png'
    chart=json.loads(sources[-1].read_text())
    data={'kind':'posthoc_offline_diagnosis','new_api_cost_usd':0,
          'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [image,*sources]},
          'diagnostics':coverage_diagnostics(chart['channels']),
          'original_claim_count':sum(len(c.get('claims',[])) for c in chart['channels']),
          'note':'No chart values estimated; no new accuracy score. See REPORT.md for visual inspection and limitations.'}
    data['implementation_sha256']={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in (
        'src/claimcheck/coverage_diagnostics.py','src/claimcheck/ingest.py','src/claimcheck/stock_review.py',
        'scripts/replay_chart_diagnosis.py','tests/test_coverage_diagnostics.py')}
    (OUT/'diagnosis.json').write_text(json.dumps(data,indent=2)+'\n')
    # A new directory is mandatory; never overwrite a previous summary.
    if not (OUT/'summary/stock-review.json').exists():
        build_stock_review('TSLA',sources,OUT/'summary')
    print('PASS: saved coverage diagnosis; original paid records unchanged; no API calls')
if __name__=='__main__':main()
