#!/usr/bin/env python3
"""Capture real pod progress over SSH; filter by a request ID learned later."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import selectors
import signal
import subprocess
import sys
import time

LIVE = re.compile(r"\blive id=([0-9a-f]{32})\b[^\r\n]*")
REMOTE_COMMAND = ("sudo -S -p '' -- k3s kubectl -n dappgo-hackathon "
                  "logs -f --since=30s --timestamps=true deployment/live-check")


def request_id(value):
    if not re.fullmatch(r"[0-9a-f]{32}", value):
        raise ValueError("request ID must be 32 lowercase hex characters")
    return value


def learned_id(args):
    if args.request_id:
        return request_id(args.request_id)
    if args.request_id_file and args.request_id_file.exists():
        raw = args.request_id_file.read_text().strip()
        if raw.startswith("{"):
            raw = json.loads(raw)["request_id"]
        return request_id(raw)
    return None


def filter_log(source, output, selected):
    count = 0
    for raw in source:
        row = json.loads(raw)
        match = LIVE.search(row["line"])
        if match and (selected is None or match[1] == selected):
            output.write(json.dumps(row, ensure_ascii=True) + "\n")
            count += 1
    output.flush()
    return count


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    ids = parser.add_mutually_exclusive_group()
    ids.add_argument("--request-id")
    ids.add_argument("--request-id-file", type=Path, help="may be written while capture is running; plain ID or response JSON")
    parser.add_argument("--filter-only", type=Path, help="filter a retained .all.jsonl capture offline; no SSH")
    parser.add_argument("--stop-after-verdict", action="store_true", help="requires an ID or ID file; otherwise use Ctrl-C")
    parser.add_argument("--duration", type=float, default=0, help="optional maximum seconds (0: until Ctrl-C)")
    args = parser.parse_args(argv)
    if args.duration < 0 or not math.isfinite(args.duration):
        parser.error("duration must be finite and non-negative")
    if args.stop_after_verdict and not (args.request_id or args.request_id_file):
        parser.error("--stop-after-verdict requires --request-id or --request-id-file")
    try:
        learned_id(args)
        if args.filter_only:
            if not learned_id(args):
                parser.error("--filter-only requires an available request ID")
            with args.filter_only.open() as source, args.out.open("x") as output:
                count = filter_log(source, output, learned_id(args))
            return 0 if count else 1
        password_file = os.environ.get("DAPPGO_HA_SUDO_FILE")
        if not password_file:
            parser.error("set DAPPGO_HA_SUDO_FILE to the sudo password file path")
        password = Path(password_file).read_bytes().rstrip(b"\r\n")
        if not password or b"\n" in password or b"\r" in password or b"\0" in password:
            parser.error("sudo password file must contain one nonempty line")
        spool_path = args.out.with_name(args.out.name + ".all.jsonl")
        # Refuse to overwrite either a completed or partial capture.
        with args.out.open("x") as output, spool_path.open("x+") as spool:
            stopped = False
            def stop(_signum, _frame):
                nonlocal stopped
                stopped = True
            old_handlers = {s: signal.signal(s, stop) for s in (signal.SIGINT, signal.SIGTERM)}
            process = None
            started = time.monotonic()
            print("Online · site + server log", flush=True)
            try:
                process = subprocess.Popen(["ssh", "-T", "-oBatchMode=yes", "-oConnectTimeout=10",
                    "dappgo-ha-cp-1", REMOTE_COMMAND], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL, start_new_session=True)
                try:
                    process.stdin.write(password + b"\n")
                    process.stdin.close()
                except BrokenPipeError:
                    pass
                del password
                pending = b""
                terminal_ids = set()
                with selectors.DefaultSelector() as selector:
                    selector.register(process.stdout, selectors.EVENT_READ)
                    while not stopped and (not args.duration or time.monotonic() - started < args.duration):
                        if args.stop_after_verdict and learned_id(args) in terminal_ids:
                            break
                        if not selector.select(0.2):
                            continue
                        chunk = os.read(process.stdout.fileno(), 65536)
                        if not chunk:
                            break
                        pending += chunk
                        while b"\n" in pending:
                            raw, pending = pending.split(b"\n", 1)
                            line = raw.decode("utf-8", errors="replace")
                            match = LIVE.search(line)
                            if not match:
                                continue
                            # Kubernetes timestamps are retained in line; t_wall is host observation time.
                            row = {"t_wall": datetime.now(timezone.utc).isoformat(),
                                   "t_rel_s": round(time.monotonic() - started, 6), "line": line}
                            spool.write(json.dumps(row, ensure_ascii=True) + "\n")
                            spool.flush()
                            selected = learned_id(args)
                            if re.search(r"\bevent=(verdict|error)\b", match[0]):
                                terminal_ids.add(match[1])
                            if selected is None or match[1] == selected:
                                print(line, flush=True)
                            if (args.stop_after_verdict and match[1] == selected and
                                    re.search(r"\bevent=(verdict|error)\b", match[0])):
                                stopped = True
                exit_code = process.poll()
            finally:
                if process is not None and process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                for sig, handler in old_handlers.items():
                    signal.signal(sig, handler)
                spool.seek(0)
                count = filter_log(spool, output, learned_id(args))
            if args.request_id_file and learned_id(args) is None:
                print("No request ID learned; all live lines retained. Use --filter-only after saving the ID.", file=sys.stderr)
                return 1
            if args.stop_after_verdict and learned_id(args) not in terminal_ids:
                print("No terminal event for the selected request; partial capture retained.", file=sys.stderr)
                return 1
            if exit_code not in (None, 0):
                print(f"SSH/log stream exited with status {exit_code}; partial capture retained.", file=sys.stderr)
                return 1
            return 0 if count else 1
    except (OSError, ValueError, KeyError, TypeError):
        # Never echo file contents, SSH diagnostics, or sudo credentials.
        print("Log capture failed; check paths, request ID, SSH and sudo access. Partial files are retained.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
