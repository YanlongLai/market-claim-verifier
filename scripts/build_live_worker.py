#!/usr/bin/env python3
"""Bundle the unchanged Python core for Cloudflare. Never copy caches or keys."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]


def build(destination: Path) -> dict[str, str]:
    destination.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for source in sorted((ROOT / "src/claimcheck").glob("*.py")):
        shutil.copyfile(source, destination / source.name)
        hashes[source.name] = hashlib.sha256(source.read_bytes()).hexdigest()
    (destination.parent / "core-hashes.json").write_text(json.dumps(hashes, indent=2) + "\n")
    return hashes


if __name__ == "__main__":
    build(ROOT / "workers/live/src/claimcheck")
