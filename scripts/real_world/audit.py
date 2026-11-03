"""Offline audit of frozen gold, all attempts, ledger linkage and source archives."""
import argparse
import gzip
import hashlib
import json
import shutil
import sys
import tarfile
import tempfile
from collections import Counter
from pathlib import Path

from build_gold import build as build_gold

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def audit(out: Path, scan_secrets=False):
    freeze = json.loads((out / "FREEZE.json").read_text())
    for relative, digest in freeze["sha256"].items():
        if sha((ROOT / relative).read_bytes()) != digest:
            raise ValueError(f"frozen file changed: {relative}")
    with tempfile.TemporaryDirectory(prefix="news-gold-recheck-") as folder:
        tmp = Path(folder)
        shutil.copyfile(out / "claims.jsonl", tmp / "claims.jsonl")
        shutil.copytree(out / "sources", tmp / "sources")
        build_gold(tmp)
        for name in ("gold.jsonl", "GOLD_REVIEW.md"):
            if (tmp / name).read_bytes() != (out / name).read_bytes():
                raise ValueError("independent gold rebuild differs")
    cases = [json.loads(line) for line in (out / "claims.jsonl").read_text().splitlines()]
    ids = {case["id"] for case in cases}
    if len(ids) != 80 or len({case["url"] for case in cases}) != 80:
        raise ValueError("sample IDs/URLs not unique")
    gold = [json.loads(line) for line in (out / "gold.jsonl").read_text().splitlines()]
    for case, label in zip(cases, gold):
        if case["id"] != label["id"] or sha(case["claim"].encode()) != label["claim_sha256"]:
            raise ValueError("claim/gold mismatch")
    event_rows = [json.loads(line) for line in (out / "ledger.jsonl").read_text().splitlines()]
    reservations = {event["reservation_id"]: event for event in event_rows if event["event"] == "reserve"}
    trace_ids = []
    trace_cost = 0
    for provider in ("baseten", "fireworks", "meta"):
        for path in ("agent", "post"):
            rows = [json.loads(line) for line in (out / provider / path / "results.jsonl").read_text().splitlines()]
            if len(rows) != 80 or {row["id"] for row in rows} != ids:
                raise ValueError("missing/duplicate paid results")
            for row in rows:
                stored = json.loads((out / provider / path / row["id"] / "result.json").read_text())
                if row != stored:
                    raise ValueError("per-item result differs from results log")
        traces = list((out / provider / "agent").glob("*/trace.json")) + list((out / provider / "post").glob("*/traces/*.json"))
        for path in traces:
            trace = json.loads(path.read_text())
            for request in trace["requests"]:
                reservation = request["reservation"]
                rid = reservation["reservation_id"]
                if reservations.get(rid, {}).get("provider") != provider:
                    raise ValueError("request without matching budget reservation")
                if reservation["model"] != trace["model"]:
                    raise ValueError("model/ledger mismatch")
                trace_ids.append(rid)
                trace_cost += request["cost"]
    if Counter(trace_ids) != Counter({rid: 1 for rid in reservations}):
        raise ValueError("lost/duplicated paid request trace")
    sources = json.loads((out / "runtime-sources.json").read_text())
    source_count = 0
    for value in sources.values():
        archive = out / value["archive"]
        if sha(archive.read_bytes()) != value["sha256"]:
            raise ValueError("source archive hash mismatch")
        with tarfile.open(archive) as stream:
            members = {member.name: member for member in stream.getmembers()}
            if set(members) != {row["path"] for row in value["files"]}:
                raise ValueError("source archive inventory mismatch")
            for row in value["files"]:
                raw = stream.extractfile(members[row["path"]]).read()
                if sha(raw) != row["sha256"]:
                    raise ValueError("source member hash mismatch")
                source_count += 1
    primary_sources = json.loads((out / "sources/manifest.json").read_text())
    for source in primary_sources:
        if sha(gzip.decompress((out / "sources" / source["gzip_file"]).read_bytes())) != source["sha256"]:
            raise ValueError("primary raw SEC source hash mismatch")
    secrets_checked = 0
    if scan_secrets:
        from claimcheck.config import load_settings
        secrets = [load_settings(provider=p).model_api_key for p in ("baseten", "fireworks", "meta")]
        secrets = [secret.encode() for secret in secrets if secret]
        for path in out.rglob("*"):
            if path.is_file():
                raw = path.read_bytes()
                if any(secret in raw for secret in secrets):
                    raise ValueError(f"configured secret found in artifact: {path.name}")
        secrets_checked = len(secrets)
    receipt = {"frozen_files_checked": len(freeze["sha256"]), "independent_gold_rebuild": "2 byte-identical outputs",
               "expected_pairs": 480, "recorded_pairs": 480, "request_reservation_links": len(trace_ids),
               "every_paid_reservation_has_one_retained_request": True, "trace_cost_usd": trace_cost,
               "runtime_sec_source_files_checked": source_count, "primary_source_files_checked": len(primary_sources),
               "configured_secrets_scanned_without_printing": secrets_checked, "configured_secrets_found": 0,
               "new_paid_calls": 0, "sec_fetches": 0}
    (out / "audit.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--scan-configured-secrets", action="store_true")
    args = parser.parse_args()
    print(json.dumps(audit(args.out, args.scan_configured_secrets), indent=2))
