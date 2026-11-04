"""Offline log privacy, late-ID SSH capture and real PTY recording regressions."""
import asyncio
import copy
import json
import logging
import os
from pathlib import Path
import re
import shlex
import sys

import httpx
import pytest

from claimcheck.cli import main as cli
from claimcheck.progress import format_event
from scripts import record_cli_session, tail_live_log
from test_live_server import APPLE, PASSWORD, TOKEN, TRACE, data, fixture_sec, request, running, settings


def test_live_info_lines_match_envelope_and_exclude_private_data(tmp_path, caplog):
    async def run():
        responses = iter(copy.deepcopy(TRACE["requests"]))
        async def transport(req):
            if req.url.host == "inference.baseten.co":
                raw = next(responses)["raw_response"]
                raw["choices"][0]["message"]["reasoning_content"] = "private-reasoning-marker"
                return httpx.Response(200, json=raw)
            return httpx.Response(200, text=await fixture_sec(str(req.url)))
        async with running(settings(tmp_path), transport) as (app, services):
            result = data(await request(app))
            saved = await services.ledger.history(limit=1)
            retained = await services.ledger.history(record_id=saved["rows"][0]["id"])
            assert retained["envelope"]["request_id"] == result["request_id"]
            return result
    with caplog.at_level(logging.INFO, logger="claimcheck.live"):
        result = asyncio.run(run())
    lines = [r.getMessage() for r in caplog.records if r.name == "claimcheck.live"]
    assert re.fullmatch(r"[0-9a-f]{32}", result["request_id"])
    assert lines and all(re.match(fr"live id={result['request_id']} \+\d+\.\d{{2}}s event=\w+", line) for line in lines)
    for line in lines:
        assert "\n" not in line and "\r" not in line
        assert all("=" in field for field in shlex.split(line)[3:])
    assert "event=start" in lines[0] and "kind=text" in lines[0]
    assert "event=tool_call" in "\n".join(lines) and "ticker=AAPL" in "\n".join(lines)
    assert "event=tool_result" in "\n".join(lines) and "evidence_id=E1" in "\n".join(lines)
    assert "event=verdict verdict=supported claims=1 cost=$" in lines[-1]
    for private in (PASSWORD, TOKEN, "offline-api-key-marker", "192.0.2.1", APPLE["claim"], "private-reasoning-marker"):
        assert private not in "\n".join(lines)


def test_error_logs_do_not_echo_provider_bodies_and_keep_cost_holds(tmp_path, caplog):
    async def run():
        async def transport(req):
            return httpx.Response(500, text=PASSWORD + TOKEN + "192.0.2.1")
        async with running(settings(tmp_path), transport) as (app, services):
            result = data(await request(app))
            assert result["error"] == "provider_error" and result["cost_is_bound"]
            assert (await services.gate("budget", {}))["daily_spent_usd"] > 0
            return result
    with caplog.at_level(logging.INFO, logger="claimcheck.live"):
        result = asyncio.run(run())
    assert f"id={result['request_id']}" in caplog.text and "event=error code=provider_error" in caplog.text
    assert PASSWORD not in caplog.text and TOKEN not in caplog.text and "192.0.2.1" not in caplog.text


@pytest.mark.parametrize("bad", ["secret\nlive id=fake", {"private": "value"}, ["secret"], None, True])
def test_progress_drops_arbitrary_strings_and_malformed_fields(bad):
    line = format_event("live id=" + "a" * 32, 1.23, "tool_call", {
        "name": bad, "arguments": {"ticker": bad, "metric": bad, "period": bad}, "input": bad,
        "reasoning_content": "never-log-this", "value": float("nan")})
    assert "secret" not in line and "never-log-this" not in line and "nan" not in line
    assert "\n" not in line
    assert "ticker=" not in line and "metric=" not in line and "period=" not in line
    assert "AAPL" not in format_event("cli", 0, "tool_call", {
        "name": "lookup_fact", "arguments": {"ticker": "AAPL", "metric": "revenue", "period": "FY2024"}}, secrets=["AAPL"])


@pytest.mark.parametrize("provider,model", [("baseten", "meta-models/muse-spark-open-1026"),
    ("fireworks", "accounts/fireworks/models/muse-spark-open"), ("meta", "muse-spark-1.3")])
def test_post_dry_run_without_key_files_or_network(provider, model, tmp_path, monkeypatch, capsys):
    for key in ("BASETEN_API_KEY", "FIREWORKS_API_KEY", "MODEL_API_KEY", "CLAIMCHECK_MODEL"):
        monkeypatch.delenv(key, raising=False)
    for name in ("BASETEN_API_KEY_FILE", "FIREWORKS_API_KEY_FILE", "MODEL_API_KEY_FILE"):
        # Opening this directory as a key file would fail.
        monkeypatch.setenv(name, str(tmp_path))
    source = tmp_path / "post.txt"
    source.write_text(APPLE["claim"])
    monkeypatch.setenv("CLAIMCHECK_RUNS_DIR", str(tmp_path / "no-runs"))
    assert cli(["post", str(source), "--provider", provider, "--budget", "1", "--dry-run"]) == 0
    captured = capsys.readouterr()
    value = json.loads(captured.out)
    assert value["dry_run"] and value["model"] == model
    assert value["reservation"]["amount"] > 0
    assert "Local · CLI · dry run" in captured.err
    assert not (tmp_path / "no-runs").exists()


