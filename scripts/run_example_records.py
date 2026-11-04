#!/usr/bin/env python3
"""HOST ONLY: record the production Baseten API once per frozen example.

Requires LIVE_CHECK_PASSWORD_FILE and --execute. Preserve all attempts, redact
responses, never retry/overwrite, and publish only complete live envelopes.
The server's entire daily allowance must fit the explicit recording budget.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import time
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
IDS = tuple(f"{story}-{kind}" for story in "abc" for kind in ("text", "image", "pdf", "audio", "video"))
MODEL = "meta-models/muse-spark-open-1026"
TIMEOUT = 70


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def stamp():
    return datetime.now(timezone.utc).isoformat()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def write(path, value, *, exclusive=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb" if exclusive else "wb") as stream:
        stream.write(encoded(value))


def fetch(origin, path, body=None):
    request = Request(origin + path, data=body, headers={"Content-Type": "application/json", "Origin": origin,
                                                      "Cache-Control": "no-cache"})
    try:
        response = build_opener(NoRedirect()).open(request, timeout=TIMEOUT)
    except HTTPError as error:
        response = error
    with response:
        raw = response.read(5_000_001)
        if len(raw) > 5_000_000:
            raise ValueError("Response too large")
        return response.status, raw


def sanitized(raw, password):
    """Retain redacted response bytes, including malformed/non-JSON failures."""
    def scrub(value):
        if isinstance(value, dict):
            return {str(k).replace(password, "[REDACTED]"):
                    "[REDACTED]" if k.lower() in {"password", "authorization", "api_key", "token"} else scrub(v)
                    for k, v in value.items()}
        if isinstance(value, list):
            return [scrub(v) for v in value]
        return value.replace(password, "[REDACTED]") if isinstance(value, str) else value
    try:
        return encoded(scrub(json.loads(raw)))
    except (ValueError, UnicodeDecodeError):
        for secret in (password.encode(), json.dumps(password)[1:-1].encode(), json.dumps(password, ensure_ascii=False)[1:-1].encode()):
            raw = raw.replace(secret, b"[REDACTED]")
        return raw


def retain(path, raw, password):
    public = sanitized(raw, password)
    path.write_bytes(public)
    return public


def complete(result, asset):
    read = result.get("input", {})
    receipt = result.get("receipt", {})
    return (result.get("mode") == "live" and not result.get("error") and
            result.get("verdict") in {"supported", "contradicted", "insufficient_evidence"} and
            read.get("example_id") == asset["id"] and read.get("kind") == asset["kind"] and
            read.get("story", asset["story"]) == asset["story"] and
            isinstance(read.get("text_read"), str) and bool(read["text_read"].strip()) and
            receipt.get("provider") == "baseten" and receipt.get("model") == MODEL and
            all(isinstance(result.get(k), list) for k in ("claims", "evidence", "events")) and
            isinstance(result.get("corrections"), (dict, list)))


def recorded_envelope(folder, asset, *, root=None):
    """Reproduce a public saved result solely from a complete retained attempt."""
    root = ROOT if root is None else root
    receipt_path, response_path = folder / "receipt.json", folder / "response.json"
    receipt_raw, raw = receipt_path.read_bytes(), response_path.read_bytes()
    receipt, result = json.loads(receipt_raw), json.loads(raw)
    if (receipt.get("http_status") != 200 or receipt.get("attempts") != 1 or
        receipt.get("example_id") != asset["id"] or receipt.get("asset_sha256") != asset["sha256"] or
        receipt.get("response_sha256") != sha(raw) or not complete(result, asset)):
        raise ValueError("Incomplete or mismatched retained recording")
    result.update(mode="recorded", source=str(response_path.relative_to(root)), source_sha256=sha(raw),
                  recording={"receipt": str(receipt_path.relative_to(root)), "receipt_sha256": sha(receipt_raw),
                             "asset_sha256": asset["sha256"], "attempts": 1,
                             "retests_ocr_asr": asset["kind"] in {"image", "audio", "video"}},
                  timing_note="One production request, including the original input preprocessing; no frozen-transcript recheck.")
    return result


def check_saved(asset, *, root=None):
    root = ROOT if root is None else root
    path = root / f"docs/site/data/examples/{asset['id']}.json"
    if not path.exists():
        return None
    saved = json.loads(path.read_bytes())
    receipt = (root / saved["recording"]["receipt"]).resolve()
    if not receipt.is_relative_to((root / "docs/evidence/example-records").resolve()):
        raise ValueError("Saved recording receipt is outside retained evidence")
    expected = recorded_envelope(receipt.parent, asset, root=root)
    if path.read_bytes() != encoded(expected):
        raise ValueError(f"Stale saved example: {asset['id']}")
    return f"/data/examples/{asset['id']}.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", default="https://hackathon.dappgo.com", help="Production Pages origin")
    parser.add_argument("--ids", nargs="+", choices=IDS, default=list(IDS))
    parser.add_argument("--max-spend-usd", required=True, type=float, help="Cap covering the server's entire daily allowance")
    parser.add_argument("--output", type=Path, help="New directory under docs/evidence/example-records")
    parser.add_argument("--execute", action="store_true", help="HOST ONLY: make live model/SEC requests via the API")
    args = parser.parse_args()
    origin = args.origin.rstrip("/")
    url = urlsplit(origin)
    if url.scheme != "https" or not url.netloc or url.path or url.query or url.fragment or url.username or url.password:
        parser.error("--origin must be a plain HTTPS origin")
    if len(set(args.ids)) != len(args.ids) or not math.isfinite(args.max_spend_usd) or not 0 < args.max_spend_usd <= 20:
        parser.error("IDs must be unique; budget must be finite and in (0, 20]")
    manifest_path = ROOT / "docs/examples/manifest.json"
    assets = {row["id"]: row for row in json.loads(manifest_path.read_text())}
    for example_id in args.ids:
        asset = assets[example_id]
        path = ROOT / "docs/examples" / asset["file"]
        if (not path.resolve().is_relative_to((ROOT / "docs/examples").resolve()) or path.is_symlink() or
            asset["status"] != "ready" or sha(path.read_bytes()) != asset["sha256"] or
            path.stat().st_size != asset["size_bytes"]):
            parser.error(f"{example_id}: build/verify the real asset before recording")
        if (ROOT / f"docs/site/data/examples/{example_id}.json").exists():
            parser.error(f"{example_id}: saved result already exists; retained records are never overwritten")
    if not args.execute:
        parser.error("No requests made. Add --execute on the host to record the frozen inputs.")
    password_file = os.environ.get("LIVE_CHECK_PASSWORD_FILE")
    if not password_file:
        parser.error("Set LIVE_CHECK_PASSWORD_FILE to the host's password file")
    try:
        password = Path(password_file).read_text().rstrip("\r\n")
    except OSError:
        parser.error("Cannot read LIVE_CHECK_PASSWORD_FILE")
    if not password or len(password) < 8:
        parser.error("LIVE_CHECK_PASSWORD_FILE must contain the configured live password (at least 8 characters)")
    parent = ROOT / "docs/evidence/example-records"
    output = (args.output or parent / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")).resolve()
    if not output.is_relative_to(parent.resolve()):
        parser.error("--output must be under docs/evidence/example-records")
    output.mkdir(parents=True, exist_ok=False)
    write(output / "plan.json", {"created_at": stamp(), "origin": origin, "examples": [assets[i] for i in args.ids],
          "manifest_sha256": sha(manifest_path.read_bytes()), "max_spend_usd": args.max_spend_usd,
          "attempts_per_id": 1, "request_timeout_s": TIMEOUT, "server_media_timeout_s": 60,
          "retention": "All failures/partial responses retained with credentials redacted; no retries or overwrite.",
          "providers": {"checks": "baseten", "ocr_asr": "meta"},
          "models": {"checks": MODEL, "ocr": "muse-spark-1.3", "asr": "muse-voice-transcribe-1.0"},
          "source_hashes": {name: sha((ROOT / name).read_bytes()) for name in (
              "scripts/build_examples.py", "scripts/run_example_records.py", "docs/examples/stories.json",
              "src/claimcheck/ingest_media.py", "src/claimcheck/agent.py", "src/claimcheck/budget.py", "src/claimcheck/providers.py")},
          "record_scope": "Public API envelopes, read text, receipts, program traces and SEC evidence. Provider-private bodies are not exposed. No new accuracy claim.",
          "retests_ocr_asr": any(assets[i]["kind"] in {"image", "audio", "video"} for i in args.ids)}, exclusive=True)
    status, raw = fetch(origin, "/examples/manifest.json")
    deployed_raw = retain(output / "deployed-manifest.json", raw, password)
    deployed = {row["id"]: row for row in json.loads(deployed_raw)} if status == 200 else {}
    if any(deployed.get(i, {}).get("sha256") != assets[i]["sha256"] or deployed.get(i, {}).get("status") != "ready" for i in args.ids):
        raise SystemExit("Preflight failed: deploy these exact assets before recording; plan retained, no paid calls.")
    status, raw = fetch(origin, "/api/budget")
    budget = json.loads(retain(output / "budget-before.json", raw, password))
    if (status != 200 or budget.get("status") != "ready" or budget.get("mode") == "mock" or
        not 0 < budget.get("daily_remaining_usd", 0) <= budget.get("daily_limit_usd", 0) <= args.max_spend_usd):
        raise SystemExit("Preflight failed; server's whole daily allowance must fit --max-spend-usd. Plan retained.")
    reset = datetime.fromisoformat(budget["resets_at"].replace("Z", "+00:00")).timestamp()
    failed, attempted = [], []
    for example_id in args.ids:
        if reset - time.time() <= TIMEOUT + 5:
            break
        asset = assets[example_id]
        folder = output / example_id
        folder.mkdir()
        attempted.append(example_id)
        before = time.monotonic()
        receipt = {"example_id": example_id, "asset_sha256": asset["sha256"], "started_at": stamp(), "attempts": 1,
                   "request": {"example_id": example_id, "provider": "baseten"}, "http_status": None}
        write(folder / "receipt.json", receipt)
        try:
            status, raw = fetch(origin, "/api/check-example", json.dumps({"example_id": example_id, "provider": "baseten", "password": password}).encode())
            public = retain(folder / "response.json", raw, password)
            receipt.update(http_status=status, response_sha256=sha(public), wire_response_sha256=sha(raw),
                           response_storage="redacted JSON" if public != raw else "original bytes")
            result = json.loads(public)
            if status != 200 or not complete(result, asset):
                failed.append(example_id)
            else:
                receipt["publishable"] = True
        except Exception as error:
            receipt["failure_type"] = type(error).__name__
            failed.append(example_id)
        finally:
            receipt.update(finished_at=stamp(), latency_ms=round((time.monotonic() - before) * 1000, 3))
            write(folder / "receipt.json", receipt)
        if receipt.get("publishable"):
            write(ROOT / f"docs/site/data/examples/{example_id}.json", recorded_envelope(folder, asset), exclusive=True)
        try:
            status, raw = fetch(origin, "/api/budget")
            current = json.loads(retain(folder / "budget-after.json", raw, password))
            if (status != 200 or current.get("status") != "ready" or current.get("day") != budget["day"] or
                current.get("daily_limit_usd", float("inf")) > args.max_spend_usd or
                current.get("daily_remaining_usd", 0) <= 0):
                break
        except Exception as error:
            write(folder / "budget-after-error.json", {"failure_type": type(error).__name__})
            break
    write(output / "summary.json", {"finished_at": stamp(), "attempted": attempted, "failed": failed,
                                   "unattempted": [i for i in args.ids if i not in attempted]})
    print(output.relative_to(ROOT))
    print("Refresh catalogue offline: uv run --frozen python scripts/build_examples.py")
    if failed or len(attempted) != len(args.ids):
        raise SystemExit("Recording incomplete; all attempted outcomes retained. Review summary.json; no retries made.")
    print(f"Published {len(attempted)} recorded envelopes under docs/site/data/examples/")


if __name__ == "__main__":
    main()
