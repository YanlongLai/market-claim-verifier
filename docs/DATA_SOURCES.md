# Data sources and evidence policy

The machine-readable registry is [`sources/registry.yaml`](../sources/registry.yaml). It separates two ideas that are easy to confuse:

- claim-source tiers describe where a real-world claim came from (`primary`, `major_press`, `aggregator`, `social`, or `generated`);
- evidence tiers describe the SEC filing evidence used by this verifier (`L1`–`L4`).

## Ground-truth sources

The verifier's numeric ground truth is the SEC EDGAR XBRL companyfacts API:

`https://data.sec.gov/api/xbrl/companyfacts/CIK{cik10}.json`

The publisher is the U.S. Securities and Exchange Commission. Access is an HTTPS GET with a descriptive, contactable `User-Agent`, cached locally with a SHA-256 digest. The fair-access limit is 10 requests per second. The data is U.S. government public data, updated when filings are accepted and processed, and covers U.S. issuers filing XBRL with GAAP facts as tagged.

The SEC ticker map, `https://www.sec.gov/files/company_tickers.json`, resolves ticker symbols to CIKs. A snapshot can contain multiple share classes for one CIK, so reports retain the CIK and snapshot hash rather than treating a ticker as a permanent identity.

These sources cannot establish management guidance, forecasts, most non-GAAP measures, most segment KPIs or operational metrics, or market prices. They can also contain XBRL tagging errors, concept changes, issuer-specific fiscal calendars, and later comparative restatements. A successful lookup therefore means “the cached tagged fact was found,” not “the issuer's number has been independently audited by this program.”

L4 supplements companyfacts with the issuer's own earnings release furnished under **8-K Item 2.02, Exhibit 99.1**, plus Exhibit 99.2 when it contains HTML text. Discovery follows SEC submissions JSON (including date-relevant historical shards), the filing index, and SEC-indexed exhibit links within that accession. PDFs, image-only slides, IR mirrors, and unrelated 8-K items do not qualify. JSON, index and exhibit bytes are cached with URL, retrieval timestamp and SHA-256; hashes are checked on release-cache reads. A process-wide SEC request gate shared with XBRL starts at most nine requests per second, using `DappGo market-claim-verifier admin@dappgo.com`.

## SEC evidence tiers

| Tier | Evidence | Maximum strength |
|---|---|---|
| L1 | Audited 10-K / 10-K/A value for the exact period | high |
| L2 | Reviewed 10-Q / 10-Q/A value for the exact period | medium |
| L3 | Program derivation retaining its filing components | medium |
| L4 | Issuer earnings release, furnished 8-K Ex 99.1 / HTML Ex 99.2 | medium |

`L1` means the exact value is reported in a `10-K` or `10-K/A` audited annual filing. `audited: true` is set only when an exact-period record includes one of those forms.

`L2` means the exact value is reported only in `10-Q` or `10-Q/A` reviewed quarterly filings. A non-standard filing form is retained as a form fallback and receives low strength even though it stays in the direct-fact bucket.

`L3` means the program derived the value, for example a quarter-four flow as annual minus nine-month YTD, or a quarter from two cumulative YTD facts. L3 output keeps the component tiers and provenance. A non-restated L3 derivation is medium strength; a derivation that uses restated or form-fallback evidence is low strength.

`L4` is furnished and unaudited. It verifies what the issuer stated, including an outlook, rather than whether a future forecast will come true. It cannot become high strength through repetition. For `reported_in_release`, the program also requests the same XBRL metric/period: an exact-period, matching-unit L1/L2 filing value wins on conflict, and the result adds `release_vs_filing_mismatch`. YTD, wrong-date, form-fallback, and L3 values cannot displace an L4 number through this rule. Both sources remain cited; a low-strength authoritative filing lowers the combined strength.

For an exact `(concept, unit, start, end)` period, provenance records the number of distinct filing accessions, sorted forms, first/latest filed dates, amendment status, and whether different values were reported. `values_seen` is emitted only for restated periods and groups each distinct value with its reporting accession(s). The strength rule is:

| Strength | Rule |
|---|---|
| high | L1, at least two confirmations, and not restated |
| medium | L1/L2, a non-restated L3 derivation without fallback evidence, or furnished/unaudited L4 release evidence |
| low | Restated evidence, a derivation using a restated/fallback component, or a single filing with form fallback |

