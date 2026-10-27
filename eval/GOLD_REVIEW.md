# Gold review

Generated from the raw SEC companyfacts snapshot. Values include the selected period dates and accession where available.

| ID | Split | Category | Claim | Gold verdict | SEC values with periods and accession |
|---|---|---|---|---|---|
| C01 | dev | exact_value_true | Meta's second-quarter 2025 revenue landed at $47.5 billion. | supported | META revenue 2025Q2 = $47.516B; 2025-04-01–2025-06-30; 0001628280-26-050705 |
| C02 | dev | exact_value_true | Tesla reported $28.1 billion in revenue for Q3 2025. | supported | TSLA revenue 2025Q3 = $28.095B; 2025-07-01–2025-09-30; 0001628280-26-066775 |
| C03 | dev | exact_value_true | Alphabet's Q3 2025 revenue was $102.3 billion. | supported | GOOGL revenue 2025Q3 = $102.346B; 2025-07-01–2025-09-30; 0001652044-25-000091 |
| C04 | test | exact_value_true | Amazon's Q3 2023 net income came in at $9.9 billion. | supported | AMZN net_income 2023Q3 = $9.879B; 2023-07-01–2023-09-30; 0001018724-24-000161 |
| C05 | dev | exact_value_false | Meta's Q2 2025 revenue was $47.4 billion, according to the filing. | contradicted | META revenue 2025Q2 = $47.516B; 2025-04-01–2025-06-30; 0001628280-26-050705 |
| C06 | dev | exact_value_false | Tesla's Q3 2025 net income was $1.3 billion. | contradicted | TSLA net_income 2025Q3 = $1.373B; 2025-07-01–2025-09-30; 0001628280-26-066775 |
| C07 | dev | exact_value_false | Microsoft closed fiscal 2025 with $281.6 billion in revenue. | contradicted | MSFT revenue FY2025 = $281.724B; 2024-07-01–2025-06-30; 0001193125-26-323660 |
| C08 | test | exact_value_false | Apple's fiscal 2025 net income was $111.0 billion. | contradicted | AAPL net_income FY2025 = $112.010B; 2024-09-29–2025-09-27; 0000320193-25-000079 |
| C09 | dev | approximate | Tesla's Q3 2025 profit was about $1.4 billion. | supported | TSLA net_income 2025Q3 = $1.373B; 2025-07-01–2025-09-30; 0001628280-26-066775 |
| C10 | dev | approximate | Microsoft's September quarter brought in roughly $77 billion of revenue. | supported | MSFT revenue 2025Q3 = $77.673B; 2025-07-01–2025-09-30; 0001193125-25-256321 |
| C11 | test | approximate | NVIDIA's quarter ended in late July 2026 generated about $96 billion in revenue. | supported | NVDA revenue 2026Q2 = $96.221B; 2026-04-27–2026-07-26; 0001045810-26-000075 |
| C12 | dev | inequality | Alphabet's Q3 2025 revenue topped $100 billion. | supported | GOOGL revenue 2025Q3 = $102.346B; 2025-07-01–2025-09-30; 0001652044-25-000091 |
| C13 | dev | inequality | Amazon's Q3 2025 revenue came in below $181 billion. | supported | AMZN revenue 2025Q3 = $180.169B; 2025-07-01–2025-09-30; 0001018724-25-000123 |
| C14 | test | inequality | Apple's June 2026 quarter cleared $110 billion in revenue. | contradicted | AAPL revenue 2026Q2 = $109.417B; 2026-03-29–2026-06-27; 0000320193-26-000020 |
| C15 | dev | yoy_true | Meta's Q2 2025 revenue was up 22% year over year. | supported | META revenue 2025Q2 = $47.516B; 2025-04-01–2025-06-30; 0001628280-26-050705<br>META revenue 2024Q2 = $39.071B; 2024-04-01–2024-06-30; 0001628280-25-036791 |
| C16 | test | yoy_true | NVIDIA's revenue for the quarter ended October 2025 jumped 62% from a year earlier. | supported | NVDA revenue 2025Q3 = $57.006B; 2025-07-28–2025-10-26; 0001045810-25-000230<br>NVDA revenue 2024Q3 = $35.082B; 2024-07-29–2024-10-27; 0001045810-25-000230 |
| C17 | dev | yoy_true | Tesla's Q3 2025 sales grew 12% from the same quarter a year earlier. | supported | TSLA revenue 2025Q3 = $28.095B; 2025-07-01–2025-09-30; 0001628280-26-066775<br>TSLA revenue 2024Q3 = $25.182B; 2024-07-01–2024-09-30; 0001628280-25-045968 |
| C18 | dev | yoy_false | Tesla's Q3 2025 revenue fell 10% year over year. | contradicted | TSLA revenue 2025Q3 = $28.095B; 2025-07-01–2025-09-30; 0001628280-26-066775<br>TSLA revenue 2024Q3 = $25.182B; 2024-07-01–2024-09-30; 0001628280-25-045968 |
| C19 | dev | yoy_false | Meta's Q2 2025 revenue rose 30% from a year earlier. | contradicted | META revenue 2025Q2 = $47.516B; 2025-04-01–2025-06-30; 0001628280-26-050705<br>META revenue 2024Q2 = $39.071B; 2024-04-01–2024-06-30; 0001628280-25-036791 |
| C20 | test | yoy_false | Apple's June 2026 revenue was down 8% year over year. | contradicted | AAPL revenue 2026Q2 = $109.417B; 2026-03-29–2026-06-27; 0000320193-26-000020<br>AAPL revenue 2025Q2 = $94.036B; 2025-03-30–2025-06-28; 0000320193-26-000020 |
| C21 | dev | period_trap | Apple's fiscal 2025 revenue of $416.2 billion was generated in the fourth quarter. | contradicted | AAPL revenue FY2025Q4 = $102.466B; 2025-06-29–2025-09-27; 0000320193-25-000079 |
| C22 | dev | period_trap | Microsoft's fourth-quarter 2025 revenue was $281.7 billion. | contradicted | MSFT revenue FY2025Q4 = $76.441B; 2025-04-01–2025-06-30; 0000950170-25-100235<br>MSFT revenue 2025Q4 = $81.273B; 2025-10-01–2025-12-31; 0001193125-26-027207 |
| C23 | test | period_trap | NVIDIA's fiscal 2025 third-quarter revenue was $57.0 billion. | contradicted | NVDA revenue FY2025Q3 = $35.082B; 2024-07-29–2024-10-27; 0001045810-24-000316<br>NVDA revenue FY2026Q3 = $57.006B; 2025-07-28–2025-10-26; 0001045810-25-000230 |
| C24 | dev | unit_trap | Amazon's Q3 2025 revenue was $180.2 million. | contradicted | AMZN revenue 2025Q3 = $180.169B; 2025-07-01–2025-09-30; 0001018724-25-000123 |
| C25 | test | unit_trap | Meta's Q2 2025 revenue was $47,516 million. | supported | META revenue 2025Q2 = $47.516B; 2025-04-01–2025-06-30; 0001628280-26-050705 |
| C26 | dev | multi_part | Meta's Q2 2025 revenue was $47.5 billion, and net income was $18.9 billion. | contradicted | META revenue 2025Q2 = $47.516B; 2025-04-01–2025-06-30; 0001628280-26-050705<br>META net_income 2025Q2 = $18.337B; 2025-04-01–2025-06-30; 0001628280-26-050705 |
| C27 | test | multi_part | Amazon's Q3 2025 revenue topped $180 billion, while net income topped $22 billion. | contradicted | AMZN revenue 2025Q3 = $180.169B; 2025-07-01–2025-09-30; 0001018724-25-000123<br>AMZN net_income 2025Q3 = $21.187B; 2025-07-01–2025-09-30; 0001018724-25-000123 |
| C28 | dev | record_first | Meta's Q2 2026 revenue was the first quarterly result above $60 billion. | supported | META revenue 2026Q2 = $60.801B; 2026-04-01–2026-06-30; 0001628280-26-050705<br>META revenue 2025Q4 = $59.893B; 2025-10-01–2025-12-31; 0001628280-26-003942 |
| C29 | dev | insufficient_evidence | Tesla expects to deliver 2.2 million vehicles in 2026. | insufficient_evidence | — not checkable with SEC companyfacts |
| C30 | test | insufficient_evidence | NVIDIA held roughly 90% of the 2025 AI accelerator market. | insufficient_evidence | — not checkable with SEC companyfacts |
