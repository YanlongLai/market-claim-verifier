# Local Git handoff

The requested branch is `eval/real-world`, based on `bd4aee4`. The shared worktree's Git index is outside the sandbox's writable roots; staging there returned `Operation not permitted`. Authorized commits were therefore made in an isolated local Git directory and are exported as `runs/real-world-2026-11-02.bundle`. No push occurred. Each new commit has the requested `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` footer.

The sampling protocol commit is `0773959`; the gold/runtime freeze commit is `ae1ff073bda3c14ebd25a5d8a68f784609440dd3`. [RUN_START.json](RUN_START.json) proves that committed input/source/runtime bytes matched before paid calls. Later reporting/input-quality notes do not overwrite the frozen inputs or gold. The original worktree's branch ref remains at its starting commit until the bundle is imported.

In a normal terminal with Git write access, from this worktree:

```sh
git bundle verify runs/real-world-2026-11-02.bundle
git fetch runs/real-world-2026-11-02.bundle refs/heads/eval/real-world
git log --oneline bd4aee4..FETCH_HEAD
```

The completed work files are already present. To adopt the fetched commits on the current branch while preserving working files:

```sh
git reset --mixed FETCH_HEAD
git status --short
```

The bundle and its checksum/commit summary are ignored transport artifacts under `runs/`; the evidence, scripts, tests, docs and validation receipts are committed inside the bundle. Raw third-party feed payloads have a reusable ignored copy at `runs/real-world-2026-11-02/.cache`; the original `/private/tmp/mcv-real-world-20261102/.cache` is also retained. The [cache-retention receipt](cache-retention.json) records hashes without publishing raw news. The existing root `.cache` and `.venv` symlinks were preserved.
