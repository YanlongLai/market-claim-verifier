#!/usr/bin/env python3
"""Key/cut the five generated sheets; make the locally labelled review contact.

Run from the worktree: .venv/bin/python docs/site/img/auditor/candidates-v3/process-candidates.py
No artwork is drawn here. Matting follows ../process-auditor.py: estimate the
magenta matte, unmix edge RGB, despill, then cut at empty column gaps. Each
candidate uses one common scale for its four poses, on equal 576 x 512 canvases.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
POSES = ("idle", "inspect", "stamp-down", "approve")
CANDIDATES = (("1-chibi-b", "1 Chibi B"), ("2-calc", "2 Calc"),
              ("3-hover", "3 Hover"), ("4-neko", "4 Neko"),
              ("5-stampy", "5 Stampy"))
CANVAS = (576, 512)
BASELINE = 500
WARM, DARK, MINT = "#f7f5ef", "#111a20", "#3ddc97"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key_and_despill(image):
    rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
    border = np.concatenate([rgb[:12].reshape(-1, 3), rgb[-12:].reshape(-1, 3),
                             rgb[:, :12].reshape(-1, 3), rgb[:, -12:].reshape(-1, 3)])
    background = np.median(border, axis=0)
    assert background[0] > 240 and background[1] < 20 and background[2] > 240, background
    red_excess = (rgb[..., 0] - rgb[..., 1]) / (background[0] - background[1])
    blue_excess = (rgb[..., 2] - rgb[..., 1]) / (background[2] - background[1])
    alpha = np.clip(1 - np.minimum(red_excess, blue_excess), 0, 1)
    core = Image.fromarray(np.uint8(alpha > 0.25) * 255)
    near_core = np.asarray(core.filter(ImageFilter.MaxFilter(5))) > 0
    alpha = np.where(near_core & (alpha > 0.07), alpha, 0)
    foreground = np.clip((rgb - (1 - alpha[..., None]) * background)
                         / np.maximum(alpha[..., None], 1e-6), 0, 255)
    spill = np.maximum(np.minimum(foreground[..., 0], foreground[..., 2])
                       - foreground[..., 1] - 6, 0)
    foreground[..., 0] -= spill
    foreground[..., 2] -= spill
    foreground[alpha == 0] = 0
    rgba = np.dstack([foreground, alpha * 255]).round().astype(np.uint8)
    return Image.fromarray(rgba), background.tolist()


def split_boundaries(keyed):
    occupancy = np.count_nonzero(np.asarray(keyed.getchannel("A")) > 64, axis=0)
    width = keyed.width
    boundaries = [0]
    for index in range(1, 4):
        lo, hi = int(width * (index - .45) / 4), int(width * (index + .45) / 4)
        candidates = np.flatnonzero(occupancy[lo:hi] == 0) + lo
        runs = np.split(candidates, np.flatnonzero(np.diff(candidates) > 1) + 1)
        runs = [run for run in runs if len(run)]
        if not runs:
            raise ValueError(f"No safe gap at pose {index}")
        run = max(runs, key=len)
        boundaries.append(int(run[len(run) // 2]))
    return boundaries + [width]


def clean_resampled_edges(image):
    rgba = np.asarray(image).copy()
    rgb = rgba[..., :3].astype(np.int16)
    spill = np.maximum(np.minimum(rgb[..., 0], rgb[..., 2]) - rgb[..., 1] - 6, 0)
    rgba[..., 0] = np.maximum(rgb[..., 0] - spill, 0).astype(np.uint8)
    rgba[..., 2] = np.maximum(rgb[..., 2] - spill, 0).astype(np.uint8)
    rgba[rgba[..., 3] == 0, :3] = 0
    return Image.fromarray(rgba)


def file_info(path):
    im = Image.open(path).convert("RGBA")
    rgba = np.asarray(im)
    a = rgba[..., 3]
    rgb = rgba[..., :3].astype(np.int16)
    pink = (np.minimum(rgb[..., 0], rgb[..., 2]) - rgb[..., 1] > 18) & (a > 32)
    bbox = im.getbbox()
    border_clear = not (np.any(a[0]) or np.any(a[-1]) or np.any(a[:, 0]) or np.any(a[:, -1]))
    assert im.size == CANVAS and a.min() == 0 and a.max() == 255
    assert border_clear and not np.count_nonzero(pink), path
    return {"file": str(path.relative_to(ROOT)), "dimensions": list(im.size),
            "bytes": path.stat().st_size, "sha256": sha(path), "alpha_bbox": list(bbox),
            "content_dimensions": [bbox[2]-bbox[0], bbox[3]-bbox[1]],
            "partial_alpha_pixels": int(np.count_nonzero((a > 0) & (a < 255))),
            "transparent_border": border_clear, "pink_fringe_pixels": int(np.count_nonzero(pink))}


def process_candidate(folder, label):
    directory = ROOT / folder
    source = directory / "sheet.png"
    keyed, background = key_and_despill(Image.open(source))
    boundaries = split_boundaries(keyed)
    crops, source_boxes = [], []
    for left, right in zip(boundaries, boundaries[1:]):
        cell = keyed.crop((left, 0, right, keyed.height))
        bbox = cell.getbbox()
        assert bbox and bbox[0] > 1 and bbox[1] > 1
        assert bbox[2] < cell.width - 1 and bbox[3] < cell.height - 1, (folder, bbox)
        source_boxes.append([left+bbox[0], bbox[1], left+bbox[2], bbox[3]])
        crops.append(cell.crop(bbox))
    scale = min(488 / max(im.height for im in crops), 552 / max(im.width for im in crops))
    files = []
    for pose, crop, source_bbox in zip(POSES, crops, source_boxes):
        scaled = crop.resize((round(crop.width * scale), round(crop.height * scale)), Image.Resampling.LANCZOS)
        scaled = clean_resampled_edges(scaled)
        offset = ((CANVAS[0]-scaled.width)//2, BASELINE-scaled.height)
        assert min(offset) >= 2
        output = Image.new("RGBA", CANVAS)
        output.paste(scaled, offset)
        path = directory / f"{pose}.webp"
        output.save(path, "WEBP", lossless=True, quality=100, method=6, exact=True)
        assert np.array_equal(np.asarray(output), np.asarray(Image.open(path).convert("RGBA")))
        info = file_info(path)
        info.update(source_bbox=source_bbox, canvas_offset=list(offset))
        files.append(info)
        print(f"{folder}/{pose}: {info['content_dimensions']} px, {info['bytes']} bytes")
    return {"id": folder, "label": label, "source": str(source.relative_to(ROOT)),
            "source_dimensions": list(keyed.size), "source_sha256": sha(source),
            "measured_background_rgb": background, "split_boundaries": boundaries,
            "shared_scale": scale, "pose_files": files}


def font(size):
    for path in ("/System/Library/Fonts/Supplemental/Arial.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def center_text(draw, x, y, text, fill, size):
    f = font(size)
    box = draw.textbbox((0, 0), text, font=f)
    draw.text((round(x-(box[2]-box[0])/2), y), text, fill=fill, font=f)


def contact():
    width, half, header, row_height = 2400, 1200, 84, 320
    im = Image.new("RGB", (width, header+row_height*5), WARM)
    draw = ImageDraw.Draw(im)
    draw.rectangle((half, 0, width, im.height), fill=DARK)
    draw.text((28, 17), "AUDITOR / 5 cute candidates", fill=DARK, font=font(32))
    draw.text((half+28, 17), "Same poses / dark background", fill=WARM, font=font(32))
    draw.text((28, 56), "Warm #f7f5ef  |  Generated artwork; labels rendered locally", fill="#58635d", font=font(17))
    draw.text((half+28, 56), "Navy #111a20  |  Rightmost idle previews are exactly 72 px tall", fill="#9aada5", font=font(17))
    previews = []
    for row, (folder, label) in enumerate(CANDIDATES):
        top = header + row*row_height
        for side, color in ((0, DARK), (half, WARM)):
            draw.line((side+28, top, side+half-28, top), fill="#d9ddd4" if side == 0 else "#33433e", width=1)
            draw.text((side+28, top+12), label, fill=color, font=font(27))
            for index, pose in enumerate(POSES):
                sprite = Image.open(ROOT/folder/f"{pose}.webp").convert("RGBA")
                # A common canvas scale preserves the relative size of all four poses.
                preview = sprite.resize((245, 218), Image.Resampling.LANCZOS)
                center = side+148+index*234
                im.paste(preview, (center-preview.width//2, top+61), preview)
                center_text(draw, center, top+287, pose, color, 19)
            idle = Image.open(ROOT/folder/"idle.webp").convert("RGBA")
            idle = idle.crop(idle.getbbox())
            small = idle.resize((round(idle.width*72/idle.height), 72), Image.Resampling.LANCZOS)
            center = side+1095
            x, y = center-small.width//2, top+157
            im.paste(small, (x, y), small)
            center_text(draw, center, top+111, "PHONE", MINT if side else "#237750", 16)
            center_text(draw, center, top+246, "idle / 72 px", color, 17)
            previews.append({"candidate": folder, "background": WARM if side == 0 else DARK,
                             "rect": [x, y, x+small.width, y+72], "idle_content_height_px": 72})
    path = ROOT / "contact.png"
    im.save(path, optimize=True)
    return {"file": "contact.png", "dimensions": list(im.size), "bytes": path.stat().st_size,
            "sha256": sha(path), "backgrounds": [WARM, DARK], "labels_added_locally": True,
            "phone_previews": previews}


def main():
    results = [process_candidate(folder, label) for folder, label in CANDIDATES]
    manifest = {"generation_tool": "built-in image_gen", "pose_order": list(POSES),
                "canvas": list(CANVAS), "baseline_exclusive_y": BASELINE,
                "resampling": "One uniform scale per candidate, no per-pose fitting; LANCZOS",
                "encoding": "Lossless WebP; decoded RGBA equality asserted",
                "matting_reference": "../process-auditor.py key_and_despill + split_boundaries",
                "characters": results, "contact": contact()}
    (ROOT/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")


if __name__ == "__main__":
    main()
