# In the wild

This separate page shares the saved demo’s colors, system fonts and language preference. All automatic requests stay on the current origin; SEC and Threads links are ordinary navigation. Paths are relative so `/wild/` works with `docs/` as the Cloudflare Pages root and with a GitHub Pages project prefix. No third-party images or verbatim post bodies are included.

## Build from evidence

```sh
python3 docs/scripts/build_wild.py
python3 docs/scripts/build_wild.py --check
```

Both News and Threads phases must be complete under `docs/evidence/real-world-2026-11-02/`. The compiler requires frozen claims/gold, completion records, recorded metrics, every result row, Threads selection metadata and the corrected source-tier gold file. It checks input hashes, inventories, outcome totals and costs. It fails before writing if evidence is missing or inconsistent. It never fetches sources, runs models, emits placeholder numbers or modifies recorded evidence.

Conflict cards use independent primary-source reference labels. Agent verdicts stay in the coverage panel, including erroneous support, incomplete attempts and budget stops. Auto-translation display metadata does not establish translation causation. Review items without resolved periods do not become conflict cards. The Threads selection record does not contain reliable engagement measurements.

The optional `real-world-2026-11-03-fixcheck` directory must provide a separately identified post-hoc recheck with an explicit Before/After table in `REPORT.md`, or a structured `summary.json` (`kind: posthoc_fixcheck`, `comparisons` containing descriptions, before/after values and evidence paths). The report adapter retains source wording and skips claim/body columns. If present but incomplete, compilation fails rather than omitting it. Its comparisons remain separate from the original probe results. Text-only rechecks do not establish OCR/ASR improvements.

When the required evidence has not been merged, there is no saved page data. The page shows an explicit unavailable message and the README/JUDGES “In the wild” TODOs stay unchanged. The offline verifier exercises the compiler and page with clearly synthetic fixtures in that state. Once evidence is merged, generate and commit `data.json`; the verifier requires its byte-identical offline rebuild.

## Checks

`tests/test_wild_builder.py` uses synthetic filesystem fixtures to check accounting, denominator handling, source attribution, missing evidence, independent reference cards and deterministic output. `tests/test_wild_page.py` executes the shipped HTML/JavaScript with an offline DOM adapter for both languages, provider/workflow changes, themes, missing data, blocked storage, CSP and project-prefix paths. CSS contracts check the phone composition; browser screenshots provide separate visual QA. The offline suite does not launch Chromium.
