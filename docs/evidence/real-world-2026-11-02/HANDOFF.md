# Local Git handoff: News plus Threads phase 2

The requested branch is `eval/real-world`, based on `bd4aee4`. The worktree's Git index/ref directory is outside the sandbox's writable roots; phase 1 recorded `Operation not permitted` when staging there. The authorised local history therefore lives in `/private/tmp/mcv-real-world-20261102.git`, using this worktree's files. **No push occurred.** Every new commit has `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

The completed history is exported as **`runs/real-world-phase2-2026-11-02.bundle`**. Its checksum, final commit and import verification are recorded in ignored `runs/real-world-phase2-2026-11-02.handoff.json`. The previous phase-1 bundle `runs/real-world-2026-11-02.bundle` remains retained. The new bundle includes that phase-1 history and all phase-2 commits; it does not require separately applying both bundles.

Pre-call boundaries:

- News sampling: `0773959`; News gold/runtime freeze: `ae1ff073bda3c14ebd25a5d8a68f784609440dd3`; [phase-1 proof](RUN_START.json).
- Threads protocol: `9dee36b`; Threads gold/runtime freeze: `3ae0040`; [phase-2 proof](threads/RUN_START.json). Original input/gold/source/runtime bytes remain unchanged.
- Compound-post scoring notes: `b67b116`, with the separately timestamped completion clarification in [SCORING_NOTE.json](threads/SCORING_NOTE.json). The phase-1 supported-output exposure is retained beside whole-item false support.
- Source-tier-only metadata correction: `ab218e9`; [erratum](threads/GOLD_METADATA_ERRATA.md). Quarterly 10-Q values and derived growth were mislabelled L1 by the original builder. Corrected metadata preserves all original numeric truth labels and scoring denominators.
- Inherited News-only protocol metadata correction: `fe313d4`; [provenance erratum](threads/PROTOCOL_METADATA_ERRATA.md). The frozen Threads protocol retains its original bytes; actual Threads counts come from its frozen claims and gold.

The original worktree's branch ref remains at its starting commit until the bundle is imported. The completed files are already present. In a normal terminal with Git write access, from this worktree:

```sh
git bundle verify runs/real-world-phase2-2026-11-02.bundle
git fetch runs/real-world-phase2-2026-11-02.bundle refs/heads/eval/real-world
git log --oneline bd4aee4..FETCH_HEAD
git reset --mixed FETCH_HEAD
git status --short
```

The mixed reset adopts the fetched local history while preserving the working files. Inspect any concurrent user changes before doing so.

Raw supplied Threads bodies remain only at the Owner's original ignored collection path. Original cards, full OCR/extraction responses and media traces are retained under ignored `runs/threads-phase2/media/`, with public hashes and accounting. Public text traces contain the evaluated paraphrases. [Offline reuse](threads/REUSE.md), [audit](threads/audit.json), [full validation](threads/validation.json) and [combined results/spend](REPORT.md#threads) document what is reproducible from a fresh checkout and what requires the local private artifacts. The root `.cache` and `.venv` symlinks are preserved.
