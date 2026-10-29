#!/usr/bin/env python3
"""Deterministically key, cut, despill and encode the approved Auditor artwork.

Run from this worktree with:
  .venv/bin/python docs/site/img/auditor/process-auditor.py

The default v3 path uses sheet-B-v3.png, one shared scale, and padding-only
normalization of the original four B exports. --prepare-inputs reproduces the
image_gen edit references. --legacy retains the historical A/B/C processor.
Artwork is never drawn or regenerated here. See the prompt log for provenance.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parent
POSES = ("idle", "inspect", "present", "stamp")
LIMIT = 120_000
PADDING = 2
CONTENT_HEIGHT = 508
PROCESSOR = Path("/Users/yan/.codex/skills/generate2dsprite/scripts/generate2dsprite.py")
TITLES = {
    "A": "Compact studio automaton",
    "B": "Precision desk clerk",
    "C": "Quiet capsule auditor",
}
SOURCES = {
    "A": "exec-11640cc2-79bc-434c-b304-6ec8d197bb74.png",
    "B": "exec-24ade898-1e76-455c-a6ba-84619bf7210b.png",
    "C": "exec-cb002e30-7e54-473a-a04f-c6aa8da9c2e9.png",
}
V3_POSES = ("reach", "point", "think", "stamp-down", "approve", "concern", "shrug")
ALL_POSES = POSES + V3_POSES
ATLAS_POSES = ("idle-calibration",) + V3_POSES
V3_LIMIT = 90_000
V3_CANVAS = (576, 512)
V3_BASELINE = 510  # exclusive alpha-bbox bottom; last covered row is 509


def load_processor():
    spec = importlib.util.spec_from_file_location("sprite_processor", PROCESSOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def key_and_despill(image: Image.Image):
    rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
    border = np.concatenate([
        rgb[:12].reshape(-1, 3), rgb[-12:].reshape(-1, 3),
        rgb[:, :12].reshape(-1, 3), rgb[:, -12:].reshape(-1, 3),
    ])
    background = np.median(border, axis=0)
    # Estimate magenta coverage from red/blue excess over green. Warm whites,
    # charcoal joints and mint surfaces remain opaque; the edge gets soft alpha.
    red_excess = (rgb[..., 0] - rgb[..., 1]) / (background[0] - background[1])
    blue_excess = (rgb[..., 2] - rgb[..., 1]) / (background[2] - background[1])
    alpha = np.clip(1 - np.minimum(red_excess, blue_excess), 0, 1)
    # The generated background has small color fluctuations. Keep soft pixels
    # only within two source pixels of a reliable foreground core. This also
    # opens the magnifying glass instead of retaining tinted magenta glass.
    core = Image.fromarray(np.uint8(alpha > 0.25) * 255)
    near_core = np.asarray(core.filter(ImageFilter.MaxFilter(5))) > 0
    alpha = np.where(near_core & (alpha > 0.07), alpha, 0)
    # Unmix the measured magenta matte instead of retaining pink edge RGB.
    safe_alpha = np.maximum(alpha[..., None], 1e-6)
    foreground = (rgb - (1 - alpha[..., None]) * background) / safe_alpha
    foreground = np.clip(foreground, 0, 255)
    spill = np.maximum(
        np.minimum(foreground[..., 0], foreground[..., 2]) - foreground[..., 1] - 6,
        0,
    )
    foreground[..., 0] -= spill
    foreground[..., 2] -= spill
    foreground[alpha == 0] = 0
    rgba = np.dstack([foreground, alpha * 255]).round().astype(np.uint8)
    return Image.fromarray(rgba), background.tolist()


def split_boundaries(keyed: Image.Image):
    occupancy = np.count_nonzero(np.asarray(keyed.getchannel("A")) > 64, axis=0)
    width = keyed.width
    boundaries = [0]
    for index in range(1, 4):
        lo, hi = int(width * (index - .45) / 4), int(width * (index + .45) / 4)
        candidates = np.flatnonzero(occupancy[lo:hi] == 0) + lo
        runs = np.split(candidates, np.flatnonzero(np.diff(candidates) > 1) + 1)
        runs = [run for run in runs if len(run)]
        if not runs:
            raise ValueError(f"No safe gap near pose boundary {index}")
        run = max(runs, key=len)
        boundaries.append(int(run[len(run) // 2]))
    return boundaries + [width]


def png_bytes(image: Image.Image):
    # Keep true-color RGBA rather than forcing soft 3D shading into a small
    # indexed palette. A few integer RGB levels remove invisible source noise
    # and lower entropy; all 256 alpha levels remain available at the contour.
    original = np.asarray(image).astype(np.float32)
    for step in (1, 2, 3, 4, 5, 6, 8, 10):
        rgba = original.copy()
        rgba[..., :3] = np.clip(np.round(rgba[..., :3] / step) * step, 0, 255)
        candidate = final_despill(Image.fromarray(rgba.astype(np.uint8)))
        packed = io.BytesIO()
        candidate.save(packed, "PNG", optimize=True, compress_level=9)
        if len(packed.getvalue()) <= LIMIT:
            return packed.getvalue(), f"true-color RGBA; RGB step {step}/255; full 8-bit alpha", candidate
    raise ValueError("PNG exceeded the byte cap")


def encode_pose(image: Image.Image, stem: Path):
    data, png_encoding, image = png_bytes(image)
    stem.with_suffix(".png").write_bytes(data)
    image.save(stem.with_suffix(".webp"), "WEBP", lossless=True,
               quality=100, method=6, exact=True)
    webp_encoding = "lossless RGBA; pixels identical to paired PNG"
    if stem.with_suffix(".webp").stat().st_size > LIMIT:
        raise ValueError("WebP exceeded the byte cap")
    return {"png_encoding": png_encoding, "webp_encoding": webp_encoding}


def final_despill(image: Image.Image):
    rgba = np.asarray(image).astype(np.int16)
    spill = np.maximum(np.minimum(rgba[..., 0], rgba[..., 2]) - rgba[..., 1] - 6, 0)
    rgba[..., 0] -= spill
    rgba[..., 2] -= spill
    rgba[rgba[..., 3] == 0, :3] = 0
    return Image.fromarray(rgba.astype(np.uint8))


def font(size: int):
    return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", size)


def preview(variant: str, poses: list[Image.Image]):
    width, height, row_height = 1840, 1320, 660
    canvas = Image.new("RGB", (width, height), "#111a20")
    draw = ImageDraw.Draw(canvas)
    for row, (background, ink, muted, label) in enumerate([
        ("#111a20", "#f7f5ef", "#95aaa4", "DARK  /  #111a20"),
        ("#f7f5ef", "#111a20", "#53665d", "LIGHT  /  #f7f5ef"),
    ]):
        top = row * row_height
        draw.rectangle((0, top, width, top + row_height - 1), fill=background)
        draw.text((40, top + 25), f"AUDITOR  {variant}  /  {TITLES[variant]}",
                  fill=ink, font=font(28))
        draw.text((width - 286, top + 34), label, fill=muted, font=font(17))
        for index, (pose, image) in enumerate(zip(POSES, poses)):
            x = int(index * width / 4 + (width / 4 - image.width) / 2)
            y = top + 590 - image.height
            canvas.paste(image, (x, y), image)
            draw.text((index * width // 4 + 38, top + 612),
                      f"0{index + 1}  {pose.upper()}", fill=muted, font=font(18))
    canvas.save(ROOT / f"variant-{variant}-preview.png", optimize=True)


def check_pose(path: Path):
    image = Image.open(path).convert("RGBA")
    rgba = np.asarray(image).astype(np.int16)
    alpha = rgba[..., 3]
    pink = (np.minimum(rgba[..., 0], rgba[..., 2]) - rgba[..., 1] > 18) & (alpha > 32)
    edge_alpha = np.concatenate([alpha[0], alpha[-1], alpha[:, 0], alpha[:, -1]])
    assert path.stat().st_size <= LIMIT, path
    assert alpha.min() == 0 and alpha.max() == 255, path
    assert np.count_nonzero((alpha > 0) & (alpha < 255)), path
    assert edge_alpha.max() == 0, path
    assert not pink.any(), (path, int(pink.sum()))
    assert 450 <= image.height <= 512, (path, image.size)
    return {"file": str(path.relative_to(ROOT)), "bytes": path.stat().st_size,
            "width": image.width, "height": image.height,
            "alpha_extrema": [int(alpha.min()), int(alpha.max())],
            "partial_alpha_pixels": int(((alpha > 0) & (alpha < 255)).sum()),
            "pink_fringe_pixels": int(pink.sum()),
            "transparent_outer_border": True,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def legacy_main():
    processor = load_processor()
    manifest = {"limit_bytes_per_pose_file": LIMIT,
                "generation_tool": "built-in image_gen",
                "source_directory": "/Users/yan/.codex/generated_images/01a18605-e1a2-75f1-9a7a-741a7bb2e8ee",
                "processor": str(PROCESSOR), "variants": {}, "files": []}
    for variant in "ABC":
        source = ROOT / f"sheet-{variant}.png"
        image = Image.open(source)
        keyed, background = key_and_despill(image)
        boundaries = split_boundaries(keyed)
        crops, boxes = [], []
        for lo, hi in zip(boundaries, boundaries[1:]):
            cell = keyed.crop((lo, 0, hi, keyed.height))
            box = cell.getbbox()
            if box is None:
                raise ValueError(f"Empty pose in {variant}")
            crops.append(cell.crop(box))
            boxes.append([lo + box[0], box[1], lo + box[2], box[3]])
        # Repack existing cutouts into equal cells solely for the skill's
        # deterministic shared-scale/feet-anchor processor. No pose is resized.
        cell_width = max(crop.width for crop in crops) + 48
        cell_height = keyed.height
        prepared = Image.new("RGBA", (4 * cell_width, cell_height))
        for index, (crop, box) in enumerate(zip(crops, boxes)):
            prepared.paste(crop, (index * cell_width + (cell_width - crop.width) // 2, box[1]))
        output_cell = 640
        fit_scale = CONTENT_HEIGHT * max(cell_width, cell_height) / (
            output_cell * max(crop.height for crop in crops))
        _, qc = processor.split_grid(
            prepared, rows=1, cols=4, cell_size=output_cell,
            threshold=0, edge_threshold=0, fit_scale=fit_scale,
            trim_border_px=0, edge_clean_depth=0, align="feet",
            shared_scale=True, component_mode="largest", min_component_area=8,
            scale_strategy="preserve",
        )
        out = ROOT / variant
        out.mkdir(exist_ok=True)
        previews, pose_info = [], {}
        scales = []
        for index, (pose, info) in enumerate(zip(POSES, qc)):
            assert not info["is_empty"] and not info["source_edge_touch"]
            assert not info["output_edge_touch"] and not info["paste_clamped"]
            source_cell = prepared.crop(tuple(info["source_box"]))
            crop = source_cell.crop(tuple(info["crop_bbox"]))
            scaled = final_despill(crop.resize(tuple(info["output_size"]), Image.Resampling.LANCZOS))
            # Paste without an alpha mask: preserve coverage rather than
            # multiplying alpha by itself at the antialiased contour.
            final = Image.new("RGBA", (scaled.width + 2 * PADDING, scaled.height + 2 * PADDING))
            final.paste(scaled, (PADDING, PADDING))
            encoding = encode_pose(final, out / pose)
            pose_info[pose] = {"source_bbox": boxes[index], "size": list(final.size),
                               "scale": info["source_to_output_scale"], **encoding,
                               "qc": {k: info[k] for k in ("source_edge_touch", "output_edge_touch", "paste_clamped")}}
            scales.append(info["source_to_output_scale"])
            for extension in ("png", "webp"):
                manifest["files"].append(check_pose((out / pose).with_suffix("." + extension)))
            previews.append(Image.open(out / (pose + ".webp")).convert("RGBA"))
        assert max(scales) - min(scales) < 1e-12
        preview(variant, previews)
        manifest["variants"][variant] = {
            "title": TITLES[variant], "source_filename": SOURCES[variant],
            "raw_sheet": source.name, "source_dimensions": list(image.size),
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "measured_magenta_background_rgb": background,
            "source_x_boundaries": boundaries, "shared_scale": scales[0],
            "poses": pose_info,
            "visual_consistency": "Reviewed: same character, materials, anatomical scale and lighting across all four poses; no identity mismatch observed.",
        }
        for path in (source, ROOT / f"variant-{variant}-preview.png"):
            with Image.open(path) as im:
                manifest["files"].append({"file": path.name, "bytes": path.stat().st_size,
                                          "width": im.width, "height": im.height,
                                          "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        print(variant, "shared scale", round(scales[0], 6),
              "sizes", {pose: data["size"] for pose, data in pose_info.items()})
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Verified", len(manifest["files"]), "artwork files; all 24 pose exports meet the byte and alpha checks.")


def prepare_v3_inputs():
    """Repack approved source pixels and draft images; never synthesize artwork."""
    source = ROOT / "v3/source"
    source.mkdir(parents=True, exist_ok=True)
    keyed, _ = key_and_despill(Image.open(ROOT / "sheet-B.png"))
    reference = Image.new("RGBA", (1024, 1024), "#ff00ff")
    reference.alpha_composite(keyed.crop((89, 42, 453, 682)), (330, 260))
    reference.convert("RGB").save(source / "reference-idle.png", optimize=True)
    names = ("reference-idle",) + tuple(pose + "-draft" for pose in V3_POSES)
    if all((source / (name + ".png")).exists() for name in names):
        # A simple reference contact, not an export scale adjustment. Only the
        # approved 1024px reference is resolution-matched to the 1254px drafts.
        atlas = Image.new("RGB", (5016, 2508), "#ff00ff")
        for index, name in enumerate(names):
            image = Image.open(source / (name + ".png")).convert("RGB")
            if index == 0:
                image = image.resize((1254, 1254), Image.Resampling.LANCZOS)
            assert image.size == (1254, 1254), (name, image.size)
            atlas.paste(image, ((index % 4) * 1254, (index // 4) * 1254))
        atlas.save(source / "pose-drafts.png", optimize=True)


def feet_center(image: Image.Image):
    """Anchor the boot pair, so a sideways prop does not shift the whole body."""
    box = image.getbbox()
    depth = max(8, round((box[3] - box[1]) * .06))
    feet = image.getchannel("A").crop((0, box[3] - depth, image.width, box[3]))
    foot_box = feet.getbbox()
    return (foot_box[0] + foot_box[2]) / 2


def on_v3_canvas(image: Image.Image):
    box = image.getbbox()
    x = round(V3_CANVAS[0] / 2 - feet_center(image))
    y = V3_BASELINE - box[3]
    placed = (x + box[0], y + box[1], x + box[2], y + box[3])
    assert placed[0] >= 2 and placed[1] >= 2, placed
    assert placed[2] <= V3_CANVAS[0] - 2 and placed[3] == V3_BASELINE, placed
    canvas = Image.new("RGBA", V3_CANVAS)
    canvas.paste(image, (x, y))  # no mask: do not square the antialias coverage
    return canvas, [x, y]


def encode_v3_pose(image: Image.Image, path: Path, preserve_pixels=False):
    """Lossless WebP, with the existing RGB quantization only if needed."""
    rgba = np.asarray(image)
    steps = (1,) if preserve_pixels else (1, 2, 3, 4, 5, 6, 8, 10)
    for step in steps:
        if step == 1:
            candidate = image
        else:
            quantized = rgba.copy()
            quantized[..., :3] = np.clip(
                np.round(quantized[..., :3].astype(np.float32) / step) * step,
                0, 255,
            ).astype(np.uint8)
            candidate = final_despill(Image.fromarray(quantized))
        packed = io.BytesIO()
        candidate.save(packed, "WEBP", lossless=True, quality=100, method=6, exact=True)
        if len(packed.getvalue()) <= V3_LIMIT:
            path.write_bytes(packed.getvalue())
            assert np.array_equal(np.asarray(Image.open(path).convert("RGBA")),
                                  np.asarray(candidate)), path
            return {"webp_encoding": "lossless RGBA; full 8-bit alpha",
                    "rgb_quantization_step": step,
                    "approved_pixels_preserved": preserve_pixels}
    raise ValueError(f"WebP exceeds {V3_LIMIT} bytes: {path}")


def check_v3_pose(path: Path):
    image = Image.open(path).convert("RGBA")
    rgba = np.asarray(image).astype(np.int16)
    alpha = rgba[..., 3]
    pink = ((np.minimum(rgba[..., 0], rgba[..., 2]) - rgba[..., 1] > 18)
            & (alpha > 32))
    partial = (alpha > 0) & (alpha < 255)
    box = image.getbbox()
    border = np.concatenate([alpha[0], alpha[-1], alpha[:, 0], alpha[:, -1]])
    assert image.size == V3_CANVAS, (path, image.size)
    assert path.stat().st_size <= V3_LIMIT, path
    assert alpha.min() == 0 and alpha.max() == 255 and partial.any(), path
    assert not border.any() and not pink.any(), path
    assert box[3] == V3_BASELINE, (path, box)
    assert not rgba[alpha == 0, :3].any(), path
    return {
        "file": str(path.relative_to(ROOT)), "bytes": path.stat().st_size,
        "width": image.width, "height": image.height,
        "alpha_bbox": list(box),
        "alpha_bbox_dimensions": [box[2] - box[0], box[3] - box[1]],
        "feet_baseline_exclusive_y": box[3], "last_alpha_row": box[3] - 1,
        "alpha_extrema": [int(alpha.min()), int(alpha.max())],
        "partial_alpha_pixels": int(partial.sum()),
        "pink_fringe_pixels": int(pink.sum()),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def contact_v3():
    # All eleven at 1:1 scale, in manifest order, on both requested backgrounds.
    # No captions or other marks: the no-text rule also applies to this PNG.
    width, row_height = len(ALL_POSES) * V3_CANVAS[0], 560
    contact = Image.new("RGB", (width, 2 * row_height))
    for row, background in enumerate(("#f7f5ef", "#111a20")):
        contact.paste(background, (0, row * row_height, width, (row + 1) * row_height))
        for index, pose in enumerate(ALL_POSES):
            image = Image.open(ROOT / "B" / (pose + ".webp")).convert("RGBA")
            contact.paste(image, (index * V3_CANVAS[0], row * row_height + 24), image)
    contact.save(ROOT / "contact-v3.png", optimize=True)


def image_file_info(path: Path):
    with Image.open(path) as image:
        return {"file": str(path.relative_to(ROOT)), "bytes": path.stat().st_size,
                "width": image.width, "height": image.height,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def process_v3():
    original_manifest = json.loads((ROOT / "v3/manifest-v2.json").read_text())
    original_poses = original_manifest["variants"]["B"]["poses"]
    source = ROOT / "sheet-B-v3.png"
    keyed, background = key_and_despill(Image.open(source))
    assert keyed.size == (1536, 1024), keyed.size
    crops, source_boxes, row_boundaries = {}, {}, []
    for row in range(2):
        top = row * keyed.height // 2
        image = keyed.crop((0, top, keyed.width, top + keyed.height // 2))
        boundaries = split_boundaries(image)
        row_boundaries.append(boundaries)
        for column, (lo, hi) in enumerate(zip(boundaries, boundaries[1:])):
            pose = ATLAS_POSES[row * 4 + column]
            cell = image.crop((lo, 0, hi, image.height))
            box = cell.getbbox()
            assert box is not None and box[0] > 0 and box[1] > 0, pose
            assert box[2] < cell.width and box[3] < cell.height, pose
            crops[pose] = cell.crop(box)
            source_boxes[pose] = [lo + box[0], top + box[1],
                                  lo + box[2], top + box[3]]
    # The atlas idle is an explicit standing-size calibration. Include reach's
    # 2px taller silhouette when choosing the ONE shared scale, so its antenna
    # also fits the approved 508px content budget. No per-pose bbox fitting.
    scale = CONTENT_HEIGHT / max(crop.height for crop in crops.values())
    out = ROOT / "B"
    out.mkdir(exist_ok=True)
    pose_info = {}
    file_info = []
    for pose in ALL_POSES:
        approved = pose in POSES
        if approved:
            original = ROOT / "v3/source/approved-B" / (pose + ".webp")
            pixels = Image.open(original).convert("RGBA")
            image, offset = on_v3_canvas(pixels)
            details = {**original_poses[pose],
                       "source_file": str(original.relative_to(ROOT)),
                       "original_canvas": list(pixels.size),
                       "original_alpha_bbox": list(pixels.getbbox()),
                       "original_sha256": hashlib.sha256(original.read_bytes()).hexdigest()}
            details.pop("png_encoding", None)
        else:
            crop = crops[pose]
            scaled_size = (round(crop.width * scale), round(crop.height * scale))
            scaled = final_despill(crop.resize(scaled_size, Image.Resampling.LANCZOS))
            image, offset = on_v3_canvas(scaled)
            details = {"source_file": source.name, "source_bbox": source_boxes[pose],
                       "source_crop_size": list(crop.size), "scale": scale,
                       "scaled_crop_size": list(scaled_size)}
        encoding = encode_v3_pose(image, out / (pose + ".webp"), preserve_pixels=approved)
        if approved:
            decoded = Image.open(out / (pose + ".webp")).convert("RGBA")
            recovered = decoded.crop((offset[0], offset[1],
                                      offset[0] + pixels.width, offset[1] + pixels.height))
            assert np.array_equal(np.asarray(recovered), np.asarray(pixels)), pose
        qc = check_v3_pose(out / (pose + ".webp"))
        pose_info[pose] = {**details, **encoding, "canvas_offset": offset,
                           "size": list(V3_CANVAS), "alpha_bbox": qc["alpha_bbox"],
                           "qc": {"source_edge_touch": False, "output_edge_touch": False,
                                  "paste_clamped": False, "pink_fringe_pixels": 0}}
        file_info.append(qc)
        print(f"{pose:11} bbox={qc['alpha_bbox']} "
              f"content={qc['alpha_bbox_dimensions']} bytes={qc['bytes']} "
              f"partial-alpha={qc['partial_alpha_pixels']} pink={qc['pink_fringe_pixels']}")
    contact_v3()
    source_files = [ROOT / "sheet-B.png", source, ROOT / "contact-v3.png"]
    source_files += sorted((ROOT / "v3/source").rglob("*.png"))
    source_files += sorted((ROOT / "v3/source/approved-B").glob("*.webp"))
    file_info += [image_file_info(path) for path in source_files]
    manifest = {
        "version": "stamp-v3", "limit_bytes_per_pose_file": V3_LIMIT,
        "generation_tool": "built-in image_gen",
        "processor": "process-auditor.py (local key/cut/despill/trim/encode only)",
        "source_directory": "v3/source", "runtime_pose_order": list(ALL_POSES),
        "canonical_canvas": list(V3_CANVAS),
        "feet_baseline_exclusive_y": V3_BASELINE,
        "last_alpha_row": V3_BASELINE - 1,
        "runtime_bytes": sum(item["bytes"] for item in file_info[:len(ALL_POSES)]),
        "contact_sheet": {"file": "contact-v3.png", "row_backgrounds": ["#f7f5ef", "#111a20"],
                          "pose_order": list(ALL_POSES), "pose_scale": 1,
                          "page_runtime_asset": False, "text_or_labels": False},
        "retained_source_sheet": "sheet-B.png",
        "variants": {"B": {
            "title": "Precision desk clerk", "approved_original_sheet": "sheet-B.png",
            "original_shared_scale": original_manifest["variants"]["B"]["shared_scale"],
            "raw_sheet": source.name, "source_dimensions": list(keyed.size),
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "measured_magenta_background_rgb": background,
            "source_row_x_boundaries": row_boundaries,
            "shared_scale": scale, "shared_scale_applies_to": list(V3_POSES),
            "idle_calibration_source_bbox": source_boxes["idle-calibration"],
            "idle_calibration_scaled_height": round(crops["idle-calibration"].height * scale),
            "scale_method": "one factor from 508px approved content budget / tallest atlas crop; no independent pose fitting",
            "approved_originals": "Padding only; decoded original RGBA pixels recovered and compared exactly",
            "poses": pose_info,
        }},
        "verification": {
            "all_poses_real_alpha": True, "all_poses_under_90000_bytes": True,
            "all_canvases_equal": True, "all_baselines_equal": True,
            "all_outer_borders_transparent": True, "pink_fringe_pixels_total": 0,
            "original_four_pixel_preservation_asserted": True,
            "visual_review": "See prompt log for human-readable visual checks and limitations.",
        },
        "files": file_info,
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Shared v3 source scale {scale:.12f}; canvas {V3_CANVAS}; "
          f"baseline {V3_BASELINE}; eleven poses {manifest['runtime_bytes']} bytes.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--legacy", action="store_true", help="historical three-variant sheets")
    mode.add_argument("--prepare-inputs", action="store_true", help="rebuild edit references only")
    args = parser.parse_args()
    if args.legacy:
        legacy_main()
    elif args.prepare_inputs:
        prepare_v3_inputs()
    else:
        process_v3()
