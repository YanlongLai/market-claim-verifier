# L4 Baseten agent evaluation

Accuracy: 31/32 = 96.9% (Wilson 95% 84.3–99.4%).

False-supported: 0/19 non-supported gold claims.

Ledger spend: $0.715698; model calls: 131.

Median wall latency: 10.597033 s; p95: 28.288324 s.

Gold/source freeze commit: `3530800c16e2e9eb6789d6ef1bda239659d096fe`.

One run of 32 generated atomic claims from eight issuers; 13 supported, 10 numeric perturbations, nine insufficient. The same fixtures informed implementation: this is a regression benchmark, not a blinded held-out estimate. The model sees only claim text and tool responses. SEC retrieval is restricted to recorded source chains and explicitly trimmed XBRL snapshots; missing corpus documents fail closed. No live SEC lookups, gold coordinates, or expected verdicts are supplied to the agent. Errors and budget stops remain scored as insufficient_evidence. All calls share one $5 ledger; SDK retries are disabled. Cost uses [Baseten's published rates](https://www.baseten.co/pricing/) checked 2026-10-29 ($1.25/M input, $0.15/M cached input, $4.25/M output), not a provider invoice.

| Claim | Gold | Program | Seconds | Cost |
|---|---|---|---:|---:|
| L4-01 | supported | supported | 9.87 | $0.02188 |
| L4-02 | contradicted | contradicted | 14.10 | $0.02289 |
| L4-03 | supported | insufficient_evidence | 6.56 | $0.01360 |
| L4-04 | insufficient_evidence | insufficient_evidence | 17.38 | $0.03264 |
| L4-05 | supported | supported | 6.48 | $0.01004 |
| L4-06 | contradicted | contradicted | 4.62 | $0.00730 |
| L4-07 | insufficient_evidence | insufficient_evidence | 8.51 | $0.01266 |
| L4-08 | insufficient_evidence | insufficient_evidence | 10.68 | $0.01932 |
| L4-09 | supported | supported | 9.91 | $0.01963 |
| L4-10 | contradicted | contradicted | 12.90 | $0.02325 |
| L4-11 | supported | supported | 7.98 | $0.01546 |
| L4-12 | insufficient_evidence | insufficient_evidence | 28.29 | $0.04821 |
| L4-13 | supported | supported | 10.86 | $0.02071 |
| L4-14 | contradicted | contradicted | 12.79 | $0.02129 |
| L4-15 | contradicted | contradicted | 9.15 | $0.01689 |
| L4-16 | insufficient_evidence | insufficient_evidence | 10.63 | $0.01713 |
| L4-17 | supported | supported | 8.49 | $0.01688 |
| L4-18 | contradicted | contradicted | 10.57 | $0.01856 |
| L4-19 | supported | supported | 7.95 | $0.01501 |
| L4-20 | insufficient_evidence | insufficient_evidence | 30.07 | $0.05095 |
| L4-21 | supported | supported | 10.50 | $0.01715 |
| L4-22 | contradicted | contradicted | 16.31 | $0.02267 |
| L4-23 | contradicted | contradicted | 10.77 | $0.02351 |
| L4-24 | insufficient_evidence | insufficient_evidence | 20.96 | $0.03592 |
| L4-25 | supported | supported | 9.30 | $0.01523 |
| L4-26 | contradicted | contradicted | 11.01 | $0.01913 |
| L4-27 | supported | supported | 6.72 | $0.01367 |
| L4-28 | insufficient_evidence | insufficient_evidence | 24.33 | $0.03821 |
| L4-29 | supported | supported | 9.74 | $0.01724 |
| L4-30 | contradicted | contradicted | 12.01 | $0.02011 |
| L4-31 | supported | supported | 7.01 | $0.01108 |
| L4-32 | insufficient_evidence | insufficient_evidence | 26.25 | $0.05749 |
