# Auditor robot — approved B and pose provenance

## Owner selection for stamp v2

Variant **B** is the approved character. Stamp v2 selected `B/idle.webp`,
`B/inspect.webp`, `B/present.webp`, and `B/stamp.webp` (originally 311,514 bytes total).
Stamp v3 adds seven poses; the new section below records their generation,
common-canvas normalization, exact prompts and verification results.
The original `sheet-B.png` is retained as the source sheet and is never loaded
by the page. Variants A and C, preview images, and unused PNG pose exports were
removed from the site assets. The historical generation prompts below remain
as provenance. The scene mirrors B toward the inspection desk; pose changes
cross-fade over 120 ms using the deterministic scene clock.

## v3 poses

Seven new poses of the approved B character: **reach, point, think, stamp-down,
approve, concern, shrug**. Generated with the built-in **image_gen** tool, edited
from the approved artwork, then keyed/cut/despilled/trimmed/encoded locally.
No commit, push, or page-code edit was made for this asset task.

### Sources, reusable inputs and scale

- Approved reference: [sheet-B.png](../../site/img/auditor/sheet-B.png), SHA-256
  `84687b675f5d7e352fdeaa57d6c2f340441f0c00ed1c2899379c72622eda1c7d`, unchanged.
- Individual pose edit input 1:
  `docs/site/img/auditor/v3/source/reference-idle.png`; input 2:
  `docs/site/img/auditor/sheet-B.png`. The first is a deterministic repack of
  the approved source idle crop (89, 42, 453, 682), without resizing its pixels,
  onto 1024 × 1024 magenta at (330, 260). Its standing content height is 640.
- The seven individual tool outputs are retained as
  `v3/source/<pose>-draft.png`. Their actual resolution is 1254 × 1254.
  Those drafts had small camera/scale differences and served as gesture references.
- `v3/source/pose-drafts.png` repacks the drafts into four columns and two rows.
  Top: idle calibration, reach, point, think. Bottom: stamp-down, approve,
  concern, shrug. Only the approved reference is resolution-matched from 1024
  to 1254 pixels for this *reference contact*. The draft artworks are copied
  without rescaling.
- The final consistency edit uses `sheet-B.png` as input 1 and
  `v3/source/pose-drafts.png` as input 2. Its exact prompt appears below.
  The selected final source is [sheet-B-v3.png](../../site/img/auditor/sheet-B-v3.png),
  actual resolution **1536 × 1024** (the requested size was 3072 × 2048).
- All seven final exports come from that one final atlas. **One shared source-to-export
  scale = 508 / 414 = 1.227053140097**; no per-pose bbox fitting.
  The atlas idle calibration measures 412 source pixels and becomes 506 pixels;
  the approved idle content is 508 pixels. The reach silhouette sets the 508-pixel
  maximum content budget. Bent knees and tilted heads retain their natural lower
  silhouette tops.
- The original four files had different trimmed canvases (293 × 512, 376 × 502,
  347 × 510, 338 × 510). For a common canvas and baseline, **all eleven are now
  576 × 512**. Original artwork is preserved pixel-for-pixel and only padded.
  The original WebP files and v2 manifest remain under
  `v3/source/approved-B/` and `v3/manifest-v2.json`.
- Every pose is boot-pair-centered; the exclusive alpha-bbox bottom is **y=510**
  (last covered row **509**), with two fully transparent rows below.
- Output is real 8-bit RGBA. The existing key/matte unmix/despill method is reused.
  The WebP codec is lossless; new RGB values are quantized only by 2/255 (think)
  or 3/255 (the other six), as in the prior pipeline, to meet **90,000 bytes**.
  Alpha keeps all 256 levels. The padded originals receive no color quantization.
- `v3/generation-requests.json` and `v3/atlas-request.json` retain the exact
  tool argument values, original generated-file paths, and source mapping.
  All successful generation prompts are also copied verbatim below.
  Every call uses `transparent_background: false`, because this brief requires
  the magenta keying workflow.

To rebuild edit references locally:

```sh
.venv/bin/python docs/site/img/auditor/process-auditor.py --prepare-inputs
```

To reproduce the final exports, contact and manifest from the retained sources:

```sh
.venv/bin/python docs/site/img/auditor/process-auditor.py
```

### Review and measured results

[contact-v3.png](../../site/img/auditor/contact-v3.png) is **6336 × 1120**,
2,333,327 bytes. It shows all eleven at 1:1 scale, left to right in the table
order below, first on **#f7f5ef**, then on **#111a20**. It has no labels, text,
numbers, logos, or other marks and is not referenced by page code.

Visual review covered the squared head/crown, one inset visor and continuous mint
eye strip, eyeshade brim/attachments, antenna attachment, ear hardware, torso,
waist, mint cuffs, hand construction, shin guards, boot soles and mint inserts,
material colors and upper-left lighting. Gestures were reviewed at export size:
blank folder/tab pull, sideways index, thoughtful chin gesture, downward stamp at
the hip with bent knees, small thumbs-up with stamp at side, outward stop palm,
and both palms-up shrug. The approval eye strip curves gently within the same
visor. Full silhouettes, antennae and props are visible. No text, logos or numbers
were observed in the artwork. Both background composites were inspected for
fringe, edge holes, halos and clipping.

Automated checks cover all eleven: full transparency and opacity, nonempty partial
alpha, transparent outer borders, common canvas, exact feet baseline, <=90,000
bytes, lossless encode/decode equality, zero RGB in transparent pixels, and
**zero magenta-fringe pixels** by the existing criterion
`min(R,B) - G > 18 and alpha > 32`. For the original four, the padded result
is cropped back and compared against every decoded original RGBA pixel.
The original source sheet hash is unchanged. File hashes are in
[manifest.json](../../site/img/auditor/manifest.json).

Bboxes use `(left, top, right, bottom)` with exclusive right/bottom; dimensions
are the visible alpha-bbox dimensions, not the common 576 × 512 canvas.

| Pose | Alpha bbox | Visible dimensions | Bytes | KB (1000 bytes) |
|---|---|---|---:|---:|
| idle | (122, 2, 411, 510) | 289 × 508 | 81,886 | 81.886 |
| inspect | (151, 12, 523, 510) | 372 × 498 | 79,822 | 79.822 |
| present | (170, 4, 513, 510) | 343 × 506 | 78,534 | 78.534 |
| stamp | (146, 4, 480, 510) | 334 × 506 | 80,024 | 80.024 |
| reach | (176, 2, 536, 510) | 360 × 508 | 86,266 | 86.266 |
| point | (146, 18, 550, 510) | 404 × 492 | 78,790 | 78.790 |
| think | (181, 7, 395, 510) | 214 × 503 | 83,162 | 83.162 |
| stamp-down | (156, 14, 487, 510) | 331 × 496 | 79,638 | 79.638 |
| approve | (124, 19, 426, 510) | 302 × 491 | 80,350 | 80.350 |
| concern | (134, 18, 424, 510) | 290 × 492 | 82,188 | 82.188 |
| shrug | (76, 39, 498, 510) | 422 × 471 | 80,078 | 80.078 |

Seven new poses total **570,472 bytes**; all eleven total **890,738 bytes**.
The contact and retained sources are review/provenance assets; only `B/<pose>.webp`
is intended for pose loading. Page code uses explicit pose paths and does not
request the contact or source atlas.

Canvas integration note: the existing page uses a 190 × 260 CSS `object-fit:
contain` box on desktop. Common horizontal padding makes the pose artwork fit
that box by width (about 168 pixels for the 508-pixel-tall poses). An integration
that wants a 260-pixel-tall robot should give the 576 × 512 asset a roughly
293 × 260 display box. This task's edit scope excludes page/CSS changes.

### Exact v3 generation prompt — reach

```text
Edit the FIRST reference image, a square 1024 x 1024 magenta canvas containing the approved Auditor robot B. The SECOND reference is the original four-pose sheet: it is identity and tool reference only. Produce ONE square 1024 x 1024 production pose image with ONE full-body robot. This is a pose edit of the exact existing character, not a redesign or a new interpretation.

IDENTITY LOCK: Match the approved B robot exactly: softly squared off-white head and crown, wide inset black rounded-rectangular visor, one continuous luminous mint eye strip, narrow projecting mint accountant eyeshade with dark attachment band, thin antenna with mint ball on the same viewer-left side of the crown as the reference, mint-edged circular ear hardware, short off-white rounded-rectangular chest, narrow dark neck and waist couplings, off-white pelvic shell, black joints, small segmented three-digit robot hands with off-white plates, off-white forearms with mint cuff bands, off-white shin guards and compact rounded-square off-white boots with dark soles and mint heel/ankle inserts. Preserve the reference proportions, geometry, warm off-white material, mint hue, dark navy joints, restrained surface detail, camera perspective and soft upper-left studio illumination. No new chest marks or mechanical decorations. Do not make the head rounder, larger, cuter or more toy-like.

FRAME AND SCALE LOCK: The first reference has a 640-pixel standing-equivalent robot height including its antenna; its visible content is x=330..694 and y=260..900. Keep exactly that anatomical pixel scale: head shell approximately 255 pixels wide, standing feet baseline y=900, standing antenna top y=260. Do not enlarge the robot to fill the canvas. Keep its torso centered approximately x=535. Preserve the body-part dimensions even when joints bend; a crouch or head tilt naturally lowers the top rather than changing scale. Boots remain grounded on baseline y=900. Keep generous magenta margin around every limb, antenna and prop. No cropping. No duplicate robot, no reference robot inset, no contact sheet.

POSE:
Turn the robot three-quarter toward the viewer's RIGHT. Extend its left arm sideways toward the viewer's right, gently pulling open the projecting tab of a plain blank off-white file folder held at chest-to-waist height to its right. The folder has a simple visible open flap and a small blank tab, no content or markings. The reaching hand visibly grasps the tab. The other hand steadies the folder closer to the torso. Keep its visor fully visible, its familiar head geometry and its small antenna on the same physical crown attachment. No stamp or magnifier.

BACKGROUND: perfectly flat solid MAGENTA #FF00FF outside the robot and its specified prop, including every gap between limbs and fingers. No background gradients, no floor, no ground or contact shadow, no haze, no reflected pink light, no scenery. Visor glow stays inside the visor. No text, letters, numbers, logos, badges, captions, labels, borders, grid lines or watermarks anywhere. Return only the single finished pose image.
```

### Exact v3 generation prompt — point

```text
Edit the FIRST reference image, a square 1024 x 1024 magenta canvas containing the approved Auditor robot B. The SECOND reference is the original four-pose sheet: it is identity and tool reference only. Produce ONE square 1024 x 1024 production pose image with ONE full-body robot. This is a pose edit of the exact existing character, not a redesign or a new interpretation.

IDENTITY LOCK: Match the approved B robot exactly: softly squared off-white head and crown, wide inset black rounded-rectangular visor, one continuous luminous mint eye strip, narrow projecting mint accountant eyeshade with dark attachment band, thin antenna with mint ball on the same viewer-left side of the crown as the reference, mint-edged circular ear hardware, short off-white rounded-rectangular chest, narrow dark neck and waist couplings, off-white pelvic shell, black joints, small segmented three-digit robot hands with off-white plates, off-white forearms with mint cuff bands, off-white shin guards and compact rounded-square off-white boots with dark soles and mint heel/ankle inserts. Preserve the reference proportions, geometry, warm off-white material, mint hue, dark navy joints, restrained surface detail, camera perspective and soft upper-left studio illumination. No new chest marks or mechanical decorations. Do not make the head rounder, larger, cuter or more toy-like.

FRAME AND SCALE LOCK: The first reference has a 640-pixel standing-equivalent robot height including its antenna; its visible content is x=330..694 and y=260..900. Keep exactly that anatomical pixel scale: head shell approximately 255 pixels wide, standing feet baseline y=900, standing antenna top y=260. Do not enlarge the robot to fill the canvas. Keep its torso centered approximately x=535. Preserve the body-part dimensions even when joints bend; a crouch or head tilt naturally lowers the top rather than changing scale. Boots remain grounded on baseline y=900. Keep generous magenta margin around every limb, antenna and prop. No cropping. No duplicate robot, no reference robot inset, no contact sheet.

POSE:
Turn the robot three-quarter toward the viewer's RIGHT. Extend one forearm horizontally toward the viewer's right at chest height, with the index digit clearly pointing sideways to the right and the remaining digits curled. Rest the other hand on its hip. The pointing gesture is confident and precise. Keep both boots grounded, visor visible, and the same physical antenna attachment. No prop and no stamp.

BACKGROUND: perfectly flat solid MAGENTA #FF00FF outside the robot and its specified prop, including every gap between limbs and fingers. No background gradients, no floor, no ground or contact shadow, no haze, no reflected pink light, no scenery. Visor glow stays inside the visor. No text, letters, numbers, logos, badges, captions, labels, borders, grid lines or watermarks anywhere. Return only the single finished pose image.
```

### Exact v3 generation prompt — think

