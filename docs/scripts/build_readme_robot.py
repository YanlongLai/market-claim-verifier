"""Animate the existing Hover pose; run with `uv run python docs/scripts/build_readme_robot.py`.

No new AI generation: original prompt/provenance lives in
../prompts/site/auditor-robot.md. Shared palette and full-frame disposal avoid
color flicker and motion trails on GitHub's light and dark backgrounds.
"""
from math import cos, pi
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs/site/img/auditor/H/present.webp"
OUTPUT = ROOT / "docs/figures/hover-readme.gif"


def main():
    source = Image.open(SOURCE).convert("RGBA")
    source = source.crop(source.getbbox())
    source.thumbnail((288, 272), Image.Resampling.LANCZOS)
    palette = source.convert("RGB").quantize(colors=255)
    frames = []
    for index in range(40):
        canvas = Image.new("RGBA", (320, 296))
        offset = round(8 * (1 - cos(2 * pi * index / 40)))
        canvas.alpha_composite(source, ((320 - source.width) // 2, 4 + offset))
        frame = canvas.convert("RGB").quantize(palette=palette, dither=Image.Dither.NONE)
        transparent = canvas.getchannel("A").point(lambda alpha: 255 if alpha < 128 else 0)
        frame.paste(255, mask=transparent)
        frame.info["transparency"] = 255
        frames.append(frame)
    frames[0].save(
        OUTPUT, save_all=True, append_images=frames[1:], duration=80,
        loop=0, transparency=255, disposal=2, optimize=False,
    )
    with Image.open(OUTPUT) as result:
        assert result.n_frames > 1 and result.info["loop"] == 0
        print(f"{OUTPUT.relative_to(ROOT)}: {result.n_frames} frames, {OUTPUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
