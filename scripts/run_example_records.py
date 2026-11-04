#!/usr/bin/env python3
"""HOST ONLY: freeze and retain one real request per example. Never retry/overwrite.

The API server, not this script, enforces the durable spending cap. Preflight
requires its whole daily limit to fit the frozen run budget.
Passwords remain in request memory; only public responses and hashes are saved.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import getpass
import hashlib
import json
import os
from pathlib import Path
import time
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
IDS = ("text", "image", "pdf", "audio", "video")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def stamp():
    return datetime.now(timezone.utc).isoformat()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def fetch(origin, path, body=None):
    request = Request(origin + path, data=body, headers={"Content-Type": "application/json", "Origin": origin,
                                                      "Cache-Control": "no-cache"})
    try:
        response = build_opener(NoRedirect()).open(request, timeout=70)
    except HTTPError as error:
        response = error
    with response:
        raw = response.read(5_000_001)
        if len(raw) > 5_000_000:
            raise ValueError("Response too large")
        return response.status, raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", required=True, help="Pages site origin, e.g. https://hackathon.dappgo.com")
    parser.add_argument("--ids", nargs="+", choices=IDS, default=list(IDS))
    parser.add_argument("--max-spend-usd", required=True, type=float, help="Freeze a cap at least as large as the server's whole daily limit")
    parser.add_argument("--output", type=Path, help="New directory under docs/evidence/example-records")
    parser.add_argument("--execute", action="store_true", help="Required to make model/SEC requests through the live API")
    args = parser.parse_args()
    origin = args.origin.rstrip("/")
    url = urlsplit(origin)
    if url.scheme != "https" or not url.netloc or url.path or url.query or url.fragment or url.username or url.password:
        parser.error("--origin must be a plain HTTPS origin")
    if len(set(args.ids)) != len(args.ids) or not 0 < args.max_spend_usd <= 20:
        parser.error("IDs must be unique; budget must be finite and in (0, 20]")
    assets = {row["id"]: row for row in json.loads((ROOT / "docs/site/examples/manifest.json").read_text())}
    for example_id in args.ids:
        asset = assets[example_id]
        path = ROOT / "docs/site/examples" / asset["file"]
        if asset["status"] != "ready" or hashlib.sha256(path.read_bytes()).hexdigest() != asset["sha256"]:
            parser.error(f"{example_id}: build/verify the real asset before recording")
    if not args.execute:
        parser.error("No requests made. Add --execute on the host to record the frozen inputs.")
    parent = ROOT / "docs/evidence/example-records"
    output = args.output or parent / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    output = output.resolve()
    if not output.is_relative_to(parent.resolve()):
        parser.error("--output must be under docs/evidence/example-records")
    output.mkdir(parents=True, exist_ok=False)
    write(output / "plan.json", {"created_at": stamp(), "origin": origin, "examples": [assets[i] for i in args.ids],
          "max_spend_usd": args.max_spend_usd, "attempts_per_id": 1, "request_timeout_s": 70,
          "server_media_timeout_s": 60, "retention": "All failures/partial responses retained; no retries.",
          "providers": {"checks": "baseten", "ocr_asr": "meta"},
          "models": {"checks": "meta-models/muse-spark-open-1026", "ocr": "muse-spark-1.3", "asr": "muse-voice-transcribe-1.0"},
          "limits": {"check_calls": 4, "check_output_tokens": 2000, "tools": 6, "ocr_output_tokens": 3000},
          "source_hashes": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in (
              "server/live/server.py", "workers/live/src/live.py", "src/claimcheck/ingest_media.py",
              "src/claimcheck/agent.py", "src/claimcheck/budget.py", "src/claimcheck/providers.py")},
          "expected_outcomes": "Self-made post includes an intentionally wrong Apple quarter. No new accuracy or extraction-recall claim.",
          "record_scope": "Public API envelopes: read text, cost metrics, tool/program trace and SEC evidence; provider-private bodies are not exposed.",
          "retests_ocr_asr": any(i in {"image", "audio", "video"} for i in args.ids)})
    status, raw = fetch(origin, "/api/budget")
    (output / "budget-before.json").write_bytes(raw)
    budget = json.loads(raw)
    if (status != 200 or budget.get("status") != "ready" or budget.get("mode") == "mock" or
        not 0 < budget["daily_remaining_usd"] <= budget["daily_limit_usd"] <= args.max_spend_usd):
        raise SystemExit("Preflight failed; retain this plan. Server's whole daily limit must fit --max-spend-usd.")
    reset = datetime.fromisoformat(budget["resets_at"].replace("Z", "+00:00")).timestamp()
    password = os.environ.get("LIVE_CHECK_PASSWORD")
    if password is None and os.environ.get("LIVE_CHECK_PASSWORD_FILE"):
        password = Path(os.environ["LIVE_CHECK_PASSWORD_FILE"]).read_text().rstrip("\r\n")
    if password is None:
        password = getpass.getpass("Live-check password (not recorded): ")
    failed = []
    for example_id in args.ids:
        if reset - time.time() <= 75:
            break  # Do not start a 70-second request near the next allowance.
        folder = output / example_id
        folder.mkdir()
        started, before = stamp(), time.monotonic()
        receipt = {"example_id": example_id, "asset_sha256": assets[example_id]["sha256"], "started_at": started,
                   "attempts": 1, "request": {"example_id": example_id}, "http_status": None}
        write(folder / "receipt.json", receipt)
        try:
            status, raw = fetch(origin, "/api/check-example", json.dumps({"example_id": example_id, "password": password}).encode())
            (folder / "response.json").write_bytes(raw)
            receipt.update(http_status=status, response_sha256=hashlib.sha256(raw).hexdigest())
            result = json.loads(raw)
            if status != 200 or result.get("mode") != "live" or result.get("error"):
                failed.append(example_id)
        except Exception as error:
            # Exception messages may contain remote bodies; retain only type.
            receipt["failure_type"] = type(error).__name__
            failed.append(example_id)
        finally:
            receipt.update(finished_at=stamp(), latency_ms=round((time.monotonic() - before) * 1000, 3))
            write(folder / "receipt.json", receipt)
        status, raw = fetch(origin, "/api/budget")
        (folder / "budget-after.json").write_bytes(raw)
        current = json.loads(raw)
        if (status != 200 or current.get("status") != "ready" or current.get("day") != budget["day"] or
            current.get("daily_limit_usd", float("inf")) > args.max_spend_usd):
            break  # Never cross a daily reset into a second allowance.
    print(output.relative_to(ROOT))
    if failed:
        raise SystemExit("Retained incomplete/failed attempts: " + ", ".join(failed))
    if len(list(output.glob("*/receipt.json"))) != len(args.ids):
        raise SystemExit("Budget stopped the recording; all attempted records were retained")
    print("Build saved envelopes: python3 scripts/build_example_results.py --records " + str(output.relative_to(ROOT)))


if __name__ == "__main__":
    main()