```text
Edit the FIRST reference image, a square 1024 x 1024 magenta canvas containing the approved Auditor robot B. The SECOND reference is the original four-pose sheet: it is identity and tool reference only. Produce ONE square 1024 x 1024 production pose image with ONE full-body robot. This is a pose edit of the exact existing character, not a redesign or a new interpretation.

IDENTITY LOCK: Match the approved B robot exactly: softly squared off-white head and crown, wide inset black rounded-rectangular visor, one continuous luminous mint eye strip, narrow projecting mint accountant eyeshade with dark attachment band, thin antenna with mint ball on the same viewer-left side of the crown as the reference, mint-edged circular ear hardware, short off-white rounded-rectangular chest, narrow dark neck and waist couplings, off-white pelvic shell, black joints, small segmented three-digit robot hands with off-white plates, off-white forearms with mint cuff bands, off-white shin guards and compact rounded-square off-white boots with dark soles and mint heel/ankle inserts. Preserve the reference proportions, geometry, warm off-white material, mint hue, dark navy joints, restrained surface detail, camera perspective and soft upper-left studio illumination. No new chest marks or mechanical decorations. Do not make the head rounder, larger, cuter or more toy-like.

FRAME AND SCALE LOCK: The first reference has a 640-pixel standing-equivalent robot height including its antenna; its visible content is x=330..694 and y=260..900. Keep exactly that anatomical pixel scale: head shell approximately 255 pixels wide, standing feet baseline y=900, standing antenna top y=260. Do not enlarge the robot to fill the canvas. Keep its torso centered approximately x=535. Preserve the body-part dimensions even when joints bend; a crouch or head tilt naturally lowers the top rather than changing scale. Boots remain grounded on baseline y=900. Keep generous magenta margin around every limb, antenna and prop. No cropping. No duplicate robot, no reference robot inset, no contact sheet.

POSE:
Face the robot front as in idle. Raise one hand to the lower visor/chin area in a small thoughtful gesture: one digit rests near the bottom outer corner of the visor, never hiding the mint eye strip. Tilt the head slightly, about 7 degrees, in quiet thought. The other arm rests loosely across the waist supporting the raised elbow. Keep the same single luminous mint strip, neutral attentive expression, head size, torso and boots. No props and no stamp.

BACKGROUND: perfectly flat solid MAGENTA #FF00FF outside the robot and its specified prop, including every gap between limbs and fingers. No background gradients, no floor, no ground or contact shadow, no haze, no reflected pink light, no scenery. Visor glow stays inside the visor. No text, letters, numbers, logos, badges, captions, labels, borders, grid lines or watermarks anywhere. Return only the single finished pose image.
```

### Exact v3 generation prompt — stamp-down

```text
Edit the FIRST reference image, a square 1024 x 1024 magenta canvas containing the approved Auditor robot B. The SECOND reference is the original four-pose sheet: it is identity and tool reference only. Produce ONE square 1024 x 1024 production pose image with ONE full-body robot. This is a pose edit of the exact existing character, not a redesign or a new interpretation.

IDENTITY LOCK: Match the approved B robot exactly: softly squared off-white head and crown, wide inset black rounded-rectangular visor, one continuous luminous mint eye strip, narrow projecting mint accountant eyeshade with dark attachment band, thin antenna with mint ball on the same viewer-left side of the crown as the reference, mint-edged circular ear hardware, short off-white rounded-rectangular chest, narrow dark neck and waist couplings, off-white pelvic shell, black joints, small segmented three-digit robot hands with off-white plates, off-white forearms with mint cuff bands, off-white shin guards and compact rounded-square off-white boots with dark soles and mint heel/ankle inserts. Preserve the reference proportions, geometry, warm off-white material, mint hue, dark navy joints, restrained surface detail, camera perspective and soft upper-left studio illumination. No new chest marks or mechanical decorations. Do not make the head rounder, larger, cuter or more toy-like.

FRAME AND SCALE LOCK: The first reference has a 640-pixel standing-equivalent robot height including its antenna; its visible content is x=330..694 and y=260..900. Keep exactly that anatomical pixel scale: head shell approximately 255 pixels wide, standing feet baseline y=900, standing antenna top y=260. Do not enlarge the robot to fill the canvas. Keep its torso centered approximately x=535. Preserve the body-part dimensions even when joints bend; a crouch or head tilt naturally lowers the top rather than changing scale. Boots remain grounded on baseline y=900. Keep generous magenta margin around every limb, antenna and prop. No cropping. No duplicate robot, no reference robot inset, no contact sheet.

POSE:
Create the downstroke that follows the original sheet's raised STAMP pose. Face mostly front with a slight turn to the viewer's right. Its stamp-holding arm is now brought firmly DOWN IN FRONT of its body. Grip the EXACT SAME rubber stamp as the reference idle and raised stamp poses: short dark bulb-like handle and rectangular mint-and-dark base. The base is horizontal at HIP HEIGHT, pressing downward in a decisive strike; the hand and forearm press vertically down above it. Keep the stamp fully visible in front beside the centerline, not hidden behind the torso, and no surface under it. The free arm balances out slightly. Add a slight natural knee bend, keeping both boots on the same feet baseline. This is a compact downward strike, not a wind-up. No motion lines, no effect marks, no props besides that one stamp.

BACKGROUND: perfectly flat solid MAGENTA #FF00FF outside the robot and its specified prop, including every gap between limbs and fingers. No background gradients, no floor, no ground or contact shadow, no haze, no reflected pink light, no scenery. Visor glow stays inside the visor. No text, letters, numbers, logos, badges, captions, labels, borders, grid lines or watermarks anywhere. Return only the single finished pose image.
```

### Exact v3 generation prompt — approve

```text
Edit the FIRST reference image, a square 1024 x 1024 magenta canvas containing the approved Auditor robot B. The SECOND reference is the original four-pose sheet: it is identity and tool reference only. Produce ONE square 1024 x 1024 production pose image with ONE full-body robot. This is a pose edit of the exact existing character, not a redesign or a new interpretation.

IDENTITY LOCK: Match the approved B robot exactly: softly squared off-white head and crown, wide inset black rounded-rectangular visor, one continuous luminous mint eye strip, narrow projecting mint accountant eyeshade with dark attachment band, thin antenna with mint ball on the same viewer-left side of the crown as the reference, mint-edged circular ear hardware, short off-white rounded-rectangular chest, narrow dark neck and waist couplings, off-white pelvic shell, black joints, small segmented three-digit robot hands with off-white plates, off-white forearms with mint cuff bands, off-white shin guards and compact rounded-square off-white boots with dark soles and mint heel/ankle inserts. Preserve the reference proportions, geometry, warm off-white material, mint hue, dark navy joints, restrained surface detail, camera perspective and soft upper-left studio illumination. No new chest marks or mechanical decorations. Do not make the head rounder, larger, cuter or more toy-like.

FRAME AND SCALE LOCK: The first reference has a 640-pixel standing-equivalent robot height including its antenna; its visible content is x=330..694 and y=260..900. Keep exactly that anatomical pixel scale: head shell approximately 255 pixels wide, standing feet baseline y=900, standing antenna top y=260. Do not enlarge the robot to fill the canvas. Keep its torso centered approximately x=535. Preserve the body-part dimensions even when joints bend; a crouch or head tilt naturally lowers the top rather than changing scale. Boots remain grounded on baseline y=900. Keep generous magenta margin around every limb, antenna and prop. No cropping. No duplicate robot, no reference robot inset, no contact sheet.

POSE:
Face the robot front as in idle, upright and quietly pleased. Keep the original stamp in the SAME hand down at the SAME side as in idle: exact dark handle and rectangular mint-and-dark base. With its free hand give a SMALL clearly readable thumbs-up near chest height: thumb upright, other digits curled, hand compact. Inside the existing single black visor, gently curve the single mint luminous eye strip upward at its ends into a subtle pleased expression while preserving its thickness and continuous form. No separate human eyes, no mouth, no redesign. Keep head, antenna, torso, stance and boot geometry as close to idle as possible.

BACKGROUND: perfectly flat solid MAGENTA #FF00FF outside the robot and its specified prop, including every gap between limbs and fingers. No background gradients, no floor, no ground or contact shadow, no haze, no reflected pink light, no scenery. Visor glow stays inside the visor. No text, letters, numbers, logos, badges, captions, labels, borders, grid lines or watermarks anywhere. Return only the single finished pose image.
```

### Exact v3 generation prompt — concern

```text
Edit the FIRST reference image, a square 1024 x 1024 magenta canvas containing the approved Auditor robot B. The SECOND reference is the original four-pose sheet: it is identity and tool reference only. Produce ONE square 1024 x 1024 production pose image with ONE full-body robot. This is a pose edit of the exact existing character, not a redesign or a new interpretation.

IDENTITY LOCK: Match the approved B robot exactly: softly squared off-white head and crown, wide inset black rounded-rectangular visor, one continuous luminous mint eye strip, narrow projecting mint accountant eyeshade with dark attachment band, thin antenna with mint ball on the same viewer-left side of the crown as the reference, mint-edged circular ear hardware, short off-white rounded-rectangular chest, narrow dark neck and waist couplings, off-white pelvic shell, black joints, small segmented three-digit robot hands with off-white plates, off-white forearms with mint cuff bands, off-white shin guards and compact rounded-square off-white boots with dark soles and mint heel/ankle inserts. Preserve the reference proportions, geometry, warm off-white material, mint hue, dark navy joints, restrained surface detail, camera perspective and soft upper-left studio illumination. No new chest marks or mechanical decorations. Do not make the head rounder, larger, cuter or more toy-like.

FRAME AND SCALE LOCK: The first reference has a 640-pixel standing-equivalent robot height including its antenna; its visible content is x=330..694 and y=260..900. Keep exactly that anatomical pixel scale: head shell approximately 255 pixels wide, standing feet baseline y=900, standing antenna top y=260. Do not enlarge the robot to fill the canvas. Keep its torso centered approximately x=535. Preserve the body-part dimensions even when joints bend; a crouch or head tilt naturally lowers the top rather than changing scale. Boots remain grounded on baseline y=900. Keep generous magenta margin around every limb, antenna and prop. No cropping. No duplicate robot, no reference robot inset, no contact sheet.

POSE:
Face the robot front as in idle. Raise one forearm with its small robotic palm facing outward toward the viewer at upper-chest height in a polite 'stop / that is wrong' gesture. Three familiar segmented digits spread just enough to read clearly, palm visible. Lean the torso and head back slightly in mild concern while keeping both boots grounded and body dimensions unchanged. The other arm rests by its side with an open relaxed hand. Keep the visor's single luminous mint strip, perhaps angled slightly with the head, no new face. No stamp and no other props.

BACKGROUND: perfectly flat solid MAGENTA #FF00FF outside the robot and its specified prop, including every gap between limbs and fingers. No background gradients, no floor, no ground or contact shadow, no haze, no reflected pink light, no scenery. Visor glow stays inside the visor. No text, letters, numbers, logos, badges, captions, labels, borders, grid lines or watermarks anywhere. Return only the single finished pose image.
```

### Exact v3 generation prompt — shrug

```text
Edit the FIRST reference image, a square 1024 x 1024 magenta canvas containing the approved Auditor robot B. The SECOND reference is the original four-pose sheet: it is identity and tool reference only. Produce ONE square 1024 x 1024 production pose image with ONE full-body robot. This is a pose edit of the exact existing character, not a redesign or a new interpretation.

IDENTITY LOCK: Match the approved B robot exactly: softly squared off-white head and crown, wide inset black rounded-rectangular visor, one continuous luminous mint eye strip, narrow projecting mint accountant eyeshade with dark attachment band, thin antenna with mint ball on the same viewer-left side of the crown as the reference, mint-edged circular ear hardware, short off-white rounded-rectangular chest, narrow dark neck and waist couplings, off-white pelvic shell, black joints, small segmented three-digit robot hands with off-white plates, off-white forearms with mint cuff bands, off-white shin guards and compact rounded-square off-white boots with dark soles and mint heel/ankle inserts. Preserve the reference proportions, geometry, warm off-white material, mint hue, dark navy joints, restrained surface detail, camera perspective and soft upper-left studio illumination. No new chest marks or mechanical decorations. Do not make the head rounder, larger, cuter or more toy-like.

FRAME AND SCALE LOCK: The first reference has a 640-pixel standing-equivalent robot height including its antenna; its visible content is x=330..694 and y=260..900. Keep exactly that anatomical pixel scale: head shell approximately 255 pixels wide, standing feet baseline y=900, standing antenna top y=260. Do not enlarge the robot to fill the canvas. Keep its torso centered approximately x=535. Preserve the body-part dimensions even when joints bend; a crouch or head tilt naturally lowers the top rather than changing scale. Boots remain grounded on baseline y=900. Keep generous magenta margin around every limb, antenna and prop. No cropping. No duplicate robot, no reference robot inset, no contact sheet.

POSE:
Face the robot front as in idle. Raise BOTH forearms out to either side at lower-chest height, elbows bent, both small robotic palms facing UP in a clear gentle shrug. Lift the shoulders slightly and tilt the head only a little in uncertainty. Keep the three-digit hand construction and all joints anatomically coherent, both boots grounded, and the same continuous mint visor eye strip. No stamp and no props.

BACKGROUND: perfectly flat solid MAGENTA #FF00FF outside the robot and its specified prop, including every gap between limbs and fingers. No background gradients, no floor, no ground or contact shadow, no haze, no reflected pink light, no scenery. Visor glow stays inside the visor. No text, letters, numbers, logos, badges, captions, labels, borders, grid lines or watermarks anywhere. Return only the single finished pose image.
```

### Exact v3 final atlas prompt

Reference/edit inputs, in order:
`docs/site/img/auditor/sheet-B.png`,
`docs/site/img/auditor/v3/source/pose-drafts.png`.
`transparent_background: false`.

