"""Retain every SEC cache byte from the completed run, excluding all news cache."""
import argparse
import gzip
import hashlib
import io
import json
import re
import tarfile
from pathlib import Path


def retain(cache: Path, out: Path):
    if not (out / "RUN_END.json").exists():
        raise RuntimeError("do not archive a changing paid-run cache")
    manifest = {}
    for provider in ("baseten", "fireworks", "meta"):
        target = out / f"runtime-cache-{provider}.tar.gz"
        if target.exists():
            raise FileExistsError("retained source archive exists; never replace it")
        records = []
        with target.open("wb") as handle, gzip.GzipFile(filename="", fileobj=handle, mode="wb", mtime=0) as zipped, tarfile.open(fileobj=zipped, mode="w|") as archive:
            for path in sorted((cache / provider).rglob("*")):
                if not path.is_file():
                    continue
                relative = str(path.relative_to(cache / provider))
                if not re.fullmatch(r"(?:company_tickers\.json|companyfacts-CIK\d{10}\.json)(?:\.meta\.json)?|releases/[a-f0-9]{64}(?:\.meta\.json)?", relative):
                    raise ValueError("unexpected cache file; archive only SEC cache bytes")
                raw = path.read_bytes()
                member = tarfile.TarInfo(relative)
                member.size = len(raw)
                member.mtime = 0
                archive.addfile(member, io.BytesIO(raw))
                records.append({"path": relative, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
        manifest[provider] = {"archive": target.name, "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "files": records}
    (out / "runtime-sources.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return {key: len(value["files"]) for key, value in manifest.items()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(retain(args.cache, args.out))
