"""Build the README GIF: uv run python docs/scripts/build_readme_robot.py.

Reuses website Hover assets and the supported-review timing from
 docs/site/script.js (paintRobot). This is a standalone mascot adaptation,
not a recording of the interactive evidence scene. Original AI artwork and
prompts: docs/prompts/site/auditor-robot.md. No new AI generation is needed.
A shared palette and full-frame disposal prevent flicker and motion trails.
"""
from math import pi, sin
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "docs/site/img/auditor/H"
OUTPUT = ROOT / "docs/figures/hover-readme.gif"
TRANSITIONS = [(0, "idle"), (700, "inspect"), (1500, "reach"),
               (2300, "point"), (3700, "think"), (4500, "stamp"),
               (4800, "stamp-down"), (5300, "approve"), (6400, "idle")]


def main():
    poses = {name: Image.open(ASSETS / f"{name}.webp").convert("RGBA")
             for _, name in TRANSITIONS}
    jets = {name: Image.open(ASSETS / f"thruster-{name}.webp").convert("RGBA")
            for name in [*map(str, range(6)), "burst"]}
    # Learn one palette from every pose, including the green exhaust.
    sheet = Image.new("RGB", (176 * (len(poses) + 1), 186))
    for i, sprite in enumerate([*poses.values(), jets["burst"]]):
        sheet.paste(sprite.resize((176, 186)).convert("RGB"), (i * 176, 0))
    palette = sheet.quantize(colors=255)
    frames = []
    for age in range(0, 8000, 80):
        current = max(i for i, (at, _) in enumerate(TRANSITIONS) if age >= at)
        at, pose = TRANSITIONS[current]
        previous = TRANSITIONS[max(0, current - 1)][1]
        blend = min(1, (age - at) / 120) if current else 1
        body = Image.blend(poses[previous], poses[pose], blend)
        since_strike = age - 4800
        burst = 0 <= since_strike < 250
        jet = jets["burst" if burst else str(age // 80 % 6)]
        factor = 1.6 if burst else 1
        jet = jet.resize((round(160 * factor), round(160 * factor)), Image.Resampling.LANCZOS)
        sprite = Image.new("RGBA", (704, 744))
        sprite.alpha_composite(jet, (round(352 - 80 * factor), round(520 - 20 * factor)))
        sprite.alpha_composite(body)
        sprite = sprite.resize((282, 298), Image.Resampling.LANCZOS)
        direction = {"inspect": -1, "stamp": -1, "stamp-down": -1, "reach": 1, "point": 1}
        lean = direction.get(pose, 0) * 3 * (0.5 + 0.5 * sin(age / 420))
        sprite = sprite.rotate(-lean, Image.Resampling.BICUBIC)
        dip = 0
        if 0 <= since_strike < 220:
            ease = lambda t: 1 - (1 - max(0, min(1, t))) ** 3
            dip = 8 * (ease(since_strike / 60) if since_strike < 60 else 1 - ease((since_strike - 60) / 160))
        canvas = Image.new("RGBA", (320, 320))
        canvas.alpha_composite(sprite, (19, 10 + round(4 * sin(age / 1600 * 2 * pi) + dip)))
        frame = canvas.convert("RGB").quantize(palette=palette, dither=Image.Dither.NONE)
        transparent = canvas.getchannel("A").point(lambda alpha: 255 if alpha < 128 else 0)
        frame.paste(255, mask=transparent)
        frame.info["transparency"] = 255
        frames.append(frame)
    frames[0].save(OUTPUT, save_all=True, append_images=frames[1:], duration=80,
                   loop=0, transparency=255, disposal=2, optimize=False)
    with Image.open(OUTPUT) as result:
        assert result.n_frames > 1 and result.info["loop"] == 0
        print(f"{OUTPUT.relative_to(ROOT)}: {result.n_frames} frames, {OUTPUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