```text
Create the FINAL production source atlas for the SAME approved Auditor robot B. This is a consolidation and consistency edit, not a redesign. Image 1 is the original approved four-pose B sheet and controls identity, proportions, materials, lighting and tool design. Image 2 is the draft atlas: top row idle calibration, reach, point, think; bottom row stamp-down, approve, concern, shrug. It preserves all the individual draft artwork; read each cell as the gesture reference. Keep those precise gestures, but correct their small scale differences so EVERY robot is exactly the same anatomical size.

OUTPUT: ONE landscape atlas, requested 3072 x 2048 pixels, four columns and two rows, eight full-body depictions total, with generous solid-magenta gaps between silhouettes. Use equal invisible cells, no drawn panels. Every cell has the SAME fixed camera, head dimensions, chest dimensions, leg segment dimensions, boot size, and standing-equivalent scale. Do not fit each pose independently. Every robot is identical apart from joint rotations and the specified visor expression. Head shell width is 40% of standing-equivalent antenna-to-sole height. Arms and props may extend wider but never trigger zoom or body resizing. Baseline in each row is shared. The knee bend and head tilt change top height naturally without resizing any body part.

ORDER IS MANDATORY:
TOP ROW LEFT TO RIGHT:
1. IDLE CALIBRATION: reproduce the approved original idle robot, standing front, its dark-handled rectangular mint-and-dark rubber stamp down at its viewer-left side. This cell establishes the anatomical scale for all seven other cells.
2. REACH: three-quarter toward viewer's RIGHT, arm extended sideways to viewer's right, gripping and pulling open the tab of a blank off-white file folder; other hand steadies the folder. Match draft atlas top-row cell 2. No stamp.
3. POINT: three-quarter toward viewer's RIGHT, index digit pointing horizontally right at chest height, other hand on hip. Match draft atlas top-row cell 3. No props.
4. THINK: front, small 7-degree head tilt, one digit near the lower visor/chin, other forearm supports that elbow. Do not hide the eye strip. Match draft atlas top-row cell 4. No props.
BOTTOM ROW LEFT TO RIGHT:
5. STAMP-DOWN: downward strike with the EXACT original rubber stamp. Holding arm brought DOWN IN FRONT. Hand directly above the stamp's short dark handle, rectangular mint-and-dark base horizontal at HIP HEIGHT and pressing vertically down. Stamp must be in front of the pelvis at the waist/hip level, not dangling below the thigh. Slight knee bend; both boots remain planted. Free arm balances slightly. Use draft atlas bottom-row cell 1 for character and gesture, but bring the stamp base up to hip height and make downward pressure readable. No table, impact mark or motion line.
6. APPROVE: front, upright, small thumbs-up at chest height with the free hand, original stamp held down at the viewer-left side as in idle. Same single continuous mint visor strip gently curves upward at its ends, pleased. Match draft atlas bottom-row cell 2.
7. CONCERN: front, one palm facing outward in a polite stop gesture, slight lean backward, free hand down. Match draft atlas bottom-row cell 3. No props.
8. SHRUG: front, both elbows bent and both forearms raised out sideways, palms UP, shoulders slightly up, mild head tilt. Match draft atlas bottom-row cell 4. No props.

IDENTITY MUST MATCH IMAGE 1 EXACTLY: softly squared off-white head/crown, wide black inset rounded-rectangular visor, ONE continuous mint luminous eye strip (only approve curves it), mint narrow projecting accountant eyeshade with dark attachments, slim antenna with mint ball on the same viewer-left crown side, mint-edged dark circular ear hardware, original short rounded-rectangular chest, dark neck/waist, off-white pelvic shell, black joint construction, off-white forearms and mint cuff bands, familiar small segmented robot hands with off-white plates, off-white thigh/shin shells, compact original boots with dark soles and mint heel/ankle inserts. Match the head-to-body and chest-to-leg proportions of image 1. No bigger heads, no elongated bodies, no extra face features, no mouth, no chest marks or badges. Maintain original warm off-white and mint #3ddc97 colors and soft upper-left studio lighting, not a new material finish.

BACKGROUND: completely FLAT SOLID MAGENTA #FF00FF throughout every empty pixel, gaps, holes between limbs, between fingers, around all eight silhouettes. No gradients, ground plane, contact shadows, floor shadows, scene, haze or reflected pink. Every antenna, boot, hand and prop is fully visible with magenta margin. No overlap across cell boundaries. No text, letters, numbers, labels, logos, watermarks, borders, grid lines, panels, tick marks or decorative marks anywhere.
```

## Historical v2 scope and source

- Brief: `/Users/yan/note/dappgo/flow-atlas/hackathon-briefs/brief-auditor-robot.md`.
- Visual contract: `docs/site/STAMP-V2-DESIGN.md`, section 2.
- Built-in `image_gen` only for artwork; local deterministic cutting, chroma key, despill, trimming and encoding afterward.
- Four poses come from one sheet per variant, ordered left to right: **idle, inspect, present, stamp**.
- Raw source must be solid magenta #FF00FF without background shadows. All pose exports must have real alpha transparency.
- Requested ~512 px export height and <=120,000 bytes for each pose PNG and WebP. Apply one shared scale within a variant so raised arms and lean remain natural.
- Edit scope: `docs/site/img/auditor/**` and this file only. No commit or push. Existing untracked `.venv` and `docs/site/STAMP-V2-DESIGN.md` belong to the pre-existing workspace and are untouched.
- Governance discovery: Git remote `YanlongLai/market-claim-verifier` has no match in the DappGo developer registry or repository catalog; discovery is degraded and this neighboring hackathon repository is treated as outside the AI001 registered fleet.
- The brief explicitly requires one horizontal four-pose sheet, overriding the sprite skill's default multi-row, per-action generation guidance. The brief also explicitly requests local chroma-key/cutting postprocessing instead of generated native transparency.

## Exact generation prompts

Each prompt below is the exact `prompt` argument passed to the built-in tool. `transparent_background: false`; no input/reference images.

### Variant A

```text
Use case: stylized-concept.
Asset: a production character sheet for the Auditor robot on a financial fact-checking website.
Create ONE wide landscape character sheet, requested canvas 3072 x 1024 pixels, with exactly four full-body depictions of ONE IDENTICAL robot side by side in one horizontal row, no other characters. Four equal invisible cells. Left to right: idle, inspect, present, stamp. This is a single coherent character design in four poses, not four different robots.

Shared visual direction: clean modern 3D-ish editorial illustration, soft controlled shading, crisp precise edges, matte off-white body, mint #3ddc97 accents, dark navy #111a20 mechanical joints and ONE wide continuous dark visor eye with a single mint luminous horizontal eye surface, a small antenna, and a tiny mint accountant's eyeshade above the visor. Friendly and precise, quietly capable, not childish, not a baby toy. Small rounded three-digit robotic hands. No mouth, no human face. Restrained material detail. A balanced off-white silhouette with enough dark contour definition to sit beautifully on both dark navy #111a20 and warm off-white #f7f5ef.

POSES, exactly in this left-to-right order:
1. IDLE: standing calmly, right hand holding a rubber stamp down at its side. The rubber stamp has a dark handle and a clearly visible rectangular mint-and-dark base.
2. INSPECT: same robot leaning forward attentively from its hips, visor glowing mint, left hand raising a circular magnifying glass close to the visor. The glass is clear and reveals the background, dark thin rim with mint handle. Right hand relaxed near hip.
3. PRESENT: same robot holding up one blank off-white document page toward the viewer, at chest height to its left side, so the page is clearly visible and does not hide its visor. Page is completely blank: no words, no letters, no numbers, no logos, no simulated text.
4. STAMP: same robot with right arm raised mid-swing above its shoulder, holding the EXACT same rubber stamp as in idle, stamp base angled downward ready to strike. Clearly anticipatory energetic gesture, feet remain grounded, full tool and antenna visible.

Consistency contract: identical head shape and head width, visor geometry, eyeshade, antenna, torso, joint construction, colors, materials, hand design and foot design in all four poses. Fixed camera and fixed standing-equivalent anatomical scale across all four cells. Do not zoom any pose to fit. Keep a shared feet baseline near 85% of image height. Use the same soft upper-left studio lighting on every robot. Inspection leans but does not become a smaller model. Leave generous empty magenta space between the four silhouettes. Keep every limb, antenna, tool and page within its own cell with a safe margin. Nothing cropped. No ground plane.

BACKGROUND: perfectly flat SOLID MAGENTA #FF00FF everywhere outside the character silhouettes and props, including between feet and through the magnifying lens. Zero gradient, zero background texture, zero background shadows, zero floor or contact shadows, no reflected pink light on the robot. No scenery. No glow haze on the background; visor light is confined to its own surface. No text, labels, letters, numbers, logos, captions, borders, grid lines, panels or decorative marks anywhere.

VARIANT A — compact studio automaton. A broad horizontal pill-shaped head with softly beveled corners, distinctly wider than its short upright oval torso. One continuous panoramic visor inset into the head, a thin short mint eyeshade brim immediately above it, a single small centered antenna with a mint tip. Stubby rounded mechanical arms, visible dark elbow joints, two short legs with substantial rounded off-white boots and a mint sole stripe. Subtle mint shoulder rings and a small flush mint rectangular chest inset without markings. Silhouette is broad, compact, professional and calm.
```

### Variant B

```text
Use case: stylized-concept.
Asset: a production character sheet for the Auditor robot on a financial fact-checking website.
Create ONE wide landscape character sheet, requested canvas 3072 x 1024 pixels, with exactly four full-body depictions of ONE IDENTICAL robot side by side in one horizontal row, no other characters. Four equal invisible cells. Left to right: idle, inspect, present, stamp. This is a single coherent character design in four poses, not four different robots.

Shared visual direction: clean modern 3D-ish editorial illustration, soft controlled shading, crisp precise edges, matte off-white body, mint #3ddc97 accents, dark navy #111a20 mechanical joints and ONE wide continuous dark visor eye with a single mint luminous horizontal eye surface, a small antenna, and a tiny mint accountant's eyeshade above the visor. Friendly and precise, quietly capable, not childish, not a baby toy. Small rounded three-digit robotic hands. No mouth, no human face. Restrained material detail. A balanced off-white silhouette with enough dark contour definition to sit beautifully on both dark navy #111a20 and warm off-white #f7f5ef.

POSES, exactly in this left-to-right order:
1. IDLE: standing calmly, right hand holding a rubber stamp down at its side. The rubber stamp has a dark handle and a clearly visible rectangular mint-and-dark base.
2. INSPECT: same robot leaning forward attentively from its hips, visor glowing mint, left hand raising a circular magnifying glass close to the visor. The glass is clear and reveals the background, dark thin rim with mint handle. Right hand relaxed near hip.
3. PRESENT: same robot holding up one blank off-white document page toward the viewer, at chest height to its left side, so the page is clearly visible and does not hide its visor. Page is completely blank: no words, no letters, no numbers, no logos, no simulated text.
4. STAMP: same robot with right arm raised mid-swing above its shoulder, holding the EXACT same rubber stamp as in idle, stamp base angled downward ready to strike. Clearly anticipatory energetic gesture, feet remain grounded, full tool and antenna visible.

Consistency contract: identical head shape and head width, visor geometry, eyeshade, antenna, torso, joint construction, colors, materials, hand design and foot design in all four poses. Fixed camera and fixed standing-equivalent anatomical scale across all four cells. Do not zoom any pose to fit. Keep a shared feet baseline near 85% of image height. Use the same soft upper-left studio lighting on every robot. Inspection leans but does not become a smaller model. Leave generous empty magenta space between the four silhouettes. Keep every limb, antenna, tool and page within its own cell with a safe margin. Nothing cropped. No ground plane.

BACKGROUND: perfectly flat SOLID MAGENTA #FF00FF everywhere outside the character silhouettes and props, including between feet and through the magnifying lens. Zero gradient, zero background texture, zero background shadows, zero floor or contact shadows, no reflected pink light on the robot. No scenery. No glow haze on the background; visor light is confined to its own surface. No text, labels, letters, numbers, logos, captions, borders, grid lines, panels or decorative marks anywhere.

VARIANT B — precision desk clerk. A compact rounded-square head with a softly squared crown, a wide single rounded-rectangular visor across its front, a tiny mint accountant eyeshade with a narrow projecting brim and a slim dark band. A small antenna offset on the robot's left crown. A short rounded-rectangular matte off-white torso with a narrow dark waist coupling, fine mint cuff bands at the wrists, compact rounded-square boots with mint heel inserts. Slightly more upright than a pill robot but still compact and rounded, economical joints and a clean accurate instrument-like silhouette. No badges or markings.
```

### Variant C

```text
Use case: stylized-concept.
Asset: a production character sheet for the Auditor robot on a financial fact-checking website.
Create ONE wide landscape character sheet, requested canvas 3072 x 1024 pixels, with exactly four full-body depictions of ONE IDENTICAL robot side by side in one horizontal row, no other characters. Four equal invisible cells. Left to right: idle, inspect, present, stamp. This is a single coherent character design in four poses, not four different robots.

Shared visual direction: clean modern 3D-ish editorial illustration, soft controlled shading, crisp precise edges, matte off-white body, mint #3ddc97 accents, dark navy #111a20 mechanical joints and ONE wide continuous dark visor eye with a single mint luminous horizontal eye surface, a small antenna, and a tiny mint accountant's eyeshade above the visor. Friendly and precise, quietly capable, not childish, not a baby toy. Small rounded three-digit robotic hands. No mouth, no human face. Restrained material detail. A balanced off-white silhouette with enough dark contour definition to sit beautifully on both dark navy #111a20 and warm off-white #f7f5ef.

POSES, exactly in this left-to-right order:
1. IDLE: standing calmly, right hand holding a rubber stamp down at its side. The rubber stamp has a dark handle and a clearly visible rectangular mint-and-dark base.
2. INSPECT: same robot leaning forward attentively from its hips, visor glowing mint, left hand raising a circular magnifying glass close to the visor. The glass is clear and reveals the background, dark thin rim with mint handle. Right hand relaxed near hip.
3. PRESENT: same robot holding up one blank off-white document page toward the viewer, at chest height to its left side, so the page is clearly visible and does not hide its visor. Page is completely blank: no words, no letters, no numbers, no logos, no simulated text.
4. STAMP: same robot with right arm raised mid-swing above its shoulder, holding the EXACT same rubber stamp as in idle, stamp base angled downward ready to strike. Clearly anticipatory energetic gesture, feet remain grounded, full tool and antenna visible.

Consistency contract: identical head shape and head width, visor geometry, eyeshade, antenna, torso, joint construction, colors, materials, hand design and foot design in all four poses. Fixed camera and fixed standing-equivalent anatomical scale across all four cells. Do not zoom any pose to fit. Keep a shared feet baseline near 85% of image height. Use the same soft upper-left studio lighting on every robot. Inspection leans but does not become a smaller model. Leave generous empty magenta space between the four silhouettes. Keep every limb, antenna, tool and page within its own cell with a safe margin. Nothing cropped. No ground plane.

BACKGROUND: perfectly flat SOLID MAGENTA #FF00FF everywhere outside the character silhouettes and props, including between feet and through the magnifying lens. Zero gradient, zero background texture, zero background shadows, zero floor or contact shadows, no reflected pink light on the robot. No scenery. No glow haze on the background; visor light is confined to its own surface. No text, labels, letters, numbers, logos, captions, borders, grid lines, panels or decorative marks anywhere.

VARIANT C — quiet capsule auditor. A smoothly rounded oval capsule head, a wide single sweeping wraparound visor, a small mint accountant eyeshade projecting as a subtle curved brim above it, a delicate short central antenna with a tiny mint rounded tip. A compact softly pear-shaped off-white torso, clean ball-and-socket shoulders, restrained mint wrist collars, short sturdy legs and small oval off-white feet with a dark bottom edge and mint ankle accents. Understated mid-century office-appliance character, calm and exact, no bulky chest emblem, no markings.
```

