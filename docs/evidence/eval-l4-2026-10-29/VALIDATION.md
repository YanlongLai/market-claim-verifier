# Verification — 2026-10-29

- Final full suite: `.venv/bin/python -m pytest -q` → **341 passed in 40.08 s**.
- Pre-run full suite on the measured implementation: **325 passed in 40.40 s**.
- Gold rebuild: `.venv/bin/python eval/l4/build_gold.py` → 32 claims, eight companies, 13 supported / 10 contradicted / nine insufficient, no runtime parser imports or model calls. Byte-reproducibility is covered by the suite. Gold was committed before every model call.
- Pre-run commit/hash check: code `3530800c16e2e9eb6789d6ef1bda239659d096fe`, gold `88ad3160c614fc5c62372897b998187b42d7ce44`, **99 frozen files**, zero model calls in preflight.
- Post-run offline replay: `.venv/bin/python eval/l4/replay_agent.py` → **32/32 unchanged**, zero new model calls. The original raw model responses and tool arguments are used; source/gold snapshot hashes are checked. `POST_RUN_REPLAY.json` records the tested source hashes.
- All 32 live cases and 131 requests are retained. No provider errors, budget stops, gold corrections or model reruns. Trace and ledger costs agree at **$0.71569815**, below $5.
- Prompt exports are synchronized and checked by the full suite. Canonical quote/cell/highlight offsets and raw-byte SHA-256 source chains are checked offline.
- Before every local commit: staged diff whitespace check plus a scan against actual locally configured key values and credential patterns. The scan prints file counts only; keys are never logged or persisted. `.venv` and `.cache` are not tracked. The final bundle is ignored output under `runs/`.
- Git metadata writes in the original worktree are blocked by the managed sandbox. The series is committed in an isolated local Git directory and exported as a portable, verified bundle, without a push. `HANDOFF.md` explains import for Claude.
