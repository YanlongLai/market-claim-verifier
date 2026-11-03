#!/usr/bin/env python3
"""Audit the frozen feasibility records offline; never imports a provider SDK."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def read_json(name: str):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def read_jsonl(name: str):
    return [json.loads(line) for line in (ROOT / name).read_text().splitlines()]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL {message}")


def main() -> None:
    manifest = read_json("manifest.json")
    for name, expected in manifest["artifacts_sha256"].items():
        path = ROOT / name
        require(path.parent == ROOT, f"unexpected artifact path: {name}")
        require(hashlib.sha256(path.read_bytes()).hexdigest() == expected,
                f"artifact hash changed: {name}")
    require(manifest["training_dataset"] is None, "unexpected training dataset")
    require(manifest["evaluation_dataset"] is None, "unexpected evaluation dataset")
    require(manifest["paid_execution_started"] is False, "paid execution flag")

    base = read_json("api-muse-spark-open.json")
    nvfp4 = read_json("api-muse-spark-open-nvfp4.json")
    require(base["supportsServerless"] and not base["supportsServerlessTraining"],
            "base inference/training flags")
    require(nvfp4["supportsServerlessTraining"] and nvfp4["supportsLora"],
            "NVFP4 training flags")
    for record in read_jsonl("model-probes.jsonl"):
        require(record["http_status"] == 200, "model metadata status")
        require(record["response_sha256"] == manifest["artifacts_sha256"][record["response_file"]],
                "metadata response hash")

    records = []
    created_sessions = set()
    deleted_sessions = set()
    allowed_control = {"create_session", "create_model", "retrieve_future", "get_info"}
    for name in ("shape-probes.jsonl", "session-probes.jsonl", "session-info-probes.jsonl"):
        for record in read_jsonl(name):
            records.append(record)
            path = record["path"]
            require(record["estimated_charge_usd"] == 0, "nonzero probe charge")
            if record["method"] == "POST" and "/training/" in path:
                require(path.rsplit("/", 1)[-1] in allowed_control,
                        f"unexpected training operation: {path}")
            elif record["method"] == "POST":
                require(path.endswith("/deploymentShapeVersions:match"),
                        f"unexpected mutation: {path}")
            if path.endswith("/create_session") and record["http_status"] == 200:
                created_sessions.add(record["response"]["session_id"])
            if record["method"] == "DELETE" and record["http_status"] == 200:
                deleted_sessions.add(path.rsplit("/", 1)[-1])
            if path.startswith("/v1/accounts?"):
                require("response" not in record and "response_projection" in record,
                        "account body was retained")
    require(len(created_sessions) == 2 and created_sessions == deleted_sessions,
            "all temporary sessions must have successful deletion records")
    infos = [r["response"] for r in records if r["path"].endswith("/get_info")]
    require(len(infos) == 1 and infos[0]["is_lora"] and infos[0]["lora_rank"] == 8,
            "awaited rank-8 initialization")
    require(infos[0]["model_data"]["tokenizer_id"] is None, "tokenizer ID observation")

    access = read_json("tokenizer-access.json")
    require(not access["training_model_local_path_present"], "server-local path observation")
    require(all(c["complete_tokenizer_snapshots"] == 0 for c in access["tokenizer_cache_checks"]),
            "named tokenizer cache observations")
    tokenizer = read_jsonl("nvfp4-tokenizer-probes.jsonl")
    require(len(tokenizer) == 2 and all(r["http_status"] == 401 for r in tokenizer),
            "tokenizer HTTP observations")
    require("expired" in next(r for r in tokenizer if r["authenticated"])["response"],
            "expired credential observation")
    for record in tokenizer:
        require(hashlib.sha256(record["response"].encode()).hexdigest() == record["response_sha256"],
                "tokenizer error response hash")

    ledger = read_json("ledger.json")
    require(len(ledger["events"]) == 18, "retained HTTP event count")
    require(len({e["event_id"] for e in ledger["events"]}) == 18, "unique ledger events")
    require(sum(Decimal(str(e["estimated_incurred_usd"])) for e in ledger["events"])
            == Decimal(str(ledger["estimated_incurred_usd"])) == 0, "estimated spend total")
    require(sum(Decimal(str(e["reserved_usd"])) for e in ledger["events"])
            == Decimal(str(ledger["outstanding_reservations_usd"])) == 0, "reservation total")
    require(Decimal(str(ledger["task_cap_usd"])) == 15, "task cap")
    plan = ledger["unexecuted_estimates"]
    train = Decimal(256 * 1536) * Decimal("18.58") / 1_000_000
    paired = Decimal(32 * 2 * 1536) * (Decimal("6.19") + Decimal("15.48")) / 1_000_000
    production = Decimal(32 * 1536) * (Decimal("1.25") + Decimal("4.25")) / 1_000_000
    require(Decimal(str(plan["training"]["estimated_usd"])) == train, "training estimate")
    require(Decimal(str(plan["paired_same_sampler_eval"]["estimated_usd"])) == paired,
            "paired sampler estimate")
    require(Decimal(str(plan["token_work_total_with_optional_base_usd"]))
            == train + paired + production < 15, "unexecuted planning total")
    require(plan["on_demand"]["usd_per_replica_hour"] == 4 * 15, "deployment arithmetic")
    print(f"PASS {len(manifest['artifacts_sha256'])} frozen artifact hashes")
    print("PASS model support, rank-8 initialization, tokenizer errors, and both session deletions")
    print("PASS 18 retained HTTP events; estimated spend $0.00; reservations $0.00; cap $15.00")
    print("PASS unexecuted planning arithmetic; no training/evaluation dataset or paid token calls")


if __name__ == "__main__":
    main()
