# SEC companyfacts data quality

Snapshot date: **2026-10-27**. Issuers: **24**. Checks use only the cached SEC companyfacts JSON; no network or live calls are used.

A quarterly sum check runs when an annual fact and all four quarters are derivable. The tolerance is the larger of 0.5% of the annual value and $1 million. YTD monotonicity is checked only for metrics that cannot decrease within a year (revenue, gross profit, capex, R&D); income lines can legitimately fall after a loss quarter. Fiscal years and quarters are assigned from each period's own dates (SEC `fy`/`fp` describe the filing, not the period). Anomalies are consistency failures (quarterly sum ≠ annual, falling YTD totals) and non-statement-form fallbacks. Periods that later filings report with a different value are listed separately as revisions — routine reclassifications are common — and counted as material when the change exceeds 0.5%. Detail examples are capped at 12 per metric while counts remain complete.

## Summary by issuer

| Issuer | Ticker | Checks passed | Checks total | Anomalies | Revised periods | Material revisions | Form fallbacks |
|---|---|---:|---:|---:|---:|---:|---:|
| ADVANCED MICRO DEVICES INC | AMD | 160 | 164 | 0 | 31 | 27 | 0 |
| JPMORGAN CHASE & CO | JPM | 32 | 34 | 0 | 21 | 6 | 0 |
| COCA COLA CO | KO | 127 | 131 | 0 | 48 | 29 | 0 |
| INTEL CORP | INTC | 170 | 172 | 0 | 23 | 8 | 0 |
| PEPSICO INC | PEP | 77 | 79 | 0 | 21 | 13 | 0 |
| Walmart Inc. | WMT | 111 | 114 | 1 | 42 | 9 | 0 |
| Johnson & Johnson | JNJ | 123 | 126 | 0 | 27 | 19 | 0 |
| NIKE, Inc. | NKE | 112 | 115 | 0 | 36 | 16 | 0 |
| Apple Inc. | AAPL | 159 | 162 | 0 | 15 | 12 | 0 |
| UnitedHealth Group Incorporated | UNH | 114 | 114 | 0 | 0 | 0 | 0 |
| Microsoft Corporation | MSFT | 179 | 186 | 4 | 35 | 26 | 1 |
| ADOBE INC. | ADBE | 152 | 152 | 0 | 36 | 0 | 0 |
| CISCO SYSTEMS, INC. | CSCO | 177 | 177 | 0 | 0 | 0 | 0 |
| COSTCO WHOLESALE CORP /NEW | COST | 84 | 84 | 0 | 0 | 0 | 0 |
| AMAZON COM INC | AMZN | 81 | 83 | 1 | 8 | 8 | 0 |
| NVIDIA CORP | NVDA | 161 | 165 | 0 | 49 | 7 | 0 |
| Netflix, Inc. | NFLX | 158 | 161 | 0 | 33 | 26 | 0 |
| Salesforce, Inc. | CRM | 176 | 190 | 10 | 45 | 31 | 0 |
| Tesla, Inc. | TSLA | 171 | 173 | 0 | 69 | 11 | 0 |
| Meta Platforms, Inc. | META | 125 | 128 | 0 | 24 | 14 | 0 |
| Oracle Corporation | ORCL | 141 | 150 | 5 | 27 | 18 | 0 |
| VISA INC. | V | 76 | 76 | 0 | 0 | 0 | 0 |
| Alphabet Inc. | GOOGL | 102 | 104 | 0 | 13 | 9 | 0 |
| ExxonMobil Holdings Corp | XOM | 6 | 6 | 0 | 0 | 0 | 0 |

## Metric coverage

