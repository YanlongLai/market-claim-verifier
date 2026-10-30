# Versioned evidence records

Implemented 2026-10-30: a common export contract and its first connector, SEC issuer earnings-release HTML. This extends the existing L4 source path; it does not add arbitrary web scraping or a new non-SEC authority.

## Runtime integration

After `ReleaseService.quote` revalidates a selected quote against cached bytes, it attaches `evidence_record` to the tool result. Existing financial checkers remain responsible for the verdict, source conflicts, units and periods. The nested record does not override those rules or promote an upload to trusted evidence.

[EvidenceRecord and EvidenceConnector](../src/claimcheck/evidence.py) define immutable canonical serialization and the connector protocol. `SecReleaseConnector` checks the SEC accession URL, source hash, normalized text and quote bounds, and independently re-extracts the numeric range, unit and period. The outer pipeline supplies SEC filing-index admission. A standalone record is an audit artifact, not a cryptographic proof that SEC published a document.

## Record fields

| Field | Meaning |
|---|---|
| schema_version / connector | Contract and parser-adapter version |
| source | Issuer publisher, SEC distributor, CIK, accession, form, filing date, retrieval time, URL and original-byte hash |
| locator | Quote and start/end offsets in normalized text, text hash and normalizer version |
| fact | Ticker, metric, fiscal/calendar label, period type, unit, range endpoints and claim kind |
| authority | Issuer-statement scope, L4, unaudited, medium maximum strength, permitted claim kind |
| limitations | Forecast boundary, offset interpretation and unchanged conflict policy |

A missing retrieval timestamp remains null; no date is invented. Filing date is not claimed to be an exact publication timestamp. A quarter label is the fact's effective period; this interface does not implement historical as-of selection. Original HTML bytes and normalized text are distinct artifacts with distinct hashes. Normalizer changes require a version change and regression tests.

## Offline US-issuer example

From the repository root:

```sh
uv run python examples/evidence/export_sec_release.py --out /tmp/claimcheck-evidence
```

The [example](../examples/evidence/export_sec_release.py) uses the committed [SEC release fixtures](../tests/fixtures/releases/manifest.json), disables network fallback and makes no model requests. It exports META's FY2025Q3 revenue guidance of USD 47.5–50.5 billion from the July 30, 2025 issuer release. This is a recorded replay, not a fresh retrieval or forecast validation.

The output directory contains hash-named original HTML, normalized UTF-8 text and canonical JSON. `export_bundle` validates input hashes and uses exclusive creation: identical repeat exports are allowed, changed existing artifacts cause an error rather than an overwrite. Inspect the JSON locator to reproduce the exact quoted span in the text file. The record hash includes metadata; it is not a substitute for the source-byte identity or a deduplication key across different retrieval times.

## Extension boundary

Future connectors can implement the protocol, but each needs independent source admission, parsing, authority and verdict integration. Merely constructing a record cannot authorize a new source. PDF input currently remains a claim source. General URL fetching, non-SEC issuer mirrors, source conflict policies for new domains and a plugin registry remain planned in the [delivery plan](DAY5_PLAN.md).

## Verification

[Tests](../tests/test_evidence.py) cover a recorded US issuer document, numeric range, immutable copies, repeat export, changed bundle files, unapproved URLs, unverified spans, changed offsets/quotes/hashes and altered numeric values. The existing release regression suite retains the same supported/contradicted/insufficient-evidence expectations.
