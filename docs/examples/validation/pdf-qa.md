# PDF/PNG visual check

All three native-text PDFs were rendered at 2× resolution using PDFium, then
compared side by side with their 1280×720 PNGs. All six views were inspected:
matching font, text, line breaks, alignment, colors and margins; no clipping or
missing glyphs. Native text extraction is independently checked in pytest.
Poppler was absent on this host.

The first renderer setup used `uv run --no-project --with pypdfium2`; conversion
to PIL failed with `ModuleNotFoundError: No module named 'PIL'`. This was an
environment-only failure before any PDF was rendered. Adding `--with pillow`
rendered all three pages successfully. The final render command was:

```sh
UV_CACHE_DIR=/private/tmp/w3-assets-uv-cache \
  uv run --no-project --with pypdfium2 --with pillow python - <<'PY'
from pathlib import Path
import pypdfium2 as pdfium
out = Path('/private/tmp/w3-assets-pdf-qa')
out.mkdir(exist_ok=True)
for story in 'abc':
    doc = pdfium.PdfDocument(f'docs/examples/{story}.pdf')
    doc[0].render(scale=2).to_pil().save(out / f'{story}.png')
    print(story, len(doc), 'rendered')
PY
```

Output: `a 1 rendered`, `b 1 rendered`, `c 1 rendered`. Temporary review renders
are reproducible from the committed PDFs and are not additional example inputs.
No model, SEC, synthesis or OCR/ASR requests were made for this check.
