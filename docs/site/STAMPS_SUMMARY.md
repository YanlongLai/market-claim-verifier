# Stamp v2 implementation and verification

Implemented the Owner's animation brief on `site/stamp-v2` in
`/Users/yan/git/market-claim-verifier-stamp2`, against `STAMP-V2-DESIGN.md` sections
3–6, including the round-2b persona note and the persona implementation brief.
The brief is the bounded implementation authority; the approved gap math
and existing unrelated worktree edits were preserved. No commit, push, or
publication was performed.

The character is **B only**: lazy, asynchronously decoded idle/inspect/present/stamp
WebP poses, with a deterministic 120 ms cross-fade and small lean/bob transforms.
A/C image files, previews, and redundant PNG pose exports were removed. The
four runtime poses total **311,514 bytes**. With the five 128 px persona avatars,
new runtime artwork totals **335,118 bytes**, below the 400,000-byte budget. The
Owner-required `sheet-B.png` and historical prompts remain as source material;
the page never requests the source sheet.

Cards show the fictional post author's circular avatar (40 px desktop / 32 px
phone), localized display name, handle or outlet, example follower count, post
date and **Example post / 示範貼文** tag. The tag explains that authors and follower
counts are fictional, while claims and verdicts come from real checks. Below it
are the real ticker, SEC company name, source kind, enlarged claim number and
bilingual period chip. The example dates are validated against SEC companyfacts;
the source reports remain unmodified. The unused `news-paper` images were deleted.
After review they show the existing verdict, severity, rounded score out of
100, meter, gap description, and compact filed value. Forecasts and opinions
have no passage, filed value, severity, or meter; the robot shrugs in idle and
a grey CAN'T CHECK stamp lands.

Each card runs the specified phases on the same clock at both widths:

| Local time | Phase |
| --- | --- |
| 0.0–0.7 s | Enter and stop at the desk; idle |
| 0.7–1.4 s | Inspect, scan, number glow |
| 1.4–3.0 s | Present the filing passage and sweep its matching value amber |
| 3.0–3.6 s | Reveal severity and fill score meter |
| 3.6–4.2 s | Stamp impact and small card shake |
| 4.2–5.0 s | Exit with verdict, meter and filed value; fold passage away |
| 5.0–6.5 s | Rest before the next card |

CAN'T CHECK substitutes a shrug for the passage/meter phases. The eleven-card loop
is **71.5 s**, with no adjacent equal verdicts, including wraparound. The
deterministic `?stamp-t=` and `window.__stampScene.seek(seconds)`
hooks work forward, backward, and across loop boundaries. `getState()` and the
frozen `timing` object expose the review state for reproducible local checks.
Off-screen, hidden-tab, manual pause and reduced-motion changes cancel the
animation clock; resuming preserves its time. Only transform and opacity animate.

Desktop has a central desk, B on its right, source paper between card and robot,
and a 70%-scale upcoming queue on the left. Cards have natural content height
with no desktop minimum height; the filed value joins the compact meter/stamp
footer. The compact layout puts B above/right
and the passage in a reserved area in the lower half of the card. The filed
value, meter and stamp have separate space. Reduced motion uses a complete,
linked static list with verdict, severity, score, filed value, and passage text;
that same list is available to assistive technology during animation. EN/中文
are retained. Light mode keeps warm paper; dark mode uses cool slate
(`#202d36`) with subtle grain and a slight lift from the background. Playback is
right-aligned below the stage, with space reserved before the next section.
Failed ink masks leave readable solid verdict text.

## Final card list and date evidence

All requested example dates passed without adjustment. `date_basis.facts` in
`site.json` records each concept, unit, exact start/end, earliest `filed`, first
reported value, form, accession, CIK and SEC companyfacts URL.
`date_basis.not_before` is the latest of those earliest filing dates. Both years
of growth checks and both components of the derived Apple quarter are included;
duplicate evidence references are collapsed. Opinions and forecasts have no
checked figures, so their basis is empty, and their dates still cannot be future.

