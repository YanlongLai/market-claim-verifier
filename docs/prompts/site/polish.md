# Site polish — exact built-in image_gen prompts

Art direction follows [STAMP-V2-DESIGN.md §9](../../site/STAMP-V2-DESIGN.md#9-polish-pass-owner-round-6-quality-paper-filing-platform-style-posts-bigger-avatars). These are decorative AI production assets, separate from the real claim/evidence data. No source reports or recorded verdicts are altered.

Each entry is one built-in `image_gen` call (`transparent_background: false`). Magenta cutouts are keyed and despilled to straight alpha; opaque textures/illustrations stay opaque. Exported WebPs are resized for their display sizes. Raw generation outputs stay outside the site. The footer reuses Hover's existing palm-out `H/concern.webp` as a greeting; no new character pose is required.

## paper-grain

Output: `docs/site/img/polish/paper-grain.webp` · 256 × 256 px · opaque.

Exact prompt:

```text
Art direction: quiet editorial finance website, warm ivory bond paper, deep navy ink, restrained mint accents, tactile high-quality print detail. No real brand, platform logo, trademark, SEC seal, watermark, signatures, numbers, or text unless explicitly requested. Create one seamless square tile of uncoated light ivory bond paper, photographed straight on in even diffuse light. Extremely subtle short cellulose fibers, tiny natural tonal variation, no folds, creases, stains, vignette, borders, objects, shadows, or visible pattern. RGB should stay near warm white, ready to tile behind legible document text. Fill the whole square.
```

## stack-edge

Output: `docs/site/img/polish/stack-edge.webp` · 384 × 96 px · magenta → alpha.

Exact prompt:

```text
Art direction: quiet editorial finance website, warm ivory bond paper, deep navy ink, restrained mint accents, tactile high-quality print detail. No real brand, platform logo, trademark, SEC seal, watermark, signatures, numbers, or text unless explicitly requested. Create one isolated horizontal strip showing the bottom and right edge of two slightly offset sheets of fine ivory bond paper, a tiny realistic layered paper stack, seen almost straight on with a slight downward angle. Crisp fine fibers, restrained soft contact shadow, no curl, no writing. Very wide low composition, centered, with generous separation from every canvas edge. Everything outside the paper strip is perfectly flat pure magenta #FF00FF for chroma-key transparency. No magenta on the subject.
```

## paperclip

Output: `docs/site/img/polish/paperclip.webp` · 96 × 160 px · magenta → alpha.

Exact prompt:

```text
Art direction: quiet editorial finance website, warm ivory bond paper, deep navy ink, restrained mint accents, tactile high-quality print detail. No real brand, platform logo, trademark, SEC seal, watermark, signatures, numbers, or text unless explicitly requested. Create one isolated slender brushed-silver wire paperclip, classic double-loop shape, vertical with a very slight clockwise tilt, photographed as a premium macro stationery object from directly above. Clean realistic subtle highlights and a small soft contact shadow, elegant and utilitarian. Center the whole object with ample empty space. Perfectly flat pure magenta #FF00FF background for chroma-key transparency. No paper, no additional objects, no magenta on the metal.
```

## ink-ring

Output: `docs/site/img/polish/ink-ring.webp` · 256 × 128 px · magenta → alpha.

Exact prompt:

```text
Art direction: quiet editorial finance website, warm ivory bond paper, deep navy ink, restrained mint accents, tactile high-quality print detail. No real brand, platform logo, trademark, SEC seal, watermark, signatures, numbers, or text unless explicitly requested. Create a single horizontal oval rubber date-stamp border made of dark muted terracotta ink, distressed with realistic microscopic missing flecks and uneven ink pressure. Two fine oval outlines, empty clear center, strictly no letters, words, date, numerals, emblem, seal or imagery. Wide oval, centered, 2:1 proportions, ample margin. Perfectly flat pure magenta #FF00FF background inside and outside the ring for chroma-key transparency.
```

## banana-masthead

Output: `docs/site/img/polish/banana-masthead.webp` · 520 × 96 px · magenta → alpha.

Exact prompt:

```text
Art direction: quiet editorial finance website, warm ivory bond paper, deep navy ink, restrained mint accents, tactile high-quality print detail. No real brand, platform logo, trademark, SEC seal, watermark, signatures, numbers, or text unless explicitly requested. Design one premium fictional newspaper masthead logotype with the exact words 'Banana News Flash' and no other text. Highly readable dark navy editorial serif lettering with an individual but restrained character, a small simple curved yellow banana accent above or beside the B, professional newsroom rather than playful cartoon. Single horizontal line, wide low composition, generous spacing from edges. Perfectly flat pure magenta #FF00FF background for chroma-key transparency. No real outlet resemblance, no border, no seal, no slogan.
```

## article-revenue

Output: `docs/site/img/polish/article-revenue.webp` · 320 × 180 px · opaque.

Exact prompt:

```text
Art direction: quiet editorial finance website, warm ivory bond paper, deep navy ink, restrained mint accents, tactile high-quality print detail. No real brand, platform logo, trademark, SEC seal, watermark, signatures, numbers, or text unless explicitly requested. Create one small landscape editorial illustration about a company's quarterly revenue: three ivory shipping cartons, a folded blank ledger sheet and one mint rising bar shape, arranged as a carefully lit tabletop still life. Sophisticated tactile painted-paper illustration, soft dry gouache detail, warm cream ground, deep navy linework, a little muted ochre. Quiet balanced composition with objects centered and generous breathing room. Absolutely no labels, text, numerals, logos, arrows predicting performance, or stock ticker.
```

## article-ledger

Output: `docs/site/img/polish/article-ledger.webp` · 320 × 180 px · opaque.

Exact prompt:

```text
Art direction: quiet editorial finance website, warm ivory bond paper, deep navy ink, restrained mint accents, tactile high-quality print detail. No real brand, platform logo, trademark, SEC seal, watermark, signatures, numbers, or text unless explicitly requested. Create one small landscape editorial illustration about comparing financial records: two open blank cream ledger pages side by side with ruled lines but no text or numbers, a mint magnifying glass resting across their edges, one small terracotta rubber stamp to the side. Sophisticated tactile painted-paper illustration, soft dry gouache detail, warm cream ground, deep navy linework. Quiet balanced composition, generous breathing room, no writing, logos, faces or emblems.
```

## how-claim

Output: `docs/site/img/polish/how-claim.webp` · 384 × 288 px · magenta → alpha.

Character reference: `docs/site/img/auditor/H/inspect.webp`. Reference only; generate a new illustration.

Exact prompt:

```text
Art direction: quiet editorial finance website, warm ivory bond paper, deep navy ink, restrained mint accents, tactile high-quality print detail. No real brand, platform logo, trademark, SEC seal, watermark, signatures, numbers, or text unless explicitly requested. The supplied image is a character reference only. Create a new small editorial spot illustration of exactly this Hover robot: round ivory floating body, dark navy wide visor with two mint dot eyes, mint accountant eyeshade, antenna, small mint bottom nozzle, no legs. Preserve its identity and proportions. Hover uses its magnifying glass to inspect a floating blank social-post slip with a few navy horizontal marks but absolutely no legible text or numerals. Charming precise action, tactile soft 3D illustration, front three-quarter view, one concise scene, whole robot and props visible with generous margins. No flame. Perfectly flat pure magenta #FF00FF background for chroma-key transparency; no magenta on subject.
```

## how-filing

Output: `docs/site/img/polish/how-filing.webp` · 384 × 288 px · magenta → alpha.

Character reference: `docs/site/img/auditor/H/point.webp`. Reference only; generate a new illustration.

Exact prompt:

```text
Art direction: quiet editorial finance website, warm ivory bond paper, deep navy ink, restrained mint accents, tactile high-quality print detail. No real brand, platform logo, trademark, SEC seal, watermark, signatures, numbers, or text unless explicitly requested. The supplied image is a character reference only. Create a new small editorial spot illustration of exactly this Hover robot: round ivory floating body, dark navy wide visor with two mint dot eyes, mint accountant eyeshade, antenna, small mint bottom nozzle, no legs. Preserve its identity and proportions. Hover opens a small ivory paper filing folder and points to one amber-highlighted ruled row on a blank document, no legible text or numerals. Tactile soft 3D illustration, front three-quarter view, one concise scene, whole robot and props visible with generous margins. No flame. Perfectly flat pure magenta #FF00FF background for chroma-key transparency; no magenta on subject.
```

## how-code

Output: `docs/site/img/polish/how-code.webp` · 384 × 288 px · magenta → alpha.

Character reference: `docs/site/img/auditor/H/approve.webp`. Reference only; generate a new illustration.

Exact prompt:

```text
Art direction: quiet editorial finance website, warm ivory bond paper, deep navy ink, restrained mint accents, tactile high-quality print detail. No real brand, platform logo, trademark, SEC seal, watermark, signatures, numbers, or text unless explicitly requested. The supplied image is a character reference only. Create a new small editorial spot illustration of exactly this Hover robot: round ivory floating body, dark navy wide visor with mint happy chevron eyes, mint accountant eyeshade, antenna, small mint bottom nozzle, no legs. Preserve its identity and proportions. Hover holds a small navy rubber stamp beside two neatly aligned blank ledger slips with matching mint blocks, conveying a completed precise comparison. No letters, no numerals, no text, no checkmark seal. Tactile soft 3D illustration, front three-quarter view, one concise scene, whole robot and props visible with generous margins. No flame. Perfectly flat pure magenta #FF00FF background for chroma-key transparency; no magenta on subject.
```

## section-grain

Output: `docs/site/img/polish/section-grain.webp` · 256 × 256 px · opaque.

Exact prompt:

```text
Art direction: quiet editorial finance website, warm ivory bond paper, deep navy ink, restrained mint accents, tactile high-quality print detail. No real brand, platform logo, trademark, SEC seal, watermark, signatures, numbers, or text unless explicitly requested. Create one seamless square tile of very fine warm-gray graphite and paper fiber grain on a nearly white ivory ground, a subtle archival print surface for broad website section backgrounds. Extremely low contrast, uniform lighting, no discrete objects, no clouds, gradients, vignette, creases, borders or visible repeats. Fill the whole square, tonal range very close to white so content remains dominant.
```


## Export receipt

Built-in `image_gen` produced all eleven assets above. The [export manifest](../../site/img/polish/manifest.json) records the exact prompts, character references, original SHA-256 hashes and WebP SHA-256 hashes. The [processor](../../site/img/polish/process-assets.py) only keys, despills, crops empty margins, resizes and encodes; it does not draw artwork. Recheck committed exports with:

```sh
.venv/bin/python docs/site/img/polish/process-assets.py --check
```

| WebP | Dimensions | Bytes |
| --- | --- | ---: |
| [paper-grain.webp](../../site/img/polish/paper-grain.webp) | 256 × 256 | 802 |
| [stack-edge.webp](../../site/img/polish/stack-edge.webp) | 384 × 96 | 2,216 |
| [paperclip.webp](../../site/img/polish/paperclip.webp) | 96 × 160 | 5,580 |
| [ink-ring.webp](../../site/img/polish/ink-ring.webp) | 256 × 128 | 12,180 |
| [banana-masthead.webp](../../site/img/polish/banana-masthead.webp) | 520 × 96 | 15,352 |
| [article-revenue.webp](../../site/img/polish/article-revenue.webp) | 320 × 180 | 5,254 |
| [article-ledger.webp](../../site/img/polish/article-ledger.webp) | 320 × 180 | 7,748 |
| [how-claim.webp](../../site/img/polish/how-claim.webp) | 384 × 288 | 19,484 |
| [how-filing.webp](../../site/img/polish/how-filing.webp) | 384 × 288 | 18,882 |
| [how-code.webp](../../site/img/polish/how-code.webp) | 384 × 288 | 19,852 |
| [section-grain.webp](../../site/img/polish/section-grain.webp) | 256 × 256 | 654 |

**Total: 108,004 bytes (108.004 KB), under the 600,000-byte cap.** The footer reuses the existing 35,290-byte `H/concern.webp` palm-out greeting. Existing 256 px persona exports are reused; no persona images were generated. Runtime artwork uses native `loading="lazy"` and `decoding="async"`; moving stage decorations also wait for scene start/seek. Raw PNGs and review contacts are not included in the site or this budget.

