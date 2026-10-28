# Data sources and evidence policy

The machine-readable registry is [`sources/registry.yaml`](../sources/registry.yaml). It separates two ideas that are easy to confuse:

- claim-source tiers describe where a real-world claim came from (`primary`, `major_press`, `aggregator`, `social`, or `generated`);
- evidence tiers describe the SEC filing evidence used by this verifier (`L1`, `L2`, or `L3`).

## Ground-truth sources

The verifier's numeric ground truth is the SEC EDGAR XBRL companyfacts API:

`https://data.sec.gov/api/xbrl/companyfacts/CIK{cik10}.json`

The publisher is the U.S. Securities and Exchange Commission. Access is an HTTPS GET with a descriptive, contactable `User-Agent`, cached locally with a SHA-256 digest. The fair-access limit is 10 requests per second. The data is U.S. government public data, updated when filings are accepted and processed, and covers U.S. issuers filing XBRL with GAAP facts as tagged.

The SEC ticker map, `https://www.sec.gov/files/company_tickers.json`, resolves ticker symbols to CIKs. A snapshot can contain multiple share classes for one CIK, so reports retain the CIK and snapshot hash rather than treating a ticker as a permanent identity.

These sources cannot establish management guidance, forecasts, most non-GAAP measures, most segment KPIs or operational metrics, or market prices. They can also contain XBRL tagging errors, concept changes, issuer-specific fiscal calendars, and later comparative restatements. A successful lookup therefore means “the cached tagged fact was found,” not “the issuer's number has been independently audited by this program.”

## SEC evidence tiers

`L1` means the exact value is reported in a `10-K` or `10-K/A` audited annual filing. `audited: true` is set only when an exact-period record includes one of those forms.

`L2` means the exact value is reported only in `10-Q` or `10-Q/A` reviewed quarterly filings. A non-standard filing form is retained as a form fallback and receives low strength even though it stays in the direct-fact bucket.

`L3` means the program derived the value, for example a quarter-four flow as annual minus nine-month YTD, or a quarter from two cumulative YTD facts. L3 output keeps the component tiers and provenance. A non-restated L3 derivation is medium strength; a derivation that uses restated or form-fallback evidence is low strength.

For an exact `(concept, unit, start, end)` period, provenance records the number of distinct filing accessions, sorted forms, first/latest filed dates, amendment status, and whether different values were reported. `values_seen` is emitted only for restated periods and groups each distinct value with its reporting accession(s). The strength rule is:

| Strength | Rule |
|---|---|
| high | L1, at least two confirmations, and not restated |
| medium | L1/L2, or a non-restated L3 derivation without fallback evidence |
| low | Restated evidence, a derivation using a restated/fallback component, or a single filing with form fallback |

The program checks attach the weakest strength across the evidence cited by each sub-claim. A supported or contradicted result based only on restated evidence retains its verdict and adds the `restated_evidence` flag. The overall result also includes a compact `evidence_summary`, for example `Evidence: audited 10-K, confirmed in 3 filings, not restated`.

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