| # | Persona · claim | Kind · followers (EN / 中文) | Post date | `date_basis` first-filed dates | Verdict | Severity · score |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Ticker Owl · @tickerowl · AMZN Q3 2023 | Thread · 18.4K / 1.84 萬 | 2025-11-03 | AMZN Q3: 2023-10-27 | TRUE | Exact · 100 |
| 2 | Ticker Owl · @tickerowl · AAPL fiscal Q4 2025 | Thread · 18.4K / 1.84 萬 | 2025-11-03 | Full year: 2025-10-31; nine months: 2025-08-01 | FALSE | Severe · 0 |
| 3 | Ticker Owl · @tickerowl · NVDA valuation opinion | Thread · 18.4K / 1.84 萬 | 2025-11-03 | None: opinion | CAN'T CHECK | — |
| 4 | Ticker Owl · @tickerowl · NVDA FY2024 revenue + growth | Thread · 18.4K / 1.84 萬 | 2025-11-03 | FY2024: 2024-02-21; FY2023: 2023-02-24 | TRUE | Exact · 100 |
| 5 | Chart Coon · @chartcoon · TSLA FY2025 growth | Thread · 52.1K / 5.21 萬 | 2026-02-03 | FY2025: 2026-01-29; FY2024: 2025-01-30 | FALSE | Major · 46 |
| 6 | US Stocks in 1 Minute / 美股懶人包 · MSFT FY2024 | Social post · 43K / 4.3 萬 | 2025-02-24 | FY2024: 2024-07-30; FY2023: 2023-07-27 | TRUE | Exact · 100 |
| 7 | Chart Coon · @chartcoon · AAPL forecast | Thread · 52.1K / 5.21 萬 | 2026-02-03 | None: forecast | CAN'T CHECK | — |
| 8 | Chart Coon · @chartcoon · AAPL FY2024 | Thread · 52.1K / 5.21 萬 | 2026-02-03 | FY2024: 2024-11-01 | TRUE | Exact · 100 |
| 9 | US Stocks in 1 Minute / 美股懶人包 · KO FY2024 | Social post · 43K / 4.3 萬 | 2025-02-24 | FY2024: 2025-02-20 | FALSE | Moderate · 88 |
| 10 | Banana News Flash / 香蕉新聞快報 · AMZN headline | Article · 96K / 9.6 萬 | 2023-10-27 | Q3 2023: 2023-10-27 | TRUE | Exact · 100 |
| 11 | Market Recap · KO repost | Repost · 210K / 21 萬 | 2025-02-25 | FY2024: 2025-02-20 | FALSE | Moderate · 88 |

Chart Coon is the fictional finance influencer; Banana News Flash is the
fictional newsroom. The two added cards share their original `check_id`, quote,
verdict, exact unrounded score, severity, gap, filed value and excerpt. There are
still **nine source claims**. The repost says **Reposted from 美股懶人包 / 轉貼自
美股懶人包**; the article uses bilingual headline copy of the same Amazon claim.

## Filing provenance

All **9 checkable cards** (seven original numeric claims plus two presentations
of existing claims) have `stamp_cards[].excerpt`, selected with the same
`filing_excerpts.py` fact matcher used by the See filing modal. Six reuse existing
matched modal rows; Apple's Q4 source is matched from the actual 10-K HTML.
The excerpts include form, filed date, company, verbatim row label, matching
period header, raw value, scale, source evidence, and original-filing URLs.

Apple's $416.2B quarter claim is labelled explicitly:

- 10-K, filed 2025-10-31, Full year, Total net sales, **416,161** (USD millions).
- SEC nine-month revenue is **313,695** (USD millions), from the 10-Q filed
  2025-08-01. Both source accessions, dates, ranges and values are preserved.
- **Q4 = full year − nine months = $102.5B**; exact raw result is $102.466B.
- The claim's original missing quarter filing URL is preserved; the static card
  links to the source report and the excerpt retains its real annual-filing URL.

Only the SEC filing index and primary Apple HTML were fetched, with the required
`User-Agent: DappGo market-claim-verifier admin@dappgo.com`, at no more than
5 requests/s, cached under `.cache/filings/`. The pre-existing dangling cache
symlink was replaced with a local cache directory. Subsequent `--offline` rebuilds
reuse matching stored excerpt/component provenance. The persona round read
companyfacts from existing local SEC caches and seeded the SEC-only build cache
under `.cache/filings/`; no external download was needed. Every build, including
`--offline`, resolves minimum `filed` from those facts again and fails for a post
preceding any checked figure, a missing first-filing match, or a future date.
The fetcher now rejects uncached requests in offline mode and allows only
`www.sec.gov` and `data.sec.gov`.

## Verification and gate status

- **380 tests passed** in the full suite; **81 stamp tests passed**. Source lint
  reports **0 failures, 0 warnings**. The offline rebuild is byte-identical.
- Stamp data/runtime tests cover exact phase boundaries on all eleven cards,
  120 ms pose blending, the CAN'T CHECK branch, all checkable excerpts, Apple
  derivation, scores, personas, bilingual headers and attribution, example dates,
  complete date bases, failing date cases, offline fact caches, artwork budgets
  and lazy decoding.
- Offline CSS envelope checks sample the whole loop at 25 ms intervals at
  **375 / 1024 / 1280 px**, checking held-card, passage, robot and rotated stamp bounds,
  separate meter/stamp space, and no overlapping moving cards. Enter/exit may
  cross the clipped track edge intentionally. These checks do not render glyphs.
- Forward/backward/loop seek, resize repaint, both languages, reduced motion,
  off-screen/hidden pause, resumption and texture fallback are tested.
- `node --check docs/site/script.js`, `git diff --check`, source design lint and
  an offline data rebuild are the local source/data checks.
- Use `PYTHONPATH="$PWD/src:$PWD" .venv/bin/python -m pytest -q` for the full
  suite: this worktree's existing `.venv` is linked to another checkout, so the
  source path must point here to load the approved gap helpers.

Actual browser screenshots and visual inspection remain **pending**. Chrome's
headless process did not start in the sandbox; the browser tool then rejected
the localhost preview because browser network access was declined. No browser
workaround, screenshot, Claude review, second-AI review, Owner visual approval,
or publication is claimed.

[Owner key-frame times](STAMP-V2-KEYFRAMES.md): **7.55 s** inspecting,
**8.95 s** passage + amber sweep, **10.24 s** stamp + Severe meter; identical
for desktop and phone. These are concrete review frames, not an approval record.
