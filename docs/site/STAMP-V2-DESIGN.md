# Stamp animation v2 — director's design (Claude)

Owner's ask: richer, higher-quality stock cards; an AI-made robot character who reviews each card; it pulls out the
most relevant SEC passage and highlights it, then stamps; and a **score** beyond TRUE / FALSE / CAN'T CHECK that says
how wrong a claim is.

## 1. The score: "Gap" (program-computed, not the model)

Every checked number already has `stated_value_used`, `actual_value`, `comparator` and `tolerance` from the program.
Add a deterministic gap measure in `src/claimcheck` and expose it in reports and the site:

| Claim type | Gap | Example |
|---|---|---|
| Level, `eq`/`approx` | relative gap = \|stated − actual\| / \|actual\| | Apple $416.2B vs $102.466B → 306% |
| Threshold, `gt`/`gte` | shortfall = (stated − actual) / \|actual\| if not met, else 0 | Coca-Cola ">$50B" vs $47.061B → 6.2% short |
| Threshold, `lt`/`lte` | overshoot, mirrored | — |
| Percent change | gap in percentage points; **direction flag** if signs differ | Tesla +3% vs −2.93% → 5.9 pp, direction wrong |

Within tolerance → gap 0.

Severity bands (shown as a label + meter):

| Severity | Level/threshold gap | Percent-change gap |
|---|---|---|
| **Exact** | within tolerance | within tolerance |
| **Minor** | < 2% | < 1 pp |
| **Moderate** | 2–10% | 1–5 pp |
| **Major** | 10–50% | 5–20 pp, or direction wrong |
| **Severe** | > 50% | > 20 pp |

Accuracy score 0–100 for the meter: 100 when exact; otherwise `max(0, 100 − 200·gap)` for relative gaps and
`max(0, 100 − 4·pp)` for percentage-point gaps, minus 30 if the direction is wrong (floor 0). It is a display signal,
not a new verdict: the verdict still comes from the existing checks. CAN'T CHECK has no score.

Expected on the current cards: Amazon Exact 100 · NVIDIA Exact 100 · Apple FY2024 Exact 100 · Microsoft Exact 100 ·
Apple Q4 "$416.2B" **Severe 0 (306% off)** · Tesla **Major (direction wrong, 5.9 pp)** · Coca-Cola **Moderate 88
(6.2% short)**.

## 2. Character: the "Auditor" robot (Codex image_gen)

