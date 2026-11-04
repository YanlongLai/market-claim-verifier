# Site round 4 — readable saved results

Base: `adc9406d`; delivery branch: `site/r4`.
This is a presentation change to the saved and live result renderer. AI001
remains disabled. `DESIGN-final.md` is absent from this checkout, as recorded
in round 3; the owner's R5–R9 instructions and existing design govern this pass.
The design-taste component workflow preserves the surrounding direction.

## Rendered result

[Captured primary lines](rendered-primary-lines.json) come from executing the
shipped JavaScript with the offline DOM adapter, in EN/zh at 390/768/1280 px.
They are rendered text, not screenshots or browser geometry measurements.

The two citation lines are:

- **10-K · fiscal 2025 (annual) · $416.2B revenue · Open SEC filing**
- **10-Q · nine months to 28 Jun 2025 · $313.7B revenue · Open SEC filing**

The four evidence items each have one compact disclosure, with these primary lines:

- **$143.1B · Amazon revenue · calendar Q3 2023 · 10-Q**
- **$60.9B · NVIDIA revenue · fiscal 2024 (annual) · 10-K**
- **125.9% · NVIDIA revenue growth · fiscal 2024 vs 2023 · 10-K**
- **$102.5B · Apple revenue · fiscal Q4 2025 · 10-K − 10-Q**

**Filed quarter = annual − nine months** replaces the raw unit/period/evidence-ID
line. Citation accessions, evidence IDs, source dates and raw integers are retained
under **Inspect data**. Evidence cards keep their full original objects, including
the growth comparison and derived-quarter components, inside that disclosure.
The filing forms on direct evidence remain links to the SEC archive.

Draft, citations and evidence use the same formatter: one decimal for B/M,
the stated scale when available, and `$`/B/M in both languages. This also formats
program-check amounts; their evidence IDs remain in their raw data disclosures.
The draft displays **$416.2B → $102.5B**. Original recorded text and correction
spans are preserved in the input and raw edit data.

All four **Not corrected** entries retain numbering, with separate assertion and
reason paragraphs at 16 px in muted text. Quotation marks are removed.
**Agent trace (23 steps)** starts collapsed for the corrected post. The one-claim
example, a result without corrections and a result with an invalid edit span all
start with the trace open. Trace events and their contents are unchanged.

`/zh/`, all affected CSS/JS asset stamps, the demo Hover source hash and the
offline preview hash were regenerated. [Preservation audit](preservation.log)
checks source logic, prompts, evaluations, saved filing evidence, site data,
saved envelopes and narration against the starting commit.

## Retained checks

- [Full offline verifier](verify-attempt1.log), `UV_OFFLINE=1 bash scripts/verify.sh`:
  **1,259 product tests, 206 demo tests and 97 standalone Node tests passed**.
  Static zh and asset stamps pass; both saved envelopes rebuild byte for byte;
  figure input/check/rebuild, all three site/explorer outputs, wild data, offline
  guards and Markdown links pass. This isolated run also covers the site cases
  from the earlier focused runs.
- [Initial runtime run](runtime-attempt1.log.gz): 41 passed, six stale assertions
  expected the former word “billion” in the one-claim draft; those expectations
  now use B. The new citation/evidence/scale checks passed.
- [Broader site run](targeted-attempt2.log.gz): 360 passed, one failed while asset
  regeneration briefly left an HTML file empty during a read. Its error was
  `document.documentElement` being undefined. The
  [isolated rerun of that exact case](spotlight-recheck.log) passed. Regeneration
  finished before the full verifier took its disposable snapshot.
- [Route audit](routes.log): 38 local paths, zero missing, two runtime routes.
- [Demo refresh](demo-refresh.log): 13 scenes / 177.2611 seconds; no media render.
- [Final local Markdown check](links.log) includes this receipt.
- [Source hashes](sources.sha256.json) identify the reviewed implementation,
  generated artifacts, tests and saved envelopes.
- [First packaging check](packaging-attempt1.log.gz) rejected trailing whitespace
  in retained pytest tracebacks. Failed-run logs are gzip-compressed with their
  exact original bytes preserved.

## Browser boundary

The real-browser inspector failed before page access both
[before](inspect-before.log) and [after](inspect-after.log) the change: Chrome
exited early. [Computer Use](browser-access.log) reported an unavailable browser
host; native Chrome access was not approved. Physical line wrapping, browser
overflow and visual scores remain unverified. No screenshots are claimed.

[Frontend lint before](taste-before.json) and [after](taste-after.json) retain
the existing thread-emoji finding in the verbatim input placeholder, plus the
same four warnings: trace zero-padding, two real form outlines and
em-dash usage. This pass adds no decorative imagery or new design direction.

All checks reuse frozen data. No paid calls, SEC fetches, OCR/ASR rechecks,
synthesis, publishing or deployment were performed.
