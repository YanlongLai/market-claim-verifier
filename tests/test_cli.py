from __future__ import annotations

import json
from pathlib import Path

from claimcheck.cli import main


def test_cli_flags_plumb_output_limit_and_reasoning_effort(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setenv("CLAIMCHECK_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("CLAIMCHECK_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("CLAIMCHECK_MAX_OUTPUT_TOKENS", "321")
    monkeypatch.setenv("CLAIMCHECK_REASONING_EFFORT", "low")

    exit_code = main(
        [
            "verify",
            "Meta Q2 2025 revenue was $47.5B",
            "--dry-run",
            "--max-output-tokens",
            "777",
            "--reasoning-effort",
            "high",
        ]
    )

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["request"]["max_output_tokens"] == 777
    assert output["request"]["reasoning"] == {"effort": "high"}
    assert output["reservation"]["max_output_tokens"] == 777
