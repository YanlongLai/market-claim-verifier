"""Run one paid Meta-model probe with recorded SEC fixtures and a shared cap.

Example: .venv/bin/python scripts/multimodal/run_probe.py text post.txt
Input paths are relative to tests/fixtures/multimodal unless absolute. Existing
runs cannot be overwritten. This is an exploratory probe, not held-out scoring.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import httpx
from claimcheck.budget import Ledger
from claimcheck.config import load_settings
from claimcheck.edgar import EdgarClient
from claimcheck.ingest import ingest_file
from claimcheck.ingest_media import sha256, write_json
from claimcheck.providers import create_client
from claimcheck.release_fetch import ReleaseClient

OUT = ROOT / "docs/evidence/multimodal-2026-10-30"
MEDIA = ROOT / "tests/fixtures/multimodal"


def no_sec_network(url: str):
    raise RuntimeError("SEC document is outside the committed probe corpus")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name")
    parser.add_argument("file", type=Path)
    parser.add_argument("--provider", choices=("meta", "baseten", "fireworks"), default="meta")
    parser.add_argument("--max-output-tokens", type=int, default=8000)
    parser.add_argument("--out-root", type=Path, default=OUT)
    parser.add_argument("--budget", type=float, default=8.0)
    args = parser.parse_args()
    if not args.name.replace("-", "").isalnum():
        parser.error("name must contain letters, digits and hyphens")
    if not 0 < args.budget <= 8:
        parser.error("this recall task permits at most $8 of new spend")
    output = args.out_root.resolve()
    path = args.file if args.file.is_absolute() else MEDIA / args.file
    dest = output / args.name
    if dest.exists():
        parser.error("run already exists; choose a new name")
    meta = load_settings(provider="meta")
    text = meta if args.provider == "meta" else load_settings(provider=args.provider)
    if not meta.model_api_key or not text.model_api_key:
        parser.error("required provider key is unavailable")
    partition = {provider: args.budget / 3 for provider in ("meta", "baseten", "fireworks")}
    ledger = Ledger(output / "ledger.jsonl", budget_usd=args.budget, provider_budgets=partition)
    client = create_client(args.provider, text.model_api_key).with_options(max_retries=0, timeout=120)
    vision = client if args.provider == "meta" else create_client("meta", meta.model_api_key).with_options(max_retries=0, timeout=120)
    dest.mkdir(parents=True)
    sources = [*sorted((ROOT / "src/claimcheck").glob("*.py")), Path(__file__),
               ROOT / "pyproject.toml", ROOT / "uv.lock"]
    protocol = {"started_at": datetime.now(timezone.utc).isoformat(), "kind": "exploratory development probe",
                "input": str(path.relative_to(ROOT)), "input_sha256": sha256(path),
                "provider": args.provider, "text_model": text.model, "vision_model": "muse-spark-1.3",
                "asr_model": "muse-voice-transcribe-1.0", "total_budget_usd": args.budget,
                "budget_scope": "all runs sharing this output root; three equal provider caps",
                "partition_usd": partition, "sdk_retries": 0,
                "claim_limit_policy": "8 unique checks per extraction window for inputs over 6000 chars; otherwise 8 per channel; exact rewrite checks reused with source quotes retained",
                "transient_retry_policy": "at most 3 attempts for HTTP 500/502/503/504; 1s, 2s backoff; each attempt reserved and traced",
                "max_output_tokens": args.max_output_tokens,
                "extraction_reasoning_effort": "low for long inputs above 6000 characters; otherwise provider default",
                "sec_policy": "committed SEC snapshots only; missing data fails closed; no SEC network",
                "source_hashes": {str(p.relative_to(ROOT)): sha256(p) for p in sources}}
    write_json(dest / "protocol.json", protocol)
    print(f"Starting {args.name} ({args.provider}); total ledger ${ledger.spent_total:.6f}", flush=True)
    with tempfile.TemporaryDirectory(prefix="claimcheck-mm-corpus-") as tmp, httpx.Client(timeout=120) as http:
        cache = Path(tmp)
        for fixture in (ROOT / "tests/fixtures/sec-offline").glob("*.json"):
            shutil.copyfile(fixture, cache / fixture.name)
        shutil.copytree(ROOT / "tests/fixtures/releases/releases", cache / "releases")
        edgar = EdgarClient(cache_dir=cache, fetcher=no_sec_network)
        releases = ReleaseClient(cache, fetcher=no_sec_network)
        report = ingest_file(path, client=client, vision_client=vision, asr_http=http, meta_api_key=meta.model_api_key,
            edgar=edgar, release_client=releases, ledger=ledger, model=text.model, provider=args.provider,
            out_dir=dest, max_claims=8, max_output_tokens=args.max_output_tokens,
            secrets=[meta.model_api_key, text.model_api_key])
        protocol.update(finished_at=datetime.now(timezone.utc).isoformat(),
                        companyfacts_hashes=edgar.companyfacts_snapshot_hashes(),
                        release_documents=releases.loaded, ledger_total_usd=ledger.spent_total)
    write_json(dest / "protocol.json", protocol)
    # Decoded media can be recreated from committed inputs; retain their hashes,
    # not redundant multi-megabyte WAVs in every evidence directory.
    for channel in report["channels"]:
        if "audio" in channel:
            (dest / channel.pop("audio")).unlink(missing_ok=True)
            channel["decoded_audio"] = "recreate with ingest; redundant WAV omitted from evidence commit"
        for chunk in channel.get('audio_chunks', []):
            (dest / chunk.pop('audio')).unlink(missing_ok=True)
            chunk['decoded_audio'] = 'recreate with ingest; redundant WAV omitted from evidence commit'
        if channel["kind"] == "ocr" and "image" in channel:
            (dest / channel.pop("image")).unlink(missing_ok=True)
    write_json(dest / "ingest.json", report)
    print(json.dumps({"name": args.name, "status": report["status"], "cost_usd": report["cost_usd"],
                      "seconds": report["wall_clock_s"], "stages": [s["status"] for s in report["stages"]],
                      "ledger_total_usd": ledger.spent_total}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
