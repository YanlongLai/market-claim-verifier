"""One-time scheduling of registered unscored Baseten diagnostics after its tests.
Not a general concurrent resume interface; the main benchmark owns the other phases.
"""
import json,sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'eval/multimodal-v1'))
import bench
provider='baseten'
manifest,docs=bench.freeze()
profile=json.loads((bench.OUT/'selected-profiles.json').read_text())['selected'][provider]
assert len(list((bench.OUT/'test'/provider/profile).glob('*/ingest.json')))==54
assert all(len(list((bench.OUT/'test'/p).glob('*/*/ingest.json')))<36 for p in ('meta','fireworks')), 'too near the main diagnostic phase; leave it to the main runner'
cases=[c for c in manifest['cases'] if c['split']=='diagnostic']
bench.write_json(bench.OUT/'diagnostic-schedule-note.json',{'provider':provider,'started_at':bench.stamp(),'reason':'All 54 Baseten test cells completed; run its already-registered unscored diagnostics while other providers finish test cells. Same frozen function, selected profile, shared ledger and maximum two text workers. Main runner will reuse completed records. Native-image schedule is unchanged. This overlaps only unscored work across providers and adds no test attempts.'})
with ThreadPoolExecutor(max_workers=2) as pool:
    list(pool.map(lambda c:bench.run_case(c,provider,profile,'diagnostic',[]),cases))
print('Finished preregistered Baseten diagnostics',flush=True)