A friendly, precise robot auditor — compact, rounded, matte off-white body with mint (#3ddc97) accents, one wide visor
eye, small antenna, clerk's sleeve garters or a tiny eyeshade as a nod to accountants. No text, no logos.
Four poses from **one sheet** for consistency (then cut into separate transparent images):
1. **idle** — standing, holding a rubber stamp at its side
2. **inspect** — leaning forward, visor glowing, magnifier raised
3. **present** — holding up a document page toward the viewer (the SEC passage pops out from here)
4. **stamp** — arm raised mid-swing with the stamp

Generated on flat magenta, keyed to transparency, saved as WebP ≤ 120 KB each, prompts saved in
`docs/prompts/site/auditor-robot.md`.

## 3. Richer stock cards

Card = a mini social-post card, not a grey box:
- header: ticker chip ($AAPL) + company name (Apple Inc.) + source kind (Thread / Social post) + post date
- the claim quote, with the key number set larger (e.g. **$416.2B**) and the period chip (Fiscal Q4 2025)
- footer after review: verdict stamp, severity label and score meter, "Filed: $102.5B"
Paper texture, soft shadow, consistent grid; real data only.

## 4. Choreography per card (~6.5 s, loop of 9 cards)

| t (s) | Card | Robot | Other |
|---|---|---|---|
| 0.0–0.7 | slides in, **stops** at the inspection desk | idle | |
| 0.7–1.4 | holds | **inspect** (leans in) | scan beam sweeps the card; the key number glows |
| 1.4–3.0 | holds | **present** | the SEC passage card rises from the robot's hand: form + filed date + table row or sentence; the matching value sweeps amber; "Filed: $102.5B" |
| 3.0–3.6 | holds | present | score meter fills to its value; severity label pops (Exact / Minor / … / Severe) |
| 3.6–4.2 | small shake | **stamp** | stamp slams TRUE / FALSE (CAN'T CHECK skips passage + meter: robot shrugs into idle, grey stamp) |
| 4.2–5.0 | slides out with stamp, score and filed value | back to idle | passage card folds away |

Passage content comes from the real filing excerpts (`filing_excerpts` built by `build_site.py` from SEC filings),
showing one table row (label + period header + value, value highlighted) or one sentence.

## 5. Layout

Desktop: inspection desk centre; robot on the right of the desk; passage card pops up to the left of the robot,
above/beside the stock card; queue of upcoming cards dims on the left. Phone: robot small at top-right of the
stage, card centred, passage overlays the lower half of the card. Reduced motion: static list with verdict,
severity, score and filed value. Seek hook kept (`?stamp-t=`).

## Gates

1. Score definition + numbers for every card (this doc §1) → Owner check.
2. Robot sheet (4 poses) → Owner picks / asks for changes.
3. Three key frames (inspect, present+highlight, stamp) → Owner check.
4. Full animation → Claude review (desktop/phone, dark/light, EN/中文, reduced motion) + second AI → Owner OK → publish.

## 6. Post authors, dates and followers (Owner request, round 2)

Cards should feel like real posts / news / reposts, without pretending to be real accounts.

| Card source | Persona (fictional) | Avatar | Kind | Followers | Post date rule |
|---|---|---|---|---|---|
| demo-thread (AMZN, NVDA ×2, AAPL Q4) | @tickerowl · "Ticker Owl" | retail-owl | Thread | 18.4K | ≥ last first-filing date among its facts (Apple FY2025 10-K, 2025-10-31) |
| bigtech-thread (TSLA, AAPL FY2024, AAPL forecast) | @chartcoon · "Chart Coon" — fictional finance influencer | chart-raccoon | Thread | 52.1K | ≥ Tesla FY2025 10-K first filed (2026-01-29) |
| tw-social-post (MSFT, KO) | 美股懶人包 · "US Stocks in 1 Minute" | lazy-cat | Social post | 4.3 萬 | ≥ Coca-Cola FY2024 10-K first filed (2025-02-20) |
| one repost of the KO claim | "Market Recap" (repost) | repost-bird | Repost | 210K | same as the original |
| one news-style card for AMZN (and its 中文 label) | 香蕉新聞快報 · "Banana News Flash" — fictional newsroom | banana-news | Article | 96K | ≥ Amazon Q3 2023 10-Q (2023-10-27) |

Rules (precision):
- Names, handles and outlets are fictional and checked not to match well-known real accounts or outlets; no real logos.
- Every card shows a small "Example post" tag; the claim text, numbers and verdicts are the real program checks.
- Post date must be on/after the date the referenced figures were first filed with the SEC (earliest filing that
  reports that period, from SEC companyfacts `filed`), and before today; build_site.py validates this and fails the
  build otherwise. Numbers on the card are exactly the claim's stated values; the filed value comes from evidence.
- Follower counts are round, plausible numbers for the persona type and are labelled as part of the example.

Owner (round 2b): the individual can be a finance influencer; the media outlet is the fictional 香蕉新聞快報 /
Banana News Flash; other fictional personas are welcome (owl thread writer, lazy-cat blogger, repost bird).

## 7. Round 3 (Owner: fill the phone gap with detail)

- The SEC sheet now also shows the statement section title, the accession number, and a two-row ledger:
  derived quarters show "nine months (10-Q, filed date) − value / = Q4 (derived)", and direct facts show
  "Post says / Filed" (growth claims are signed and labelled as growth rates; thresholds show ">").
- Phone: the sheet starts under the period chip (top 234 px, min 230 px tall) and ends just above the review footer.
- The empty meter track arrives with the sheet; the severity label, score and gap fade in when scoring starts.

## 8. v3 — director's redesign (Owner round 4)

Owner: the robot needs more, finer actions; the animation is too tall to see in one screen (Owner views at
1024×768); use the width; separate the SEC block from the post under review; think about phone viewing, page
comfort, content and order.

### 8.1 Stage layout — two panels, robot between them

```
 ① Post under review              robot             ② SEC filing
 ┌──────────────────────┐      (faces the panel   ┌──────────────────────┐
 │ avatar · name · tag  │       it works on;      │ SEC 10-K · filed     │
 │ $AAPL Apple · Thread │       mirrored)         │ company · section    │
 │ claim, number large  │                         │ period               │
 │ period chip          │   ── connector line ──▶ │ row  [416,161]       │
 │ meter … [STAMP]      │                         │ ledger rows, accn    │
 └──────────────────────┘                         └──────────────────────┘
 [1 Find the claim]──[2 Open the filing]──[3 Code decides]──[4 Stamp]     Next: $NVDA $TSLA   Pause
```

| Viewport | Grid | Stage height (incl. labels + strip) | Robot |
|---|---|---|---|
| ≥ 1024 | panel 1fr · robot 190 px · panel 1fr, max 1180 px | ≤ 400 px | 190 × 260 |
| 640–1023 | panel 1fr · robot 120 px · panel 1fr | ≤ 420 px | 120 × 165 |
| < 640 | stacked: strip, post panel, robot band (72 px, right), filing panel | ≤ 600 px | 72 × 100 |

- Panels are fixed boxes; content swaps per card. The filing panel is never a floating sheet any more.
- The hero headline shrinks (one or two lines, ≤ 64 px) so header + headline + whole stage fit in 768 px at
  1024 wide and 900 px at 1440; on phones the whole stage fits within one 844 px screen when scrolled to it.
- Queue: tiny ticker chips "Next: $NVDA $TSLA" in the strip; the old left stack is removed.
- The progress strip uses the same words as "How it works" and lights the active step.

### 8.2 Robot beats (checkable card, ~8 s)

| t (ms) | Beat | Robot pose (facing) | Post panel | Filing panel | Strip |
|---|---|---|---|---|---|
| 0–700 | Enter | idle (front) | post slides in | empty "waiting for filing" state | — |
| 700–1500 | Read | inspect (→ post) | scan beam; number glows; chip "Claim: $416.2B · Fiscal Q4 2025" | — | 1 |
| 1500–2300 | Reach | reach (→ filing) | — | folder tab opens; header (form, filed, company, section, period) slides in | 2 |
| 2300–3700 | Find | point (→ filing) | — | row appears, amber sweep on the value; ledger rows reveal 200 ms apart; accession | 2 |
| 3700–4500 | Compare | think (front) | connector line from post number to filed value; meter fills; severity label | compare row lit | 3 |
| 4500–4800 | Wind-up | stamp (raised, → post) | — | — | 4 |
| 4800–5300 | Strike | stamp-down (→ post), 6 px hop | stamp slams, card shakes | — | 4 |
| 5300–6400 | React | approve (TRUE) / concern (FALSE) | hold for reading | hold | 4 |
| 6400–7200 | Exit | idle | slides out | content fades | — |

CAN'T CHECK (~5.4 s): Read → **shrug** at 1500 with chip "Opinion / forecast — no filed number"; filing panel shows
"No SEC number to check" (muted); grey stamp at 3000; exit at 4600.

Between poses: 120 ms cross-fade, plus continuous micro-motion from the scene clock (2 px bob, ±3° lean toward the
active panel, 6 px hop on strike). Poses are mirrored by CSS to face the active panel.

New poses (Codex image_gen, same B character, edited from the B sheet as reference): **reach, point, think,
stamp-down, approve, concern, shrug** (+ existing idle, inspect, present, stamp).

### 8.3 Page order and comfort

Hero (smaller headline, lede, stage) → **How it works** (moved up; its three headings match strip steps 1–3) →
A real post, checked → Does it work? → Why you can trust it → Run the check yourself.

### 8.4 Spotlight (Owner round 5: "像探照燈…要有電影的效果")

The connector is a beam of light, not a line.
- **Find:** a searchlight cone leaves the robot's visor, sweeps down the filing panel row by row, and locks on the
  matching row. While it searches, the filing panel dims (vignette); only the lit pool is bright. Locking on:
  the value blooms, then the amber highlight sweeps.
- **Compare:** the whole stage dims to ~55 %. Two beams from the visor — one onto the post's big number, one onto
  the filed value (and the compare row). Both pools are crisp; dust motes drift in the beams; soft volumetric
  falloff toward the targets. Thin cinematic letterbox bars (12 px) ease in at the top and bottom of the stage.
- **Strike:** beams cut, a short white flash on the post (80 ms), the dim lifts as the stamp lands; letterbox eases out on React.
- Light theme: warm amber light over a darkened stage (dim overlay), so the beam reads on paper. Dark theme: mint-white light.
- Phone: the robot band sends a beam up to the post number and down to the filed value.
- The highlighted text never loses contrast; everything is deterministic from the scene clock (seekable).
  Reduced motion: no beams or dimming.

### 8.5 Owner selection — v3 Hover final, separate thruster

Candidate **3 Hover** is now the runtime auditor (`img/auditor/H/`). This
supersedes the B artwork and walking/hop motion described in §8.2. B and the
five selection candidates remain on disk; the page requests only H.

The eleven poses are **idle, inspect, reach, present, point, think, stamp,
stamp-down, approve, concern, shrug**. Every body was generated with the
candidate-3 images as edit/reference inputs, on flat magenta, then keyed and
despilled to alpha. Neutral eyes are two round dots, approve uses `^ ^`, and
wind-up/strike/concern use `> <`. The magnifier, blank folder tab, blank page,
pointing finger, thinking hand, thumbs-up, palm-out concern and open shrug are
legible as distinct silhouettes in the contact sheet's 88 px phone preview.

All body masters are 1254×1254. A single **0.5× scale** applies to every pose;
translation puts every nozzle outlet at **(352, 520)** on a **704×744** canvas.
Transparent space below the nozzle accommodates the burst plus the phone dip.
There is no individual pose fitting. `H/manifest.json` records the decoded
alpha bbox, visor anchor and nozzle anchor in image pixels, source coordinates,
scale, translation, size and hash for each pose. The stamp-down block lands in
front and to the side, within four source-output pixels of nozzle height; its
arm and block leave the nozzle and vertical exhaust corridor uncovered. No
body sprite contains a flame, floor shadow, impact or motion trail.

The thruster is a separate **160×160 alpha layer**, attached at **(80, 20)**.
Six generated frames cycle every **80 ms** (480 ms per loop), selected from the
same deterministic scene clock. A separately generated larger burst frame
replaces the loop and scales **1.6× for exactly 250 ms** after each strike.
Straight alpha preserves the mint core on both themes. Two effect instances
follow the outgoing and incoming nozzle anchors through the **120 ms** pose
cross-fade; each is mirrored with its own body pose. Both render below the
character/stamp. The empty corridor guarantees the jet remains visible.

Hover motion is **±4 px** bob over approximately **1.6 s**, with up to **3°**
lean toward the working panel. There are 52 bob cycles per 82.8 s scene loop
(1592.31 ms each), so the loop boundary is continuous. Strike moves **down
8 px in 60 ms**, recovers over **160 ms**, and fires the separate thruster and
existing impact-burst on the post. A stationary soft floor ellipse shrinks
when the body rises and grows when it approaches the floor. There is no feet
hop. Spotlight origins use the new per-pose visor anchors with the same
contain-fit, mirroring, pose blend, lean, bob and dip as the body.

All eighteen WebPs retain the existing lazy-load and reduced-motion behavior.
Every body file is below **70,000 bytes**; effects are below **5,000 bytes**
each. `H/contact.png` shows all eleven poses on ivory/navy with the separate
flame composited, an 88 px phone preview, and six stamp-down/recoil samples
on each theme (120, 160, 200, 240, 250 and 420 ms after strike, starting after
the body cross-fade). The exact sixteen image-generation calls, including rejected
stamp-height attempts and the final geometry-guided edit, are saved under
**“v3 Hover — final”** in `docs/prompts/site/auditor-robot.md` and in
`H/source/prompts.json`. Rebuild assets/contact/manifest with
`.venv/bin/python docs/site/img/auditor/H/process-hover.py`.

Verification covers decoded alpha, empty exhaust corridors, shared scale and
anchors, runtime byte budgets, both themes, all existing breakpoints, mirrored
visor and jet origins, 8 px dip, 250 ms burst boundary, stationary/shrinking
shadow, deterministic seeks, texture failure, lazy loading and reduced motion.
The contact was inspected visually. The browser permission gate declined the
local preview; these checks do not claim a browser font/layout review.

Final budget: eleven bodies **364,786 bytes**, seven thruster frames **22,532 bytes**, total **387,318 bytes**. Largest body: **35,862 bytes**. Full suite: **498 passed** (`.venv/bin/python -m pytest -q`); site subset: **199 passed**. JavaScript syntax and whitespace checks passed. The calibration table and per-file sizes are in `STAMP-V2-KEYFRAMES.md`; complete per-pose bboxes/anchors/hashes remain in `H/manifest.json`. Archived B hashes are unchanged. No commit or push.
