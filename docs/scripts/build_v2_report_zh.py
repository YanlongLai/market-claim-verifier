"""Build a Traditional Chinese reading layer without changing recorded data rows."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / 'docs/evidence/eval-v2-2026-10-27'
EN_SWITCH = '**English** | [繁體中文](REPORT.zh-TW.md)'
ZH_SWITCH = '[English（主要版本）](REPORT.md) | **繁體中文**'
HEADINGS = {
'Market claim evaluation report': '金融主張查核評測報告',
'Per-system totals': '各系統總計', 'Provider comparison': '平台比較',
'Prompt versions': 'Prompt 版本', 'Metrics': '評測指標',
'Per-gold-class precision and recall': '依標準答案類別的精確率與召回率',
'Paired comparisons': '配對比較', 'Source scorecard': '來源評分',
'Source reliability by claim-source tier': '依主張來源類型的可靠度',
'Source reliability by domain (n ≥ 20 only)': '依網域的來源可靠度（僅 n ≥ 20）',
'System accuracy by source tier': '依來源類型的系統準確率',
'Agent evidence strength': 'Agent 證據強度', 'Per-claim results': '逐筆主張結果',
'Agent errors': 'Agent 錯誤紀錄', 'Accounting': '費用紀錄',
}
PARAGRAPHS = {
'Accuracy uses all expected claims in the denominator; a missing, failed, or budget-stopped pair is not a correct prediction. Per-class recall uses all claims of that gold class, while precision uses completed predictions of that class. False-supported rate is the harmful error rate among gold contradicted or insufficient-evidence claims. Latency and cost summaries use completed pairs only.': '準確率以全部預期主張為分母；缺漏、失敗或因預算停止的配對不算正確。各類別召回率以該標準答案類別的全部主張計算；精確率使用已完成且預測為該類別的結果。錯誤支持率指標準答案為矛盾或證據不足，卻被判為支持的比例。此處延遲與成本摘要使用已完成配對；下方各系統總計另有自己的統計範圍。',
'Tokens are shown as input/cached/output/reasoning. Totals include every recorded pair; latency percentiles include pairs with a recorded model call.': 'Token 順序為輸入／快取／輸出／推理。總計包含所有已記錄配對；延遲百分位數包含有模型呼叫紀錄的配對。',
'No significance claims are made for groups with n < 50; Wilson intervals and paired tests there are descriptive and unstable.': 'n < 50 的群組不作統計顯著性主張；這些群組的 Wilson 區間與配對測試僅供描述，結果不穩定。',
'Reasoning share is reasoning tokens divided by output tokens; provider totals include both methods.': '推理占比＝推理 token ÷ 輸出 token；各平台總計同時包含單次回答與 Agent 兩種方法。',
'Accuracy difference is left minus right; bootstrap intervals use 10,000 seeded paired resamples and McNemar is exact two-sided.': '準確率差值為左側減右側；bootstrap 區間使用固定隨機種子的 10,000 次配對重抽樣；McNemar 使用雙尾精確檢定。',
'Source reliability uses gold labels and is independent of the verifier systems. Per-domain values are shown only at n ≥ 20; Wilson intervals are 95% intervals.': '來源可靠度使用標準答案，與查核系統的預測無關。僅列出 n ≥ 20 的個別網域；Wilson 區間為 95% 信賴區間。',
'Tokens are shown as input/cached/output/reasoning for each system.': '每個系統的 token 順序為輸入／快取／輸出／推理（i/c/o/r）。',
'Budget stop: none recorded.': '預算停止：未記錄到。',
}
LABELS = {
'System':'系統','Pairs':'配對數','Completed':'已完成','Total cost':'總費用（美元）',
'Input tokens':'輸入 tokens','Cached tokens':'快取 tokens','Output tokens':'輸出 tokens',
'Reasoning tokens':'推理 tokens','Model calls':'模型呼叫數','Tool calls':'工具呼叫數',
'Mean latency ms':'平均延遲（ms）','p50 ms':'p50（ms）','p95 ms':'p95（ms）',
'Provider':'平台','Accuracy':'準確率','False-supported rate':'錯誤支持率',
'Input':'輸入','Cached':'快取','Output':'輸出','Reasoning':'推理','Reasoning share':'推理占比',
'Prompt':'Prompt','SHA-256 prefix':'SHA-256 前綴','Split':'資料集','n':'n',
'completed':'已完成','errors':'錯誤數','accuracy':'準確率','accuracy 95% CI':'準確率 95% CI',
'false-supported rate':'錯誤支持率','false-supported 95% CI':'錯誤支持率 95% CI',
'insufficient rate':'證據不足率','insufficient 95% CI':'證據不足率 95% CI',
'mean latency ms':'平均延遲（ms）','total cost':'總費用（美元）','mean cost':'平均費用（美元）',
'Gold class':'標準答案類別','Support':'該類別樣本數','Predicted':'預測數',
'Precision':'精確率','Recall':'召回率','Pair':'比較配對','Accuracy difference':'準確率差值',
'Bootstrap 95% CI':'Bootstrap 95% CI','McNemar exact p':'McNemar 精確 p 值',
'Discordant left/right':'僅左側／僅右側答對數','Tier':'來源類型',
'Supported share (95% CI)':'支持比例（95% CI）','Contradicted share (95% CI)':'矛盾比例（95% CI）',
'Insufficient share (95% CI)':'證據不足比例（95% CI）','Domain':'網域','Source tier':'來源類型',
'Wilson 95% CI':'Wilson 95% CI','Agent system':'Agent 系統','Strength':'證據強度','Share':'占比',
'Correct':'正確數','ID':'ID','Category':'類別','Claim':'原始主張','Gold':'標準答案',
'Status':'狀態','Message':'原始訊息',
}

def label(cell):
    if cell in LABELS:
        return LABELS[cell]
    for suffix, translated in [(' tokens (i/c/o/r)', ' tokens（輸入／快取／輸出／推理）'),
                               (' latency ms', ' 延遲（ms）'), (' correct?', ' 是否正確'),
                               (' verdict', ' 判定'), (' cost', ' 費用（美元）')]:
        if cell.endswith(suffix):
            return cell[:-len(suffix)].replace('Single Shot', '單次回答') + translated
    raise ValueError('Untranslated table heading: ' + cell)


def build():
    source = DIRECTORY / 'REPORT.md'
    english = source.read_text()
    if EN_SWITCH not in english:
        title, rest = english.split('\n', 1)
        english = title + '\n\n' + EN_SWITCH + '\n' + rest
        source.write_text(english)
    lines = english.splitlines()
    result = []
    for i, line in enumerate(lines):
        if line == EN_SWITCH:
            result += [ZH_SWITCH, '', '> [!NOTE]', '> 本頁翻譯章節、表頭與閱讀說明；數字、原始主張、模型判定、ID 與錯誤訊息保持英文報告原樣。英文為主要版本。', '',
                       '**代碼說明：** `dev`＝開發集；`test`＝獨立測試集；`supported`＝有證據支持；`contradicted`＝與證據矛盾；`insufficient_evidence`＝證據不足；`yes/no`＝是／否；CI＝信賴區間。']
        elif line.startswith('#'):
            prefix, title = line.split(' ', 1)
            result.append(prefix + ' ' + HEADINGS[title])
        elif i+1 < len(lines) and lines[i+1].startswith('|---'):
            result.append('| ' + ' | '.join(label(c.strip()) for c in line.strip('|').split('|')) + ' |')
        elif line in PARAGRAPHS:
            result.append(PARAGRAPHS[line])
        else:
            for before, after in [('Generated: ', '報告產生時間：'), ('Run window: ', '執行期間：'),
                                  ('Wall clock: ', '記錄的 wall-clock 時間：'),
                                  ('Suppressed domains below n ≥ 20: ', '樣本不足 20 而未單獨呈現的網域：'),
                                  ('Ledger spend before/after: ', 'Ledger 執行前／後累計支出：')]:
                if line.startswith(before):
                    line = after + line[len(before):]
                    break
            result.append(line)
    # Every data row and alignment row must be preserved exactly.
    def data_rows(rows):
        return [l for i,l in enumerate(rows) if l.startswith('|') and not (i+1<len(rows) and rows[i+1].startswith('|---'))]
    assert data_rows(lines) == data_rows(result)
    (DIRECTORY / 'REPORT.zh-TW.md').write_text('\n'.join(result)+'\n')
    print('PASS Chinese report generated; all data and alignment rows unchanged')

if __name__ == '__main__':
    build()