The program checks attach the weakest strength across the evidence cited by each sub-claim. A supported or contradicted result based only on restated evidence retains its verdict and adds the `restated_evidence` flag. The overall result also includes a compact `evidence_summary`, for example `Evidence: audited 10-K, confirmed in 3 filings, not restated`.

### L4 parsing and decision rules

- HTML parsing and numeric extraction use Python's standard library, with no model. Hidden/script/style text is removed, whitespace collapses inside blocks and cells, blocks use LF, and table cells use ` | `. Colspan and rowspan preserve column coordinates. All quote/highlight offsets are Python character offsets into that canonical text, not the original HTML bytes. Period/scale headings are retained as separate exact context spans.
- The model calls `find_earnings_release(ticker, metric, period, claim_kind)`, then `quote_release(candidate_id, start, end)`. The program checks the snapshot hash and re-extracts that exact span at tool selection and final verdict time. It reads the asserted numbers from the original claim; model `stated_value` and `model_found_value` never determine the L4 answer.
- `guidance` requires a literal issuer outlook sentence or outlook table, the requested metric, and a matching period. `non_gaap` supports adjusted/non-GAAP diluted EPS, adjusted operating income, free cash flow and adjusted free cash flow. `reported_in_release` supports consolidated GAAP revenue, operating/net income and diluted EPS where label and period are explicit. Segment totals, constant-currency/organic measures, percentages as monetary totals, and basic EPS as diluted EPS are not interchangeable.
- Fiscal labels stay fiscal. A calendar alias requires companyfacts evidence that the fiscal year ends December 31. An explicit ordinal outlook without a year may inherit the release's explicit reporting year, rolling Q4→Q1 into the next fiscal year. Date columns bind to the release's explicit quarter and period end; six/nine-month YTD and trailing-twelve-month values cannot answer a quarterly claim. Unresolved dates, labels or periods yield `insufficient_evidence`.
- Numeric ranges compare **both endpoints**, not containment. Shared scale words apply to both endpoints. Literal `plus or minus $300 million` is an absolute width; `plus or minus 2%` is a relative width (for example $54 billion → $52.92–55.08 billion). A point can match the explicitly stated center of such a range; a point merely inside an ordinary range is insufficient. Point claims allow half of the last displayed unit for rounding; explicit range endpoints use only floating-point roundoff tolerance.
- **Verbal-range rule:** “low to mid single digits,” “mid-70% range,” and similar verbal bounds have **no numeric mapping**. They return `insufficient_evidence`. Missing Apple guidance, missing non-GAAP labels, ambiguous/revised same-period values, and unverified spans also fail closed. Inequality-only release claims are currently insufficient.
- Evidence retains `form`, `filed`, `accession`, `exhibit_url`, raw-byte `sha256`, exact `quote`, `start`/`end`, `highlight_offsets`, contextual header spans, and L4 provenance (`furnished: true`, `unaudited: true`, `strength: medium`). Reports preserve these fields and highlight the cited numeric span.

The [L4 gold corpus and independent builder](../eval/l4/GOLD_REVIEW.md) register 32 claims across eight companies. SEC fixtures contain full recorded release source chains and separately marked, trimmed XBRL snapshots. Cached snapshots are immutable for a run; refreshing evidence requires a new snapshot/cache. The [Baseten evaluation runner](../eval/l4/run_agent.py) refuses model calls before those gold/source bytes match a local commit and caps all calls at $5 total.

## Claim-source tiers

| Tier | Meaning | Examples |
|---|---|---|
| `primary` | Direct issuer material or issuer-controlled filing-level material | Issuer press release, SEC 8-K, investor-relations page |
| `major_press` | Wire service or established general/financial outlet | Reuters, AP, Bloomberg, major financial-news outlet |
| `aggregator` | Repackaged market-data/news material or trading-platform blog | Market-data aggregator, news aggregator, trading-platform blog |
| `social` | Public social-network publication | X, LinkedIn, public forum post |
| `generated` | Synthetic evaluation claim | Benchmark claim or perturbed eval claim |

Source reliability is an empirical reporting layer independent of this verifier's system accuracy. It is published per claim-source tier as the share of gold claims that are `supported`, `contradicted`, or `insufficient_evidence`, each with a Wilson 95% confidence interval. Per-domain reliability is published only when that domain has at least 20 claims; otherwise domains are suppressed and results are aggregated by tier. System accuracy is reported separately by source tier, also with a Wilson interval.

Article claims are stored as short paraphrases with URL, title, and publication date. Verbatim article text is never stored in the registry or evaluation claim record.
