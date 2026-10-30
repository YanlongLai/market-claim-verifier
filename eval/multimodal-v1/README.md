# Paired multimodal benchmark v1 — preregistration

[Delivery plan and spending authority](../../docs/FAIR_BENCHMARK_AND_STOCK_REVIEW_PLAN.md). The corpus and harness must be committed before any paid call; `bench.py` refuses an uncommitted freeze.

- **Development:** AAPL and NVDA, TXT/PNG, default and low reasoning, four assertions per document. Select one profile per provider using correctness, false-supported count, then cost.
- **Test:** AMZN, INTC, TSLA, MSFT, GOOGL and META, four assertions each, nine formats: TXT, Markdown, native-text PDF, PNG, JPEG, WebP, WAV, MP3 and MP4. **24 underlying assertions / six issuer clusters**, not 216 independent facts.
- Same exact input bytes per format/provider. Shared Meta preprocessing is frozen before three-provider text checking. Native PNG/JPEG/WebP reading is a separate 54-cell controlled endpoint study (plus nine real-image diagnostic calls), not confused with the product's OCR route.
- Two supported assertions, one deliberately changed net-income value and one future-period insufficient-evidence assertion per document. [Gold and raw SEC row references](gold.json); [manifest, exact paths, hashes and generation](manifest.json).
- This is a controlled study on clean text cards and synthetic eSpeak audio. MP4 uses the same static image plus that audio. It is **not** an independent real-world recording benchmark, dynamic-video benchmark or a broad accuracy guarantee. No real executive voice is synthesized.
- Gold is calculated directly from SEC JSON rows without importing the verifier. The same evidence source still underlies both truth and retrieval; there has been no external human gold review. No provider receives the gold labels or source coordinates.
- All rejected/missing/unresolved assertions remain in strict end-to-end denominators. Conflicting duplicate verdicts are wrong; any false-supported duplicate is counted unsafe. Exact text-cache reuse is disclosed and excluded from fresh-call latency.

## Files and reuse

All 72 input files, including both splits, are under [inputs](inputs/). Their original bytes are the reproducibility source; the generator uses locally installed eSpeak, FFmpeg, Pillow and pypdf. Re-generation on a different encoder version can change hashes, so reuse committed bytes for paired comparisons. [SEC raw snapshots](../../docs/evidence/sec-refresh-2026-10-30/REPORT.md) can be restored offline.

The runner writes `docs/evidence/fair-multimodal-v1/`: freeze proof, shared ledger, preprocessing requests/responses, frozen channel texts, complete tool traces, per-case HTML/JSON, selected profiles, native-image request/response records and costs. Image bytes in API requests are referenced by committed path/hash instead of duplicating base64 strings. Unknown interrupted calls are not automatically retried.

```sh
# Paid: requires the new $40/platform authorization and frozen committed files.
.venv/bin/python eval/multimodal-v1/bench.py all
```

$35/platform admission ceilings leave a $5 buffer below each $40 authorization; reported fees remain estimates, not provider invoices. Each actual call is charged to its provider, including all shared preprocessing to Meta. Same-text cache reuse does not fabricate additional independent calls. Existing calls in the same ledger count against the ceilings. This command is not permission for another separately budgeted study.

[Scorer safety checks](harness-tests.log) cover missing/wrong-ticker/wrong-period claims, conflicting duplicates, ambiguous alignment, summary source boundaries and existing budget/queue safeguards. [Precommit refusal](precommit-refusal.log) records a successful safety check: no ledger or API call was created when corpus/code were not yet committed.

Three existing real Tesla slide PNGs are additional diagnostic inputs shared across providers, including native image reading. They have no complete independent gold annotation and never contribute to accuracy/recall denominators. Development media outside TXT/PNG are committed for reuse but are not executed during profile selection.

The archived generator records the authoring environment and uses macOS Arial plus `/tmp/claimcheck-mm-espeak/bin/espeak-ng`; it is not a portable installation script. For verification, reuse the committed bytes. For a new corpus, copy the generator to a new version, configure local font/speech paths and publish new hashes rather than replacing v1.