def executable(tmp_path, name, source):
    path = tmp_path / name
    path.write_text(f"#!{sys.executable}\n" + source)
    path.chmod(0o755)
    return path


def test_host_log_buffers_then_filters_a_late_id_and_keeps_partial_spool(tmp_path, monkeypatch, capsys):
    selected, other = "a" * 32, "b" * 32
    password = tmp_path / "password"
    password.write_text("sudo-private-marker\n")
    id_file = tmp_path / "request-id"
    executable(tmp_path, "ssh", f'''import os, sys, time
password = sys.stdin.readline()
assert password.strip() == "sudo-private-marker"
assert "dappgo-ha-cp-1" in sys.argv
assert "sudo -S" in sys.argv[-1] and "deployment/live-check" in sys.argv[-1]
print("unrelated private text", flush=True)
print("2026-11-04T00:00:00Z live id={other} +0.00s event=start", flush=True)
print("2026-11-04T00:00:01Z live id={selected} +0.00s event=start", flush=True)
print("2026-11-04T00:00:02Z live id={selected} +1.00s event=verdict verdict=supported", flush=True)
time.sleep(0.05)
from pathlib import Path
Path({str(id_file)!r}).write_text('{{"request_id": "{selected}"}}')
time.sleep(10)
''')
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + os.environ["PATH"])
    monkeypatch.setenv("DAPPGO_HA_SUDO_FILE", str(password))
    out = tmp_path / "online.jsonl"
    assert tail_live_log.main(["--out", str(out), "--request-id-file", str(id_file), "--stop-after-verdict", "--duration", "3"]) == 0
    rows = [json.loads(line) for line in out.read_text().splitlines()]
    assert len(rows) == 2 and all(selected in row["line"] for row in rows)
    assert all(set(row) == {"t_wall", "t_rel_s", "line"} for row in rows)
    assert rows[0]["t_rel_s"] <= rows[1]["t_rel_s"]
    assert len((tmp_path / "online.jsonl.all.jsonl").read_text().splitlines()) == 3
    assert "sudo-private-marker" not in capsys.readouterr().out + out.read_text()
    filtered = tmp_path / "filtered.jsonl"
    assert tail_live_log.main(["--filter-only", str(out) + ".all.jsonl", "--request-id", other, "--out", str(filtered)]) == 0
    assert len(filtered.read_text().splitlines()) == 1


def test_pty_capture_preserves_chunks_command_exit_receipt_and_split_key(tmp_path, monkeypatch, capsys):
    executable(tmp_path, "uv", '''import json, os, sys, time
assert os.isatty(1) and os.isatty(2)
assert sys.argv[1:6] == ["run", "python", "-m", "claimcheck", "post"]
os.write(1, b"tool_call lookup_fact AAPL\\nprivate-key-")
time.sleep(0.05)
os.write(1, b"marker\\n")
print(json.dumps({"counts": {"verified": 1}, "verdicts": {"contradicted": 1}, "cost_usd": 0.01}), flush=True)
raise SystemExit(7)
''')
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + os.environ["PATH"])
    monkeypatch.setenv("BASETEN_API_KEY", "private-key-marker")
    for name in ("BASETEN_API_KEY_FILE", "FIREWORKS_API_KEY_FILE", "MODEL_API_KEY_FILE"):
        monkeypatch.setenv(name, str(tmp_path / "missing-key"))
    (tmp_path / "post.txt").write_text(APPLE["claim"])
    out = tmp_path / "cli.json"
    assert record_cli_session.main(["post.txt", "--out", str(out), "--cwd", str(tmp_path), "--dry-run"]) == 7
    saved = json.loads(out.read_text())
    assert saved["label"] == "Local · CLI" and saved["dry_run"]
    assert saved["command"][0:6] == ["uv", "run", "python", "-m", "claimcheck", "post"]
    assert "--budget" in saved["command"] and "--dry-run" in saved["command"]
    assert saved["exit_code"] == 7 and saved["duration_s"] > 0
    assert saved["receipt_summary"]["cost_usd"] == 0.01
    assert len(saved["chunks"]) >= 2
    assert all(set(row) == {"t_rel_s", "text"} for row in saved["chunks"])
    assert "private-key-marker" not in out.read_text() + capsys.readouterr().out
    assert "[REDACTED]" in "".join(row["text"] for row in saved["chunks"])
    assert record_cli_session.main(["post.txt", "--out", str(out), "--cwd", str(tmp_path), "--dry-run"]) == 2
