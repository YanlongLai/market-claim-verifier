# Tesla page 23 chart diagnosis and improvements — 2026-10-30

**The image is readable; the main gap is a structured representation of chart geometry with source coordinates and uncertainty.** No paid calls were added, bar values were not invented, and neither the original benchmark nor the two repair experiments was changed. [Traditional Chinese](REPORT.zh-TW.md).

[Original image](../real-media-2026-10-30/images/tesla-q3-2026-23.png) · [Saved OCR](../fair-multimodal-v1/prepared/REAL-TSLA-23/prepared.json) · [Saved extraction](../stock-context-posthoc-2026-10-30/attempt-2/REAL-TSLA-23/ingest.json) · [Three-document summary](summary/stock-review.html) · [Source hashes and diagnosis](diagnosis.json)

## What is missing from the image representation?

The original 1800 × 1013 image was inspected against saved OCR. This is a case diagnosis, not an independently annotated dataset or a new accuracy evaluation.

| Chart | Readable content | Relationships absent from OCR |
| --- | --- | --- |
| Vehicle deliveries | Quarters, 0.0–0.5 scale, millions of units | Each bar's delivery count; bars have no exact labels |
| Operating / free cash flow | Quarters, -3–7 scale, two legends, $B | Colors, series, bar heights/negative bars and values by quarter |
| Net income / adjusted EBITDA | Quarters, 0–8 scale, legends, $B | Series-to-bar association, exact values and GAAP/non-GAAP basis |

Quarter labels, legends, scales and three footnotes reached OCR; blur is not established as the cause. **Axis ticks 7, 6 and 5 are not quarterly cash-flow values.** Enlarging or cropping cannot create labels that are absent.

Saved text has no bar coordinates, colors or heights. Stock-context extraction explicitly refuses to guess values from bar/line positions, so zero claims follows its conservative contract. This does not verify the chart or prove that a model can never read it. `completed` means the pipeline ended; financial verification was not reached.

Footnotes cover capital-expenditure presentation changes, restated 2024 quarters and adjusted EBITDA excluding digital-asset gains/losses. Any geometric estimate still needs the presentation's version, quarter and accounting basis; non-GAAP EBITDA is not SEC net income.

## Improvements made

1. Every OCR channel discloses that text verification does not validate bar heights, lines, colors or series/quarter association, even when text assertions succeed.
2. Distinguish no text, text with zero claims and processing errors. Zero claims is not automatically diagnosed as a chart; an error is not successful abstention.
3. Individual and stock-summary reports suggest an actionable remedy: provide values, units, periods and footnotes, inspect the trace, then consider a separately authorized paid rerun.
4. Rebuild summaries from the same three Tesla results, retaining source hashes and links. Results remain three supported and five insufficient; no chart assertion became verified. **Automatic geometric validation is unfinished.**

[Verification](verification.log) and [replay](replay.log) retain the runs. Five new offline tests cover the real chart, text/geometry distinction, error precedence, empty text and HTML escaping. Replay with `uv run python scripts/replay_chart_diagnosis.py`; it reads no keys and requires no SEC network. Original paid inputs/outputs remain unchanged; added API cost was $0.

## Next steps, ordered by usefulness and verifiability

| Priority | Work | Acceptance boundary |
| --- | --- | --- |
| P1 | Link charts to tables in the same official presentation; require review | Company, quarter, unit, accounting basis, version and page retained; a correct table does not validate geometry |
| P1 | Add quarterly operating-cash-flow and deliveries evidence | Do not treat YTD as a quarter; retain compatible components, formulas and non-GAAP reconciliations |
| P2 | Optional native visual extraction of chart bounds, axes, series, bars, quarters and footnotes | Compare identical images/prompts across providers; retain inputs/outputs; label estimates approximate |
| P2 | Geometric values and interval comparison | Include scale/pixel error, negative/truncated/log axes; overlapping intervals do not establish exact equality |
| P3 | Larger blind and adversarial chart sets | Include restatements, dual axes, stacking, occlusion and misleading scales; separate extraction coverage, error and false support |

The current demo can identify unchecked documents and explain what is missing. It cannot claim universal financial-chart verification. More plain OCR would not supply the missing geometry; later experiments need separate versions and bounded budgets.

## Verification results and limits

906 product tests, 149 demo Python tests and 55 Node tests passed, as did figure rebuilds and three byte-identical data outputs. The original complete runner failed its final link check because the disposable copy was created before this diagnosis JSON and summary HTML existed. [verification.log](verification.log) preserves that failure; after artifacts were written, [links.log](links.log) passed on the current tree. The failure was not rewritten as success, and already-passing unchanged suites were not rerun.
