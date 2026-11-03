# Wild page verification — 2026-11-02

The separate page, compiler and fixture tests are implemented. The required real-world News/Threads evidence is not yet merged into this worktree, and no production `data.json` has been fabricated. The compiler exits with `FAIL wild evidence: Required evidence missing` before writing anything. README, README.zh-TW and JUDGES retain their “In the wild” TODO links until real data exists.

## Recorded checks

- Final full `UV_OFFLINE=1 sh scripts/verify.sh`: 957 product/site tests, 149 demo tests and 55 standalone Node tests passed. Figures regenerated successfully; the three pre-existing data outputs rebuilt byte for byte. Local Markdown links passed. The runner reported its explicit wild-data skip because the evidence was absent; the new compiler/page fixture tests were included in the full product suite. Earlier passing full runs remain retained separately.
- The [compiler tests](../../tests/test_wild_builder.py) and [page tests](../../tests/test_wild_page.py): 26 passed. They cover deterministic bytes, failure before overwrite, missing completion/results, duplicate attempts, source/gold integrity, budgets, failures, source denominators, independent reference cards, restraint about translation causation, bilingual controls, themes, blocked storage, CSP, report/JSON fixcheck comparisons and same-origin requests under both root and project-prefix hosting.
- Frontend source lint: no failures or warnings. CSS contract checks cover the phone composition and readable controls. These are not browser measurements.
- `docs/site/index.html`, `docs/site/script.js` and `docs/site/styles.css` were not changed.

## Limits and retained attempts

Browser screenshots were not obtained. The design skill’s inspector could not launch Chrome in this sandbox (`Chrome exited early`). A subsequent computer-access request for Google Chrome was rejected without a stated reason. Runtime/layout contracts therefore pass without claiming visual browser approval.

Local logs and design notes are retained under ignored `runs/wild-page/`, including the full offline run. The initial targeted-test attempts exposed a test-file syntax error and a favicon path error; both were fixed before the passing runs. No paid calls, source fetches, OCR/ASR or live evaluations were used. Synthetic fixture data is kept in `tests/fixtures/wild/` and is never published as findings.

## After merging the evidence

Run `python3 docs/scripts/build_wild.py`, inspect its saved output, replace the README/JUDGES findings TODOs, then rerun `UV_OFFLINE=1 sh scripts/verify.sh`. The presence of either real evidence or a saved wild snapshot activates the strict fourth data-output rebuild; stale or missing evidence/output fails verification. A present but incomplete optional fixcheck also fails compilation.