## Generation and processing notes

Completed with three built-in `image_gen` calls, one per variant. A was generated and inspected first; B and C followed. There were no reference images, edit calls, or regeneration prompts. All exact generation prompts are preserved above. `transparent_background: false` was used for each source sheet, as required by the magenta workflow.

### Original sheets

The requested canvas was 3072 × 1024. The tool returned the dimensions below. `sheet-A.png`, `sheet-B.png`, and `sheet-C.png` are unchanged copies of the generated originals, verified by SHA-256. The originals remain in the built-in tool’s output directory. Although pure #FF00FF was requested, the generated backgrounds contain slight near-magenta variation; the measured RGB medians below were used for accurate matting. All such background variation is removed from the transparent exports.

| Variant | Source image in built-in output directory | Saved dimensions | Measured background RGB |
|---|---|---|---|
| A | `exec-11640cc2-79bc-434c-b304-6ec8d197bb74.png` | 2172 × 724 | 250, 4, 250 |
| B | `exec-24ade898-1e76-455c-a6ba-84619bf7210b.png` | 2172 × 724 | 251, 4, 250 |
| C | `exec-cb002e30-7e54-473a-a04f-c6aa8da9c2e9.png` | 2170 × 725 | 251, 4, 250 |

Built-in output directory: `/Users/yan/.codex/generated_images/01a18605-e1a2-75f1-9a7a-741a7bb2e8ee`.

### Deterministic processing

The reproducible processor is `docs/site/img/auditor/process-auditor.py`. It uses the existing worktree `.venv` (NumPy 2.5.4, Pillow 13.0.0) and the installed sprite skill’s `split_grid` primitive. No packages were installed and no environment files were changed.

```sh
.venv/bin/python docs/site/img/auditor/process-auditor.py
```

1. Measure the near-magenta matte from the outer 12-pixel border. Estimate soft alpha from red/blue excess over green, retain a two-pixel neighborhood of the reliable foreground core, and unmix the background RGB. This removes magenta spill and opens the magnifying glass.
2. Find the widest empty vertical gap near each quarter boundary. These adaptive cuts preserve complete silhouettes where the generated spacing differs slightly from an equal grid. Repack only existing cutouts into equal invisible cells for the sprite processor; do not redraw any art.
3. Run the sprite primitive with `rows=1`, `cols=4`, `cell_size=640`, `align=feet`, `shared_scale=True`, `component_mode=largest`, and `scale_strategy=preserve`. Use zero additional hard-key thresholds, border trimming or edge erosion because soft matting has already been applied. Derive one uniform source-to-output scale per variant from the tallest pose, targeting 508 pixels of content plus two transparent pixels of padding on every side.
4. Resize using Lanczos, despill again after resampling, and trim to the subject with the two-pixel safety border. Preserve natural differences in pose height; no individual pose is enlarged or reduced to normalize its bounding box.
5. Encode true-color RGBA PNG with optimized DEFLATE. Round RGB precision by the smallest integer step that satisfies the conservative 120,000-byte cap (steps 2–5 out of 255 in these assets), keeping the full eight-bit alpha channel. This preserves soft shading without an indexed palette. Encode the same pixel data as lossless WebP. Each PNG/WebP pair decodes identically.
6. Build one 1840 × 1320 contact preview per variant from the final WebP files: dark navy #111a20 above, warm off-white #f7f5ef below. Preview headings and pose labels are review annotations; the artwork and source sheets contain no text, numbers or logos.

The initial export check caught color spill after resampling. An initial indexed-palette compression experiment also flattened the shading in two A poses. Those trial exports were replaced by the final true-color workflow above; the temporary encoding comparison was removed. No additional creative generation prompts were used.

| Variant | Original x cut boundaries | Shared source-to-output scale | Final pose heights (idle / inspect / present / stamp) |
|---|---|---|---|
| A | 0, 470, 1072, 1644, 2172 | 0.826016260 | 509 / 493 / 510 / 512 px |
| B | 0, 516, 1098, 1643, 2172 | 0.793750000 | 512 / 502 / 510 / 510 px |
| C | 0, 503, 1085, 1627, 2170 | 0.759342302 | 501 / 478 / 498 / 512 px |

### Verification and consistency

- Visually inspected all three raw sheets and all three final contact previews on both backgrounds.
- **A: no character identity mismatch observed.** Broad pill head, centered antenna, chest inset, shoulder rings, boots and stamp design remain consistent.
- **B: no character identity mismatch observed.** Rounded-square head, offset antenna, narrow waist, mint cuffs and heel inserts remain consistent.
- **C: no character identity mismatch observed.** Oval head, curved eyeshade, pear torso, mint wrist/ankle accents and oval feet remain consistent. The stamp rotates naturally during the raised-arm wind-up.
- All 24 pose files are below 120,000 bytes. PNG: 104,736–119,522 bytes; WebP: 69,672–81,356 bytes. Heights are 478–512 pixels.
- All 24 pose files have alpha extrema 0–255, partially transparent contour pixels, a completely transparent outer border and zero detected pink-fringe pixels. The spill check flags red-and-blue excess over green greater than 18/255 at alpha above 32/255.
- No source-cell clipping, output-edge contact, empty frames or paste clamping was reported. Each variant uses exactly one anatomical scale for all four poses.
- Independently verified that all 12 PNG/WebP pairs decode to identical RGBA pixels, all three saved raw sheets match their built-in source hashes, and all 30 artwork hashes/sizes match `manifest.json`.
- Variant matching note: **none of the three variants has a detected mismatch between its four poses.** Tilt, stance, raised tools and trimmed dimensions differ intentionally by pose.
- All task-authored files are confined to the authorized image directory and this prompt log. Other workspace changes observed during the session were left untouched. No commit, push or website integration was performed.

## Files and sizes

All paths below are relative to `docs/site/img/auditor/`. KB uses 1,000 bytes. The <=120 KB cap applies to pose PNG and WebP files; source sheets and review contacts retain larger review-quality dimensions.

| File | Dimensions | Bytes | KB |
|---|---|---:|---:|
| [A/idle.png](../../site/img/auditor/A/idle.png) | 308 × 509 | 112,119 | 112.119 |
| [A/idle.webp](../../site/img/auditor/A/idle.webp) | 308 × 509 | 76,306 | 76.306 |
| [A/inspect.png](../../site/img/auditor/A/inspect.png) | 397 × 493 | 115,445 | 115.445 |
| [A/inspect.webp](../../site/img/auditor/A/inspect.webp) | 397 × 493 | 74,968 | 74.968 |
| [A/present.png](../../site/img/auditor/A/present.png) | 381 × 510 | 114,009 | 114.009 |
| [A/present.webp](../../site/img/auditor/A/present.webp) | 381 × 510 | 77,118 | 77.118 |
| [A/stamp.png](../../site/img/auditor/A/stamp.png) | 364 × 512 | 116,224 | 116.224 |
| [A/stamp.webp](../../site/img/auditor/A/stamp.webp) | 364 × 512 | 74,584 | 74.584 |
| [B/idle.png](../../site/img/auditor/B/idle.png) | 293 × 512 | 117,245 | 117.245 |
| [B/idle.webp](../../site/img/auditor/B/idle.webp) | 293 × 512 | 78,464 | 78.464 |
| [B/inspect.png](../../site/img/auditor/B/inspect.png) | 376 × 502 | 119,522 | 119.522 |
| [B/inspect.webp](../../site/img/auditor/B/inspect.webp) | 376 × 502 | 78,130 | 78.130 |
| [B/present.png](../../site/img/auditor/B/present.png) | 347 × 510 | 114,167 | 114.167 |
| [B/present.webp](../../site/img/auditor/B/present.webp) | 347 × 510 | 76,940 | 76.940 |
| [B/stamp.png](../../site/img/auditor/B/stamp.png) | 338 × 510 | 118,910 | 118.910 |
| [B/stamp.webp](../../site/img/auditor/B/stamp.webp) | 338 × 510 | 77,980 | 77.980 |
| [C/idle.png](../../site/img/auditor/C/idle.png) | 288 × 501 | 116,091 | 116.091 |
| [C/idle.webp](../../site/img/auditor/C/idle.webp) | 288 × 501 | 81,356 | 81.356 |
| [C/inspect.png](../../site/img/auditor/C/inspect.png) | 336 × 478 | 104,736 | 104.736 |
| [C/inspect.webp](../../site/img/auditor/C/inspect.webp) | 336 × 478 | 70,234 | 70.234 |
| [C/present.png](../../site/img/auditor/C/present.png) | 305 × 498 | 105,796 | 105.796 |
| [C/present.webp](../../site/img/auditor/C/present.webp) | 305 × 498 | 74,012 | 74.012 |
| [C/stamp.png](../../site/img/auditor/C/stamp.png) | 305 × 512 | 107,723 | 107.723 |
| [C/stamp.webp](../../site/img/auditor/C/stamp.webp) | 305 × 512 | 69,672 | 69.672 |
| [sheet-A.png](../../site/img/auditor/sheet-A.png) | 2172 × 724 | 1,582,594 | 1582.594 |
| [sheet-B.png](../../site/img/auditor/sheet-B.png) | 2172 × 724 | 1,597,506 | 1597.506 |
| [sheet-C.png](../../site/img/auditor/sheet-C.png) | 2170 × 725 | 1,538,932 | 1538.932 |
| [variant-A-preview.png](../../site/img/auditor/variant-A-preview.png) | 1840 × 1320 | 907,518 | 907.518 |
| [variant-B-preview.png](../../site/img/auditor/variant-B-preview.png) | 1840 × 1320 | 909,636 | 909.636 |
| [variant-C-preview.png](../../site/img/auditor/variant-C-preview.png) | 1840 × 1320 | 838,677 | 838.677 |
| [manifest.json](../../site/img/auditor/manifest.json) | supporting file | 18,665 | 18.665 |
| [process-auditor.py](../../site/img/auditor/process-auditor.py) | supporting file | 12,519 | 12.519 |

Total: **30 artwork files** (3 raw sheets + 24 transparent pose exports + 3 dual-background review previews), plus the reproducible processor and machine-readable verification manifest. The exact prompt set and full processing/review notes are this document.


## v3 cute candidates

Owner brief: 「機器人請再可愛一點，多做幾個讓我選」. Five independent candidate characters for selection; no page integration, no B asset replacement, no commit or push. Built-in `image_gen` creates four-pose magenta sheets; local processing only keys, despills, cuts, scales and encodes the generated artwork, then adds review labels. Pose order: `idle`, `inspect`, `stamp-down`, `approve`.

The worktree is `market-claim-verifier-stamp2`, branch `site/stamp-v2`. Existing changes are preserved. Repository remote is not matched in the DappGo developer registry; this is a local, bounded asset task. All task files are under `docs/site/img/auditor/candidates-v3/`, plus this appended section. Candidate design and expressions must be judged at 72 px as well as enlarged.

### Exact initial generation prompts

#### 1 Chibi B

Reference image (design and original identity only): `docs/site/img/auditor/B/idle.webp`.

Tool: built-in `image_gen`; `transparent_background: false` (explicit solid magenta brief).

```text
Create one polished 3D mascot character pose sheet for an auditor website, on a completely flat solid chroma-key magenta #FF00FF background. Wide landscape sheet, approximately 3:1 aspect ratio. Exactly FOUR full-body views of ONE IDENTICAL character in a SINGLE horizontal row, left to right, with four equal-width invisible cells. Leave generous clear magenta gaps between poses and padding around all extremities. Same camera, same anatomical scale, same materials and character construction in all four views. Near-front gentle three-quarter view. All parts, antennae, tools and action gestures entirely inside their own cell.

BRAND AND TONE: extremely cute chibi proportions, oversized expressive head, compact body, soft pillowy rounded edges and tiny simple mitten hands. A friendly, observant, careful professional auditor with a little personality. Calm competence with cheerful expressions. Matte warm off-white shell, mint #3ddc97 accents, dark navy #111a20 visor and details. Smooth clean softly modeled 3D forms, broad simple surfaces, few large readable details. A tiny mint accountant's eyeshade with a short projecting visor is clearly attached above the face in every pose. The digital screen face has only TWO LARGE glowing mint dot eyes; they change shape for expression. Use eyes, head tilt and gesture for expression; no mouth needed. Design must remain readable at only 72 pixels tall. Stubby limbs, no long adult legs or fingers, no exposed complex joints, no intricate machinery. Each pose includes the same small rubber stamp with mint handle/collar and a dark navy rectangular rubber base; the rubber stamp must be visibly held, not floating.

FOUR POSES IN EXACT LEFT-TO-RIGHT ORDER:
1. IDLE: upright relaxed attentive posture, two big round glowing dot eyes, holding the little rubber stamp down beside the body.
2. INSPECT: leaning forward a little with focused curious eyes, holding one simple navy-rimmed magnifying glass in one hand while keeping the rubber stamp in the other hand. Keep the face legible.
3. STAMP-DOWN: a decisive downward stamping strike; the hand grips the stamp firmly against an imaginary flat surface at the feet/bottom level. Body leans into the action, eyes are two clear squeezed chevrons > < conveying cute effort. Keep the stamp visible. No impact symbols, no drawn lines, no extra stamp copies.
4. APPROVE: happy glowing eyes shaped ^ ^, a clear little thumbs-up with one mitten hand and the same rubber stamp held in the other, a delighted but careful little auditor.

BACKGROUND/EXCLUSIONS: background is pure uniform #FF00FF edge to edge, including all gaps. NO shadows on the background, NO ground or contact shadows, no floor, no horizon, no platforms apart from the character's own body, no gradients in the background, no text, letters, numerals, digits, logos, watermarks, dividers, labels, checkmarks, speech bubbles or decorative symbols. Do not paint any magenta or pink on the character. Gentle surface shading is allowed only on the character itself. Exactly four separated poses, not a collage or a multi-row grid.

CHARACTER: CHIBI B. The supplied image is a design-reference source, not artwork to copy at its existing adult proportions. Redesign that same auditor robot to be MUCH cuter. Preserve its rounded-square off-white head, dark rounded-rectangle visor, mint accountant eyeshade, circular mint-trimmed ear discs and a single offset thin antenna with round mint tip on the robot's right (viewer-left). Replace the single horizontal eye bar with TWO BIG DISTINCT luminous dot eyes. Make the head approximately 1.3 times the height of the torso-and-hip body combined, and wider than the entire tiny torso. The combined stubby legs and feet are shorter than half the head height. Neck almost hidden. Tiny rounded bean torso, short pill arms, simple little boots, reduced navy joints. The silhouette is top-heavy and rounded, not tall, muscular, stiff or adult. Keep exactly this construction in all four poses.
```

