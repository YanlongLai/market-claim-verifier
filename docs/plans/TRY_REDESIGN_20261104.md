# Try section redesign — FINAL design (decided by Claude Code, 2026-11-04)

**Source of truth: `docs/plans/try-redesign-mockup.html`.** Open it in a browser and match it: layout, spacing,
radii, component shapes, states and copy. Where this text and the mockup disagree, the mockup wins. Map its
colours onto the site's existing tokens (`--surface`, `--track`, `--accent`, `--true-surface`, …) in both light
and dark schemes; add tokens only for values the site lacks (`--raised`, `--warn`, `--warn-surface`).

Final decisions (Claude Code):
1. One filled button in the whole section: **Run check** (48 px, accent). While a run is in flight it becomes
   disabled with a spinner and the text "Checking…" (localized on the Chinese page).
2. Story and input pickers are segmented controls; selection = raised segment with accent label. The expected
   outcome shows as one hint line for the selected story only. Phone labels: "A Wrong / B Correct / C Mixed"
   (short Chinese equivalents on the Chinese page).
3. Provider: desktop three outline cards (name, "$27.88 left today", 4 px meter, model id one line mono with
   ellipsis, lifetime budget in `title`; Fireworks shows "Slow today" in warn colour when the existing note is on).
   Phone: three single-line rows (radio · name · amount). Selected = accent outline. Compare = switch row.
4. Run row: password + Run check on one row (stacked on phone); one footer line "Password is our team name. Saved
   results need none." + "See saved result" text button + "Details" disclosure (privacy, retention, rate limit).
   The "Recorded … · Baseten" caption moves into the saved-result button's `title` and the saved result header.
5. Right column = **Now** card above **Recent checks** card; sticky on desktop.
6. Now card states exactly as the mockup: Idle (dashed hint + faded six-stage stepper) → Running (pulsing dot,
   "Running", m:ss clock, "Baseten · <current stage sentence>", stepper with done/active/pending, server log panel
   with newest line highlighted and auto-scroll) → Done (verdict pill, "finished in 9.7 s", all steps done, three
   tiles Time / Cost / Claims, log collapsed to "› Server log (N lines)", "View result ↓" link). Failure states use the
   error/timeout pill and keep the log open.
7. Phone: while a run is in flight and the Now card is off-screen, a sticky bottom bar shows dot · Running · current
   stage · clock; tapping it scrolls to the Now card. It disappears when the run ends.
8. Recent checks: list rows (verdict pill column 112 px · "Story A · Text" / "Baseten · 15.7 s · $0.02" · relative
   time · chevron). Your own in-flight run is the first row, tinted, with a spinner pill "Running" and "you" until the
   history refresh replaces it. Show 6 rows, then "Show more" (+10 each). Refresh is an icon button with accessible
   name "Refresh". Device and exact UTC time live in the row `title` and the existing modal.
9. Do not reuse any earlier partial implementation; start from the current `main` files in this worktree.

---


Owner request (translated): rework the layout and UI of the Try controls, Recent checks and the live terminal.
Make it clean and clear like Google and Apple, easy to operate, and make current and running work easy to see.

Goal: the Try section (`#live-check`) on EN `docs/site/index.html` and Traditional Chinese `docs/zh/index.html` reads like a
Google / Apple settings-style tool: one clear primary action, calm surfaces, obvious "what is running now", and a
history list you can scan in one glance. Keep the dark theme and existing colour tokens; this is layout,
hierarchy and component styling, not a rebrand. Keep every behaviour that exists today.

## Problems on the live page (desktop 1352 px and phone 375 px)
1. Story picker: three dense boxes; the selected one is a solid green slab; "Expected outcome" text wraps 3–4 lines.
2. Input picker: tabs fine, but helper lines below the textarea (Reset, count, description, Open input file) are
   scattered over three rows.
3. Provider picker: long model IDs and two budget numbers per card make three columns of small text.
4. Run row: password, Run, See saved result, then four separate small-print lines (recording, password note,
   privacy + rate limit, Details). The primary action does not stand out.
5. Recent checks: a 4-column table in a narrow panel; every cell wraps (timestamps over 2 lines, device over
   2 lines); the "today" time is a green underlined link; rows are ~105 px tall; the panel scrolls internally.
6. Live terminal (`#live-progress`) appears under the form, far from the history; it is a `<details>` with a
   stage chip row and raw lines, and nothing at a glance says "running · step · elapsed".

## Original brief details (still apply unless the mockup or decisions above differ)

### Layout
- Desktop (≥ 960 px): two columns, left "Run a check" card (~58 %), right column (~42 %) with two stacked cards:
  **Now** (current run) on top, **Recent checks** below. Right column is `position: sticky; top: 24px` when it
  fits the viewport; no internal scroll on the page level except the history list (max ~8 rows visible, then
  a "Show more" button that reveals the next 10; keep all 50 loaded).
- Phone / < 960 px: single column in this order: Run card, Now card, Recent checks. 16 px gutters, no
  horizontal scroll at 375 px.
- Cards: `border-radius: 16px`, 1 px hairline border (existing `--track`), surface `--surface`, padding 24 px
  (16 px on phone). Controls: radius 10 px. Spacing scale 4/8/12/16/24/32. Section headings in the card are
  15–16 px semibold sentence case, no "1 ·" numbering clutter: use a small muted step number before each
  label ("1  Story", "2  Input", "3  Model provider").

### Run card (left)
- **Story**: a segmented control (one rounded track, three equal segments: "A Wrong period", "B All correct",
  "C Mixed claims"). Selected segment = raised surface + accent text/outline, not a solid green fill. Under
  the control, one line of muted text for the selected story only: "Expected: Contradicted · $416.2B →
  $102.5B" (reuse the existing expected strings). Keep the `data-story-slot` buttons and `aria-pressed`.
