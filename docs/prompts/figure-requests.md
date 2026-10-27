# Reusable figure requests

Use these plain-language requests when asking an AI agent to add or update a visual. Every request assumes [`STYLE.md`](STYLE.md), the registry at [`../figures/figures.json`](../figures/figures.json), and the offline generator [`../scripts/make_figures.py`](../scripts/make_figures.py).

## New or updated chart from an evaluation

> Read `docs/prompts/STYLE.md` and `docs/figures/figures.json`. Find the latest complete `docs/evidence/eval-*/summary.json`, or use the evaluation directory I name. Add or update a deterministic chart generator in `docs/scripts/make_figures.py` using only values present in that summary. Include the source glob, output SVG and PNG, sample size, split, and run date in the registry and README marker. Use `--eval <dir>` when I specify a run. Do not call a model or invent missing metrics. Run `--all`, then `--check`.

## New verdict card from a trace

> Read `docs/prompts/STYLE.md` and `docs/figures/figures.json`. Add the named committed trace to the verdict-card selection in `docs/scripts/make_figures.py`, or create a new card figure if this is a separate visual. Show provider/model, overall program verdict, cost/latency, every sub-claim, stated value, SEC actual, accession, and trace path. Size the card to its content. Add the exact trace path to `data_sources`, update the README figure marker and registry, and run `--all` plus `--check`. Do not use values outside the trace.

## New or updated Mermaid diagram

> Read `docs/prompts/STYLE.md` and `docs/figures/figures.json`. Put the complete Mermaid source in `docs/diagrams/<id>.mmd`, using the repository's neutral/model/source/program/audit classes where applicable. Add a registry entry with the `.mmd` source as its generator and data source, add `<!-- diagram:<id>:start -->` / `<!-- diagram:<id>:end -->` in the appropriate README section, and let `docs/scripts/make_figures.py --all` sync the block. Run `--check` and confirm the README matches the `.mmd` source byte-for-byte inside the markers.

## New reusable hero or image variant

> Read `docs/prompts/STYLE.md` and `docs/prompts/hero-image.md`. Preserve the base prompt's palette, tactile editorial treatment, generous negative space, and no-readable-text constraints. Add the exact prompt, tool, date, output file, and ready-to-run variant request to the prompt library. Register the output and prompt source. Do not replace an existing image without updating its registry hash and README caption.

## Evidence refresh

> After a new eval, a live run that should be shown, a BUILD_LOG edit, or a diagram edit, run `.venv/bin/python docs/scripts/make_figures.py --all` and then `.venv/bin/python docs/scripts/make_figures.py --check`. Treat any stale figure reported by `--check` as a required regeneration, not as a cosmetic warning.
