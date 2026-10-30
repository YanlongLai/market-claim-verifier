"""Update the two READMEs from completed retained benchmark records, offline."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/evidence/fair-multimodal-v1'
def main():
    s=json.loads((OUT/'summary.json').read_text())
    if any(r['result'] is None or r['status']=='running' for r in s['case_index']):raise ValueError('test split incomplete')
    if any(r['result'] is None or r['status']=='running' for r in s['native_images']):raise ValueError('native study incomplete')
    posthoc=json.loads((ROOT/'docs/evidence/stock-context-posthoc-2026-10-30/audit.json').read_text())
    extra={'meta':0,'baseten':posthoc['total_baseten_estimated_or_reserved_usd'],'fireworks':0}
    totals={p:s['actual_estimated_or_reserved_spend_usd'][p]+extra[p] for p in extra}
    assert all(v<=40 for v in totals.values())
    (OUT/'task-spend.json').write_text(json.dumps({'primary_benchmark_usd':s['actual_estimated_or_reserved_spend_usd'],'posthoc_product_validation_usd':extra,'total_task_estimated_or_reserved_usd':totals,'authorized_per_provider_usd':40,'billed_usd':None,'note':'Each primary ledger reservation counted once; the post-hoc Baseten ledger is shared across both attempts. Not a remaining-credit balance or invoice.'},indent=2)+'\n')
    providers=('meta','baseten','fireworks')
    for zh,name in ((False,'README.md'),(True,'README.zh-TW.md')):
        lines=['<!-- multimodal-v1:start -->','']
        if zh:
            lines+=['**配對 benchmark：每種格式正確數 / 24。** 六家公司、24 個基礎主張，重複轉成九種格式；不是 216 個獨立題目。漏抽、未完成與判錯都留在分母。圖片／音訊／影片共用凍結的 Meta OCR／ASR，再比較文字查核。','']
        else:
            lines+=['**Paired benchmark: correct / 24 per format.** Six issuers, 24 underlying assertions repeated across nine encodings—not 216 independent facts. Missing, incomplete and wrong outcomes remain in the denominator. Media uses shared frozen Meta OCR/ASR before text verification.','']
        lines+=['| '+('格式' if zh else 'Format')+' | Meta | Baseten | Fireworks |','| --- | ---: | ---: | ---: |']
        for fmt in ('txt','md','pdf','png','jpg','webp','wav','mp3','mp4'):
            rows=[next(r for r in s['format_results'] if r['provider']==p and r['format']==fmt) for p in providers]
            lines.append('| '+fmt.upper()+' | '+' | '.join(f"{r['correct']}/{r['denominator']}" for r in rows)+' |')
        if zh:
            lines+=['','[完整結果與限制](docs/evidence/fair-multimodal-v1/REPORT.md) · [中文分析](docs/evidence/fair-multimodal-v1/ANALYSIS.zh-TW.md) · [輸入、原始回應與離線重用](docs/evidence/fair-multimodal-v1/REUSE.md)。這是清晰合成素材的單次受控測試；真實 Tesla 頁面另列無完整標準答案的診斷，不能據此宣稱全面準確率。','', '**原生圖片端點：完成回應 / 6 張控制圖，並非準確率。** 原生辨識的文字／數字指標見完整報告。此測試沒有改變產品仍使用 Meta OCR 的路徑。','']
        else:
            lines+=['','[Full results and limits](docs/evidence/fair-multimodal-v1/REPORT.md) · [inputs, raw outputs and offline reuse](docs/evidence/fair-multimodal-v1/REUSE.md). This is one controlled run on clean synthetic media. Real Tesla pages are separate diagnostics without complete gold; these scores are not broad real-world accuracy.','', '**Native image endpoints: completed responses / 6 control images, not accuracy.** Reading metrics are in the full report. These probes do not change the product’s shared Meta OCR route.','']
        lines+=['| '+('圖片格式' if zh else 'Image format')+' | Meta | Baseten | Fireworks |','| --- | ---: | ---: | ---: |']
        for fmt in ('png','jpg','webp'):
            counts=[]
            for p in providers:
                rows=[r for r in s['native_images'] if r['provider']==p and r['format']==fmt and r['split']=='test']
                counts.append(f"{sum(r['status']=='completed' for r in rows)}/{len(rows)}")
            lines.append('| '+fmt.upper()+' | '+' | '.join(counts)+' |')
        lines+=['','**'+('API 花費（USD，估算／保留額）' if zh else 'API spend (USD, estimated/reserved)')+'**','', '| '+('平台 | Benchmark | 事後產品驗證 | 本次工作合計' if zh else 'Platform | Benchmark | Post-hoc product checks | Total task spend')+' |','| --- | ---: | ---: | ---: |']
        for p in providers:lines.append(f"| {p.title()} | ${s['actual_estimated_or_reserved_spend_usd'][p]:.6f} | ${extra[p]:.6f} | ${totals[p]:.6f} |")
        if zh:
            lines+=['','每平台授權上限 $40；共用前處理全計入 Meta，失敗也保留。這不是帳單或剩餘 credit。詳細 [ledger／費用合計](docs/evidence/fair-multimodal-v1/task-spend.json)與[官方單價核對](docs/evidence/fair-multimodal-v1/RATE_CHECK.md)。','', '**同一股票多文件：** `review-stock` 可批次查核，`stock-summary` 可無新增模型費用重用報告。股票背景與表格引文修正的[真實 Tesla 摘要](docs/evidence/stock-context-posthoc-2026-10-30/attempt-2/summary/stock-review.html)保留三個 supported、五個 insufficient-evidence 主張及無可查核主張的圖表頁。這是[保留兩次嘗試的事後產品驗證](docs/evidence/stock-context-posthoc-2026-10-30/REPORT.md)，未替換 benchmark 分數，也不是獨立準確率。網頁上傳介面與 AI 敘述摘要仍在計畫中。']
        else:
            lines+=['','Authorization: $40 per platform. All shared preprocessing is charged to Meta; failures remain counted. These are not invoices or remaining-credit balances. [Ledger totals](docs/evidence/fair-multimodal-v1/task-spend.json) · [official rate cross-check](docs/evidence/fair-multimodal-v1/RATE_CHECK.md).','', '**Single-stock multi-file review:** `review-stock` checks a batch; `stock-summary` reuses reports without new inference. The [real Tesla summary](docs/evidence/stock-context-posthoc-2026-10-30/attempt-2/summary/stock-review.html) retains three supported and five insufficient-evidence claim occurrences plus a chart page with no checked claims. This is a [two-attempt post-hoc product check](docs/evidence/stock-context-posthoc-2026-10-30/REPORT.md), not an independent accuracy estimate or replacement benchmark score. Upload UI and AI narrative remain planned.']
        lines+=['','<!-- multimodal-v1:end -->']
        p=ROOT/name;text=p.read_text();start='<!-- multimodal-v1:start -->';end='<!-- multimodal-v1:end -->'
        if start in text:
            a=text.index(start);b=text.index(end,a)+len(end);text=text[:a]+'\n'.join(lines)+text[b:]
        else:
            marker='**公平比較：**' if zh else '**Fair comparison:**'
            a=text.index('\n\n',text.index(marker));text=text[:a]+'\n\n'+'\n'.join(lines)+text[a:]
        text=text.replace('These new real-media candidates have not been model-evaluated.','Three Tesla pages now have separately recorded unscored diagnostics and post-hoc product checks; linked webcasts have not been evaluated.')
        text=text.replace('這批真實素材尚未進行模型評測。','三張 Tesla 頁面已有獨立列示的診斷與事後產品驗證；連結中的法說會影音尚未評測。')
        p.write_text(text)
    print(json.dumps({'total_task_estimated_or_reserved_usd':totals}))
if __name__=='__main__':main()
