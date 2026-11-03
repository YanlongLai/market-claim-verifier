# Reuse the Threads evidence without new paid calls

The [protocol](protocol.json), [selection](selection.json), [paraphrases](claims.jsonl), [original gold](gold.jsonl), [freeze](FREEZE.json) and [pre-call commit proof](RUN_START.json) belong to the original phase-2 execution. Do not overwrite the frozen source, labels, inputs or failed attempts. [Source-tier metadata errata](GOLD_METADATA_ERRATA.md) correct L1/L2/L3 classification without changing numeric truth labels. [Scoring notes](SCORING_NOTE.json) distinguish whole-item false support from supported true components inside compound posts; the phase-1 exposure count remains available.

From the repository root, these commands rebuild derived reporting and audit saved artifacts only:

```sh
python3 scripts/real_world/correct_threads_tiers.py --out docs/evidence/real-world-2026-11-02/threads
python3 scripts/real_world/report_threads.py --out docs/evidence/real-world-2026-11-02/threads
python3 scripts/real_world/audit_threads.py --out docs/evidence/real-world-2026-11-02/threads
UV_OFFLINE=1 sh scripts/verify.sh
```

No model keys, live SEC retrieval, media decoding, OCR or ASR are required. The report builder preserves the News portion and replaces its own marked Threads section deterministically. Running the older phase-1 report builder alone restores a News-only report; follow it with the phase-2 builder to restore the extension. Full verification uses disposable environments/copies and network guards; it does **not** rerun image extraction.

## Artifact roles

- `baseten/`, `fireworks/`, `meta/`: every expected text item/path result, failed/partial attempts, raw redacted requests/responses, tools/evidence, and actual post CLI command/exit/stdout/stderr. Inputs are paraphrases, not raw post bodies or third-party headlines.
- `ledger.jsonl`: one append-only shared ledger for all phase-2 calls. Reservations are attributed to the billed provider; fresh Meta OCR for Baseten/Fireworks routes debits Meta. Failed/unknown-usage reservations remain in estimated spend. Costs are not provider invoices.
- `sources/`: hash-checked official SEC bytes for independent gold. Companyfacts JSON pointers and release text offsets/anchors identify the reference values. `runtime-cache-*.tar.gz` and `runtime-sources.json` separately preserve all SEC retrieval used by the verifier, including wrong-issuer lookups.
- `media/<provider>/<M01|M02>/`: allowlisted outcomes, coverage, actual CLI command/exit metadata, request/reservation accounting and full-local-artifact hashes. These do not contain original cards, verbatim OCR, copied third-party titles or full private media responses.
- Original supplied Threads files remain at the Owner's ignored collection path recorded in selection/media manifests. Full image responses and derived media remain under ignored `runs/threads-phase2/media/`. Public hashes bind the private artifacts; a fresh clone does not contain those originals. The audit's optional `--local runs/threads-phase2 --original /Users/yan/git/market-claim-verifier/.cache/real-world-2026-11-02/threads` validates them when locally available, without acquisition or paid calls.
- Validation receipts/logs retain full suites and disconnected verification. Synthetic sampler/privacy tests and offline gold rebuilds are regression checks, not new live results.

A text-only recheck of retained OCR or an incomplete extraction response is **OCR/ASR not retested**. A future paid repeat needs a new directory, explicit budget, frozen sources/settings/inputs and pre-call gold commit. Keep the current attempt, including every failure and budget-stop record, rather than selecting successful outputs. Do not infer engagement metrics or missing reporting years retrospectively.