- **Input**: keep the tablist (same ids/roles/keyboard); style as a pill segmented control. Textarea: rounded,
  calm border, focus ring in accent. One tools row under it: Reset example (text button) · description
  (muted, truncates with ellipsis on one line, full text on title) · Open input file (text link) · count
  right-aligned in tabular numerals.
- **Model provider**: three selectable rows/cards (radio inside): line 1 provider name; line 2 muted
  "$27.93 left today" with a 4 px rounded meter. Model id and lifetime budget move into a single muted line
  that is visually smaller (12 px, one line, ellipsis, full value in `title`), so each card is ≤ 3 short
  lines. Selected card = accent outline. Compare on all = an iOS-style switch row with its note as helper
  text. Keep radio/checkbox inputs, names and values.
- **Run row**: password field (full width on phone) + a prominent primary **Run check** button (accent fill,
  48 px tall, the only filled button in the section). "See saved result" becomes a secondary text button next
  to it; the "Recorded … · Baseten" line sits under that button as its caption. The four small-print lines
  collapse into one muted line: "Password: our team name · saved results need none" plus a "Details" disclosure
  that holds privacy, retention and the rate-limit text. Keep all ids (`live-password-note`, `live-privacy`,
  `example-recording`, `live-status`, …) and aria-describedby links.
- Result area (`#live-result`, `#compare-result`, `#result-edit`) stays in the left column below the run row.

### Now card (right, top) — the live terminal
- Move `#live-progress` into this card. Idle state (no run since load): one muted line "No check running. Your
  run will appear here with each server step." and a short legend of the six stages. Keep `#live-progress`
  as the container the script fills; add an idle placeholder element that the script hides when a run starts.
- Running state header: status dot (pulsing accent) + "Running · Baseten" + elapsed clock right-aligned
  (tabular numerals). Below: a horizontal stepper of the six stages (Sent → Model → SEC tools → Model →
  Program checks → Verdict): done = check mark + accent text, active = filled accent dot + bold, pending =
  muted. Keep `.terminal-stages` children order and `data-active` semantics (tests read them); you may add
  `data-done`.
- Below the stepper: the server log in monospace (15 px stays per test), dark inset panel, radius 10 px, max
  height ~14 rem, auto-scroll to the newest line, line timestamps muted. Keep `.terminal-lines`, text-node-only
  rendering and the existing polling cadence.
- Finished state: header becomes "Done in 9.7 s · Supported · $0.01" (or the failure text), the log stays
  collapsible (collapsed by default after finish, as today), and a "View result" link scrolls to `#live-result`.
- Compare runs: one compact panel per provider stacked in this card.
- After a run finishes, refresh Recent checks automatically (if the script does not already) so the new run
  appears at the top.

### Recent checks card (right, below)
- Replace the 4-column table look with a list layout (you may keep `<table>` semantics but render each row as a
  two-line item; or switch to a `<ul>` with buttons — then update tests accordingly and keep keyboard/focus
  and the history modal behaviour). Each row, 64–72 px tall:
  - leading verdict pill (Supported / Contradicted / Provider error / Timeout, existing colours, small).
  - line 1 (ink): "Story A · Text" or "Custom text · Text".
  - line 2 (muted, one line): "Baseten · 15.7 s · $0.02".
  - trailing (muted, right): relative time ("5 min ago", "2 h ago", then "Nov 3"), exact UTC time + device in
    `title` and inside the modal. Chevron at the far right.
  - Whole row is the click/Enter target that opens the existing history modal.
- Header: "Recent checks" + icon-style Refresh button (keep `#history-refresh`, accessible name "Refresh") +
  muted subtitle "Last 50 runs · public · 14 days".
- An in-flight run of this browser shows as the first row with a spinner "Running…" until history refreshes.

### Copy and i18n
- Every new string goes through the existing EN/ZH copy tables; the Chinese page gets natural Traditional Chinese
  for every new string (idle, running, done, relative times). No mixed-language rows.
- Numbers: one style everywhere (tabular numerals, `$0.02`, `15.7 s`, with the localized seconds unit on the Chinese page).

## Constraints
- Do not change server code, API contracts, polling cadence, abuse/lockout logic or the history modal content.
- Keep all element ids, `data-*` hooks, roles and ARIA relationships that `docs/site/script.js` and the tests
  use, unless you update both the code and the tests together (state each such change in the report).
  Never weaken a behavioural assertion; layout assertions may change to match the new design.
- Accessibility: visible focus rings, 44 px minimum touch targets, `prefers-reduced-motion` disables the pulse
  and any transitions, contrast ≥ 4.5:1 for text.
- Keep the page's other sections untouched. No new dependencies, fonts or external requests.
- After editing: run `python3 scripts/stamp_site_assets.py`; then update the site script hash recorded in
  `demo/motion/v3/hover-source.js` and `demo/motion/v3/preview-data.js` to the new
  `shasum -a 256 docs/site/script.js` (replace the old 64-hex value; nothing else in those files).
- Tests: run the site tests (`.venv/bin/python -m pytest -q tests/test_site_*.py`), then the full
  `bash scripts/verify.sh`. Both must pass. Add tests for: idle Now card, running header text + elapsed,
  history row two-line content and relative time, Show more, and the 375 px no-horizontal-overflow check.
- Do not commit, push, fetch or merge. Do not touch secrets or run network calls against production.

## Report (write to `docs/plans/TRY_REDESIGN_20261104-report.md`)
Files changed, every id/hook/test you changed and why, test + verify results (counts), and anything not done.
