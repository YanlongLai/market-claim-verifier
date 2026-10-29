"""Recheck the frozen agent traces offline; never creates a model client or reads a key."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from claimcheck.agent import _parse_strict_verdict
from claimcheck.checks import evaluate_verdict
from claimcheck.edgar import EdgarClient
from claimcheck.release_fetch import ReleaseClient, ReleaseError
from claimcheck.tools import ToolRunner


def offline(url):
    raise ReleaseError("URL not in recorded corpus")


def replay(directory: Path):
    protocol = json.loads((directory / "protocol.json").read_text())
    for name, expected in protocol["gold_freeze"]["sha256"].items():
        if name.startswith("tests/fixtures/releases/") or name.startswith("eval/l4/") and name != "eval/l4/run_agent.py":
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    result_rows = [json.loads(line) for line in (directory / "results.jsonl").read_text().splitlines()]
    rows = []
    for recorded in result_rows:
        trace = json.loads((directory / recorded["trace"]).read_text())
        runner = ToolRunner(EdgarClient(ROOT / "tests/fixtures/releases/xbrl", fetcher=offline),
                            release_client=ReleaseClient(ROOT / "tests/fixtures/releases", fetcher=offline))
        for call in trace["tool_calls"]:
            if call.get("role") != "program":
                runner.dispatch(call["name"], call["arguments"])
        raw = trace["requests"][-1]["raw_response"]
        message = raw.get("choices", [{}])[0].get("message", {}).get("content", "")
        verdict = _parse_strict_verdict(message)
        if verdict is None:
            predicted = "insufficient_evidence"
        else:
            checks, predicted = evaluate_verdict([{**s, "original_claim": recorded["claim"]} for s in verdict["sub_claims"]], runner)
        rows.append({"id": recorded["id"], "recorded": recorded["predicted"], "replayed": predicted})
    changes = [r for r in rows if r["recorded"] != r["replayed"]]
    output = {"frozen_runtime_commit": protocol["gold_freeze"]["revision"], "new_model_calls": 0,
              "n": len(rows), "unchanged_verdicts": len(rows) - len(changes), "changes": changes,
              "source_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                                for path in sorted((ROOT / "src/claimcheck").glob("*.py"))},
              "note": "Offline recheck after numeric edge-case guards and inspected-source report links. Original live-run metrics remain tied to the frozen commit; no model resampling or new accuracy estimate."}
    (directory / "POST_RUN_REPLAY.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({k: v for k, v in output.items() if k not in {"source_sha256", "note"}}))
    assert not changes, "Post-run code changed a frozen-trace verdict"
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, nargs="?", default=ROOT / "docs/evidence/eval-l4-2026-10-29")
    replay(parser.parse_args().directory)
