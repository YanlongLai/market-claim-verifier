# Media examples round 2 — publication path repair

Base: `eecd0650` on `feat/media-examples`. This repair uses offline tests and
static HTTP requests only. No deployment, paid model request, SEC fetch,
synthesis, OCR/ASR accuracy retest or new financial result.

## Changes

- Move the five inputs and their manifest from `docs/site/examples/` to
  `docs/examples/`, already inside the Pages output. The six files were moved
  with `git mv`; original asset bytes, hashes and readiness states are unchanged.
- Record canonical `/examples/` URLs in the manifest and generated card index.
  Update asset/record builders, the Docker copy into `/app/examples`, tests and
  documentation. The preview uses the same five-item overlay as Pages; examples
  resolve directly from `docs/`.
- Show the original PNG in a 4:5 box with `object-fit: contain`; “Open the image”
  links to the complete PNG. Shorten English and Traditional Chinese captions
  without clipping text or changing the saved-result pending states.
- Crawl the manifest and all five asset URLs, including assets absent from HTML.
  Regressions check a stale preview-overlay decoy and a missing, unlinked PNG.
- Refresh site asset versions and the generated Traditional Chinese HTML. The
  two demo metadata changes only update the site-script source hash; hover
  behavior, narration, cues, timing and existing saved check output are unchanged.

## Checks

Full verifier: **PASS**, exit 0. Product: 1,280 tests; demo: 206 tests; standalone
Node: 97 tests. Figures, saved envelopes, examples, explorer/site/wild outputs
and Markdown links passed their offline regeneration/check requirements.

See the [full verifier log](verify-r1.log), [route crawl](routes.log),
[HTTP response receipt](http.json) and [demo metadata log](demo-metadata.log).
All five HTTP responses were 200 and their
bytes matched the manifest. The PNG response was `image/png`; a nonexistent PNG
returned 404. The route crawl checked 45 local paths with zero missing paths.

The HTTP receipt was produced while serving this worktree with:

```sh
python3 scripts/serve_site.py --port 8766
```

Verification command:

```sh
UV_OFFLINE=1 UV_CACHE_DIR=/private/tmp/claimcheck-verify-uv-cache bash scripts/verify.sh
```

The original saved text envelope is byte-identical to `eecd0650`. Audio and
video remain explicit `.pending.txt` notices, not playable media. Image, PDF,
audio and video saved results remain pending; no text-result substitution.

## Browser and preparation limits

Chrome inspection was blocked by the computer-use tool: `Computer Use was not
approved to use Google Chrome`. No alternate browser automation was attempted.
Visual screenshots and actual browser line-count measurements are unavailable;
the short captions and 4:5/contain rules were reviewed in source. No visual
critique score is asserted.

The design skill's [static lint](design-lint.json) has exactly the
[baseline findings](design-lint-base.json): three literal
source-post emoji flags, two outlined-box warnings, one numbering warning and
one em-dash warning. Both JSON reports are retained. No new findings were added;
literal recorded post text was preserved.

An initial metadata preparation command using the existing `.venv` stopped
before writes with `ModuleNotFoundError: No module named 'yaml'`. A temporary
environment with locked demo dependencies then completed the preparation.

Git's shared worktree metadata is outside this session's writable roots. The
move and delivery commit were recorded with a temporary bare Git store pointing
at this worktree, then bundled. Existing untracked bundles and synthesis records
were left untouched.
