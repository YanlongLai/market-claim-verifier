# Reuse and later Threads input

The [report](REPORT.md) compares the unchanged, previously seen News 80 against the original run. [Diagnosis](FINDINGS.md) explains the repairs; [ADAPTATION.json](ADAPTATION.json) records why the additional routing repair was separately registered. Both attempts, failures and raw redacted traces remain under `sets/`. Do not report a best-of result or call this held out. No OCR/ASR was retested.

The first attempt's `FREEZE.json` matches its own recorded Git revision. Later repairs intentionally differ from that revision: use `RUN_START.json` to locate the matching code, rather than applying an old freeze to the latest code. The second attempt has its own manifest and revision. Source SHA-256 values, SEC bytes, source supplement and runtime caches permit offline inspection without paying to recollect sources.

## Threads after phase 2

No Threads cases were available in this checkout. Supply a frozen directory containing `claims.jsonl` and `gold.jsonl`, and optionally `metrics.json` from the original Threads run. Each claim needs a unique safe `id`, nonempty `claim` and ISO `published_at`. Optional `issuer_country` / `issuer_exchange` constrain issuer binding; feed tickers never authenticate identity. The runner accepts either News or Threads through the same schema.

Using the repository's Python environment:

```sh
python scripts/real_world/fixcheck.py prepare --input-set threads=docs/evidence/PATH
# Commit the new sets/threads manifest before any paid call.
python scripts/real_world/fixcheck.py run --set threads --cache runs/real-world-fixcheck/.cache-threads
```

Use the existing `docs/evidence/real-world-2026-11-03-fixcheck/ledger.jsonl`. Do not reset it, copy it to a fresh budget, or overwrite a started set. All three providers' remaining authorizations are `$5 - ledger.spent_for_provider(provider)`, including unreconciled reservations. The runner validates the three registered Meta model IDs and refuses generation overrides. Freeze a separate adaptive registration if any further execution is explicitly authorized; this task planned no third paid News repeat.

## Local Git delivery

The shared worktree Git index is outside the writable workspace, and its lock creation was denied. The user authorized a bundle fallback. Commits were therefore made with a separate local Git directory and the required coauthor footer; no push was attempted. The final bundle is `runs/real-world-fixes.bundle`, with prerequisite base `7ece36862abe15978740df85ecf365acbe2bc605`. Verify/import it from a writable clone that has that base. `--git-dir` on the runner supports the same local-directory fallback for manifest verification.
