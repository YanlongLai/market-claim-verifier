#!/usr/bin/env python3
"""Record an actual claimcheck post process in a PTY, including partial failures."""
from __future__ import annotations

import argparse
import codecs
from datetime import datetime, timezone
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pty
import re
import selectors
import shlex
import signal
import struct
import subprocess
import sys
import termios
import time

TOKEN = re.compile(r"\b(?:sk|meta|hf)_[A-Za-z0-9_-]{12,}\b")


def known_secrets():
    values = [v for k, v in os.environ.items() if v and any(
        name in k.upper() for name in ("API_KEY", "TOKEN", "PASSWORD", "SECRET")) and not k.endswith("_FILE")]
    for name, default in (("BASETEN_API_KEY", "~/secret/baseten_api_key.txt"),
                          ("FIREWORKS_API_KEY", "~/secret/fireworks-api-key.txt"),
                          ("MODEL_API_KEY", "~/.config/dappgo/meta-model-api.env")):
        path = Path(os.environ.get(name + "_FILE", default)).expanduser()
        if path.is_file():
            raw = path.read_text().strip()
            if name == "MODEL_API_KEY":
                for line in raw.splitlines():
                    key, sep, value = line.strip().partition("=")
                    if sep and key.strip() == name:
                        values.append(value.strip().strip("\"'"))
            else:
                values.append(raw)
    return sorted({v for v in values if v}, key=len, reverse=True)


def scrub(text, secrets):
    for value in secrets:
        text = text.replace(value, "[REDACTED]")
    return TOKEN.sub("[REDACTED]", text)


def scrub_record(value, secrets):
    if isinstance(value, str):
        return scrub(value, secrets)
    if isinstance(value, dict):
        return {k: scrub_record(v, secrets) for k, v in value.items()}
    if isinstance(value, list):
        return [scrub_record(v, secrets) for v in value]
    return value


def redact_chunks(chunks, secrets):
    """Redact even when a token crosses reads; retain one entry per PTY read."""
    full = "".join(row["text"] for row in chunks)
    spans = [m.span() for m in TOKEN.finditer(full)]
    for secret in secrets:
        spans.extend(m.span() for m in re.finditer(re.escape(secret), full))
    merged = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(end, merged[-1][1])
        else:
            merged.append([start, end])
    result, offset = [], 0
    for row in chunks:
        end = offset + len(row["text"])
        text, position = "", offset
        for left, right in merged:
            if left >= end or right <= offset:
                continue
            text += full[position:max(position, left)]
            if left >= offset:
                text += "[REDACTED]"
            position = min(end, right)
        text += full[position:end]
        result.append({"t_rel_s": row["t_rel_s"], "text": text})
        offset = end
    return result


def receipt_from_output(text):
    decoder = json.JSONDecoder()
    candidates = []
    for match in re.finditer(r"(?m)^\{", text.replace("\r\n", "\n")):
        try:
            value, _ = decoder.raw_decode(text.replace("\r\n", "\n")[match.start():])
            if isinstance(value, dict) and ("counts" in value or value.get("dry_run")):
                candidates.append(value)
        except ValueError:
            pass
    if not candidates:
        return {"available": False}
    value = candidates[-1]
    return {"available": True, **{k: value[k] for k in
        ("provider", "model", "counts", "verdicts", "cost_usd", "out", "report", "dry_run") if k in value}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--provider", choices=("baseten", "fireworks", "meta"), default="baseten")
    parser.add_argument("--out", type=Path, required=True, help="new session JSON; never overwrites a prior attempt")
    parser.add_argument("--cwd", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    cwd = args.cwd.resolve()
    source = (cwd / args.file).resolve()
    if not source.is_file():
        parser.error("input must be a local text file")
    command = ["uv", "run", "python", "-m", "claimcheck", "post", str(args.file),
               "--provider", args.provider, "--budget", "1"]
    if args.dry_run:
        command.append("--dry-run")
    # Select a unique report directory so even runs within one second survive.
    report_dir = args.out.resolve().with_name(args.out.name + ".report")
    if report_dir.exists():
        parser.error("capture report directory already exists")
    command.extend(["--out", str(report_dir)])
    try:
        secrets = known_secrets()
        output = args.out.open("x", encoding="utf-8")
    except (OSError, ValueError):
        print("Cannot create a new capture or read configured redaction keys.", file=sys.stderr)
        return 2
    started = time.monotonic()
    record = {"label": "Local · CLI", "command": command, "cwd": str(cwd), "dry_run": args.dry_run,
              "started_at": datetime.now(timezone.utc).isoformat(),
              "input": {"path": str(args.file), "sha256": hashlib.sha256(source.read_bytes()).hexdigest()},
              "chunks": [], "exit_code": None, "duration_s": None, "receipt_summary": {"available": False}}
    chunks, process, master = [], None, None
    interrupted = False
    def stop(_signum, _frame):
        nonlocal interrupted
        interrupted = True
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
    old_handlers = {s: signal.signal(s, stop) for s in (signal.SIGINT, signal.SIGTERM)}
    try:
        master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 32, 110, 0, 0))
        print("Local · CLI" + (" · dry run (no paid call)" if args.dry_run else ""), flush=True)
        print(scrub("$ " + shlex.join(command), secrets), flush=True)
        try:
            process = subprocess.Popen(command, cwd=cwd, stdin=subprocess.DEVNULL, stdout=slave, stderr=slave,
                env={**os.environ, "PYTHONUNBUFFERED": "1", "NO_COLOR": "1"}, start_new_session=True)
        finally:
            os.close(slave)
        decoder, pending = codecs.getincrementaldecoder("utf-8")("replace"), ""
        with selectors.DefaultSelector() as selector:
            selector.register(master, selectors.EVENT_READ)
            while True:
                if interrupted:
                    break
                if not selector.select(0.2):
                    continue
                try:
                    data = os.read(master, 65536)
                except OSError as exc:
                    if exc.errno != errno.EIO:
                        raise
                    data = b""
                if not data:
                    break
                text = decoder.decode(data)
                chunks.append({"t_rel_s": round(time.monotonic() - started, 6), "text": text})
                # Whole-line buffering keeps split secrets out of the visible terminal too.
                pending += text
                while "\n" in pending:
                    line, pending = pending.split("\n", 1)
                    print(scrub(line.rstrip("\r"), secrets), flush=True)
        pending += decoder.decode(b"", final=True)
        if pending:
            print(scrub(pending, secrets), end="", flush=True)
        record["exit_code"] = process.wait(timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        record["capture_error"] = "process_or_pty_failed"
    finally:
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        if process is not None:
            record["exit_code"] = process.returncode
        if master is not None:
            os.close(master)
        for sig, handler in old_handlers.items():
            signal.signal(sig, handler)
        record["duration_s"] = round(time.monotonic() - started, 6)
        record["interrupted"] = interrupted
        record["chunks"] = redact_chunks(chunks, secrets)
        record["receipt_summary"] = receipt_from_output("".join(r["text"] for r in record["chunks"]))
        # Scrub metadata too, without losing the chunk boundaries or timestamps.
        output.write(json.dumps(scrub_record(record, secrets), ensure_ascii=True, indent=2) + "\n")
        output.close()
    return record["exit_code"] if record["exit_code"] is not None and record["exit_code"] >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