#### 2 Calc

Fresh generation; no image reference.

Tool: built-in `image_gen`; `transparent_background: false` (explicit solid magenta brief).

```text
Create one polished 3D mascot character pose sheet for an auditor website, on a completely flat solid chroma-key magenta #FF00FF background. Wide landscape sheet, approximately 3:1 aspect ratio. Exactly FOUR full-body views of ONE IDENTICAL character in a SINGLE horizontal row, left to right, with four equal-width invisible cells. Leave generous clear magenta gaps between poses and padding around all extremities. Same camera, same anatomical scale, same materials and character construction in all four views. Near-front gentle three-quarter view. All parts, antennae, tools and action gestures entirely inside their own cell.

BRAND AND TONE: extremely cute chibi proportions, oversized expressive head, compact body, soft pillowy rounded edges and tiny simple mitten hands. A friendly, observant, careful professional auditor with a little personality. Calm competence with cheerful expressions. Matte warm off-white shell, mint #3ddc97 accents, dark navy #111a20 visor and details. Smooth clean softly modeled 3D forms, broad simple surfaces, few large readable details. A tiny mint accountant's eyeshade with a short projecting visor is clearly attached above the face in every pose. The digital screen face has only TWO LARGE glowing mint dot eyes; they change shape for expression. Use eyes, head tilt and gesture for expression; no mouth needed. Design must remain readable at only 72 pixels tall. Stubby limbs, no long adult legs or fingers, no exposed complex joints, no intricate machinery. Each pose includes the same small rubber stamp with mint handle/collar and a dark navy rectangular rubber base; the rubber stamp must be visibly held, not floating.

FOUR POSES IN EXACT LEFT-TO-RIGHT ORDER:
1. IDLE: upright relaxed attentive posture, two big round glowing dot eyes, holding the little rubber stamp down beside the body.
2. INSPECT: leaning forward a little with focused curious eyes, holding one simple navy-rimmed magnifying glass in one hand while keeping the rubber stamp in the other hand. Keep the face legible.
3. STAMP-DOWN: a decisive downward stamping strike; the hand grips the stamp firmly against an imaginary flat surface at the feet/bottom level. Body leans into the action, eyes are two clear squeezed chevrons > < conveying cute effort. Keep the stamp visible. No impact symbols, no drawn lines, no extra stamp copies.
4. APPROVE: happy glowing eyes shaped ^ ^, a clear little thumbs-up with one mitten hand and the same rubber stamp held in the other, a delighted but careful little auditor.

BACKGROUND/EXCLUSIONS: background is pure uniform #FF00FF edge to edge, including all gaps. NO shadows on the background, NO ground or contact shadows, no floor, no horizon, no platforms apart from the character's own body, no gradients in the background, no text, letters, numerals, digits, logos, watermarks, dividers, labels, checkmarks, speech bubbles or decorative symbols. Do not paint any magenta or pink on the character. Gentle surface shading is allowed only on the character itself. Exactly four separated poses, not a collage or a multi-row grid.

CHARACTER: CALC. A tiny boxy pocket-calculator robot with a very large soft rounded-square upper head/screen and a smaller short calculator-keypad belly. The upper screen/head occupies about 60 percent of the entire character height, with two enormous simple mint dot eyes on a navy face screen. A tiny mint accountant's eyeshade clips to the top of the screen bezel. Below it, a compact belly has exactly SIX broad blank rounded-square off-white keys, in two rows of three, on a subtle mint recessed panel. All keys are completely blank, without numbers, letters or icons. These six keys and their layout stay identical in every pose. Short mint-trimmed feet and tiny side mitten arms attach to the compact calculator body. No antenna, no ears, no tail. Very low rounded calculator silhouette, readable broad keys, no complicated gadgets. It is an embodied auditor character rather than an ordinary inanimate calculator. Keep exactly this construction in all four poses.
```

#### 3 Hover

Fresh generation; no image reference.

Tool: built-in `image_gen`; `transparent_background: false` (explicit solid magenta brief).

```text
Create one polished 3D mascot character pose sheet for an auditor website, on a completely flat solid chroma-key magenta #FF00FF background. Wide landscape sheet, approximately 3:1 aspect ratio. Exactly FOUR full-body views of ONE IDENTICAL character in a SINGLE horizontal row, left to right, with four equal-width invisible cells. Leave generous clear magenta gaps between poses and padding around all extremities. Same camera, same anatomical scale, same materials and character construction in all four views. Near-front gentle three-quarter view. All parts, antennae, tools and action gestures entirely inside their own cell.

BRAND AND TONE: extremely cute chibi proportions, oversized expressive head, compact body, soft pillowy rounded edges and tiny simple mitten hands. A friendly, observant, careful professional auditor with a little personality. Calm competence with cheerful expressions. Matte warm off-white shell, mint #3ddc97 accents, dark navy #111a20 visor and details. Smooth clean softly modeled 3D forms, broad simple surfaces, few large readable details. A tiny mint accountant's eyeshade with a short projecting visor is clearly attached above the face in every pose. The digital screen face has only TWO LARGE glowing mint dot eyes; they change shape for expression. Use eyes, head tilt and gesture for expression; no mouth needed. Design must remain readable at only 72 pixels tall. Stubby limbs, no long adult legs or fingers, no exposed complex joints, no intricate machinery. Each pose includes the same small rubber stamp with mint handle/collar and a dark navy rectangular rubber base; the rubber stamp must be visibly held, not floating.

FOUR POSES IN EXACT LEFT-TO-RIGHT ORDER:
1. IDLE: upright relaxed attentive posture, two big round glowing dot eyes, holding the little rubber stamp down beside the body.
2. INSPECT: leaning forward a little with focused curious eyes, holding one simple navy-rimmed magnifying glass in one hand while keeping the rubber stamp in the other hand. Keep the face legible.
3. STAMP-DOWN: a decisive downward stamping strike; the hand grips the stamp firmly against an imaginary flat surface at the feet/bottom level. Body leans into the action, eyes are two clear squeezed chevrons > < conveying cute effort. Keep the stamp visible. No impact symbols, no drawn lines, no extra stamp copies.
4. APPROVE: happy glowing eyes shaped ^ ^, a clear little thumbs-up with one mitten hand and the same rubber stamp held in the other, a delighted but careful little auditor.

BACKGROUND/EXCLUSIONS: background is pure uniform #FF00FF edge to edge, including all gaps. NO shadows on the background, NO ground or contact shadows, no floor, no horizon, no platforms apart from the character's own body, no gradients in the background, no text, letters, numerals, digits, logos, watermarks, dividers, labels, checkmarks, speech bubbles or decorative symbols. Do not paint any magenta or pink on the character. Gentle surface shading is allowed only on the character itself. Exactly four separated poses, not a collage or a multi-row grid.

CHARACTER: HOVER. A round floating egg/ball auditor robot. Almost the entire body is one very large smooth plump off-white egg with a huge dark navy screen face on the upper front; the screen has two enormous luminous mint dot eyes. A tiny mint accountant's eyeshade clips just above that screen. One short offset antenna with a mint round tip grows from the top. Two tiny mitten arms emerge from the sides of the egg. The large egg is both the head and the compact body; no separate torso. NO legs and NO feet in any pose. The underside has one small mint thruster nozzle and a short compact mint exhaust glow immediately beneath it. The exhaust is confined to a small clean mint teardrop shape with no magenta, long rays or diffuse haze; no glow spills onto the background. It hovers consistently a little above the imaginary ground. In the downward stamping pose the little arm reaches down so the held stamp reaches that imaginary ground while the egg still floats. Keep exactly this construction in all four poses.
```

#### 4 Neko

Fresh generation; no image reference.

Tool: built-in `image_gen`; `transparent_background: false` (explicit solid magenta brief).

```text
Create one polished 3D mascot character pose sheet for an auditor website, on a completely flat solid chroma-key magenta #FF00FF background. Wide landscape sheet, approximately 3:1 aspect ratio. Exactly FOUR full-body views of ONE IDENTICAL character in a SINGLE horizontal row, left to right, with four equal-width invisible cells. Leave generous clear magenta gaps between poses and padding around all extremities. Same camera, same anatomical scale, same materials and character construction in all four views. Near-front gentle three-quarter view. All parts, antennae, tools and action gestures entirely inside their own cell.

BRAND AND TONE: extremely cute chibi proportions, oversized expressive head, compact body, soft pillowy rounded edges and tiny simple mitten hands. A friendly, observant, careful professional auditor with a little personality. Calm competence with cheerful expressions. Matte warm off-white shell, mint #3ddc97 accents, dark navy #111a20 visor and details. Smooth clean softly modeled 3D forms, broad simple surfaces, few large readable details. A tiny mint accountant's eyeshade with a short projecting visor is clearly attached above the face in every pose. The digital screen face has only TWO LARGE glowing mint dot eyes; they change shape for expression. Use eyes, head tilt and gesture for expression; no mouth needed. Design must remain readable at only 72 pixels tall. Stubby limbs, no long adult legs or fingers, no exposed complex joints, no intricate machinery. Each pose includes the same small rubber stamp with mint handle/collar and a dark navy rectangular rubber base; the rubber stamp must be visibly held, not floating.

FOUR POSES IN EXACT LEFT-TO-RIGHT ORDER:
1. IDLE: upright relaxed attentive posture, two big round glowing dot eyes, holding the little rubber stamp down beside the body.
2. INSPECT: leaning forward a little with focused curious eyes, holding one simple navy-rimmed magnifying glass in one hand while keeping the rubber stamp in the other hand. Keep the face legible.
3. STAMP-DOWN: a decisive downward stamping strike; the hand grips the stamp firmly against an imaginary flat surface at the feet/bottom level. Body leans into the action, eyes are two clear squeezed chevrons > < conveying cute effort. Keep the stamp visible. No impact symbols, no drawn lines, no extra stamp copies.
4. APPROVE: happy glowing eyes shaped ^ ^, a clear little thumbs-up with one mitten hand and the same rubber stamp held in the other, a delighted but careful little auditor.

BACKGROUND/EXCLUSIONS: background is pure uniform #FF00FF edge to edge, including all gaps. NO shadows on the background, NO ground or contact shadows, no floor, no horizon, no platforms apart from the character's own body, no gradients in the background, no text, letters, numerals, digits, logos, watermarks, dividers, labels, checkmarks, speech bubbles or decorative symbols. Do not paint any magenta or pink on the character. Gentle surface shading is allowed only on the character itself. Exactly four separated poses, not a collage or a multi-row grid.

CHARACTER: NEKO. A tiny cat-inspired auditor ROBOT, with a very large rounded-square off-white head at least 1.3 times the height of its little bean torso, a broad navy face screen with two enormous glowing mint dot eyes, and TWO SMALL ROUNDED CAT-EAR PANELS attached to the top corners. Ear panels are soft blunt triangles with mint inner panels, mechanically part of the shell, not furry ears. The tiny mint accountant's eyeshade sits just above the screen, between the ears. Short pill arms, tiny rounded mint-trimmed boot feet, no exposed complex joints. One short dark navy tail cable curls in a simple open hook beside/behind the body with a small mint rounded end cap; it stays clearly readable against the background and present in all four poses. No whiskers, no fur, no paw prints, no animal nose, no extra antenna. Friendly careful auditor first, cat-ear charm second. Keep exactly this construction in all four poses.
```

#### 5 Stampy

Fresh generation; no image reference.

Tool: built-in `image_gen`; `transparent_background: false` (explicit solid magenta brief).

```text
Create one polished 3D mascot character pose sheet for an auditor website, on a completely flat solid chroma-key magenta #FF00FF background. Wide landscape sheet, approximately 3:1 aspect ratio. Exactly FOUR full-body views of ONE IDENTICAL character in a SINGLE horizontal row, left to right, with four equal-width invisible cells. Leave generous clear magenta gaps between poses and padding around all extremities. Same camera, same anatomical scale, same materials and character construction in all four views. Near-front gentle three-quarter view. All parts, antennae, tools and action gestures entirely inside their own cell.

BRAND AND TONE: extremely cute chibi proportions, oversized expressive head, compact body, soft pillowy rounded edges and tiny simple mitten hands. A friendly, observant, careful professional auditor with a little personality. Calm competence with cheerful expressions. Matte warm off-white shell, mint #3ddc97 accents, dark navy #111a20 visor and details. Smooth clean softly modeled 3D forms, broad simple surfaces, few large readable details. A tiny mint accountant's eyeshade with a short projecting visor is clearly attached above the face in every pose. The digital screen face has only TWO LARGE glowing mint dot eyes; they change shape for expression. Use eyes, head tilt and gesture for expression; no mouth needed. Design must remain readable at only 72 pixels tall. Stubby limbs, no long adult legs or fingers, no exposed complex joints, no intricate machinery. Each pose includes the same small rubber stamp with mint handle/collar and a dark navy rectangular rubber base; the rubber stamp must be visibly held, not floating.

FOUR POSES IN EXACT LEFT-TO-RIGHT ORDER:
1. IDLE: upright relaxed attentive posture, two big round glowing dot eyes, holding the little rubber stamp down beside the body.
2. INSPECT: leaning forward a little with focused curious eyes, holding one simple navy-rimmed magnifying glass in one hand while keeping the rubber stamp in the other hand. Keep the face legible.
3. STAMP-DOWN: a decisive downward stamping strike; the hand grips the stamp firmly against an imaginary flat surface at the feet/bottom level. Body leans into the action, eyes are two clear squeezed chevrons > < conveying cute effort. Keep the stamp visible. No impact symbols, no drawn lines, no extra stamp copies.
4. APPROVE: happy glowing eyes shaped ^ ^, a clear little thumbs-up with one mitten hand and the same rubber stamp held in the other, a delighted but careful little auditor.

BACKGROUND/EXCLUSIONS: background is pure uniform #FF00FF edge to edge, including all gaps. NO shadows on the background, NO ground or contact shadows, no floor, no horizon, no platforms apart from the character's own body, no gradients in the background, no text, letters, numerals, digits, logos, watermarks, dividers, labels, checkmarks, speech bubbles or decorative symbols. Do not paint any magenta or pink on the character. Gentle surface shading is allowed only on the character itself. Exactly four separated poses, not a collage or a multi-row grid.

CHARACTER: STAMPY. The robot's whole BODY IS A RUBBER STAMP. Its oversized handle-shaped head is a broad soft off-white mushroom/pear-shaped stamp handle with a navy rounded face screen on its front and TWO BIG glowing mint dot eyes. The head/handle occupies about 60 percent of the total character height. A tiny mint accountant's eyeshade projects over the face screen from the top of the handle. The handle narrows into one very short off-white stem that connects directly to a wide soft rounded-rectangular mint stamp base with a navy rubber sole. The broad stamp base IS its feet; absolutely no separate legs, shoes, humanoid torso or belly. Two very short off-white mitten arms emerge from the narrow neck just above the mint base. In addition to BEING a stamp-shaped robot it holds one separate miniature handheld rubber stamp in its hand for each of the specified gestures. This little tool is clearly smaller than its own body. The screen must be large and charming; it should unmistakably read as a living rubber-stamp auditor rather than a robot standing on a platform. Keep exactly this construction in all four poses.
```

