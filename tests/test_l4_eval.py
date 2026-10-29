from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest


def runner_module():
    path = Path(__file__).resolve().parents[1] / "eval/l4/run_agent.py"
    spec = importlib.util.spec_from_file_location("l4_runner", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_wilson_and_false_supported_denominators():
    module = runner_module()
    low, high = module.wilson(0, 19)
    assert low == 0 and .16 < high < .18
    rows = [{"gold": g, "predicted": p, "kind": "guidance", "cost_usd": .1, "wall_seconds": i + 1, "model_calls": 2}
            for i, (g, p) in enumerate([("supported", "supported"), ("contradicted", "supported"), ("insufficient_evidence", "insufficient_evidence")])]
    metrics = module.summarize(rows, .31)
    assert metrics["correct"] == 2 and metrics["false_supported_rate"] == .5
    assert metrics["false_discovery_among_supported"] == .5
    assert metrics["cost_usd"] == .31 and metrics["wall_seconds_p95_nearest_rank"] == 3
    assert module.wilson(0, 0) is None


def test_uncommitted_gold_prevents_any_model_run(monkeypatch):
    module = runner_module()
    monkeypatch.setattr(module.subprocess, "check_output", lambda *a, **k: b"a" * 40)
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 128, stdout=b"", stderr=b"not committed"))
    with pytest.raises(RuntimeError, match="Gold must be committed"):
        module.freeze_proof()
