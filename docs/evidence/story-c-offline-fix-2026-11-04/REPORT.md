# Story C: offline program diagnosis and regression

The exact original post now produces **contradicted**, with Microsoft supported,
Meta contradicted and the forecast/opinion unjudged. The corrected draft replaces
**$164,501 billion → $164.5 billion**. No rewording of Story C is needed.

This is a deterministic program recheck of previously seen text and retained SEC
tool results. **Zero paid calls; no SEC fetches, extraction, OCR/ASR or new accuracy
measurement.** Original production attempts and public saved envelopes remain
unchanged. [Before](before.json), [final recheck](after-r4.json),
[replay script](../../../scripts/replay_story_c.py),
[regressions](../../../tests/test_story_c.py).

## Cause and change

The agent/live pipeline attaches the full user post as `original_claim` to each
proposed assertion. `checks.evaluate_sub_claim` passed that whole post to
`requires_release`; the separate **My forecast** sentence therefore routed every
assertion to `evaluate_release_claim`. That checker saw both FY2025 and FY2024.
Its multi-period guard requires a literal atomic quote, but the saved assertions
inserted **was** where the original uses **:**. All four checks consequently
returned `ambiguous_release_claim_period`, before parsing a number or using E1/E2.

The fix binds a period-bearing assertion to its complete source sentence before
release routing, period interpretation, comparator inference or evidence recovery.
Matching permits whitespace, colon/copula and final-punctuation differences;
company, metric, amount, units and period words must still match. The complete
source sentence and heading/prefix are retained, with original character spans.
Guidance/non-GAAP qualifiers cannot be dropped by a model rewrite. Distinct
possible source contexts and unattached release headings remain ambiguous.
Video channel labels delimit separate
sources, allowing identical repeated frame sentences to share one interpretation.

Assertions typed `other` remain `unchecked` even if the full post contains guidance
words. The correction layer displays their reason as `not_judged`.

The number parser already reads the literal `$164,501 billion` as
164,501,000,000,000. Regression coverage also supplies a model-normalized
164,501,000,000 and proves the program overrides it with the literal magnitude.
If the model also normalizes its separate number phrase, the matched source
assertion supplies the original literal before parsing, including through
evidence-ID recovery. A `stated_text_corrected_from_source` flag records this.
The formatter preserves the stated scale; an exact thousandfold error now allows
at least one decimal/four significant digits, producing `$164.5 billion` instead
of rounding the corrected amount to `$165 billion`. Ordinary correction precision
is unchanged.

## Rechecked results

| Assertion in the exact text post | Program result | Stated / filed USD |
| --- | --- | --- |
| Microsoft FY2025 revenue: $281.7 billion. | supported | 281,700,000,000 / 281,724,000,000 |
| Meta FY2024 revenue: $164,501 billion. | contradicted; corrected to $164.5 billion | 164,501,000,000,000 / 164,501,000,000 (exact ×1000) |
| My forecast: Microsoft will beat $281.7 billion next year. | unchecked; not judged | No financial verdict |
| Microsoft's growth beat every rival this year. | unchecked; not judged | No financial verdict |

The retained image and PDF text also produce those four results and the same
single correction. The retained video produces the same four financial results;
its combined audio/frame text repeats the amount four times, so the existing
`ambiguous_span` correction guard retains the text instead of selecting a copy.
This boundary does not affect the exact text post's correction. Media reading
quality has not been retested.

The public API does not retain private model-response bodies. The replay explicitly
reconstructs typed assertions from saved check texts and original amount literals;
it does not claim to replay a private provider transcript. The tests pin the
immutable failed attempt under
`docs/evidence/example-records/20261104T083842.915381Z/`, so a later production
recording does not replace the regression case.

## Verification and retained attempts

- [Initial failing regressions](regression-before.log.gz): four failures reproduce
  the original routing error; the post-screen check passes.
- [First focused run](targeted-r1.log.gz): 183 passed; three assertions were too
  strict about an existing `comparator_corrected` reason prefix. The assertion
  checks were corrected to accept that diagnostic prefix.
- [Focused run 2](targeted-r2.log.gz): 193 passed.
- [Focused run 3](targeted-r3.log.gz): 194 passed, including video context binding.
- [Regression run 4](regression-r4.log.gz): 15 passed, including omitted and
  ambiguous evidence-ID recovery.
- [Baseline sync and frozen-case check](baseline-sync-r5.log.gz): 20 passed.
- [Focused run 6](targeted-r6.log.gz): 199 passed, including source-header
  safeguards and the original failed production attempt.
- [Additional literal regression](literal-r7.log.gz): reproduces the remaining
  model-normalized number-phrase failure after period binding was fixed.
- [Final focused run](targeted-r8.log.gz): 202 passed, including original-literal
  recovery with cited, omitted and ambiguous evidence IDs.
- [First full-verifier attempt](verify-r1.log.gz): stopped at the stale example
  manifest inherited from the starting branch. `main` already fixes its links in
  `cda8a796`; those exact bytes were adopted.
- [Second full-verifier attempt](verify-r2.log.gz): 1,463 product tests passed;
  the isolated example-builder test failed because its copied index still named
  saved results after the fixture removed their files. `main` fixed that fixture
  in `29e5654a`; the exact upstream fix was adopted.
- [Third full-verifier attempt](verify-r3.log.gz): all 1,467 product tests,
  206 demo tests and 97 standalone Node tests passed; every offline rebuild and
  link check passed. This precedes the final normalized-number-phrase guard.
- [Final full-verifier attempt](verify-r4.log.gz): **1,470 product tests,
  206 demo tests and 97 standalone Node tests passed**, including the final
  normalized-number-phrase guard. Figure rebuild/check, saved envelopes/assets,
  all three explorer/site outputs, wild findings and Markdown links pass.
  The runner's network/credential guards remain enabled throughout verification.

The delivered commit is based on `main` at
`29e5654acc556b6a6676c7ef351dc5ffbead2407`, which also fixes the isolated example
test fixture's saved-result index. These two upstream fixes are not Story C code
changes. All failed/partial runs are retained, including the intermediate
[video recheck](after-r1.json) and [next recheck](after-r2.json).
[Source hashes](source-hashes-final.json) identify the final tested files;
the [earlier hashes](source-hashes.json) and [third recheck](after-r3.json) are
retained separately.

Reproduce the deterministic check from the repository root:

```sh
uv run --frozen python scripts/replay_story_c.py --ids c-text c-image c-pdf c-video
bash scripts/verify.sh
```

## Host recording after redeploying the patched image

Run these commands on the host, from the patched repository. The archive step
preserves existing public envelopes because the recorder refuses to overwrite
them; their original retained response/receipt directories are also preserved.
The explicit $10 cap covers the configured whole daily allowance required by the
recorder's preflight. This is a command for a future paid recording, not a claim
that one was executed here.

```sh
archive=$(mktemp -d docs/evidence/example-records/story-c-before-fix.XXXXXX)
for id in c-text c-image c-pdf c-audio c-video; do
  mv "docs/site/data/examples/$id.json" "$archive/"
done
LIVE_CHECK_PASSWORD_FILE=/absolute/path/to/live-check-password \
  uv run --frozen python scripts/run_example_records.py \
  --ids c-text c-image c-pdf c-audio c-video --max-spend-usd 10 --execute
uv run --frozen python scripts/build_examples.py
uv run --frozen python scripts/build_examples.py --check
```

Every new attempt receives a new evidence directory. Preserve partial failures;
do not retry into an existing recording or replace old response/receipt files.
