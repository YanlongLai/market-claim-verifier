# W2 site verification records

Offline UI checks for the story/input matrix, provider choice, comparison and public history. The mocked endpoint tests execute the shipped JavaScript against the parsed EN/zh HTML. They do not retest OCR/ASR, call a model, fetch SEC data, or establish financial accuracy. The synthetic B/C responses exercise UI states; W3's manifest supplies the actual example content.

The final source and fixture hashes are in [receipt.json](receipt.json). Input cases and mock responses remain in [the matrix runtime tests](../../test_site_examples_runtime.py) and [the form runtime tests](../../test_site_live_runtime.py). The DOM adapter is [the existing site harness](../../test_site_stamps_runtime.py).

| Attempt | Outcome |
| --- | --- |
| [Focused 1](targeted-r1.txt) | 29 passed, 4 failed: history selector emulation and a preserved trailing newline |
| [Focused 2](targeted-r2.txt) | 57 passed |
| [Focused 3](targeted-r3.txt) | 79 passed, including copy, SEO and asset hashes |
| [Focused 4](targeted-r4.txt) | 20 passed, 3 failed: the adapter retains whitespace text nodes in its children array |
| [Focused 5](targeted-r5.txt) | 20 passed, 3 failed: the lightweight CSS parser splits commas inside :is() |
| [Focused 6](targeted-r6.txt) | 84 passed; all fifteen inputs, EN/zh, 375/768/1440 widths, receipts, provider radio, custom text, saved/pending, compare, history row click/edit, stale replies, hostile text and budget failures |
| [Full 1](verify-r1.txt) | 1,290 product/site tests passed; demo suite had 203 passes and 3 stale provenance-hash failures |
| [Full 2](verify-r2.txt) | 1,292 product/site tests passed, 3 failed from the earlier CSS-parser snapshot; final focused run resolves those failures |
| [Full 3](verify-r3.txt) | PASS: 1,295 product/site tests, 206 demo tests, 97 standalone Node tests; figure/data/example rebuilds and Markdown links |

Intermediate failures remain available for diagnosis.

The full check is `bash scripts/verify.sh`. It runs both Python suites and Node suites in a disposable copy, installs network guards and removes provider credentials, checks SEC fixtures, rebuilds figures and data, verifies links, and checks generated assets. Local focused commands used Python 3.14.6, Node 26.6.0 and uv 0.12.1 with locked dependencies in temporary environments.

Two generated demo files and two shared evidence-page cache stamps also follow the new site script/CSS hashes. The demo changes contain one provenance hash each; their adapted animation code, measured narration, host timing and recorded evidence are unchanged.

[Source lint](lint-final.txt) reports 0 failures and 0 warnings. [Earlier lint findings](lint-baseline.txt) are retained. The spec requires monospace data; source annotations explain that exception and the recorded-post emoji. No external imagery was added. This component follows the existing paper/ink/green palette and serif/text/data type roles; no new direction draw was needed.

[Browser access attempts](browser-review.txt) were refused/unavailable, so there are no screenshots, real-browser overflow measurements, or visual-approval scores. Width checks verify the shipped CSS column rules and DOM ordering, not actual font layout.
