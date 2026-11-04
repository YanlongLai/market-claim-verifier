# Recording real online and local runs

Use two distinct on-screen labels throughout the corresponding video segments:
**Online · site + server log** and **Local · CLI**. The helpers print these labels in the
terminal and store the local label in the session metadata. Keep the label visible in the
video composition as well. Show the site beside its actual server log, then show the actual
local terminal. A saved site replay, a dry run or an animated trace is not a fresh paid check.

The owner deploys the image and starts paid captures. The implementation and offline tests
do not deploy, SSH to production or spend model credits. [Models and keys](PROVIDERS.md#models--keys)
· [Server deployment](../deploy/README.md).

## Online: site and matching server log

The HTTP adapter emits one INFO line for each progress event to the pod's stderr.
Every authenticated run envelope includes a generated 32-character hexadecimal `request_id`.
Compare members have their own IDs. Stored history retains the same ID inside the envelope;
history record IDs identify history rows separately. Invalid requests can return an error
envelope without starting a paid run. No credentials, source IP, raw post, extracted text,
provider response bodies or private model reasoning appear in progress lines.

The format is `live id=<id> +<elapsed>s event=<name> key=value ...`. Values are
allowlisted names, validated ticker/period/evidence labels and finite numbers. A tool result
shows the available evidence ID, value, unit and filing form; it is not a full result dump.
`event=model phase=running` means the request was sent to the model, not that private reasoning
was inspected. `phase=completed` is emitted after the provider response is parsed. Verdict lines
include claim count, cost and `cost_is_bound`; `true` means some usage is still a reservation.
Errors end with `event=error` and a safe code, preserving any reserved cost.

Start the log helper **before** submitting the site request. It uses existing SSH configuration
for `dappgo-ha-cp-1`, disables password-based SSH authentication, and supplies sudo's password
only on stdin from the file named by `DAPPGO_HA_SUDO_FILE`. Use a private password file outside
the repository; the helper never echoes it or raw SSH/sudo diagnostics.

```sh
mkdir -p runs/real-trace-001
export DAPPGO_HA_SUDO_FILE="$HOME/secret/dappgo-ha-sudo.txt"
python3 scripts/tail_live_log.py --out runs/real-trace-001/online.jsonl \
  --request-id-file /tmp/real-trace-request-id --stop-after-verdict --duration 180
```

Use a new ID-file path for each capture, or remove the previous file before starting.
While the helper runs, start the browser/video recorder separately and submit the site check.
From the site's network response, save the top-level `request_id` in the ID file (plain text),
or save the response JSON there. Write a temporary file and rename it into place so the reader
does not see a partial JSON document. The ID may arrive after the verdict log line: the helper
remembers terminal events and stops once that ID becomes available. Ctrl-C also finalizes the capture.

Each JSONL row has exactly `{t_wall, t_rel_s, line}`. `t_wall` is the host's UTC observation time;
`t_rel_s` is time since the helper started. Kubernetes' source timestamp remains in `line`,
and `+...s` is the runner's own elapsed time. The remote command includes `--since=30s` so startup
does not dump the pod's entire history. Already-buffered lines can have nearly identical host
arrival times; use source timestamps to place them in the video.

The helper always keeps `online.jsonl.all.jsonl` with all matching live lines. The final
`online.jsonl` contains only the selected request, including lines that arrived before its ID
was known. Without an ID it retains all live lines. A pending ID file that never appears yields
a nonzero exit and retains the spool. You can select the ID afterward without SSH or another model call:

```sh
python3 scripts/tail_live_log.py \
  --filter-only runs/real-trace-001/online.jsonl.all.jsonl \
  --request-id 0123456789abcdef0123456789abcdef \
  --out runs/real-trace-001/online-selected.jsonl
```

That ID is an illustrative placeholder; replace it with the actual response ID. All output paths
must be new. Keep partial captures and failures. Direct tailing commands are in the
[deployment guide](../deploy/README.md#tail-real-request-logs).

## Local: actual CLI in a PTY

Rehearse without model keys, model calls or SEC fetches:

```sh
python3 scripts/record_cli_session.py examples/posts/bigtech-thread.txt \
  --provider baseten --dry-run --out runs/real-trace-001/local-dry.json
```

For the owner-authorized paid recording, use a new output name and omit `--dry-run`:

```sh
python3 scripts/record_cli_session.py examples/posts/bigtech-thread.txt \
  --provider baseten --out runs/real-trace-001/local-paid.json
```

The helper runs `uv run python -m claimcheck post <file> --provider <p> --budget 1` in a real
PTY, adding a unique `--out <capture>.report` directory. It defaults to the repository root;
`--cwd` changes the command's working directory, and relative input paths resolve there.
CLI progress is printed to stderr as calls happen: model turns, tool calls before dispatch,
tool results, elapsed time and the final verdict/cost. The JSON report remains on stdout.
The terminal shows the actual command and output while another recorder can film it.

Session JSON includes `command` (argument list), `cwd`, `started_at`, `duration_s`, `exit_code`,
the source SHA-256, `dry_run`, `receipt_summary`, and `chunks`: one `{t_rel_s, text}` entry per
decoded PTY read. Timing includes process startup. Chunk boundaries describe reads, not model
token streaming. Redaction preserves those boundaries, including empty chunks when a key spans
reads. Known environment/file keys and common token shapes are scrubbed from the session and
visible output; complete lines are buffered for safe terminal display. Do not put unrelated
private information in the demo input. The helper reads configured key files only for redaction;
the CLI dry run itself does not read key files.

On interruption or failure, the helper retains a partial session and the child's exit status.
The receipt summarizes the CLI's final JSON when available; `available: false` means no final
receipt was emitted. Check the retained report/traces for partial costs. Keep all files together:
the terminal capture is not a replacement for model responses, evidence, traces and the ledger.
`--dry-run` records the extraction preview, not a local verification result. Its zero paid spend
must not be presented as measured verification cost. [Retention policy](TEST_RECORDS.md).
