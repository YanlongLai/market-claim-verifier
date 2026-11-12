import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
import pytest

SPEC = importlib.util.spec_from_file_location("native_proposals", Path(__file__).parents[1] / "scripts/claude-code-proposals.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def setup(monkeypatch, tmp_path):
    for key in list(module.os.environ):
        if key.startswith(("ANTHROPIC_", "CLAUDE_CODE_USE_")) or key == "CLAUDE_CODE_OAUTH_TOKEN": monkeypatch.delenv(key)
    source = tmp_path / "input.txt"
    source.write_text("public test claim")
    out = tmp_path / "run"
    monkeypatch.setattr(sys, "argv", ["native", str(source), "--out", str(out)])
    return out


@pytest.mark.parametrize("auth", [{"loggedIn": False}, {"loggedIn":True,"authMethod":"claude.ai","subscriptionType":"max","apiProvider":"thirdParty"}, {"loggedIn":True,"authMethod":"api_key","subscriptionType":"max"}, {"loggedIn":True,"authMethod":"claude.ai","subscriptionType":"pro"}])
def test_auth_rejected_before_inference(monkeypatch,tmp_path,auth):
    out=setup(monkeypatch,tmp_path); calls=[]
    def run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command,0,json.dumps(auth),"")
    monkeypatch.setattr(module.subprocess,"run",run)
    assert module.main()==1
    assert len(calls)==1
    assert not (out/"proposals.json").exists()
    assert json.loads((out/"receipt.json").read_text())["status"]=="failed"


def test_override_no_call(monkeypatch,tmp_path):
    setup(monkeypatch,tmp_path)
    monkeypatch.setenv("ANTHROPIC_API_KEY","test-not-a-key")
    monkeypatch.setattr(module.subprocess,"run",lambda *a,**k: pytest.fail("must not invoke"))
    with pytest.raises(SystemExit): module.main()


@pytest.mark.parametrize("failure", [False, True])
def test_isolation_and_timeout_receipt(monkeypatch,tmp_path,failure):
    out=setup(monkeypatch,tmp_path); calls=[]
    def run(command, **kwargs):
        calls.append(command)
        if len(calls)==1:
            return subprocess.CompletedProcess(command,0,json.dumps({"loggedIn":True,"authMethod":"claude.ai","apiProvider":"firstParty","subscriptionType":"max"}),"")
        for flag in ["--disable-slash-commands","--no-session-persistence","--strict-mcp-config"]: assert flag in command
        assert command[command.index("--tools")+1]==""
        assert command[command.index("--setting-sources")+1]==""
        assert json.loads(command[command.index("--settings")+1])["disableAllHooks"] is True
        assert "--bare" not in command
        schema = json.loads(command[command.index("--json-schema")+1])
        period_pattern = schema["properties"]["claims"]["items"]["properties"]["period"]["pattern"]
        for period in ("2025Q2", "FY2025Q2", "FY2025"):
            assert re.fullmatch(period_pattern, period)
        for period in ("CY2025-Q2", "2025-Q2", "2025", "latest"):
            assert not re.fullmatch(period_pattern, period)
        assert kwargs["timeout"]==180
        if failure: raise subprocess.TimeoutExpired(command,180)
        return subprocess.CompletedProcess(command,0,json.dumps({"structured_output":{"schema_version":"sec-proposals-v1","claims":[]}}),"")
    monkeypatch.setattr(module.subprocess,"run",run)
    assert module.main()==int(failure)
    assert (out/"proposals.json").exists() is not failure
    assert (out/"receipt.json").stat().st_mode & 0o777 == 0o600
