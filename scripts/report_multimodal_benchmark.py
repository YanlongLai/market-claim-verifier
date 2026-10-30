"""Offline analysis of the frozen paired study; never calls a model or changes runs."""
from collections import Counter
import hashlib,json,random,re,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'eval/multimodal-v1')]
from score import score
OUT=ROOT/'docs/evidence/fair-multimodal-v1'
DATA=ROOT/'eval/multimodal-v1'
PROVIDERS=('meta','baseten','fireworks')
def read(p):return json.loads(p.read_text())
def rel(p):return str(p.relative_to(OUT))
def pct(a,b):return f'{a}/{b} ({100*a/b:.1f}%)' if b else 'not scored'
def interval(values):
    if not values:return None
    rng=random.Random(20261030)
    vals=sorted(statistics.mean(rng.choices(values,k=len(values))) for _ in range(10000))
    return [round(vals[249],6),round(vals[9749],6)]
def words(text):return re.findall(r"[a-z0-9]+(?:[.,][0-9]+)*",text.lower())
def edits(a,b):
    row=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        nxt=[i]
        for j,y in enumerate(b,1):nxt.append(min(nxt[-1]+1,row[j]+1,row[j-1]+(x!=y)))
        row=nxt
    return row[-1]
def main():
    manifest=read(DATA/'manifest.json');gold={d['id']:d['gold'] for d in read(DATA/'gold.json')}
    selected=read(OUT/'selected-profiles.json')['selected'];test=[c for c in manifest['cases'] if c['split']=='test']
    totals=[];index=[];native=[];diagnostic=[]
    for provider in PROVIDERS:
        for fmt in manifest['formats']:
            aggregate=Counter();clusters=[];costs=[];missing=[]
            for case in [c for c in test if c['format']==fmt]:
                path=OUT/'test'/provider/selected[provider]/case['id']/'ingest.json'
                result=read(path) if path.exists() else {'channels':[],'status':'not_run'}
                s=score(gold[case['document']],result['channels'])
                if 'score' in result and result['score']!=s:raise ValueError(f'score replay mismatch: {path}')
                aggregate.update({k:s[k] for k in ('denominator','correct','extracted','checked','negative_gold','false_supported','abstentions')})
                clusters.append(s['correct']/s['denominator']);costs.append(result.get('workflow_unit_cost_usd',0))
                if not path.exists():missing.append(case['id'])
                index.append({'provider':provider,'case':case,'result':rel(path) if path.exists() else None,'status':result['status'],'score':s})
            totals.append({'provider':provider,'format':fmt,**aggregate,'issuer_cluster_bootstrap_95':interval(clusters),'workflow_unit_cost_mean_usd':statistics.mean(costs),'missing':missing})
        for case in [c for c in manifest['cases'] if c['split'] in ('test','diagnostic') and c['format'] in ('png','jpg','webp')]:
            path=OUT/'native-images'/provider/(case['id']+'.json');r=read(path) if path.exists() else {'status':'not_run','text':''}
            row={'provider':provider,'case_id':case['id'],'format':case['format'],'split':case['split'],'status':r['status'],'result':rel(path) if path.exists() else None,'cost_usd':r.get('cost_usd',0),'error':r.get('error')}
            if case['split']=='test':
                reference=(DATA/'inputs'/case['document']/'input.txt').read_text();a=words(reference);b=words(r.get('text') or '')
                nums=Counter(re.findall(r'\d+(?:[.,]\d+)*',reference));outnums=Counter(re.findall(r'\d+(?:[.,]\d+)*',r.get('text') or ''))
                row.update(word_edits=edits(a,b),reference_words=len(a),numeric_tokens_found=sum((nums&outnums).values()),numeric_tokens_total=sum(nums.values()))
            native.append(row)
        for case in [c for c in manifest['cases'] if c['split']=='diagnostic']:
            p=OUT/'diagnostic'/provider/selected[provider]/case['id']/'ingest.json';r=read(p) if p.exists() else {'channels':[],'status':'not_run'}
            claims=[c for ch in r['channels'] for c in ch.get('claims',[])]
            diagnostic.append({'provider':provider,'case_id':case['id'],'result':rel(p) if p.exists() else None,'status':r['status'],'extracted_occurrences':len(claims),'verdict_counts':dict(Counter(c.get('verdict') or c.get('status','unknown') for c in claims))})
    failures=[]
    for item in index:
        raw=read(OUT/item['result']) if item['result'] else {}
        pipeline_errors=[*raw.get('errors',[]),*[ch['error'] for ch in raw.get('channels',[]) if ch.get('error')]]
        for row in item['score']['rows']:
            if row['correct']:continue
            prediction=row['prediction']
            category=('unsafe_support' if row['unsafe_supported'] else
                      'missing_with_pipeline_error' if prediction=='missing' and pipeline_errors else
                      'not_aligned' if prediction=='missing' else
                      'channel_disagreement' if prediction=='conflict' else
                      'unresolved' if prediction=='unresolved' else
                      'abstained_on_answerable_gold' if prediction=='insufficient_evidence' else
                      'incorrect_definitive_verdict')
            failures.append({'provider':item['provider'],'case_id':item['case']['id'],'format':item['case']['format'],'result':item['result'],'category':category,'pipeline_errors':pipeline_errors,**row})
    (OUT/'error-analysis.json').write_text(json.dumps({'description':'Mechanical error categories from frozen scored outcomes, not inferred root causes. Repeated encodings are not independent errors.','failures':failures},indent=2)+'\n')
    events=[json.loads(line) for line in (OUT/'ledger.jsonl').read_text().splitlines()]
    latest={event['reservation_id']:event for event in events}
    spend={p:round(sum(event['amount'] for event in latest.values() if event['provider']==p),8) for p in PROVIDERS}
    calls={}
    for p in PROVIDERS:
        refs=set()
        for item in index:
            if item['provider']==p and item['result']:
                for ch in read(OUT/item['result'])['channels']:
                    if ch.get('text_record'):refs.add(ch['text_record'])
        calls[p]=[read(OUT/ref) for ref in sorted(refs) if (OUT/ref).exists()]
    latencies={p:{'fresh_text_jobs':len(rs),'median_seconds':round(statistics.median([r['wall_clock_s'] for r in rs]),3) if rs else None,'max_seconds':max([r['wall_clock_s'] for r in rs],default=None)} for p,rs in calls.items()}
    summary={'schema_version':1,'freeze':read(OUT/'freeze.json'),'selected_profiles':selected,'test_assertions':24,'issuer_clusters':6,'format_results':totals,'native_images':native,'real_diagnostics':diagnostic,'actual_estimated_or_reserved_spend_usd':spend,'unique_test_text_job_latency':latencies,'case_index':index,'uncertainty':'Seeded percentile bootstrap over six issuer clusters; exploratory and unstable at this sample size. Encodings are not independent facts.','native_reading_metrics':'Post-run descriptive token edit and number-token recall; no setting selection uses these metrics. Numeric tokens include years/quarters and do not measure table semantics.'}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    lines=['# Paired multimodal benchmark v1 — recorded results','', '[Frozen protocol and exact inputs](../../../eval/multimodal-v1/README.md) · [machine-readable results and case index](summary.json) · [ledger](ledger.jsonl) · [cost basis](cost-basis.json) · [official rate cross-check](RATE_CHECK.md) · [execution log](execution.log) · [selected development profiles](selected-profiles.json) · [reuse guide](REUSE.md) · [artifact audit](audit.json)','',
    'Six test issuers, four assertions each, nine encodings: **24 underlying assertions / six issuer clusters**. Scores below describe this controlled corpus, not real-world accuracy. Clean synthetic cards and speech are deliberately easier than real earnings calls. Three real Tesla slide pages are reported separately without accuracy labels. All missing/failed/unmatched assertions remain wrong; conflicting duplicates do not get best-of selection.','',
    'The pipeline uses one shared Meta OCR/ASR result per file, then the same frozen text for each verifier. Native image reading is a separate study below. Meta Muse Spark 1.3 and the two pinned Muse Spark Open endpoints are different model/serving configurations. This compares the integrated Muse models, not every model offered by each platform. The selected profile is the best of **two development settings only**, not a claim to the globally best configuration. The default/low profile changes verification reasoning; short-input extraction retains the repository default reasoning, while partitioned long-input extraction uses low. Native image calls explicitly use the selected profile.','',
    '## Strict end-to-end verdict accuracy','', '| Format | Meta | Baseten | Fireworks |','| --- | --- | --- | --- |']
    for fmt in manifest['formats']:
        rows=[next(r for r in totals if r['provider']==p and r['format']==fmt) for p in PROVIDERS]
        lines.append('| '+fmt.upper()+' | '+' | '.join(pct(r['correct'],r['denominator']) for r in rows)+' |')
    lines+=['','## Coverage, false support and abstention','', '| Provider / format | Gold extracted | Gold checked | False supported / negative gold | Insufficient-evidence predictions | Empirical issuer-bootstrap range (95%; exploratory) |','| --- | --- | --- | --- | --- | --- |']
    for r in totals:
        lo,hi=r['issuer_cluster_bootstrap_95']
        band=f'{lo:.1%}–{hi:.1%}' if lo!=hi else 'All observed clusters equal; bootstrap uninformative'
        lines.append(f"| {r['provider']} / {r['format']} | {pct(r['extracted'],r['denominator'])} | {pct(r['checked'],r['denominator'])} | {pct(r['false_supported'],r['negative_gold'])} | {r['abstentions']} | {band} |")
    lines+=['','Extraction means deterministic ticker/metric/period alignment, not exact number transcription. Unmatched extractions are retained in JSON; alignment errors can reduce the strict score. No observed false support on this small controlled set is not a zero-risk guarantee; only 12 underlying negative/insufficient assertions are repeated across formats. The six-cluster bootstrap is exploratory and fragile: it resamples these selected issuers, not a representative population. Identical observed cluster scores give a degenerate bootstrap, not certainty of true accuracy. There is no pooled 216-independent-claim confidence interval or broad vendor ranking. This is one recorded run without a repeated-inference variability study; the bootstrap does not measure model randomness.','', '## Error categories','', '[Every scored miss](error-analysis.json) links to the original result; [reviewed examples](OBSERVATIONS.md) distinguish transcription, output-limit and quotation failures. Categories describe outcomes, not a guessed root cause. Repeated encodings can share one failed text job.','', '| Provider | Missing with pipeline error | Not aligned | Unresolved | Channel disagreement | Abstained on answerable gold | Unsafe support | Other wrong definitive verdict |','| --- | --- | --- | --- | --- | --- | --- | --- |', *['| '+p+' | '+' | '.join(str(sum(r["provider"]==p and r["category"]==c for r in failures)) for c in ('missing_with_pipeline_error','not_aligned','unresolved','channel_disagreement','abstained_on_answerable_gold','unsafe_support','incorrect_definitive_verdict'))+' |' for p in PROVIDERS], '', '## Native image reading','', '| Provider / format | Completed / planned | Number-token recall | Word edit rate |','| --- | --- | --- | --- |']
    for p in PROVIDERS:
        for fmt in ('png','jpg','webp'):
            rows=[r for r in native if r['provider']==p and r['format']==fmt and r['split']=='test']
            lines.append(f"| {p} / {fmt} | {sum(r['status']=='completed' for r in rows)}/{len(rows)} | {pct(sum(r['numeric_tokens_found'] for r in rows),sum(r['numeric_tokens_total'] for r in rows))} | {sum(r['word_edits'] for r in rows)/sum(r['reference_words'] for r in rows):.1%} |")
    lines+=['','These descriptive post-run reading metrics are not financial-verdict accuracy or image-authenticity checks. The native-image probe does not change product routing: `ingest` still uses Meta OCR for all three text providers. Number recall uses unsigned numeral tokens, includes dates/quarters, and does not validate signs, unit binding or table relationships; word edits can penalize harmless formatting or wording. Failed/missing text scores as missing words. Native reading uses the profile selected on development verification, not a separately optimized OCR profile. Native audio/video endpoints were **not tested**, so no unsupported-format conclusion follows.','', '## Actual spend and observed latency','', '| Platform | Estimated or reserved USD, all phases | Authorized cap | Chosen profile | Unique test text jobs | Median / maximum test text-job seconds |','| --- | --- | --- | --- | --- | --- |']
    for p in PROVIDERS:
        l=latencies[p]
        lines.append(f"| {p} | ${spend[p]:.8f} | $40 | {selected[p]} | {l['fresh_text_jobs']} | {l['median_seconds']} / {l['max_seconds']} |")
    lines+=['','All shared preprocessing is billed to Meta in this ledger. Spend includes development, diagnostics and failures; unreconciled reservations remain charged conservatively. Latency includes only unique text jobs referenced by the test split. These are usage estimates, **not invoices**. Per-format workflow unit estimates are in JSON and must not be summed as actual spending: identical text results can be reused. Fresh text jobs can contain extraction plus multiple agent tool calls. They exclude OCR/ASR and cache hits; observed concurrency/network effects mean this is not an SLA.','', '## Real issuer diagnostic pages','', '| Platform / Tesla page | Pipeline status | Extracted occurrences | Recorded verdicts |','| --- | --- | --- | --- |']
    for r in diagnostic:
        label=r['provider']+' / '+r['case_id'];link=f"[{label}]({r['result']})" if r['result'] else label
        lines.append(f"| {link} | {r['status']} | {r['extracted_occurrences']} | {r['verdict_counts']} |")
    lines+=['','No complete independent gold exists for these pages. Verdict counts are model/program outputs, not a claim that all page contents were found or correctly judged. See the machine index for native diagnostic responses as well.','', '## Reproduce without credits','', 'Run `.venv/bin/python scripts/report_multimodal_benchmark.py` from the repository root. It recomputes scores from retained claim records and refuses mismatches. This does not rerun OCR, speech recognition or model calls. The original 72 files, three real diagnostic images, frozen prepared texts, requests, raw responses, failures and costs remain available. Media request payloads reference exact input/derived-media hashes instead of repeating base64.','', 'The report uses the frozen scorer even when a wording mismatch is visible. Any future scorer correction, real-recording gold review or model change needs a separately labeled evaluation; this run remains immutable.']
    (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'format_cells':len(totals),'planned_pipeline_results':len(index),'native_results':len(native),'spend':spend}))
if __name__=='__main__':main()
