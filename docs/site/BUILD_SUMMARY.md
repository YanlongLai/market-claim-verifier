# Site build summary

- Removed the long problem story, provider diagram, evidence tiers, oversized hero image block, old post section, and duplicated run instructions.
- Added a short bilingual page with a real English/Chinese report toggle, span-based verdict highlights, SEC filing links, three-step explanation, one accuracy chart, researcher details, trust points, and a compact footer.
- `docs/scripts/build_site.py` now reads the two post `report.json` files directly for post text, Python spans, verdicts, evidence values, filing dates, and `filing_url`; it reads the evaluation snapshot for the shared chart and research numbers, then writes `docs/site/data/site.json`.
