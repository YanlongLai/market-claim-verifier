"""Refresh only the compact paired-format table in each README, offline.

Editorial structure stays hand-authored. Detailed costs, native probes and run
history belong in their evidence reports; historical ledgers are never rewritten.
"""
from pathlib import Path
import json
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/evidence/fair-multimodal-v1'
START = '<!-- multimodal-v1:start -->'
END = '<!-- multimodal-v1:end -->'


def main():
    summary = json.loads((OUT / 'summary.json').read_text())
    if any(r['result'] is None or r['status'] == 'running' for r in summary['case_index']):
        raise ValueError('test split incomplete')
    formats = [('txt', 'TXT'), ('md', 'Markdown'), ('pdf', 'PDF'), ('png', 'PNG'),
               ('jpg', 'JPEG'), ('webp', 'WebP'), ('wav', 'WAV'), ('mp3', 'MP3'), ('mp4', 'MP4')]
    updates = []
    for zh, name in ((False, 'README.md'), (True, 'README.zh-TW.md')):
        intro = ('六家公司、24 個基礎主張，轉成九種格式；不是 216 個獨立題目。表格為正確數／24，漏抽、未完成與判錯均保留於分母。三家使用相同檔案與凍結的 Meta OCR／ASR 文字。' if zh else
                 'Six issuers, 24 underlying assertions, nine encodings—not 216 independent facts. Cells show correct / 24; missing, incomplete and wrong outcomes remain in the denominator. All providers use the same files and frozen Meta OCR/ASR text.')
        lines = [START, '', intro, '', '| ' + ('格式' if zh else 'Format') + ' | Meta | Baseten | Fireworks |', '| --- | ---: | ---: | ---: |']
        for key, label in formats:
            rows = [next(r for r in summary['format_results'] if r['provider'] == p and r['format'] == key)
                    for p in ('meta', 'baseten', 'fireworks')]
            # The scorer's explicit counts are authoritative; no display-only rescore.
            cells = [f"{r['correct']}/{r['denominator']}" for r in rows]
            lines.append('| ' + label + ' | ' + ' | '.join(cells) + ' |')
        if zh:
            lines += ['', '這是清晰控制素材上的單次測試，音訊與影片為合成內容。另列的原生圖片測試中，三家 PNG／JPEG／WebP 均各完成 6/6 張；完成回應不等於財務判定正確。原生聲音／影片端點沒有在這份比較中測試。', '', '[完整方法、失敗與限制](docs/evidence/fair-multimodal-v1/REPORT.md) · [重用輸入、輸出與離線重算](docs/evidence/fair-multimodal-v1/REUSE.md)。']
        else:
            lines += ['', 'One controlled run on clean inputs, with synthetic audio and video. Separate native-image probes completed 6/6 PNG, JPEG and WebP inputs per provider; response completion is not financial accuracy. Native audio/video endpoints were not tested in this comparison.', '', '[Methods, failures and limits](docs/evidence/fair-multimodal-v1/REPORT.md) · [Reusable inputs, outputs and offline replay](docs/evidence/fair-multimodal-v1/REUSE.md).']
        lines += ['', END]
        path = ROOT / name
        text = path.read_text()
        if text.count(START) != 1 or text.count(END) != 1:
            raise ValueError('expected exactly one table block in ' + name)
        a = text.index(START); b = text.index(END, a) + len(END)
        updates.append((path, text[:a] + '\n'.join(lines) + text[b:]))
    for path, text in updates:
        path.write_text(text)
    print('Updated paired-format tables in both READMEs; evidence records unchanged.')


if __name__ == '__main__':
    main()
