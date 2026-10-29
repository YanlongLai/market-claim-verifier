# Local handoff for Claude — 2026-10-29

Code and evidence are in `/Users/yan/git/market-claim-verifier-l4`. No push or merge was performed.

The shared Git directory at `/Users/yan/git/market-claim-verifier/.git` is read-only to this session. Git could not create the linked worktree's `index.lock`. Actual local commits use `/private/tmp/market-claim-verifier-l4-local.git`, with branch `feature/l4-earnings-release` based on `f06ac10743ac72b35a84a8ff2527c2e84574da1f`. The worktree's original branch ref/index remain unchanged, so its ordinary `git status` still shows the implemented changes as uncommitted.

The final portable bundle is `runs/l4-earnings-release.bundle` in this worktree (ignored output, not a tracked binary). From a session with shared Git write access, import it for review without changing working files:

```sh
git fetch /Users/yan/git/market-claim-verifier-l4/runs/l4-earnings-release.bundle feature/l4-earnings-release
git log --oneline f06ac10743ac72b35a84a8ff2527c2e84574da1f..FETCH_HEAD
git diff --stat f06ac10743ac72b35a84a8ff2527c2e84574da1f FETCH_HEAD
```

`FETCH_HEAD` then names the reviewable series. Reconcile the current worktree's already-present files before any checkout/cherry-pick/merge. All commits end with the requested Claude co-author footer. `.venv` and `.cache` are excluded symlinks. No API keys are in committed files or artifacts.

Reproduce the gold without a model:

```sh
.venv/bin/python eval/l4/build_gold.py
.venv/bin/python -m pytest -q
.venv/bin/python eval/l4/replay_agent.py
```

For the ordinary CLI in this shared-virtualenv worktree, use `PYTHONPATH=src .venv/bin/python -m claimcheck ...`. Its existing editable install points at another checkout; the eval scripts and pytest already select this worktree's source without changing the shared environment.

The live run used `.venv/bin/python eval/l4/run_agent.py --git-dir /private/tmp/market-claim-verifier-l4-local.git`; gold, source snapshots and runtime bytes were verified against real local commits before a key was read. Do not rerun into the existing results directory. The registered result is 31/32, zero false-supported out of 19, $0.71569815. Read [ANALYSIS.md](ANALYSIS.md) for the retained routing miss, post-run guards and evaluation limits, [DESIGN.md](DESIGN.md) for files and rules, and `COMMITS.txt` for the five implementation commits. The bundle's HEAD adds this final evidence/handoff commit.

`checks.py` only adds release types and a dispatch hook; preserve the separate gap-score branch's changes during merge review.
