#!/usr/bin/env python3
"""Key image_gen originals, apply one body scale, align nozzles, and export H.

No creative artwork is drawn here. Contact-sheet labels and the floor ellipse
are review layout only. Run with .venv/bin/python from the repository root.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import runpy

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source"
CANVAS = (704, 744)
SCALE = 0.5
NOZZLE = (352, 520)
FX_CANVAS = (160, 160)
FX_ROOT = (80, 20)
LIMIT = 70_000
POSES = {
    # Source nozzle outlet and midpoint between the two luminous eyes, in px.
    "idle": ((647, 1088), (774, 588)),
    "inspect": ((615, 1055), (739, 625)),
    "reach": ((582, 1055), (707, 615)),
    "present": ((601, 1050), (704, 579)),
    "point": ((609, 1071), (746, 592)),
    "think": ((627, 1081), (757, 579)),
    "stamp": ((569, 1062), (689, 622)),
    "stamp-down": ((570, 1034), (700, 665)),
    "approve": ((637, 1072), (756, 583)),
    "concern": ((624, 1097), (744, 629)),
    "shrug": ((629, 1056), (706, 577)),
}
helpers = runpy.run_path(str(ROOT.parent / "process-auditor.py"))
key = helpers["key_and_despill"]
despill = helpers["final_despill"]


def encode(image: Image.Image, name: str) -> dict:
    image = despill(image)
    path = ROOT / f"{name}.webp"
    image.save(path, "WEBP", quality=88, method=6, alpha_quality=100, exact=True)
    decoded = Image.open(path).convert("RGBA")
    rgba = np.asarray(decoded).astype(int)
    assert path.stat().st_size <= LIMIT, name
    assert decoded.getbbox() and decoded.getbbox()[0] > 0, name
    assert not np.any(rgba[0, :, 3]) and not np.any(rgba[-1, :, 3]), name
    assert not np.any(rgba[:, 0, 3]) and not np.any(rgba[:, -1, 3]), name
    pink = (np.minimum(rgba[..., 0], rgba[..., 2]) - rgba[..., 1] > 35) & (rgba[..., 3] > 32)
    assert not np.any(pink), name
    return {"file": path.name, "size": list(image.size), "bbox": list(decoded.getbbox()),
            "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def body_exports() -> dict:
    poses = {}
    for name, (outlet, visor) in POSES.items():
        source_name = "stamp-down-final" if name == "stamp-down" else name
        path = SOURCE / f"{source_name}.png"
        original = Image.open(path)
        assert original.size == (1254, 1254), (name, original.size)
        keyed, bg = key(original)
        scaled = keyed.resize((627, 627), Image.Resampling.LANCZOS)
        offset = (NOZZLE[0] - round(outlet[0] * SCALE), NOZZLE[1] - round(outlet[1] * SCALE))
        bbox = scaled.getbbox()
        assert bbox[0] + offset[0] > 0 and bbox[1] + offset[1] > 0, name
        assert bbox[2] + offset[0] < CANVAS[0] and bbox[3] + offset[1] < CANVAS[1], name
        image = Image.new("RGBA", CANVAS)
        image.paste(scaled, offset)
        # The central exhaust corridor must contain no baked flame or tools.
        corridor = image.getchannel("A").crop((NOZZLE[0] - 24, NOZZLE[1] + 4,
                                                 NOZZLE[0] + 24, CANVAS[1]))
        assert not corridor.getbbox(), name
        poses[name] = {**encode(image, name), "nozzle_anchor": list(NOZZLE),
                       "visor_anchor": [round(visor[0] * SCALE) + offset[0],
                                        round(visor[1] * SCALE) + offset[1]],
                       "source": f"source/{path.name}", "source_size": list(original.size),
                       "source_bbox": list(keyed.getbbox()), "source_nozzle_anchor": list(outlet),
                       "source_visor_anchor": list(visor), "scale": SCALE,
                       "translation": list(offset), "measured_background": bg}
    return poses


def flame_root(image: Image.Image) -> tuple[int, int]:
    a = np.asarray(image)
    # Find the first stable bright row of the flat jet mouth, excluding halo.
    core = (a[..., 3] > 230) & (a[..., 1] > 170)
    rows = np.flatnonzero(np.sum(core, axis=1) > 40)
    y = int(rows[0])
    xs = np.flatnonzero(core[y])
    return round(float(xs.mean())), y


def fx_export(image: Image.Image, name: str, scale: float) -> dict:
    keyed, bg = key(image)
    root = flame_root(keyed)
    size = tuple(round(n * scale) for n in keyed.size)
    scaled = keyed.resize(size, Image.Resampling.LANCZOS)
    offset = (FX_ROOT[0] - round(root[0] * scale), FX_ROOT[1] - round(root[1] * scale))
    final = Image.new("RGBA", FX_CANVAS)
    final.paste(scaled, offset)
    return {**encode(final, name), "root_anchor": list(FX_ROOT), "source_root_anchor": list(root),
            "scale": scale, "translation": list(offset), "measured_background": bg}


def fx_exports() -> dict:
    sheet = Image.open(SOURCE / "thruster-loop.png")
    assert sheet.size == (1536, 1024)
    frames = {}
    for index in range(6):
        x, y = index % 3 * 512, index // 3 * 512
        name = f"thruster-{index}"
        frames[name] = {**fx_export(sheet.crop((x, y, x + 512, y + 512)), name, 0.30),
                        "source": "source/thruster-loop.png", "source_cell": [x, y, x + 512, y + 512]}
    frames["thruster-burst"] = {**fx_export(Image.open(SOURCE / "thruster-burst.png"),
                                            "thruster-burst", 0.125),
                                "source": "source/thruster-burst.png"}
    return frames


def font(size: int):
    return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", size)


def composite(pose: str, frame: str = "thruster-0", burst: bool = False,
              dip: float = 0, mirror: bool = False) -> Image.Image:
    image = Image.new("RGBA", CANVAS)
    jet = Image.open(ROOT / f"{frame}.webp").convert("RGBA")
    factor = 1.6 if burst else 1
    jet = jet.resize(tuple(round(n * factor) for n in FX_CANVAS), Image.Resampling.LANCZOS)
    image.alpha_composite(jet, (round(NOZZLE[0] - FX_ROOT[0] * factor),
                                round(NOZZLE[1] - FX_ROOT[1] * factor)))
    image.alpha_composite(Image.open(ROOT / f"{pose}.webp").convert("RGBA"))
    if mirror:
        image = ImageOps.mirror(image)
    if dip:
        moved = Image.new("RGBA", CANVAS)
        moved.alpha_composite(image, (0, round(dip)))
        image = moved
    return image


def contact_sheet() -> None:
    width, cell, row_h = 1560, 260, 244
    canvas = Image.new("RGB", (width, 1640), "#f7f5ef")
    draw = ImageDraw.Draw(canvas)
    for theme, (bg, ink, top) in enumerate([("#f7f5ef", "#111a20", 0), ("#111a20", "#f7f5ef", 550)]):
        draw.rectangle((0, top, width, top + 549), fill=bg)
        draw.text((22, top + 12), f"HOVER / 11 clean poses + separate thruster / {'LIGHT' if not theme else 'DARK'}",
                  font=font(22), fill=ink)
        for index, pose in enumerate(POSES):
            x, y = index % 6 * cell, top + 48 + index // 6 * row_h
            sprite = composite(pose)
            sprite.thumbnail((238, 227), Image.Resampling.LANCZOS)
            canvas.paste(sprite, (x + (cell - sprite.width) // 2, y - 6), sprite)
            draw.text((x + 14, y + 218), pose, font=font(17), fill=ink)
        phone = composite("stamp-down", "thruster-burst", True, mirror=True)
        phone.thumbnail((100, 88), Image.Resampling.LANCZOS)
        canvas.paste(phone, (5 * cell + 75, top + 350), phone)
        draw.text((5 * cell + 32, top + 458), "phone / 88 px box", font=font(17), fill=ink)
    for bg, ink, top in [("#f7f5ef", "#111a20", 1100), ("#111a20", "#f7f5ef", 1370)]:
        draw.rectangle((0, top, width, top + 269), fill=bg)
        draw.text((22, top + 9), "STAMP-DOWN → RECOIL / scene clock / mirrored toward post", font=font(21), fill=ink)
        for index, delta in enumerate([120, 160, 200, 240, 250, 420]):
            burst = 0 <= delta < 250
            ease = lambda value: 1 - (1 - max(0, min(1, value))) ** 3
            dip = 0 if delta < 0 or delta >= 220 else 8 * ease(delta / 60) if delta < 60 else 8 * (1 - ease((delta - 60) / 160))
            frame = "thruster-burst" if burst else f"thruster-{int((4800 + delta) // 80) % 6}"
            sprite = composite("stamp-down", frame, burst, mirror=True)
            sprite.thumbnail((224, 210), Image.Resampling.LANCZOS)
            clock = 4800 + delta
            bob = 4 * math.sin(clock / 82800 * math.pi * 2 * 52)
            lean = -3 * (0.5 + 0.5 * math.sin(clock / 420))
            sprite = sprite.rotate(-lean, Image.Resampling.BICUBIC, center=(sprite.width / 2, sprite.height))
            x = index * cell
            canvas.paste(sprite, (x + (cell - sprite.width) // 2, top + 30 + round(bob + dip)), sprite)
            draw.text((x + 20, top + 244), f"{delta:+} ms / {'burst' if burst else 'loop'}", font=font(16), fill=ink)
    canvas.save(ROOT / "contact.png", optimize=True)


def main():
    poses, effects = body_exports(), fx_exports()
    contact_sheet()
    manifest = {"version": "v3-Hover-final", "generation_tool": "built-in image_gen",
                "reference": "../candidates-v3/3-hover", "canonical_canvas": list(CANVAS),
                "shared_body_scale": SCALE, "nozzle_baseline_y": NOZZLE[1],
                "limit_bytes_per_pose": LIMIT, "pose_order": list(POSES), "poses": poses,
                "thruster": {"canvas": list(FX_CANVAS), "root_anchor": list(FX_ROOT),
                             "frame_ms": 80, "loop_frames": 6, "burst_ms": 250, "burst_scale": 1.6,
                             "compositing": "straight alpha, behind body/stamp; no blend mode", "frames": effects},
                "runtime_bytes": sum(p["bytes"] for p in poses.values()) + sum(f["bytes"] for f in effects.values()),
                "contact": {"file": "contact.png", "themes": ["#f7f5ef", "#111a20"],
                            "strike_offsets_ms": [120, 160, 200, 240, 250, 420], "phone_height_px": 88,
                            "strip_pose": "stamp-down; samples start after the 120ms body crossfade"},
                "stamp_contact_anchor": [614, 524],
                "qc": {"one_body_scale": True, "shared_nozzle_baseline": True,
                       "all_borders_transparent": True, "central_exhaust_corridor_clear": True,
                       "no_baked_thruster": True, "stamp_contact_within_4px_of_nozzle_baseline": True}}
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    for pose, data in poses.items():
        print(f"{pose:11} {data['bytes']:6} B bbox={data['bbox']} visor={data['visor_anchor']} nozzle={data['nozzle_anchor']}")
    print("Thrusters:", {name: f["bytes"] for name, f in effects.items()})
    print("Runtime total:", manifest["runtime_bytes"], "B; contact:", (ROOT / "contact.png").stat().st_size, "B")


if __name__ == "__main__":
    main()
