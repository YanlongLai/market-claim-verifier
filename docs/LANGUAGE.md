# Language policy

English is the primary language for public documentation and judge-facing interfaces. The results explorer defaults to English at `explorer/index.html`, with an explicit Traditional Chinese switch to `explorer/index.zh.html`. Switching languages preserves the selected claim hash, including `#G0119`.

Original claims, source quotations, reference notes, model summaries and recorded evidence retain their original language. Translating interface labels must not change benchmark data or the meaning of a recorded claim. Chinese supplementary explanations may accompany English documentation.

Both explorer pages use the same `data.json`. Update both interfaces when adding functionality; keep claims, filters, verdicts and evidence links equivalent. English is the default regardless of browser locale; the explicit Chinese URL remains shareable.

## Repository README

[README.md](../README.md) remains the default English entry point. [README.zh-TW.md](../README.zh-TW.md) provides the Traditional Chinese guide with a reciprocal language switch. Keep capability tables, prices, recorded measurements, caveats and commands aligned. Detailed technical appendices link to the English source of truth.
