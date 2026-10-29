# Stamp animation textures

Generated with the built-in `image_gen.imagegen` tool on 2026-10-28. These are
decorative material textures; every claim, verdict, ticker and filing URL comes
from the stored reports. Stamp lettering is real HTML text, never generated art.

## Rubber-stamp ink grain

Exact generation prompt:

> Create one grayscale rubber-stamp ink grain texture for a CSS luminance mask, 1024 × 1024 pixels, square. Worn rubber stamp grain with uneven ink coverage, tiny irregular charcoal and gray pits, broken stippling, and rough distressed edges, on a pure white background. The texture must remain predominantly white (about 85–90 percent), with fine dark wear distributed throughout, so white preserves the real text underneath a CSS mask and dark flecks remove small pieces of its ink. Flat front-on scan, no lighting, no shadow, no perspective. No words, no letters, no numbers, no logos, no symbols, no rubber stamp object, no frame. Fine organic printmaking texture only, restrained enough that masked lettering stays clearly legible. All four edges are white with a little irregular grain just inside them.

Generation notes: one built-in-tool generation, inspected before export. The tool
returned a 1254 × 1254 RGB PNG; resized with Lanczos to the requested 1024 × 1024
and saved as WebP (quality 78, method 6). No lettering or stamp object was
generated. The white field preserves the real stamp text; the dark flecks make
small gaps through `mask-mode: luminance`. Browsers without luminance masking
keep the complete, readable text stamp.

Output: [`stamp-ink.webp`](../../site/img/stamp-ink.webp), 1024 × 1024,
**124,168 bytes** (121.3 KiB; below 150 KB).

## Paper/card grain

Exact generation prompt:

> Create one seamless tileable paper grain texture for finance article cards, 512 × 512 pixels, square. A flat front-on scan of very smooth warm-white uncoated paper, extremely low contrast, delicate tiny paper fibers and barely visible fine gray grain. Even tone across the whole image and matching opposite edges for seamless repetition. No lighting variation, no shadows, no folds, no stains, no large marks, no vignette, no objects, no text, no letters, no numbers, no logos, no border. Quiet, subtle, tactile paper texture only; the visual contrast should be so low that small printed text will remain completely clear over it.

Generation notes: one built-in-tool generation, inspected before export. The tool
returned a 1254 × 1254 RGB PNG; resized with Lanczos to the requested 512 × 512
and saved as WebP (quality 78, method 6). The low-contrast fiber texture originally
repeated over the site's card surface at 12% opacity. Fix1 reuses the same file
in an isolated, visible paper layer at 60% opacity with multiply blending,
over warm off-white or lighter slate.

Output: [`stamp-paper.webp`](../../site/img/stamp-paper.webp), 512 × 512,
**4,766 bytes** (4.7 KiB; below 150 KB).

## Reuse

Reuse these files for future stamp/card variations. To regenerate, send the exact
prompt above to the built-in image-generation tool, inspect the output, then
resize and optimize it into `docs/site/img/` at no more than 150 KB per texture.
Preserve the real text stamp and report-derived data. Record any revised prompt,
generation notes, dimensions and byte sizes here.

Fix1 reuses both generated assets without regeneration. The ink mask now uses a
340 px CSS tile (previously 220 px) for more visible wear and is enabled only
after the image loads, so a failed texture never hides the permanent stamp.
