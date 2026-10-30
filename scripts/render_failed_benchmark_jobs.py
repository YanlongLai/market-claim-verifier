"""Create explicit failure views where no standard post report was produced.
Never rewrites model outputs, case scores, or existing HTML reports.
"""
from pathlib import Path
import hashlib,html,json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/evidence/fair-multimodal-v1'
def main():
    created=[]
    for record in sorted((OUT/'text-cache').glob('*/*/record.json')):
        target=record.with_name('report.html')
        if target.exists():continue
        r=json.loads(record.read_text())
        if r['status']=='completed':raise ValueError('missing successful report; inspect rather than fabricate')
        esc=lambda x:html.escape(str(x))
        links=''.join(f'<li><a href="{esc(str(p.relative_to(record.parent)))}">{esc(p.name)}</a></li>' for p in sorted((record.parent/'traces').glob('*.json')))
        body=f'<!doctype html><html lang="en"><meta charset="utf-8"><title>Failed benchmark job</title><style>body{{font:16px/1.5 system-ui;max-width:1000px;margin:40px auto;padding:0 20px}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}</style><h1>Failed benchmark job — retained attempt</h1><p>This view was generated offline because extraction/checking did not produce a standard post report. No model call was retried and no score or raw record was changed.</p><p>Status: {esc(r["status"])}. Provider: {esc(r["provider"])}. Model: {esc(r["model"])}. Profile: {esc(r["profile"])}.</p><p>Error: {esc(r.get("error"))}</p><p>Estimated/reserved cost: ${r["cost_usd"]:.8f}.</p><p><a href="record.json">Original job record and cost accounting</a></p><h2>Retained raw traces</h2><ul>{links}</ul><h2>Input text</h2><pre>{esc(r["text"])}</pre></html>'
        target.write_text(body)
        record.with_name('failure-view-metadata.json').write_text(json.dumps({'source_record_sha256':hashlib.sha256(record.read_bytes()).hexdigest(),'generator':'scripts/render_failed_benchmark_jobs.py','scope':'Offline failure presentation only; original response, status and score unchanged.'},indent=2)+'\n')
        created.append(str(target.relative_to(ROOT)))
    print(json.dumps({'failure_views_created':created},indent=2))
if __name__=='__main__':main()