### Saved sheets and export files

Each folder contains exactly one untouched built-in source sheet, `sheet.png`, and the four transparent pose exports `idle.webp`, `inspect.webp`, `stamp-down.webp`, `approve.webp`:

| Candidate | Folder under `docs/site/img/auditor/candidates-v3/` | Built-in source filename |
|---|---|---|
| 1 Chibi B | `1-chibi-b/` | `exec-ab8e3589-b8fa-41ed-9611-db27509a891b.png` |
| 2 Calc | `2-calc/` | `exec-a13392ce-8c90-4830-811e-1ceb1a28395e.png` |
| 3 Hover | `3-hover/` | `exec-22340481-ce19-4b1d-9f4e-43e73552f1c7.png` |
| 4 Neko | `4-neko/` | `exec-f4e2b609-78b9-40d0-9b6e-1cf04d958b8b.png` |
| 5 Stampy | `5-stampy/` | `exec-55cec505-83b3-470b-9375-e9a14ae62649.png` |

All built-in originals are in `/Users/yan/.codex/generated_images/01a18852-6d47-7d72-8338-a2fcf68f51bb/`. Their local copies were compared byte for byte; source dimensions and SHA-256 hashes are recorded in [manifest.json](../../site/img/auditor/candidates-v3/manifest.json). There was one generation call per candidate, no retries or additional model edits. Only Chibi B supplied the existing `B/idle.webp` as a design reference. All five exact tool prompts appear above and also in [generation-requests.json](../../site/img/auditor/candidates-v3/generation-requests.json).

The review artifact is [contact.png](../../site/img/auditor/candidates-v3/contact.png): **2400 × 1684**, five labelled rows, warm **#f7f5ef** left half and navy **#111a20** right half. Both halves show all four poses and an idle preview with an actual **72 px alpha-content height**. View at 100% to judge that phone scale; an automatically fitted viewer may shrink the entire contact. All labels are rendered locally with Arial, never generated by the image model.

There are **29 files** in the candidate directory: **20 transparent WebP poses, 5 raw sheets, 1 contact PNG**, plus the reproducible processor, manifest and generation requests.

### Local processing and measured checks

Run from this worktree:

```sh
.venv/bin/python docs/site/img/auditor/candidates-v3/process-candidates.py
```

[process-candidates.py](../../site/img/auditor/candidates-v3/process-candidates.py) adapts the existing `process-auditor.py` approach: measure border magenta, estimate alpha from red/blue excess over green, keep the soft contour near foreground cores, unmix the matte, remove magenta spill, find clear vertical gaps, and crop the four generated poses. It does not draw or repaint any character parts.

Each candidate uses **one common uniform scale** for all four poses, not independent per-pose fitting. All exports use a **576 × 512 transparent canvas**, centered horizontally, with an exclusive alpha bottom at **y=500**. Actual art heights are **440–488 px**, with lower crouching poses kept naturally shorter. This is shared-scale artwork on a roughly 512 px-tall export, not an animation rig with exactly locked head geometry.

- All 20 exports decode as RGBA, have alpha extrema **0–255**, retain soft partially transparent contours, and have fully transparent outer borders.
- Lossless WebP decoding was compared to the RGBA pixels before encoding. Export file sizes are **102,416–159,430 bytes**, **2,734,878 bytes total**.
- All source cells have clearance around the generated artwork; no cell-edge clipping or paste clamping was reported.
- All 20 outputs have **zero detected pink-fringe pixels**, using red-and-blue excess over green >18/255 at alpha >32/255. A second despill after LANCZOS resampling removes interpolation spill. Magnifying glass interiors remain softly translucent rather than retaining the magenta matte.
- All 20 saved pose hashes match the manifest; all five copied sheets match their built-in originals. All ten small contact previews have actual 72 px alpha-content bounds.
- Visual QA covered the full contact and a separate native-size 72 px idle strip on both backgrounds. No background/ground shadows, model text, digits, logos, added limbs or wrong pose ordering were observed.

### Per-candidate review and consistency limitations

| Candidate | What works | Weakness / consistency observations |
|---|---|---|
| **1 Chibi B** | The strongest continuity with B: rounded-square head, offset antenna, circular ear discs and eyeshade. Big dot eyes and oversized head are much friendlier. | The least soft of these five: segmented gloves, hips and navy joints still create mechanical detail at 72 px. Its source poses retain small perspective/proportion variations; it is not a rigid 3D turntable. |
| **2 Calc** | Clearest accounting identity, simple mitten hands, short legs and six consistently blank keys. Face and keypad remain readable at 72 px. | The keypad adds visual density; inspect is expressed mostly through the lean and magnifier, while the eyes remain round rather than visibly narrowed. No material identity mismatch was observed across its four poses. |
| **3 Hover** | Simple, distinctive floating egg silhouette; no legs. Big face, short antenna and tiny mint thruster survive the 72 px test. | The thruster is partly occluded by the stamping arm/tool in stamp-down, so the float cue is weaker in that pose. Inspection also keeps round eyes; the glass partially crosses the face. |
| **4 Neko** | Softest, most immediately cute character. Rounded ear panels and tail cable distinguish it even at phone scale; both ears and the chest accent persist. | Approve changes the stamp to the opposite hand and the tail swings to the other side. This is acceptable for selection art but would need a handedness decision if made into a continuous animation. The ears are a stronger playful cue than an accounting cue. |
| **5 Stampy** | Most ownable silhouette: the handle/head, narrow stem and broad mint rubber-stamp base form the body. No separate feet/legs; it also visibly holds a separate little stamp. | Weaker as an expressive moving robot: the stem is longer than the intended tiny neck and can read as a pedestal at 72 px. In stamp-down, the handheld stamp overlaps its own base, reducing tool separation. More memorable as a stamp character than as a nimble auditor. |

All five visibly share off-white shells, mint accents/eyeshades and navy screen faces, with round idle eyes, effort chevrons and happy approval eyes. The rendered mint varies with the 3D surface lighting, so it is not a flat color chip everywhere. Inspection focus is communicated mainly by body lean, gaze toward the magnifier and the tool itself, not a separately drawn squint. Small head-angle, tool-angle and highlight variations remain within each generated sheet. These are honest selection candidates, not approved animation-ready masters.

For the Owner's first comparison, **Calc** best communicates the job and **Neko** best answers the request for extra cuteness. **Chibi B** is the conservative continuity option; **Hover** is the clean silhouette option; **Stampy** is the more experimental object-character option.

### Scope verification

Task-authored changes are confined to `docs/site/img/auditor/candidates-v3/**` and this appended `v3 cute candidates` section. Existing prompt-log content was preserved. The protected-file baseline covered 7,847 existing files; B artwork retains its baseline hashes. Concurrent changes to `docs/site/STAMP-V2-DESIGN.md` and later `docs/site/index.html` were observed during verification; this task did not edit or revert either file. Other sessions may continue updating this shared worktree, so the baseline is observation evidence, not a claim that the entire worktree is frozen. No candidate paths are referenced by the page or its existing build script at final inspection. No commit, push or page integration was performed.


## v3 Hover — final

Owner selected candidate 3, Hover. Built-in `image_gen` edited the supplied candidate images for each pose. Every exact call is below, including the three stamp-height corrections. All calls used `transparent_background=false`: pure magenta was keyed and despilled locally. Source originals and the geometry-only stamp-height guide are retained in `docs/site/img/auditor/H/source/`. The final strike uses `stamp-down-final.png`; earlier strike attempts are provenance only.

### Runtime contract and reuse

Run `.venv/bin/python docs/site/img/auditor/H/process-hover.py`. All eleven 1254×1254 body originals use exactly **0.5×** scale and translation only, on **704×744** canvases. Every nozzle outlet is **(352, 520)**. The manifest records source coordinates, translations, decoded alpha bboxes, per-pose visor/nozzle anchors, bytes and SHA-256. No pose is fitted independently. Flame frames are a separate 160×160 alpha layer with root **(80, 20)**: the six source cells use one 0.30× FX scale, and the larger burst master uses 0.125×. At runtime the burst also scales **1.6× for 250 ms**. Straight alpha compositing keeps the mint core readable on both themes. No screen blend is needed.

The final strike stamp is outside the body, to its right before mirroring. Its contact edge is within four image pixels of the nozzle baseline (about 1 px on desktop and half a pixel on phones), and the central exhaust corridor is empty. The body has no flame, shadow, impact, or motion trail baked in. Round eyes mark neutral poses, happy carets approval, and effort chevrons wind-up, strike, and concern. Inspect has a clear magnifier; reach a blank tab; present a blank page.

`H/contact.png` composites the body and separate jet on ivory and navy, includes an actual 88 px phone preview, and shows six stamp-down/recoil samples on each theme. These are generated sprites, not independently hand-redrawn poses; small natural changes of body tilt and highlights remain. B and all selection candidates are preserved.

### Exact call 1: idle

Reference/edit inputs: `docs/site/img/auditor/candidates-v3/3-hover/idle.webp`, `docs/site/img/auditor/candidates-v3/3-hover/stamp-down.webp`, `docs/site/img/auditor/candidates-v3/3-hover/sheet.png`. Retained output: `H/source/idle.png`.

```text
Create ONE production 2D sprite of the EXACT selected candidate-3 Hover robot in the provided reference images. This is an edit of that identical character, not a redesign. Match its toy-like softly shaded off-white spherical egg body, broad glossy navy-black face screen, thick curved mint green eyebrow/cap brim, one short navy bent antenna with mint ball, circular navy/mint earpiece, tiny mitten arms, no legs or feet, mint-rimmed flat bottom nozzle, and dark navy rubber stamp with mint handle when requested. Preserve the proportions, face size, mint colors, materials, and camera of the reference. The face is the only face; do not add mouth or nose. Clean shapes readable when the sprite is 88px wide.
IMPORTANT layer separation: REMOVE ALL thruster flame, exhaust, luminous jet, floating droplets, underbody glow, cast floor shadow, motion trail, sparks and impact effects from this character sprite. The bottom is ONLY a clean flat mint-rimmed nozzle with a dark opening. No green pointed shape beneath it. The nozzle must be fully visible with open magenta space directly below, including the stamping pose.
Output exactly one square 1024x1024 image. Opaque perfectly flat solid #FF00FF magenta background, no transparency/checkerboard, no gradients or background shading. All character pixels confined to x=110..910 and y=105..800, with generous blank padding. Use exactly the same anatomical scale and camera distance for every pose: spherical body width about 570px, crown to nozzle about 570px, antenna tip around y=105; nozzle outlet center at x=512, y=800, horizontal flat nozzle baseline y=800. The body centerline is x=512. Do not fit or zoom the figure based on the hands or tools; extra tools extend sideways in the padding. Complete silhouette inside canvas. No lettering, text, labels, borders, numbers, UI or scenery. Do not replicate the reference contact sheet.

POSE: IDLE. Front view with the slight friendly 3/4 right camera of the reference idle. Two large round mint dot eyes • •. Relaxed tiny arms. Viewer-left hand casually holds its small navy rectangular rubber stamp, mint handle, beside the body; right arm relaxed. Neutral calm attention. Flat empty nozzle fully visible.
```

### Exact call 2: inspect

Reference/edit inputs: `docs/site/img/auditor/candidates-v3/3-hover/idle.webp`, `docs/site/img/auditor/candidates-v3/3-hover/stamp-down.webp`, `docs/site/img/auditor/candidates-v3/3-hover/sheet.png`. Retained output: `H/source/inspect.png`.

