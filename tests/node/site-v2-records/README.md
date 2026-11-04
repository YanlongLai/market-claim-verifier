# Site presentation v2 — offline records

These records cover the English and Traditional Chinese site, READMEs and judge guides, the saved-check stepper, provider chart, Try presentation, deployment budget copy and generated asset stamps. They reuse committed financial evidence. They are not a new benchmark or a fresh OCR/ASR test.

All work used a $0 paid-call budget: no model calls, SEC fetches, authenticated checks, production writes or private account balances. The full verifier removes credentials, blocks test/build network access, and runs in a disposable copy. Dependency setup uses the locked packages and the temporary uv cache.

## Recorded runs

| Record | Result and boundary |
| --- | --- |
| [Targeted r1](targeted-r1.txt) | 96 failed, 17 passed. Early implementation and obsolete homepage assertions; retained before adapting the DOM harness and copy tests. |
| [Targeted r2](targeted-r2.txt) | 18 failed, 108 passed. Remaining old assumptions and static saved-file request mocks. [Diagnostic](targeted-r2-diagnostic.txt): 1 failed, 9 passed. |
| [Targeted r3](targeted-r3.txt) | 10 failed, 208 passed. Harness variable collisions and link-adapter assumptions. [Diagnostic](targeted-r3-diagnostic.txt) and [selected input hashes](targeted-r3-inputs.json) retained. |
| [Targeted r4](targeted-r4.txt) | 14 passed after those repairs. |
| [Targeted r5](targeted-r5.txt) | 51 passed, including compact recorder dates. |
| [Targeted r6](targeted-r6.txt) | 51 passed on the final functional source, including filing-link validation. |
| [Full verifier r1](verify-r1.txt) | 1,443 product/site tests and 206 demo tests passed, alongside standalone Node tests, rebuilds and link checks. [Selected inputs](verify-r1-inputs.json). Precedes the final date, link and touch-target refinements. |
| [Full verifier r2](verify-r2.txt) | 1,445 product/site tests, 206 demo tests and 97 standalone Node tests passed; rebuilds, links and network guards passed. Its console log and [selected inputs](verify-r2-inputs.json) are the authoritative result. |
| [Delivery checks](delivery-checks.json) | After retaining these logs: all Markdown links, generated Chinese structure, asset stamps and patch whitespace pass. |
| [Source lint](lint-final.txt) | 0 failures, 0 warnings. Source inspection, not a rendered-browser review. |
| [GIF sandbox attempt](gif-sandbox-attempt.txt) | Playwright could not be imported; the placeholder GIF was retained. |

Early targeted logs did not capture a complete input manifest. Their failures remain visible; no retrospective hashes are presented as pre-run freezes. The full verifier receipts record selected hashes before execution. [The final receipt](receipt.json) also hashes the delivery sources and frozen UI inputs.

## Browser and GIF boundary

The skill inspector could not launch Chrome in this sandbox (`code null`), and the in-app browser host was unavailable. No rendered screenshot review, Lighthouse run or GIF capture is claimed. Keyboard behavior, language purity, saved evidence, chart filtering, responsive source rules and reduced-motion lifecycle behavior have automated coverage, but that does not replace host visual review.

The committed `readme-robot.gif` is a 720 px static placeholder built from the existing robot art. On a host with Playwright and Chromium, run from the repository root:

```sh
PLAYWRIGHT_MODULE=/absolute/path/to/playwright/index.mjs \
  uv run python scripts/capture_readme_gif.py --record-dir /tmp/mcv-site-v2-gif-host
```

The script captures only the local scene, blocks external requests and API routes, retains frames/logs and a receipt, and replaces the placeholder only after a successful 7 s, 720 px capture under 3 MB. `CHROME_PATH` can select Chromium; installed macOS Chrome is detected automatically. Omit `PLAYWRIGHT_MODULE` if Node can resolve `playwright`.

## Reuse

```sh
bash scripts/verify.sh
UV_OFFLINE=1 bash scripts/verify.sh
```

The final suite includes [language and shared Facts checks](../../test_site_copy.py), [saved-data stepper/chart/history/date checks](../../test_site_presentation_runtime.py), existing Try runtime tests, and the stamp-scene lifecycle checks. Recorded financial envelopes, model IDs, prompts, original evaluation results and Try API contracts remain the evidence inputs.
