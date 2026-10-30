# Verification policy and filing-date cutoffs

Implemented policy: `us-financial-v1`. Policy identity includes the rule version, cutoff and declared scope. A cutoff changes evidence eligibility; it never relaxes entity, unit, period or numeric checks.

## Use

The `edgar`, `verify`, `post` and `ingest` commands accept `--as-of YYYY-MM-DD`:

```sh
uv run python -m claimcheck edgar META revenue 2024Q2 --as-of 2024-07-31
uv run python -m claimcheck verify 'META expects revenue of $47.5 billion to $50.5 billion for FY2025Q3.' --as-of 2025-07-30
uv run python -m claimcheck post article.txt --as-of 2025-07-30
uv run python -m claimcheck ingest report.pdf --as-of 2025-07-30
```

Only the first command avoids model inference; SEC retrieval may still be needed if the cache is empty. These are usage examples, not records of paid runs. Historical evaluation CLI batch runs do not yet accept this flag.

Python callers use `EdgarClient(cache_dir, as_of='2025-07-30')`. The release service inherits that client's policy even when supplied a separate recorded release client. No cutoff preserves latest-eligible-filing behavior.

## What the cutoff does

The boundary is **inclusive SEC filing date**, not an intraday timestamp. An item filed on the cutoff day is eligible regardless of its time of day. Invalid dates are rejected before inference; facts/releases without a valid filing date are excluded when a cutoff is active.

XBRL rows are filtered before fiscal normalization, period selection, amendment/restatement provenance, quarter derivation, available-period discovery and history ranking. Consequently a later comparative filing cannot replace an earlier number, and a derived quarter cannot borrow an annual total first filed after the cutoff. Filtering uses a copy: cached original bytes and their SHA-256 remain unchanged.

Release filings are filtered before selecting exhibits; exhibit dates are checked as well. A selected release quote is checked again at use time. Future releases therefore cannot enter by supplying a separate release client or retaining a candidate with a later filing date.

## What it does not do

This is evidence selection from the available cached/retrieved SEC dataset. It is **not** a historical archive of the SEC API. Current companyfacts may have omissions or corrections that were not observable on the requested day. Ticker/entity metadata remains current; historical ticker reassignment is not resolved. The model's training knowledge is not rolled back. For strict point-in-time research, retain dated full snapshots and a historical identity map as additional work.

No future forecast is validated as a future outcome. A release filed July 30 can legitimately contain Q3 guidance; the filing-date cutoff does not require the forecast period to have ended. Market prices, non-SEC documents and intraday release times are outside this policy.

## Audit output and compatibility

New agent results/traces and post/ingestion JSON record `verification_policy` with version, `as_of`, cutoff semantics and a deterministic `policy_id`. HTML reports display the version and cutoff; old reports without metadata say it was not recorded. EDGAR CLI output includes the policy. Explicit-cutoff tool results also carry it.

For no-cutoff runs, historical model-facing tool payloads stay unchanged, so recorded model replay remains valid. Policy metadata lives in the surrounding results/traces; direct Python `lookup_fact` adds it only with an explicit cutoff. No saved benchmark or prior evidence record is rewritten. Source identity and policy identity are separate: the same bytes may be eligible under one cutoff and ineligible under another.

Only the current fixed policy is implemented, not a user-editable permissiveness slider. Changing a rule's meaning requires a policy version change and regression tests. Any future persistent verification cache must include policy identity alongside model, prompt and source versions; current within-post reuse shares one immutable policy for the run.

## Verification cases

[Policy tests](../tests/test_policy.py) cover later restatements versus earlier facts, inclusive boundaries, missing/invalid filing dates, latest/history/derived-quarter filtering, release selection and quote revalidation, CLI date rejection, stable/different policy identities and policy metadata on early abstention without model calls. [Source filtering](../src/claimcheck/edgar.py), [release enforcement](../src/claimcheck/release.py), [policy contract](../src/claimcheck/policy.py).