| Issuer | revenue | net_income | operating_income | gross_profit | capex | rd_expense |
|---|---:|---:|---:|---:|---:|---:|
| AMD | available | available | available | available | available | available |
| JPM | available | available | — | — | — | — |
| KO | available | available | available | available | available | — |
| INTC | available | available | available | available | available | available |
| PEP | available | available | available | available | — | available |
| WMT | available | available | available | — | available | — |
| JNJ | available | available | available | available | available | available |
| NKE | available | available | — | available | available | — |
| AAPL | available | available | available | available | available | available |
| UNH | available | available | available | — | available | — |
| MSFT | available | available | available | available | available | available |
| ADBE | available | available | available | available | available | — |
| CSCO | available | available | available | available | available | available |
| COST | available | available | available | available | available | — |
| AMZN | available | available | available | available | available | — |
| NVDA | available | available | available | available | available | available |
| NFLX | available | available | available | available | available | available |
| CRM | available | available | available | available | available | available |
| TSLA | available | available | available | available | available | available |
| META | available | available | available | — | available | available |
| ORCL | available | available | available | available | available | available |
| V | available | available | available | — | — | — |
| GOOGL | available | available | available | — | available | available |
| XOM | available | available | — | — | available | — |

## Anomalies

| Issuer | Metric | Type | Period | Accessions |
|---|---|---|---|---|
| WMT | revenue | annual_sum_mismatch | 2017 | 0000104169-18-000028, 0000104169-19-000016 |
| MSFT | net_income | annual_sum_mismatch | 2016 | 0001564590-17-014900, 0001564590-18-019062 |
| MSFT | operating_income | annual_sum_mismatch | 2016 | 0001564590-17-014900, 0001564590-18-019062 |
| MSFT | operating_income | form_fallback | 2014-04-01 | 0001193125-15-353706 |
| MSFT | gross_profit | annual_sum_mismatch | 2016 | 0001564590-17-014900, 0001564590-18-019062 |
| AMZN | net_income | annual_sum_mismatch | 2011 | 0001018724-14-000006, 0001193125-13-028520 |
| CRM | revenue | annual_sum_mismatch | 2017 | 0001108524-17-000006, 0001108524-19-000009 |
| CRM | net_income | annual_sum_mismatch | 2017 | 0001108524-18-000011, 0001108524-19-000009 |
| CRM | net_income | annual_sum_mismatch | 2020 | 0001108524-20-000014, 0001108524-20-000047, 0001108524-22-000013 |
| CRM | net_income | annual_sum_mismatch | 2021 | 0001108524-21-000055, 0001108524-23-000011 |
| CRM | net_income | annual_sum_mismatch | 2022 | 0001108524-22-000060, 0001108524-24-000005 |
| CRM | net_income | annual_sum_mismatch | 2023 | 0001108524-23-000048, 0001108524-25-000006 |
| CRM | net_income | annual_sum_mismatch | 2024 | 0001108524-24-000034, 0001108524-26-000060 |
| CRM | net_income | annual_sum_mismatch | 2025 | 0001108524-25-000238, 0001108524-26-000060 |
| CRM | operating_income | annual_sum_mismatch | 2017 | 0001108524-18-000011, 0001108524-19-000009 |
| CRM | gross_profit | annual_sum_mismatch | 2017 | 0001108524-18-000011, 0001108524-19-000009 |
| ORCL | revenue | annual_sum_mismatch | 2018 | 0001564590-18-023315, 0001564590-18-031113, 0001564590-19-008273, 0001564590-20-030125 |
| ORCL | revenue | annual_sum_mismatch | 2019 | 0001564590-19-034717, 0001564590-19-045966, 0001564590-20-010833, 0001564590-21-033616 |
| ORCL | revenue | annual_sum_mismatch | 2020 | 0001564590-20-043448, 0001564590-20-056896, 0001564590-21-012539, 0001564590-22-023675 |
| ORCL | revenue | annual_sum_mismatch | 2021 | 0000950170-23-028914, 0001564590-21-047772, 0001564590-21-060022, 0001564590-22-009859, 0001564590-22-023675 |
| ORCL | revenue | annual_sum_mismatch | 2022 | 0000950170-24-075605, 0001564590-22-023675, 0001564590-22-031545, 0001564590-22-039278, 0001564590-23-003413 |

## Interpretation

A passed arithmetic check does not make a filing correct; it only shows internal consistency between tagged facts. A restatement is not automatically an error, but it lowers evidence strength for verdicts that rely on the affected period. A form fallback means the selected period had no 10-K/10-Q statement-form row and should be treated as low strength.
