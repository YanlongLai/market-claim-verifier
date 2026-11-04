# V5 round 2 retained check attempts

All checks used saved inputs; no model, SEC, recorder, voice or film-render command ran.

The initial targeted Python run, before updating the tests for the host's wired take,
reported 32 passed / 4 failed: the old ninth chapter name, the old pending-take assertion,
the v6 synthetic receipt, and the old one-second preview cue assumption. Its stdout is in
the task transcript; this file retains the command and result summary:
`demo/.venv/bin/python -m pytest -q demo/tests/test_v5.py`.

The first Node attempt is retained in `node-first.log` (15 passed / 2 failed). It exposed
floating-point cancellation at a receipt phase boundary and a stale trace-step geometry
mock. The comparison now tolerates sub-nanosecond representation error; the mock uses
the host's trace band. Subsequent runs are retained separately.

The language cleanup exposed two legacy storyboard/shot-list mismatches. Failed logs
remain here as lossless Unicode-escaped text; their exact original UTF-8 bytes are in
the language-history archive's `checks/` directory. Financial values, spoken narration,
old review outcomes and original source bytes were retained.

`legacy-take-rejection.log` is an expected rejection: the v6 receipt cannot satisfy the
v7 startup-cover gate. The host must re-record before any live review frame or film can
be produced. `protected-contracts.json` records unchanged host cue/text/cut contracts,
unchanged choreography hold calls, and exact WebM/MP4 hashes for both existing takes.
