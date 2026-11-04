# Real AV follow-up: period provenance and safe summaries

Three changes were implemented: explicit event-period context, FY27 header parsing requiring a four-digit year anchor, and final summaries generated from program conclusions. [Usage and limits](../../EVENT_CONTEXT.md) · [Offline replay](replay.html) · [Per-item JSON](replay.json) · [Traditional Chinese](REPORT.zh-TW.md).

## How verification worked

Reuse saved OCR/ASR text and extraction proposals from the previous six real-media cases, rerunning only program filters. Original inputs, quotations, model outputs and financial verdicts were not rewritten. No API was called and no new financial verdict was produced. Source metadata is reviewed but unauthenticated; it is not SEC evidence.

The source event is Microsoft FY2027 Q1; the official page title supplies the four-digit anchor. This is a post-hoc regression on known failures, not a blind accuracy evaluation. Passing the quotation filter only permits verification; it does not establish truth.

## Offline replay results

Across 13 channels with proposals, 28 rejections became 8: 20 header proposals gained an explicit year anchor and could proceed. Six audio proposals satisfied the strict current-quarter rule and recorded separate event-period provenance. Incomplete OCR channels had no proposals; failures were not dropped or counted as success.

These are occurrences across providers/repeated frames, not independent facts. New financial verdicts remain zero, so no new accuracy can be calculated. Added API spend was $0. 88 targeted tests for context, filtering, summaries, ingestion and queues passed.

## Retained limits

- Audio saying only “this quarter” is not automatically assigned an event period unless the proposal/source quotation meets the rule; other years, issuers, guidance and historical/future periods remain separate.
- FY27 needs an explicit century anchor; FY26 is not silently interpreted as 2026. Some comparisons mentioning two periods remain rejected.
- A present header does not prove row/column alignment.
- Adjusted EPS, constant currency, cash flow and operating metrics can still lack evidence.
- No model verification was rerun: `to_verify` must not be relabelled `supported`.

## Next steps

Use a separately versioned, bounded paid check for claims with added periods, retaining original and context-bound results independently. Add GAAP/adjusted evidence and cross-modal alignment, then another issuer and independently labelled held-out cases before measuring overall accuracy. Summaries must continue to follow valid program evidence.

## Tests and reuse

[Full offline verification](full-verification.log) passed 928 product, 149 demo Python and 55 Node tests, figure rebuilds, three byte-identical outputs and links. It used a disposable copy. The later guard against treating “Fiscal Year” as calendar is included in the final [88 targeted tests](targeted-tests.log); final links are in [links.log](links.log).

Run `uv run python scripts/replay_event_context.py` offline, without keys or financial model calls. [Source snapshot](source-snapshot.zip) and [hashes](source-snapshot.json) retain the implementation version; replay.json retains hashes of original paid input reports.
