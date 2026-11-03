"""Offline audit of phase-2 frozen gold, every request and source, and caps."""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import tarfile
import tempfile

from build_threads_gold import build as build_gold
from report_threads import ledger_summary, load_rows
from run import ROOT


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def audit(out, local=None, original=None, secrets=False):
    freeze = json.loads((out / "FREEZE.json").read_text())
    for path, expected in freeze["sha256"].items():
        if sha((ROOT / path).read_bytes()) != expected:
            raise ValueError(f"frozen input changed: {path}")
    with tempfile.TemporaryDirectory(prefix="threads-gold-audit-") as directory:
        target = Path(directory)
        shutil.copytree(out / "sources", target / "sources")
        shutil.copyfile(out / "claims.jsonl", target / "claims.jsonl")
        build_gold(target)
        for name in ("gold.jsonl", "media-gold.jsonl", "GOLD_REVIEW.md"):
            if (target / name).read_bytes() != (out / name).read_bytes():
                raise ValueError("gold rebuild mismatch")
    cases = load_rows(out / "claims.jsonl")
    gold = load_rows(out / "gold.jsonl")
    if len(cases) != 78 or set(cases) != set(gold):
        raise ValueError("case inventory mismatch")
    for id, case in cases.items():
        if sha(case["claim"].encode()) != gold[id]["claim_sha256"]:
            raise ValueError("claim/gold binding mismatch")
        if (out / "inputs" / f"{id}.txt").read_text() != case["claim"] + "\n":
            raise ValueError("actual post input differs from frozen paraphrase")
    events = list(map(json.loads, (out / "ledger.jsonl").read_text().splitlines()))
    reserved = {e["reservation_id"]: e for e in events if e["event"] == "reserve"}
    if len(reserved) != sum(e["event"] == "reserve" for e in events):
        raise ValueError("duplicate reservation")
    requests = []
    for provider in ("baseten", "fireworks", "meta"):
        for path in ("agent", "post"):
            rows = load_rows(out / provider / path / "results.jsonl")
            if set(rows) != set(cases):
                raise ValueError("missing expected result")
            for id, row in rows.items():
                stored = json.loads((out / provider / path / id / "result.json").read_text())
                if row != stored:
                    raise ValueError("result log differs from per-item artifact")
            traces = list((out / provider / path).glob("*/trace.json")) + list((out / provider / path).glob("*/traces/*.json"))
            for trace in traces:
                data = json.loads(trace.read_text())
                for r in data.get("requests", []):
                    if r["reservation"]["provider"] != provider:
                        raise ValueError("text request provider mismatch")
                    requests.append(r)
        for id, row in load_rows(out / "media" / provider / "results.jsonl").items():
            target = out / "media" / provider / id
            if row != json.loads((target / "result.json").read_text()):
                raise ValueError("media result inventory mismatch")
            requests.extend(json.loads((target / "requests.json").read_text()))
            if local:
                for artifact in json.loads((target / "local-artifacts.json").read_text()):
                    raw = local / "media" / provider / id / artifact["path"]
                    if not raw.is_file() or sha(raw.read_bytes()) != artifact["sha256"]:
                        raise ValueError("local media raw evidence changed or missing")
    ids = [r["reservation"]["reservation_id"] for r in requests]
    if Counter(ids) != Counter({id: 1 for id in reserved}):
        raise ValueError("request/reservation inventory differs")
    for r in requests:
        event = reserved[r["reservation"]["reservation_id"]]
        if r["reservation"]["model"] != event["model"] or r["reservation"]["provider"] != event["provider"]:
            raise ValueError("reservation model/provider mismatch")
    source_count = 0
    for source in json.loads((out / "sources/manifest.json").read_text()):
        if "gzip_file" in source:
            if sha(gzip.decompress((out / "sources" / source["gzip_file"]).read_bytes())) != source["sha256"]:
                raise ValueError("primary SEC bytes changed")
            source_count += 1
    archived = 0
    for source in json.loads((out / "runtime-sources.json").read_text()).values():
        file = out / source["archive"]
        if sha(file.read_bytes()) != source["sha256"]:
            raise ValueError("runtime source archive changed")
        with tarfile.open(file) as archive:
            if set(archive.getnames()) != {r["path"] for r in source["files"]}:
                raise ValueError("runtime source inventory differs")
            for r in source["files"]:
                if sha(archive.extractfile(r["path"]).read()) != r["sha256"]:
                    raise ValueError("runtime source hash mismatch")
                archived += 1
    if original:
        raw = json.loads((original / "mcv-threads-dappgo-posts.json").read_text())
        needles = [p["text"].encode() for p in raw["posts"]]
        for file in out.rglob("*"):
            if file.is_file() and any(n in file.read_bytes() for n in needles):
                raise ValueError("unparaphrased original post found in public artifacts")
    if any(p.suffix.lower() in {".png", ".jpg", ".jpeg", ".mp4", ".wav"} for p in out.rglob("*")):
        raise ValueError("original media must remain ignored")
    secret_count = 0
    if secrets:
        from claimcheck.config import load_settings
        keys = [load_settings(provider=p).model_api_key for p in ("baseten", "fireworks", "meta")]
        needles = [key.encode() for key in keys if key]
        for file in out.rglob("*"):
            if file.is_file() and any(key in file.read_bytes() for key in needles):
                raise ValueError("configured secret found in public artifact")
        secret_count = len(needles)
    budgets = ledger_summary(out)
    if not all(r["cap_respected"] for r in budgets.values()):
        raise ValueError("provider cap exceeded")
    receipt = {"frozen_files_checked": len(freeze["sha256"]), "gold_rebuild": "three byte-identical outputs",
               "expected_text_pairs": 468, "expected_media_routes": 6, "request_reservation_links": len(ids),
               "every_paid_reservation_has_one_retained_request": True, "primary_source_files_checked": source_count,
               "runtime_source_files_checked": archived, "local_raw_media_checked": bool(local),
               "original_post_privacy_checked": bool(original), "public_original_media_files": 0,
               "configured_secrets_scanned_without_printing": secret_count, "configured_secrets_found": 0,
               "budgets": budgets, "new_paid_calls": 0, "new_sec_fetches": 0}
    (out / "audit.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--local", type=Path)
    parser.add_argument("--original", type=Path)
    parser.add_argument("--scan-configured-secrets", action="store_true")
    args = parser.parse_args()
    print(json.dumps(audit(args.out, args.local, args.original, args.scan_configured_secrets), indent=2))
