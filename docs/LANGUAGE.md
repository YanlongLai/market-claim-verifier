# Language policy

English is the default for human-readable Markdown, HTML, TXT and SRT files. Traditional Chinese prose belongs in a separate `NAME.zh-TW.ext` mirror or an explicit `/zh/` route; the existing explorer `index.zh.html` route is also Chinese. Each rendered interface selects one language. English files contain no CJK text. Chinese files contain no Latin prose beyond product/model identifiers, tickers, URLs, numbers and code.

JSON/YAML may retain separate language fields and original-language source records. Source quotations, reference notes, model summaries, numeric results and traces remain unchanged in those machine-readable records. A translated reading layer must identify itself and link back to the original; it must never be represented as a new model result.

## Entry points and mirrors

[README.md](../README.md) and [JUDGES.md](../JUDGES.md) are the English entry points. [README.zh-TW.md](../README.zh-TW.md) and [JUDGES.zh-TW.md](../JUDGES.zh-TW.md) mirror their section structure. Keep capability boundaries, headline figures, evidence links, costs, limits and commands aligned. Chinese technical prose is translated; source/model identifiers remain exact.

The explorer defaults to [English](explorer/index.html), with a separate [Traditional Chinese route](explorer/index.zh.html). Both use the same JSON data; switching preserves the selected claim hash, including `#G0119`.

## Retained evidence

The [language audit](evidence/readme-v3-2026-11-04/REPORT.md#language-audit) explains reading-layer changes. Its [source archive](evidence/readme-v3-2026-11-04/original-language-sources.json) retains exact pre-edit text and SHA-256 values. Original Chinese TXT inputs are retained byte for byte in `.zh-TW.txt` mirrors; English counterparts are display translations, not replacement paid-test inputs. Historical source hashes continue to describe the original bytes. Original result/traces JSON and numeric evidence are preserved.

Archived diagnostic TXT logs spell embedded source-language code strings with Unicode escapes; the exact original log text remains recoverable from the source archive. Chinese reading reports link English quotations and error messages to their English source instead of displaying mixed-language prose.

## Enforcement

[Language-purity tests](../tests/test_language_purity.py) scan every eligible repository file without Git or network access, skip environment/build directories and symlinks, and check English CJK absence plus Chinese Latin-prose absence. A finite identifier vocabulary, code/URL parsing and regression examples prevent ordinary English sentences from being accepted as identifiers. Run them through `bash scripts/verify.sh`.
