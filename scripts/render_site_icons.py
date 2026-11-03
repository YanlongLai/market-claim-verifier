#!/usr/bin/env python3
"""Derive site icons from the existing H auditor, with no generated imagery.

uv run --no-project --with pillow==11.3.0 python scripts/render_site_icons.py
"""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "docs/site/img"

# The original manifest's idle bbox is (111, 12, 572, 527). Center that
# unchanged artwork in a 560px square, leaving room around the antenna.
source = Image.open(IMG / "auditor/H/idle.webp").convert("RGBA")
art = source.crop((62, 0, 622, 560))
art.resize((64, 64), Image.Resampling.LANCZOS).save(IMG / "favicon.png", optimize=True)
touch = Image.new("RGBA", art.size, "#f7f6f0")
touch.alpha_composite(art)
touch.convert("RGB").resize((180, 180), Image.Resampling.LANCZOS).save(
    IMG / "apple-touch-icon.png", optimize=True
)
art.save(ROOT / "docs/favicon.ico", sizes=[(16, 16), (32, 32)])
print("Icons: favicon.png 64×64; apple-touch-icon.png 180×180; favicon.ico 16×16 + 32×32")
