# Visual style guide

This is the style used by the repository's charts, verdict cards, Mermaid diagrams, and hero illustration. Read it before adding or changing a visual; the figure registry in [`../figures/figures.json`](../figures/figures.json) is the index of what is actually embedded.

## Palette

| Meaning | Hex | Use |
| --- | --- | --- |
| supported | `#2f855a` | Supported verdicts and positive result bars |
| contradicted | `#d45d5d` | Contradicted verdicts and harmful-error bars |
| insufficient | `#9aa4ad` | Missing or not-yet-checkable evidence |
| neutral | `#e8edf2` | Neutral nodes, panels, and background fills |
| ink | `#28323c` | Headings and primary text |
| muted | `#647180` | Captions, sources, and explanatory text |
| slate blue | `#466a83` | Model/provider accents and outlines |
| paper | `#ffffff` | Figure background and hollow markers |

Colors carry meaning consistently. In the live development chart, provider is shape, fix phase is marker fill, and program verdict is outline color.

## Type and sizing

- Matplotlib figures use the default DejaVu Sans family; Mermaid uses the renderer's sans-serif default.
- Figure titles are normally 15–16 pt, subtitles and source lines 8–10 pt, and chart labels 8–10 pt.
- Use sentence case for titles. Keep captions short and state the sample size, run date, and whether a chart is an evaluation.
- Give long labels room to wrap. Keep right-edge margins generous enough that pills, legends, and labels cannot be clipped.

## Chart rules

- Every number must come from `BUILD_LOG.md`, a committed trace, or a complete evaluation summary selected by the generator.
- Never invent sample sizes, costs, latencies, verdicts, dates, or “actual” values. If evidence is absent, show `—` or `insufficient_evidence`.
- Include a source line in the image and a registry `data_sources` entry for every evidence-backed visual.
- Evaluation figures show accuracy, false-supported rate, total cost, and mean latency. Development-run charts are explicitly labeled “not an evaluation”.
- Do not use opaque timestamps as reader-facing point labels. Use a meaningful phase or cohort key instead.
- Use SVG for README embedding and PNG as a convenient raster export.

## Verdict-card rules

- Cards are sized to their content; do not reserve a fixed tall panel for a one-row trace.
- Show provider/model, overall program verdict, cost/latency when present, each sub-claim, stated value, SEC actual, program verdict, accession, and trace path.
- Make the program-owned verdict visually dominant; keep model prose secondary.

## Mermaid conventions

- Store source as one `.mmd` file per diagram in `docs/diagrams/`.
- Use the neutral/model/source/program/audit classes above where a flow needs semantic color.
- Keep node labels short and use `<br/>` for intentional line breaks.
- Embed only through the README markers `<!-- diagram:<id>:start -->` and `<!-- diagram:<id>:end -->`; the generator owns the rendered block.

## Hero and prompt rules

- The hero is a restrained editorial illustration: warm paper, charcoal ink, muted slate blue, forest green checks, muted coral crosses, and generous negative space.
- Do not render readable text, numbers, logos, company marks, UI, faces, hands, or watermarks in generated imagery.
- Record the exact prompt, tool, date, output, and variant prompts in `docs/prompts/hero-image.md`.
