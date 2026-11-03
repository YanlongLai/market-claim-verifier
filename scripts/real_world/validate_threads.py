"""Retain full-suite and disconnected-verifier logs without model credentials."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if (out / "validation.json").exists():
        raise RuntimeError("retain prior validation; choose a separately named attempt")
    code = runpy.run_path(str(ROOT / "scripts/verify.py"))
    with tempfile.TemporaryDirectory(prefix="threads-validation-") as temp:
        guard = Path(temp)
        (guard / "sitecustomize.py").write_text(code["PYTHON_GUARD"])
        (guard / "offline.cjs").write_text(code["NODE_GUARD"])
        env = {k: v for k, v in os.environ.items() if not k.startswith(("CLAIMCHECK_", "BASETEN_", "FIREWORKS_", "MODEL_API_", "OPENAI_", "MCV_"))
               and k not in {"PYTHONPATH", "NODE_OPTIONS"}}
        for key in ("MODEL_API_KEY_FILE", "BASETEN_API_KEY_FILE", "FIREWORKS_API_KEY_FILE"):
            env[key] = str(guard / "no-credentials")
        env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=os.pathsep.join([str(guard), str(ROOT / "src")]),
                   NODE_OPTIONS=f'--require="{guard / "offline.cjs"}"', MPLCONFIGDIR=str(guard / "mpl"),
                   XDG_CACHE_HOME=str(guard / "cache"))
        logs = []
        for name, command, extra in [("product-suite", [sys.executable, "-m", "pytest", "-q", "-ra"], {}),
                                     ("verify-offline", ["sh", "scripts/verify.sh"], {"UV_OFFLINE": "1"})]:
            started = now()
            log = out / f"{name}.log"
            print(f"Starting {name}", flush=True)
            with log.open("w") as handle:
                p = subprocess.run(command, cwd=ROOT, env={**env, **extra}, stdout=handle, stderr=subprocess.STDOUT)
            row = {"command": command, "environment": extra, "started_at": started, "finished_at": now(),
                   "exit_code": p.returncode, "log": log.name, "sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
                   "credentials": "provider environment removed; key-file settings nonexistent", "network": "Python/Node network guards; dependency setup UV_OFFLINE=1 for verifier"}
            (out / f"{name}.json").write_text(json.dumps(row, indent=2) + "\n")
            logs.append(row)
            print(f"Finished {name}: exit {p.returncode}", flush=True)
        receipt = {"status": "passed" if all(r["exit_code"] == 0 for r in logs) else "failed",
                   "completed_at": now(), "checks": logs, "new_paid_calls": 0, "new_sec_fetches": 0,
                   "scope": "Full product suite and complete UV_OFFLINE=1 sh scripts/verify.sh, including demo Python/Node, figures, byte-identical site outputs and links.",
                   "preserved_symlinks": {p: os.readlink(ROOT / p) for p in (".cache", ".venv")}}
        (out / "validation.json").write_text(json.dumps(receipt, indent=2) + "\n")
        return 0 if receipt["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