```text
Create ONE production 2D sprite of the EXACT selected candidate-3 Hover robot in the provided reference images. This is an edit of that identical character, not a redesign. Match its toy-like softly shaded off-white spherical egg body, broad glossy navy-black face screen, thick curved mint green eyebrow/cap brim, one short navy bent antenna with mint ball, circular navy/mint earpiece, tiny mitten arms, no legs or feet, mint-rimmed flat bottom nozzle, and dark navy rubber stamp with mint handle when requested. Preserve the proportions, face size, mint colors, materials, and camera of the reference. The face is the only face; do not add mouth or nose. Clean shapes readable when the sprite is 88px wide.
IMPORTANT layer separation: REMOVE ALL thruster flame, exhaust, luminous jet, floating droplets, underbody glow, cast floor shadow, motion trail, sparks and impact effects from this character sprite. The bottom is ONLY a clean flat mint-rimmed nozzle with a dark opening. No green pointed shape beneath it. The nozzle must be fully visible with open magenta space directly below, including the stamping pose.
Output exactly one square 1024x1024 image. Opaque perfectly flat solid #FF00FF magenta background, no transparency/checkerboard, no gradients or background shading. All character pixels confined to x=110..910 and y=105..800, with generous blank padding. Use exactly the same anatomical scale and camera distance for every pose: spherical body width about 570px, crown to nozzle about 570px, antenna tip around y=105; nozzle outlet center at x=512, y=800, horizontal flat nozzle baseline y=800. The body centerline is x=512. Do not fit or zoom the figure based on the hands or tools; extra tools extend sideways in the padding. Complete silhouette inside canvas. No lettering, text, labels, borders, numbers, UI or scenery. Do not replicate the reference contact sheet.

POSE: INSPECT. Slight 3/4 RIGHT view. Two neutral round mint eyes • • watching through a navy-rimmed magnifying glass held in the viewer-right hand beside, not covering, the face. Magnifier lens is clear/simple pale transparent glass. Viewer-left hand holds the little mint-handled navy stamp down by its side. Flat empty nozzle fully visible.
```

### Exact call 3: reach

Reference/edit inputs: `docs/site/img/auditor/candidates-v3/3-hover/idle.webp`, `docs/site/img/auditor/candidates-v3/3-hover/stamp-down.webp`, `docs/site/img/auditor/candidates-v3/3-hover/sheet.png`. Retained output: `H/source/reach.png`.

```text
Create ONE production 2D sprite of the EXACT selected candidate-3 Hover robot in the provided reference images. This is an edit of that identical character, not a redesign. Match its toy-like softly shaded off-white spherical egg body, broad glossy navy-black face screen, thick curved mint green eyebrow/cap brim, one short navy bent antenna with mint ball, circular navy/mint earpiece, tiny mitten arms, no legs or feet, mint-rimmed flat bottom nozzle, and dark navy rubber stamp with mint handle when requested. Preserve the proportions, face size, mint colors, materials, and camera of the reference. The face is the only face; do not add mouth or nose. Clean shapes readable when the sprite is 88px wide.
IMPORTANT layer separation: REMOVE ALL thruster flame, exhaust, luminous jet, floating droplets, underbody glow, cast floor shadow, motion trail, sparks and impact effects from this character sprite. The bottom is ONLY a clean flat mint-rimmed nozzle with a dark opening. No green pointed shape beneath it. The nozzle must be fully visible with open magenta space directly below, including the stamping pose.
Output exactly one square 1024x1024 image. Opaque perfectly flat solid #FF00FF magenta background, no transparency/checkerboard, no gradients or background shading. All character pixels confined to x=110..910 and y=105..800, with generous blank padding. Use exactly the same anatomical scale and camera distance for every pose: spherical body width about 570px, crown to nozzle about 570px, antenna tip around y=105; nozzle outlet center at x=512, y=800, horizontal flat nozzle baseline y=800. The body centerline is x=512. Do not fit or zoom the figure based on the hands or tools; extra tools extend sideways in the padding. Complete silhouette inside canvas. No lettering, text, labels, borders, numbers, UI or scenery. Do not replicate the reference contact sheet.

POSE: REACH. 3/4 RIGHT view. Two neutral round mint dot eyes • •. Viewer-right arm reaches outward to the right and PULLS a small blank off-white folder TAB, a clearly visible plain rectangular tab with no writing, not an entire oversized cabinet. Viewer-left hand rests with the little navy stamp beside the body. Flat empty nozzle visible; no flame.
```

### Exact call 4: present

Reference/edit inputs: `docs/site/img/auditor/candidates-v3/3-hover/idle.webp`, `docs/site/img/auditor/candidates-v3/3-hover/stamp-down.webp`, `docs/site/img/auditor/candidates-v3/3-hover/sheet.png`. Retained output: `H/source/present.png`.

```text
Create ONE production 2D sprite of the EXACT selected candidate-3 Hover robot in the provided reference images. This is an edit of that identical character, not a redesign. Match its toy-like softly shaded off-white spherical egg body, broad glossy navy-black face screen, thick curved mint green eyebrow/cap brim, one short navy bent antenna with mint ball, circular navy/mint earpiece, tiny mitten arms, no legs or feet, mint-rimmed flat bottom nozzle, and dark navy rubber stamp with mint handle when requested. Preserve the proportions, face size, mint colors, materials, and camera of the reference. The face is the only face; do not add mouth or nose. Clean shapes readable when the sprite is 88px wide.
IMPORTANT layer separation: REMOVE ALL thruster flame, exhaust, luminous jet, floating droplets, underbody glow, cast floor shadow, motion trail, sparks and impact effects from this character sprite. The bottom is ONLY a clean flat mint-rimmed nozzle with a dark opening. No green pointed shape beneath it. The nozzle must be fully visible with open magenta space directly below, including the stamping pose.
Output exactly one square 1024x1024 image. Opaque perfectly flat solid #FF00FF magenta background, no transparency/checkerboard, no gradients or background shading. All character pixels confined to x=110..910 and y=105..800, with generous blank padding. Use exactly the same anatomical scale and camera distance for every pose: spherical body width about 570px, crown to nozzle about 570px, antenna tip around y=105; nozzle outlet center at x=512, y=800, horizontal flat nozzle baseline y=800. The body centerline is x=512. Do not fit or zoom the figure based on the hands or tools; extra tools extend sideways in the padding. Complete silhouette inside canvas. No lettering, text, labels, borders, numbers, UI or scenery. Do not replicate the reference contact sheet.

POSE: PRESENT. Front/slight 3/4 right view, neutral round mint dot eyes • •. Both small mitten hands hold one blank off-white portrait-format page to the viewer-right side of the torso, clearly visible blank sheet with navy edge, no writing or symbols; do not hide the face or nozzle. The small stamp may be held low in the viewer-left hand. Flat empty nozzle visible.
```

### Exact call 5: point

Reference/edit inputs: `docs/site/img/auditor/candidates-v3/3-hover/idle.webp`, `docs/site/img/auditor/candidates-v3/3-hover/stamp-down.webp`, `docs/site/img/auditor/candidates-v3/3-hover/sheet.png`. Retained output: `H/source/point.png`.

```text
Create ONE production 2D sprite of the EXACT selected candidate-3 Hover robot in the provided reference images. This is an edit of that identical character, not a redesign. Match its toy-like softly shaded off-white spherical egg body, broad glossy navy-black face screen, thick curved mint green eyebrow/cap brim, one short navy bent antenna with mint ball, circular navy/mint earpiece, tiny mitten arms, no legs or feet, mint-rimmed flat bottom nozzle, and dark navy rubber stamp with mint handle when requested. Preserve the proportions, face size, mint colors, materials, and camera of the reference. The face is the only face; do not add mouth or nose. Clean shapes readable when the sprite is 88px wide.
IMPORTANT layer separation: REMOVE ALL thruster flame, exhaust, luminous jet, floating droplets, underbody glow, cast floor shadow, motion trail, sparks and impact effects from this character sprite. The bottom is ONLY a clean flat mint-rimmed nozzle with a dark opening. No green pointed shape beneath it. The nozzle must be fully visible with open magenta space directly below, including the stamping pose.
Output exactly one square 1024x1024 image. Opaque perfectly flat solid #FF00FF magenta background, no transparency/checkerboard, no gradients or background shading. All character pixels confined to x=110..910 and y=105..800, with generous blank padding. Use exactly the same anatomical scale and camera distance for every pose: spherical body width about 570px, crown to nozzle about 570px, antenna tip around y=105; nozzle outlet center at x=512, y=800, horizontal flat nozzle baseline y=800. The body centerline is x=512. Do not fit or zoom the figure based on the hands or tools; extra tools extend sideways in the padding. Complete silhouette inside canvas. No lettering, text, labels, borders, numbers, UI or scenery. Do not replicate the reference contact sheet.

POSE: POINT. 3/4 RIGHT view with neutral round mint dot eyes • • looking right. Viewer-right arm extends with a clear pointing mitten finger toward the right-side filing panel, no props in that hand. Viewer-left hand holds the little mint-handled navy stamp low beside the body. Nozzle fully visible.
```

### Exact call 6: think

Reference/edit inputs: `docs/site/img/auditor/candidates-v3/3-hover/idle.webp`, `docs/site/img/auditor/candidates-v3/3-hover/stamp-down.webp`, `docs/site/img/auditor/candidates-v3/3-hover/sheet.png`. Retained output: `H/source/think.png`.

```text
Create ONE production 2D sprite of the EXACT selected candidate-3 Hover robot in the provided reference images. This is an edit of that identical character, not a redesign. Match its toy-like softly shaded off-white spherical egg body, broad glossy navy-black face screen, thick curved mint green eyebrow/cap brim, one short navy bent antenna with mint ball, circular navy/mint earpiece, tiny mitten arms, no legs or feet, mint-rimmed flat bottom nozzle, and dark navy rubber stamp with mint handle when requested. Preserve the proportions, face size, mint colors, materials, and camera of the reference. The face is the only face; do not add mouth or nose. Clean shapes readable when the sprite is 88px wide.
IMPORTANT layer separation: REMOVE ALL thruster flame, exhaust, luminous jet, floating droplets, underbody glow, cast floor shadow, motion trail, sparks and impact effects from this character sprite. The bottom is ONLY a clean flat mint-rimmed nozzle with a dark opening. No green pointed shape beneath it. The nozzle must be fully visible with open magenta space directly below, including the stamping pose.
Output exactly one square 1024x1024 image. Opaque perfectly flat solid #FF00FF magenta background, no transparency/checkerboard, no gradients or background shading. All character pixels confined to x=110..910 and y=105..800, with generous blank padding. Use exactly the same anatomical scale and camera distance for every pose: spherical body width about 570px, crown to nozzle about 570px, antenna tip around y=105; nozzle outlet center at x=512, y=800, horizontal flat nozzle baseline y=800. The body centerline is x=512. Do not fit or zoom the figure based on the hands or tools; extra tools extend sideways in the padding. Complete silhouette inside canvas. No lettering, text, labels, borders, numbers, UI or scenery. Do not replicate the reference contact sheet.

POSE: THINK. Front view. Two neutral round mint dot eyes • •; thoughtful head tilt is subtle. Viewer-right mitten hand under the right lower corner of its face in a thinking gesture; viewer-left hand holds the little navy stamp beside its side. No mouth or symbols. Nozzle fully visible.
```

### Exact call 7: stamp

Reference/edit inputs: `docs/site/img/auditor/candidates-v3/3-hover/idle.webp`, `docs/site/img/auditor/candidates-v3/3-hover/stamp-down.webp`, `docs/site/img/auditor/candidates-v3/3-hover/sheet.png`. Retained output: `H/source/stamp.png`.

```text
Create ONE production 2D sprite of the EXACT selected candidate-3 Hover robot in the provided reference images. This is an edit of that identical character, not a redesign. Match its toy-like softly shaded off-white spherical egg body, broad glossy navy-black face screen, thick curved mint green eyebrow/cap brim, one short navy bent antenna with mint ball, circular navy/mint earpiece, tiny mitten arms, no legs or feet, mint-rimmed flat bottom nozzle, and dark navy rubber stamp with mint handle when requested. Preserve the proportions, face size, mint colors, materials, and camera of the reference. The face is the only face; do not add mouth or nose. Clean shapes readable when the sprite is 88px wide.
IMPORTANT layer separation: REMOVE ALL thruster flame, exhaust, luminous jet, floating droplets, underbody glow, cast floor shadow, motion trail, sparks and impact effects from this character sprite. The bottom is ONLY a clean flat mint-rimmed nozzle with a dark opening. No green pointed shape beneath it. The nozzle must be fully visible with open magenta space directly below, including the stamping pose.
Output exactly one square 1024x1024 image. Opaque perfectly flat solid #FF00FF magenta background, no transparency/checkerboard, no gradients or background shading. All character pixels confined to x=110..910 and y=105..800, with generous blank padding. Use exactly the same anatomical scale and camera distance for every pose: spherical body width about 570px, crown to nozzle about 570px, antenna tip around y=105; nozzle outlet center at x=512, y=800, horizontal flat nozzle baseline y=800. The body centerline is x=512. Do not fit or zoom the figure based on the hands or tools; extra tools extend sideways in the padding. Complete silhouette inside canvas. No lettering, text, labels, borders, numbers, UI or scenery. Do not replicate the reference contact sheet.

POSE: STAMP WIND-UP / RAISED. 3/4 RIGHT view. Two effort chevron mint eyes > <. Viewer-right arm holds the identical small navy rectangular rubber stamp with mint handle UP and OUT to the RIGHT of the body, ready to strike on that side, at about face height. Free viewer-left mitten arm balances. Keep spherical body and nozzle at identical scale and baseline; no squat or feet. Nozzle entirely clear.
```

### Exact call 8: stamp-down

Reference/edit inputs: `docs/site/img/auditor/candidates-v3/3-hover/idle.webp`, `docs/site/img/auditor/candidates-v3/3-hover/stamp-down.webp`, `docs/site/img/auditor/candidates-v3/3-hover/sheet.png`. Retained output: `H/source/stamp-down.png`.

