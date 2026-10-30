# Stock document context and bounded extraction

This product change follows retained failures on three real Tesla pages in the paired benchmark. It does not change that benchmark's frozen code, scorer or results. The same real pages form a **post-hoc product smoke check**, not a new held-out accuracy study.

`review-stock` now passes the chosen ticker as an explicitly unauthenticated issuer hint. The hint is separate from quotable input, is never financial evidence, and must not override an explicitly named different issuer. Source quotations remain exact spans and program checks still use the frozen SEC evidence. Ticker matching in summaries is exact; share-class aliases are not silently merged.

Stock review requests bounded extraction: at most `--max-claims` proposals per window (default 8), prioritizing the latest explicitly labeled period and core financial metrics in dense tables. It explicitly uses low extraction reasoning. The prior benchmark's short-input extractor retained default reasoning even when verification used low; raw requests preserve that distinction. Normal `post`, `ingest` and `queue` calls without stock context retain their prior extraction defaults.

Reports record the hint, its unauthenticated status, selection scope and unknown full-content recall. Unselected material is unchecked. Charts without readable values must not be converted into invented numbers. Stock summaries explicitly count documents with no target-company program checks; a completed parsing pipeline is not an entirely verified document.

## Post-hoc validation protocol

Before paid calls, commit this change and `scripts/check_stock_context_posthoc.py`. Reuse the already frozen Meta OCR for Tesla pages 4, 5 and 23; verify all three without selecting only the successful page. Baseten only, selected because its primary test and diagnostic work has finished; this is not another vendor ranking. Use the same 2026-10-30 SEC snapshot, four requested claims per window, low extraction and verification reasoning, 4,000 output tokens, and a new **$1 Baseten cap**. The original benchmark has a $35 Baseten admission ceiling, so the two admissions total $36, below the owner's combined $40 authorization. Costs from both ledgers must be reported together for total task spending.

Retain every result, failure, request, source hash and fee. Do not rerun OCR/ASR, overwrite the original failed records, replace their primary benchmark scores or call a successful post-hoc example an independent accuracy estimate. The code and evidence hashes must be committed before these calls. Unknown interrupted outcomes do not auto-retry.

### Attempt 2: exact row quotation

Attempt 1 completed extraction but rejected all four financial-page proposals because the model concatenated a header and a nonadjacent row. Retain those records. The second attempt strengthens the bounded-table instruction: quote only the exact row; use visible headers as context without joining them into the quote. No quotation guard is relaxed. Run the same three pages again into `attempt-2/`, preserving the first outputs and using the **same $1 ledger across both attempts**. Source/protocol hashes are committed again before these calls. This is further post-hoc product development, never a replacement benchmark score.
