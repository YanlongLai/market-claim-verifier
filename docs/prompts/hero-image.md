# Hero image prompt

The checked-in hero was generated for the README on 2026-10-27.

- Tool: Codex `image_gen.imagegen` (OpenAI image-generation tool)
- Model: tool-selected image model; the prior artifact did not expose a model identifier
- Date: 2026-10-27
- Output: [`docs/figures/hero.png`](../figures/hero.png), 960 × 540 PNG

## Exact prompt used

```text
Use case: editorial illustration
Asset type: wide README hero image for a technical hackathon project
Scene/backdrop: an airy off-white paper surface with subtle editorial collage texture, wide 16:9-ish composition
Subject: an abstract sentence represented only by a few dark horizontal ink marks on the left, one phrase highlighted with a translucent charcoal underline; fine thread-like lines travel from those phrase marks to a small stack of filing documents on the right, where simple abstract check and cross symbols appear as graphic marks
Style/medium: minimal contemporary editorial illustration, tactile paper cutout and ink, crisp layered shapes, restrained sophistication, no photorealism
Composition/framing: wide horizontal framing, sentence on the left, documents on the right, threads crossing the open middle, generous negative space, balanced asymmetry, readable at README width
Lighting/mood: soft diffuse daylight, calm, investigative, trustworthy
Color palette: warm white background, charcoal gray, muted slate blue, restrained forest green for checks, muted coral for crosses, tiny touches of pale yellow highlight
Materials/textures: fine paper grain, soft ink edges, thin thread lines, subtle shadows between paper layers
Text (verbatim): none; do not render any readable text or characters
Constraints: no readable text, no numbers, no fake UI text, no logos, no trademarks, no brand marks, no people's faces, no hands, no screens, no watermark; the symbols must be abstract editorial marks rather than logos
Avoid: letters, numerals, company names, SEC or Meta branding, charts, dashboards, dense detail, decorative typography
Output intent: polished, restrained hero illustration for a README captioned AI-generated illustration
```

## How to make a variant

Keep the exact prompt above as the base and change only the `Asset type`, `Composition/framing`, and `Output intent` lines. Preserve the no-readable-text constraints and the palette from [`STYLE.md`](STYLE.md).

### Slide cover, 16:9

```text
Variant: presentation slide cover, 16:9. Leave the left 38% of the frame quieter for a title overlay; move the filing stack and abstract verdict marks toward the right third. Keep the same paper-cut editorial style, palette, thread connections, and no-readable-text constraints.
```

### Social card, 1200 × 630

```text
Variant: social card, 1200 × 630. Use a tighter horizontal crop with the abstract sentence marks on the left and the filing stack on the right; preserve a calm center gap and strong silhouette at thumbnail size. Keep the same palette and no-readable-text constraints.
```

### Square, 1080 × 1080

```text
Variant: square 1080 × 1080 cover. Stack the abstract sentence marks above and the filing documents below, connected by three fine thread lines; keep generous paper-colored negative space and the same restrained editorial palette. No readable text, numbers, logos, or UI.
```