```text
Create ONE production 2D sprite of the EXACT selected candidate-3 Hover robot in the provided reference images. This is an edit of that identical character, not a redesign. Match its toy-like softly shaded off-white spherical egg body, broad glossy navy-black face screen, thick curved mint green eyebrow/cap brim, one short navy bent antenna with mint ball, circular navy/mint earpiece, tiny mitten arms, no legs or feet, mint-rimmed flat bottom nozzle, and dark navy rubber stamp with mint handle when requested. Preserve the proportions, face size, mint colors, materials, and camera of the reference. The face is the only face; do not add mouth or nose. Clean shapes readable when the sprite is 88px wide.
IMPORTANT layer separation: REMOVE ALL thruster flame, exhaust, luminous jet, floating droplets, underbody glow, cast floor shadow, motion trail, sparks and impact effects from this character sprite. The bottom is ONLY a clean flat mint-rimmed nozzle with a dark opening. No green pointed shape beneath it. The nozzle must be fully visible with open magenta space directly below, including the stamping pose.
Output exactly one square 1024x1024 image. Opaque perfectly flat solid #FF00FF magenta background, no transparency/checkerboard, no gradients or background shading. All character pixels confined to x=110..910 and y=105..800, with generous blank padding. Use exactly the same anatomical scale and camera distance for every pose: spherical body width about 570px, crown to nozzle about 570px, antenna tip around y=105; nozzle outlet center at x=512, y=800, horizontal flat nozzle baseline y=800. The body centerline is x=512. Do not fit or zoom the figure based on the hands or tools; extra tools extend sideways in the padding. Complete silhouette inside canvas. No lettering, text, labels, borders, numbers, UI or scenery. Do not replicate the reference contact sheet.

POSE: STAMP-DOWN STRIKE. 3/4 RIGHT view, mint effort eyes > <. Viewer-right mitten arm reaches DOWN AND OUTWARD to the RIGHT. The navy rectangular stamp block is landing IN FRONT AND TO THE RIGHT OF THE BODY, with its bottom face AT EXACTLY THE NOZZLE HEIGHT y=800. Crucial composition: stamp center x=835; stamp left edge x>=730; nozzle center x=512 and nozzle width about 110. There must be a clearly visible magenta gap of at least 90px between the nozzle and stamp/arm, with a completely empty vertical exhaust corridor x=455..570 below nozzle. The mitten hand and stamp are far to the side, never under the center of the body, never covering the nozzle. Free arm balances left. No flame, impact, glow or ground. Maintain full body scale and visible nozzle; runtime supplies the dip.
```

### Exact call 9: approve

Reference/edit inputs: `docs/site/img/auditor/candidates-v3/3-hover/idle.webp`, `docs/site/img/auditor/candidates-v3/3-hover/stamp-down.webp`, `docs/site/img/auditor/candidates-v3/3-hover/sheet.png`. Retained output: `H/source/approve.png`.

```text
Create ONE production 2D sprite of the EXACT selected candidate-3 Hover robot in the provided reference images. This is an edit of that identical character, not a redesign. Match its toy-like softly shaded off-white spherical egg body, broad glossy navy-black face screen, thick curved mint green eyebrow/cap brim, one short navy bent antenna with mint ball, circular navy/mint earpiece, tiny mitten arms, no legs or feet, mint-rimmed flat bottom nozzle, and dark navy rubber stamp with mint handle when requested. Preserve the proportions, face size, mint colors, materials, and camera of the reference. The face is the only face; do not add mouth or nose. Clean shapes readable when the sprite is 88px wide.
IMPORTANT layer separation: REMOVE ALL thruster flame, exhaust, luminous jet, floating droplets, underbody glow, cast floor shadow, motion trail, sparks and impact effects from this character sprite. The bottom is ONLY a clean flat mint-rimmed nozzle with a dark opening. No green pointed shape beneath it. The nozzle must be fully visible with open magenta space directly below, including the stamping pose.
Output exactly one square 1024x1024 image. Opaque perfectly flat solid #FF00FF magenta background, no transparency/checkerboard, no gradients or background shading. All character pixels confined to x=110..910 and y=105..800, with generous blank padding. Use exactly the same anatomical scale and camera distance for every pose: spherical body width about 570px, crown to nozzle about 570px, antenna tip around y=105; nozzle outlet center at x=512, y=800, horizontal flat nozzle baseline y=800. The body centerline is x=512. Do not fit or zoom the figure based on the hands or tools; extra tools extend sideways in the padding. Complete silhouette inside canvas. No lettering, text, labels, borders, numbers, UI or scenery. Do not replicate the reference contact sheet.

POSE: APPROVE. Front/slight 3/4 right view. Exactly two happy mint caret eyes ^ ^. Viewer-right mitten makes a clear thumbs-up, held beside face. Viewer-left mitten holds the identical little mint-handled navy stamp low beside body. Nozzle fully clear and flat.
```

### Exact call 10: concern

Reference/edit inputs: `docs/site/img/auditor/candidates-v3/3-hover/idle.webp`, `docs/site/img/auditor/candidates-v3/3-hover/stamp-down.webp`, `docs/site/img/auditor/candidates-v3/3-hover/sheet.png`. Retained output: `H/source/concern.png`.

```text
Create ONE production 2D sprite of the EXACT selected candidate-3 Hover robot in the provided reference images. This is an edit of that identical character, not a redesign. Match its toy-like softly shaded off-white spherical egg body, broad glossy navy-black face screen, thick curved mint green eyebrow/cap brim, one short navy bent antenna with mint ball, circular navy/mint earpiece, tiny mitten arms, no legs or feet, mint-rimmed flat bottom nozzle, and dark navy rubber stamp with mint handle when requested. Preserve the proportions, face size, mint colors, materials, and camera of the reference. The face is the only face; do not add mouth or nose. Clean shapes readable when the sprite is 88px wide.
IMPORTANT layer separation: REMOVE ALL thruster flame, exhaust, luminous jet, floating droplets, underbody glow, cast floor shadow, motion trail, sparks and impact effects from this character sprite. The bottom is ONLY a clean flat mint-rimmed nozzle with a dark opening. No green pointed shape beneath it. The nozzle must be fully visible with open magenta space directly below, including the stamping pose.
Output exactly one square 1024x1024 image. Opaque perfectly flat solid #FF00FF magenta background, no transparency/checkerboard, no gradients or background shading. All character pixels confined to x=110..910 and y=105..800, with generous blank padding. Use exactly the same anatomical scale and camera distance for every pose: spherical body width about 570px, crown to nozzle about 570px, antenna tip around y=105; nozzle outlet center at x=512, y=800, horizontal flat nozzle baseline y=800. The body centerline is x=512. Do not fit or zoom the figure based on the hands or tools; extra tools extend sideways in the padding. Complete silhouette inside canvas. No lettering, text, labels, borders, numbers, UI or scenery. Do not replicate the reference contact sheet.

POSE: CONCERN. Front/slight 3/4 right view. Two worried inward mint chevron eyes > <, gentle concerned expression. Viewer-right mitten held out to the side with its palm facing the viewer, a clear stop/wait gesture with stubby fingers. Viewer-left hand holds little stamp low beside body. Nozzle fully clear and flat.
```

### Exact call 11: shrug

Reference/edit inputs: `docs/site/img/auditor/candidates-v3/3-hover/idle.webp`, `docs/site/img/auditor/candidates-v3/3-hover/stamp-down.webp`, `docs/site/img/auditor/candidates-v3/3-hover/sheet.png`. Retained output: `H/source/shrug.png`.

```text
Create ONE production 2D sprite of the EXACT selected candidate-3 Hover robot in the provided reference images. This is an edit of that identical character, not a redesign. Match its toy-like softly shaded off-white spherical egg body, broad glossy navy-black face screen, thick curved mint green eyebrow/cap brim, one short navy bent antenna with mint ball, circular navy/mint earpiece, tiny mitten arms, no legs or feet, mint-rimmed flat bottom nozzle, and dark navy rubber stamp with mint handle when requested. Preserve the proportions, face size, mint colors, materials, and camera of the reference. The face is the only face; do not add mouth or nose. Clean shapes readable when the sprite is 88px wide.
IMPORTANT layer separation: REMOVE ALL thruster flame, exhaust, luminous jet, floating droplets, underbody glow, cast floor shadow, motion trail, sparks and impact effects from this character sprite. The bottom is ONLY a clean flat mint-rimmed nozzle with a dark opening. No green pointed shape beneath it. The nozzle must be fully visible with open magenta space directly below, including the stamping pose.
Output exactly one square 1024x1024 image. Opaque perfectly flat solid #FF00FF magenta background, no transparency/checkerboard, no gradients or background shading. All character pixels confined to x=110..910 and y=105..800, with generous blank padding. Use exactly the same anatomical scale and camera distance for every pose: spherical body width about 570px, crown to nozzle about 570px, antenna tip around y=105; nozzle outlet center at x=512, y=800, horizontal flat nozzle baseline y=800. The body centerline is x=512. Do not fit or zoom the figure based on the hands or tools; extra tools extend sideways in the padding. Complete silhouette inside canvas. No lettering, text, labels, borders, numbers, UI or scenery. Do not replicate the reference contact sheet.

POSE: SHRUG. Front view, two neutral round mint dot eyes • • with mild puzzled tilt. Both tiny arms raised outward at the sides, palms up in a symmetrical readable shrug. No question marks, no symbols. Stamp may hang in the viewer-left palm at the side but does not cover nozzle. Flat empty nozzle visible.
```

### Exact call 12: stamp-height correction 1

Reference/edit inputs: `H/source/stamp-down.png`. Retained output: `H/source/stamp-down-adjustment-1.png`.

```text
Edit ONLY the stamp-holding arm and stamp position in this clean Hover stamp-down sprite. Preserve exactly this same robot body, camera, size, antenna, visor, effort eyes, colors, flat empty nozzle and magenta background. This is a precision pose correction, not a redesign. Keep the stamp clearly OUTSIDE TO THE RIGHT of the body. Lift the entire stamp by about 90 image pixels and bend its holding arm accordingly, so the BOTTOM EDGE of the navy stamp block is on the EXACT SAME HORIZONTAL LINE as the lowest bottom edge of the mint nozzle. The stamp lands beside the robot at nozzle height, not lower. Nozzle must remain completely uncovered, with a wide empty magenta vertical corridor below its center. No flame, glow, ground or shadow. All other pixels and proportions remain visually identical. One single sprite, same square canvas, solid #FF00FF background.
```

### Exact call 13: stamp-height correction 2

Reference/edit inputs: `H/source/stamp-down-adjustment-1.png`. Retained output: `H/source/stamp-down-adjustment-2.png`.

```text
Precision edit of the provided 1254x1254 Hover robot sprite. Keep the robot's body, nozzle, antenna, face, effort eyes, left hand and all other art EXACTLY as shown. Only reposition the right-side navy stamp and its holding wrist. In this image, the navy stamp block bottom is at y=982, while the flat mint nozzle bottom is y=1031. Move the stamp block DOWN by 49 pixels (no horizontal change), so its horizontal bottom contact edge is EXACTLY on y=1031, level with the nozzle bottom. Bend the attached right arm naturally to follow. Do not raise the tool. Do not lower the robot body. Leave the clear gap under the nozzle and between nozzle and stamp. Preserve scale, colors and pure #FF00FF magenta background. No flame, glow, floor, guides or text.
```

### Exact call 14: stamp-height final with geometry guide

Reference/edit inputs: `H/source/stamp-down-adjustment-1.png`, `H/source/stamp-height-guide.png`. Retained output: `H/source/stamp-down-final.png`.

```text
Precision edit of the FIRST reference image: keep this identical Hover robot and pure magenta background. The SECOND image is a GEOMETRY GUIDE ONLY: mint rectangle marks the nozzle; navy rectangle marks the required stamp-block position; white line is the shared baseline. Align the lowest bottom edge of the right-side navy stamp block EXACTLY with the lowest bottom edge of the mint nozzle, as both rectangles rest on the one line in the guide. Move ONLY the stamp and its right holding mitten/wrist enough to match this guide; retain the robot body, face, eyes, antenna and nozzle position and the gap below the nozzle. The stamp stays far to the right, outside the body silhouette. The final stamp block should occupy x965..1207, y940..1031 in the existing 1254 square image. Do not show any white line or guide shapes in the final image. No flame, glow, shadow, ground or text. Same character, same scale and same canvas.
```

### Exact call 15: thruster loop

Reference/edit inputs: `docs/site/img/auditor/candidates-v3/3-hover/idle.webp`, `docs/site/img/auditor/candidates-v3/3-hover/stamp-down.webp`, `docs/site/img/auditor/candidates-v3/3-hover/sheet.png`. Retained output: `H/source/thruster-loop.png`.

```text
Production animation sprite sheet for the small MINT HOVER THRUSTER flame that belongs under the candidate-3 Hover robot from the reference, but show ONLY the isolated flame VFX, NO robot, NO nozzle, NO body, NO shadow, NO text. Six consecutive frames of one short softly sculpted mint/aqua luminous downward jet, an almost white mint central core with a saturated green-mint rim, gently tapering to a rounded pointed lower tip, readable at 10px wide. Match the reference robot's little mint jet, retain a solid bright core so it reads on both warm ivory and dark navy backgrounds. Subtle soft halo at the edge, not large fog.
Exact grid: THREE COLUMNS, TWO ROWS, six equal square cells, row-major chronological order. Landscape sheet, target 1536x1024. Every flame top attachment is centered at the same cell-local (256,128); flat top width 150px; normal flame is about 150px wide and 230px long, entirely in the central safe area. Leave generous magenta padding between cells. Stable root/top anchor, same global scale all six frames. Smooth loop variations only: frame1 short rounded teardrop; frame2 slightly longer leaning right; frame3 long pointed central tip; frame4 rounded short tip leaning left; frame5 medium subtly split lower tip; frame6 back toward initial short shape. Frame6 must loop smoothly into frame1. No detached sparks or large smoke. Opaque flat solid pure #FF00FF background across every cell, no cell borders, no captions, no gradients in background, no checkerboard. No pink on flame; magenta is key background only.
```

### Exact call 16: thruster burst

Reference/edit inputs: `candidates-v3/3-hover/idle.webp`, `H/source/thruster-loop.png`. Retained output: `H/source/thruster-burst.png`.

```text
Create ONE isolated bigger recoil BURST version of the mint hover thruster flame shown in the second reference. Match the first reference Hover robot's mint jet and the loop sheet's sculpted style. ONLY THE FLAME, no robot, nozzle, stamp, shadow, sparks, lettering or symbols. A luminous white-mint core, saturated aqua/mint edge, short broad downward teardrop with a gently forked bottom tip, rounded flattened horizontal top attachment, strong crisp silhouette that reads on light ivory and dark navy. Compared with a normal loop flame, this burst has a broader shoulder and more energetic three-lobed tapered lower end. Not an explosion. Square canvas 1024x1024; flame centered horizontally at x512, flat top starts y200, entire flame x300..724 y200..720. Generous blank margin. Opaque completely flat #FF00FF magenta background, no background gradient, checkerboard, floor or surrounding objects. Minimal soft halo, no pink on flame.
```
