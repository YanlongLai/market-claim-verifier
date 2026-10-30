# Reviewed event periods and safe final explanations

`review-stock` accepts optional `--event-context PATH.json`. The JSON must contain exactly: `ticker`, `period` (`2027Q1`), `basis` (`fiscal` or `calendar`), `source_url` (HTTPS reference), `source_quote` (explicit full-year quarter), and `reviewed: true`. [Example](evidence/real-av-context-posthoc/event-context.json). The caller must check that the source identifies this event and that the supplied documents belong to it. The flag records that review; it is not authentication and does not fetch or validate the URL.

```sh
uv run python -m claimcheck review-stock MSFT \
  eval/real-av-v1/inputs/msft-fy27q1-cfo-60s.wav \
  eval/real-av-v1/inputs/msft-fy27q1-cfo-60s.mp4 \
  --event-context docs/evidence/real-av-context-posthoc/event-context.json \
  --evidence-cache .cache/sec-refresh-2026-10-30 --as-of 2026-10-30 \
  --provider baseten --max-claims 4 --max-output-tokens 4000 --reasoning-effort low \
  --budget 1 --per-job-budget 0.5 --max-jobs 2 --out runs/msft-with-context
```

This command makes paid calls. The CLI is implemented; this exact live invocation has not been used to replace the original real-AV study. [Offline replay](evidence/real-av-context-posthoc/REPORT.md) costs nothing. Choose a new output directory; changing context changes queue identity and cannot silently resume a different experiment.

## Binding rules

- Only same-ticker reported facts with an actual `this quarter` phrase in both quotation and rewrite can receive the event period. Guidance, other issuers, existing explicit years/periods and historical/future relative phrases are not overridden. No current-clock or latest-filing inference occurs.
- The quotation is unchanged. `event_period_context` records the separate metadata, source quote, URL and conditional status. Outcomes depend on the supplied context being correct.
- A short `FY27 Q1` header may resolve only when the source document or reviewed event supplies an explicit matching fiscal full-year anchor. Every exact header span is retained. `27` in `$27 billion` does not gain an exemption. No century or prior-year value is inferred; unsupported comparison periods remain rejected.
- Header binding proves where the period text came from, **not column/value alignment**. Full table structure and cross-modal reconciliation remain future work.
- Source context is preserved in ingestion JSON, post JSON, stock summaries and queue identity. HTML shows the separate provenance; it is never added to the heard/read quote.

## Final explanations

After program checks, `summary` is generated from the final program verdict and check reasons. Original model prose is retained in `model_summary` and the trace; it cannot declare a correction that the program did not validate. Numeric corrections still require valid evidence IDs and successful program comparisons. Re-rendering old ingest/post data uses program wording when checks exist, without editing archived JSON.

The previously published HTML remains a historical record. New reports and the separate replay demonstrate the improved behavior; no old score, trace or paid result is overwritten.
