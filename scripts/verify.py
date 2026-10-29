#!/usr/bin/env python3
"""Run offline verification in a disposable copy; never rebuild the user's files."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", ".venv", ".cache", ".pytest_cache", "__pycache__", "node_modules"}
DATA_OUTPUTS = (
    "docs/explorer/data.json",
    "docs/site/data/site.json",
    "docs/site/BUILD_SUMMARY.md",
)

PYTHON_GUARD = '''import socket
_connect = socket.socket.connect
def _offline(*args, **kwargs):
    raise RuntimeError("verify: network access is disabled")
def _guarded_connect(self, address):
    if self.family in (socket.AF_INET, socket.AF_INET6):
        return _offline()
    return _connect(self, address)
socket.socket.connect = _guarded_connect
socket.socket.connect_ex = _guarded_connect
socket.create_connection = _offline
'''

NODE_GUARD = '''const deny = () => { throw new Error("verify: network access is disabled"); };
for (const name of ["node:http", "node:https"]) {
  const api = require(name); api.get = deny; api.request = deny;
}
const net = require("node:net");
net.connect = deny; net.createConnection = deny; net.Socket.prototype.connect = deny;
globalThis.fetch = deny;
require("node:module").syncBuiltinESMExports();
'''


def copy_ignored(folder: str, names: list[str]) -> list[str]:
    ignored = [name for name in names if name in SKIP or (Path(folder) / name).is_symlink()]
    if Path(folder) == ROOT / "demo":
        ignored.extend(name for name in names if name in {"cache", "out"})
    return ignored


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--demo-python", type=Path, required=True)
    args = parser.parse_args()
    work = args.work_dir.resolve()
    snapshot = work / "repo"
    shutil.copytree(ROOT, snapshot, ignore=copy_ignored)
    guard = work / "offline-guard"
    guard.mkdir()
    (guard / "sitecustomize.py").write_text(PYTHON_GUARD, encoding="utf-8")
    (guard / "offline.cjs").write_text(NODE_GUARD, encoding="utf-8")
    env = {
        key: value for key, value in os.environ.items()
        if not key.startswith(("CLAIMCHECK_", "BASETEN_", "FIREWORKS_", "MODEL_API_", "OPENAI_"))
        and key not in {"PYTHONPATH", "NODE_OPTIONS"}
    }
    for key in ("MODEL_API_KEY_FILE", "BASETEN_API_KEY_FILE", "FIREWORKS_API_KEY_FILE"):
        env[key] = str(work / "no-credentials")
    env.update({
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": os.pathsep.join((str(guard), str(snapshot / "src"))),
        "NODE_OPTIONS": f'--require="{guard / "offline.cjs"}"',
        "MPLCONFIGDIR": str(work / "matplotlib"),
        "XDG_CACHE_HOME": str(work / "cache"),
    })

    def run(label: str, *command: str, demo: bool = False) -> None:
        print(f"\n{label}", flush=True)
        child_env = dict(env)
        if demo:
            child_env["PYTHONPATH"] = os.pathsep.join((str(guard), str(snapshot / "demo")))
        subprocess.run(command, cwd=snapshot / "demo" if demo else snapshot, env=child_env, check=True)

    python = sys.executable
    # Assert that both interpreters and Node actually loaded the offline guard.
    probe = 'import socket;\ntry: socket.create_connection(("127.0.0.1", 9))\nexcept RuntimeError: pass\nelse: raise AssertionError("missing offline guard")'
    run("Checking offline guards", python, "-c", probe)
    run("Checking demo offline guard", str(args.demo_python), "-c", probe, demo=True)
    run("Checking Node offline guard", "node", "-e", 'try { require("node:net").connect(9); process.exit(1); } catch (e) { if (!e.message.includes("network access is disabled")) throw e; }')
    run("Checking committed SEC test fixture provenance", python, "scripts/build_offline_fixtures.py", "--check")
    run("Checking first-filing iXBRL documents and values", python, "scripts/build_site_filing_fixtures.py", "--check")
    run("Product, replay, provider and site tests", python, "-m", "pytest", "-q", "-ra")
    run("Demo pipeline tests (optional FFmpeg tests use their existing skip markers)", str(args.demo_python), "-m", "pytest", "-q", "-ra", demo=True)
    run("Standalone demo JavaScript tests", "node", "--test", "demo/tests/motion.test.mjs", "demo/tests/layout.test.mjs", "demo/tests/capture.test.mjs")
    run("Checking committed figure inputs and embeds", python, "docs/scripts/make_figures.py", "--check")
    run("Rebuilding figures in the temporary copy", python, "docs/scripts/make_figures.py", "--all")
    run("Checking rebuilt figures", python, "docs/scripts/make_figures.py", "--check")
    # Figure SVG metadata includes generation times; data outputs must be exact bytes.
    before = {name: (snapshot / name).read_bytes() for name in DATA_OUTPUTS}
    run("Rebuilding the explorer from saved evaluation results", python, "docs/scripts/build_explorer_data.py")
    run("Rebuilding site data with stored filing excerpts", python, "docs/scripts/build_site.py", "--offline")
    different = [name for name in DATA_OUTPUTS if (snapshot / name).read_bytes() != before[name]]
    if different:
        raise RuntimeError("Non-identical rebuilt outputs: " + ", ".join(different))
    run("Checking all Markdown and llms.txt links/anchors", python, "scripts/check_links.py")
    print("\nPASS offline Python and Node suites")
    print("PASS figure rebuild + --check")
    print("PASS explorer, site data and build summary: 3 byte-identical outputs")
    print("PASS Markdown links and anchors")
    print("PASS no model calls, SEC fetches or credentials; source tree unchanged")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"FAIL {error}", file=sys.stderr)
        raise SystemExit(1)
