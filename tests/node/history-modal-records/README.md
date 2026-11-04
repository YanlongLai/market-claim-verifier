# History modal validation records

Feature base: `5f385d3c`, branch `site/history-modal`.

`targeted-attempt4.log.gz` records 138 passing site runtime, result-rendering, presentation and language-purity checks. `modal-final.log.gz` separately records both modal lifecycle language cases passing. `links-final.log.gz` records the offline Markdown link check. `source-hashes.json` freezes the feature sources.

Earlier attempts are retained: attempt 1 exposed focus-selector handling in the offline DOM adapter; attempt 2 was interrupted while testing an intermediate focus implementation; attempt 3 exposed assertions expecting browser `null` rather than the adapter's `undefined` for missing nodes. Attempt 4 contains the final passing checks. These are mocked endpoint tests with no model or SEC requests.

`verify-attempt1.log.gz` records the full verifier stopping at stale shared asset stamps in `docs/evidence/index.html` and `docs/evidence/site-tour/index.html`. Those pages are outside the authorized edit scope and remain unchanged in this feature. The English and Chinese homepages carry current stamps.

`verify-scratch.log.gz` records an additional full verifier run in a disposable copy with only those two extra cache-stamp updates. `scratch-source-comparison.json` confirms that all six feature source files match the worktree byte for byte; the scope exception exists only in that temporary verification copy. Its 1,535 product tests passed; its demo suite then reported three stale provenance-hash failures. This run does not make the unmodified worktree cache-stamp gate pass.

`browser-attempt1.log.gz` records Chrome exiting at launch in the sandbox. `browser-host.log.gz` records the unavailable computer-use browser host. No screenshot or native-browser approval is claimed. The reusable mocked-API browser regression is `../history-modal-browser.mjs`.

`git-stage.log.gz` records the sandbox refusing writes to shared Git metadata outside this worktree. The delivery commit is created in a temporary clone and exported as the requested bundle; the original worktree branch reference remains unchanged.

A later temporary-copy check updates exactly the site-script hash in `demo/motion/v3/hover-source.js` and `demo/motion/v3/preview-data.js`. `demo-generated-refresh.log.gz` records all 206 demo tests passing. `remaining-offline-checks.log.gz` records the remaining verifier stages passing, including standalone Node tests, figure checks/rebuild, links and byte-identical data rebuilds. The full worktree entry point is still blocked: the four proposed generated-file updates are outside the authorized scope and are absent from the bundle. No successful full-entry-point run is claimed.
