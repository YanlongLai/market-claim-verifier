# Provider overload diagnosis (2026-11-04)

A Fireworks audio check on the live site failed at model step 1 with `provider_error`.

- Server log: Meta ASR finished (375 characters, 6.1 s); the Fireworks chat call failed 1.4 s later.
  The logged `status=503` was this server's reply status; the provider status was not recorded at the time.
- Direct calls from a separate machine to `accounts/fireworks/models/muse-spark-open`: one 90 s timeout, then four
  HTTP 503 replies in about 0.5 s with the body message "service overloaded, please try again later".
  The same key listed models with HTTP 200. Conclusion: Fireworks capacity, not this repository's code or network.
- The local CLI waited over 4 minutes because the SDK default allowed a 10-minute read timeout per attempt.

Change: a shared rule (`claimcheck.retries.provider_overloaded`, HTTP 503/529, or 429/500/502 whose body says
overloaded or at capacity) now yields `provider_overloaded` with the provider's own `provider_status` on the live
server log, the browser log, the API, history and the CLI. The CLI client times out after 90 s with SDK retries off.
Provider response bodies are still never logged. [Full verify](verify-pass.log).

## Follow-up: provider that never answers

A live Fireworks check after the deploy hit the other overload shape: no reply at all. The server stopped at 85 s and
logged `error timeout`, but the browser received a bare `unavailable` through the proxy. Direct calls at the same
time returned HTTP 200 in 1 s, HTTP 200 in 56 s and HTTP 503 "service overloaded" in 22 s.
The browser now takes the server's own error code from its log when the reply only says `unavailable`, and the
timeout message says the provider is usually slow or overloaded and suggests another provider.
[Verify after this change](verify-pass-2-site-recovery.log).
