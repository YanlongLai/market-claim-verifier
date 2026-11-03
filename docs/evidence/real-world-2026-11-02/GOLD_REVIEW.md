# Claude / Owner review before factual scoring

Frozen before model execution. No independent Claude review is claimed. A scope-policy verdict is an expected abstention, not confirmation that the news is true or false. Never edit this run's frozen gold in place; add a separately named reviewed-gold recheck.

## Ambiguous US financial claims

| ID | Paraphrase | Review needed |
|---|---|---|
| RW002 | AWS grew by 39% last quarter. | Missing reporting year/period, financial basis, or metric definition. Do not infer it from publication date, a matching source value or latest SEC filing. Claude/Owner review required. The word grew does not identify the measured AWS metric. |
| RW004 | Airbnb has a net profit margin of 20%. | Missing reporting year/period, financial basis, or metric definition. Do not infer it from publication date, a matching source value or latest SEC filing. Claude/Owner review required. |
| RW008 | TSMC generated $46.7 billion of revenue in its latest quarter. | Missing reporting year/period, financial basis, or metric definition. Do not infer it from publication date, a matching source value or latest SEC filing. Claude/Owner review required. |
| RW012 | PCs contributed 19% of Dell's segment profit last quarter. | Missing reporting year/period, financial basis, or metric definition. Do not infer it from publication date, a matching source value or latest SEC filing. Claude/Owner review required. |
| RW014 | Intuitive Surgical's revenue increased by 22%. | Missing reporting year/period, financial basis, or metric definition. Do not infer it from publication date, a matching source value or latest SEC filing. Claude/Owner review required. |
| RW015 | Shell's profit rose to $10.8 billion. | Missing reporting year/period, financial basis, or metric definition. Do not infer it from publication date, a matching source value or latest SEC filing. Claude/Owner review required. |
| RW019 | SpaceX's Q3 AI revenue exceeded $7.6 billion. | Missing reporting year/period, financial basis, or metric definition. Do not infer it from publication date, a matching source value or latest SEC filing. Claude/Owner review required. Confirm issuer identity/public filing availability. |
| RW033 | Starbucks' US comparable-store sales grew by 7.7% last quarter. | Missing reporting year/period, financial basis, or metric definition. Do not infer it from publication date, a matching source value or latest SEC filing. Claude/Owner review required. |
| RW034 | Anthropic's third-quarter revenue was nearly $17 billion. | Missing reporting year/period, financial basis, or metric definition. Do not infer it from publication date, a matching source value or latest SEC filing. Claude/Owner review required. Confirm issuer identity/public filing availability. |
| RW035 | TSMC's 2-nanometer process accounts for 8% of wafer revenue. | Missing reporting year/period, financial basis, or metric definition. Do not infer it from publication date, a matching source value or latest SEC filing. Claude/Owner review required. |
| RW036 | Booking has a net profit margin of 20%. | Missing reporting year/period, financial basis, or metric definition. Do not infer it from publication date, a matching source value or latest SEC filing. Claude/Owner review required. |
| RW039 | Costco's September net sales increased by 13%. | Missing reporting year/period, financial basis, or metric definition. Do not infer it from publication date, a matching source value or latest SEC filing. Claude/Owner review required. |
| RW043 | Broadcom's AI semiconductor revenue increased by 221%. | Missing reporting year/period, financial basis, or metric definition. Do not infer it from publication date, a matching source value or latest SEC filing. Claude/Owner review required. |
| RW048 | Airbnb generated $4.6 billion of free cash flow. | Missing reporting year/period, financial basis, or metric definition. Do not infer it from publication date, a matching source value or latest SEC filing. Claude/Owner review required. |
| RW049 | UnitedHealth's adjusted EPS increased to $4.69. | Missing reporting year/period, financial basis, or metric definition. Do not infer it from publication date, a matching source value or latest SEC filing. Claude/Owner review required. |
| RW051 | Ares Capital reported third-quarter Core Earnings of $0.46 per share. | Missing reporting year/period, financial basis, or metric definition. Do not infer it from publication date, a matching source value or latest SEC filing. Claude/Owner review required. |
| RW053 | Alibaba's net profit margin is 10%. | Missing reporting year/period, financial basis, or metric definition. Do not infer it from publication date, a matching source value or latest SEC filing. Claude/Owner review required. |
| RW055 | Airbnb's net profit margin is 20%. | Missing reporting year/period, financial basis, or metric definition. Do not infer it from publication date, a matching source value or latest SEC filing. Claude/Owner review required. |
| RW056 | Shell's third-quarter adjusted earnings were approximately $10.8 billion. | Missing reporting year/period, financial basis, or metric definition. Do not infer it from publication date, a matching source value or latest SEC filing. Claude/Owner review required. |
| RW057 | Starbucks' operating margin expanded to 14%. | Missing reporting year/period, financial basis, or metric definition. Do not infer it from publication date, a matching source value or latest SEC filing. Claude/Owner review required. |
| RW058 | Five Below's revenue increased by 23%. | Missing reporting year/period, financial basis, or metric definition. Do not infer it from publication date, a matching source value or latest SEC filing. Claude/Owner review required. |
| RW059 | Chipotle's third-quarter comparable sales increased by 2.1%. | Missing reporting year/period, financial basis, or metric definition. Do not infer it from publication date, a matching source value or latest SEC filing. Claude/Owner review required. |
| RW060 | Coupang's revenue is between 2.5 and 3 times Airbnb's revenue. | Missing reporting year/period, financial basis, or metric definition. Do not infer it from publication date, a matching source value or latest SEC filing. Claude/Owner review required. |

## Scope-only gold

These items have an operational expected outcome only; their financial truth has not been independently established:

- RW001: Third-party consensus/forecast changes require a dated analyst-estimate dataset. Issuer guidance cannot independently verify analyst estimates; factual truth unscored.
- RW003: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW005: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW007: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW009: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW010: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW011: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW013: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW016: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW017: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW018: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW020: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW021: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW022: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW023: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW024: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW025: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW027: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW028: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW029: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW030: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW031: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW032: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW037: Third-party consensus/forecast changes require a dated analyst-estimate dataset. Issuer guidance cannot independently verify analyst estimates; factual truth unscored.
- RW038: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW040: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW041: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW042: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW044: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW045: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW046: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW047: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW054: Third-party consensus/forecast changes require a dated analyst-estimate dataset. Issuer guidance cannot independently verify analyst estimates; factual truth unscored.
- RW061: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW062: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW063: Price/opinion/ownership/event/market-share statement is outside the current financial-filing checker. Expected abstention or post skip; factual truth unscored.
- RW064: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW065: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW066: Price/opinion/ownership/event/market-share statement is outside the current financial-filing checker. Expected abstention or post skip; factual truth unscored.
- RW067: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW068: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW069: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW070: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW071: Price/opinion/ownership/event/market-share statement is outside the current financial-filing checker. Expected abstention or post skip; factual truth unscored.
- RW072: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW073: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW074: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW075: Price/opinion/ownership/event/market-share statement is outside the current financial-filing checker. Expected abstention or post skip; factual truth unscored.
- RW076: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW077: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW078: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW079: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.
- RW080: TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.

TW follow-up requires MOPS/TWSE issuer records and careful ROC-year/currency/quarter alignment. Some stories repeat the same company's metric; story rows are not independent facts. The Lite-On EPS paraphrases retain both 3.27 and 3.28 from different published summaries, without choosing one. Several feed tickers refer to a different company from the statement; metadata tickers are not passed as authenticated issuer context.
