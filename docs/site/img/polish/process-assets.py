#!/usr/bin/env python3
"""Key/resize built-in image_gen artwork; never draw or regenerate artwork.

Export: python process-assets.py --sources /path/to/generation-records.json
Check committed exports without originals: python process-assets.py --check
The exact prompts live in docs/prompts/site/polish.md. Originals stay outside
the site; source hashes identify them without requiring a private cache.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import runpy

import numpy as np
from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parent
HELPERS = runpy.run_path(str(ROOT.parent / "auditor/process-auditor.py"))
LIMIT = 600_000


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(manifest):
    total = 0
    assert {p.name for p in ROOT.glob("*.webp")} == set(manifest["assets"])
    for name, data in manifest["assets"].items():
        path = ROOT / name
        image = Image.open(path)
        assert list(image.size) == data["size"]
        assert path.stat().st_size == data["bytes"]
        assert digest(path) == data["sha256"]
        total += data["bytes"]
        if data["mode"] == "key":
            pixels = np.asarray(image.convert("RGBA")).astype(int)
            assert image.getchannel("A").getextrema() == (0, 255)
            assert not np.any((np.minimum(pixels[..., 0], pixels[..., 2]) - pixels[..., 1] > 35)
                              & (pixels[..., 3] > 32)), name
    assert total == manifest["runtime_bytes"] <= LIMIT
    print(f"PASS {len(manifest['assets'])} polish WebPs: {total:,} / {LIMIT:,} bytes")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--sources", type=Path)
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = ROOT / "manifest.json"
    if args.check:
        check(json.loads(path.read_text()))
        return
    manifest = {"generator": "built-in image_gen", "prompt_log": "docs/prompts/site/polish.md", "assets": {}}
    for asset in json.loads(args.sources.read_text()):
        source = Path(asset["path"])
        image = Image.open(source).convert("RGB")
        if asset["mode"] == "key":
            image, _ = HELPERS["key_and_despill"](image)
            image = image.crop(image.getbbox())
            scaled = ImageOps.contain(image, (asset["size"][0] - 4, asset["size"][1] - 4), Image.Resampling.LANCZOS)
            image = Image.new("RGBA", tuple(asset["size"]))
            image.paste(scaled, ((image.width - scaled.width) // 2, (image.height - scaled.height) // 2))
            image = HELPERS["final_despill"](image)
        else:
            image = ImageOps.fit(image, tuple(asset["size"]), Image.Resampling.LANCZOS)
        output = ROOT / f"{asset['id']}.webp"
        image.save(output, "WEBP", quality=84, method=6, alpha_quality=100, exact=True)
        manifest["assets"][output.name] = {"size": list(image.size), "mode": asset["mode"],
            "bytes": output.stat().st_size, "sha256": digest(output), "source_sha256": digest(source),
            "prompt": asset["prompt"], "references": asset.get("references", [])}
    manifest["runtime_bytes"] = sum(item["bytes"] for item in manifest["assets"].values())
    manifest["footer_reuse"] = "img/auditor/H/concern.webp"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    check(manifest)


if __name__ == "__main__":
    main()
