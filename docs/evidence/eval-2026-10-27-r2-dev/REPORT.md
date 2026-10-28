# Market claim evaluation report

Generated: 2026-10-28T00:13:23.014330Z
Run window: 2026-10-27T23:58:57.749703Z → 2026-10-28T00:13:22.809842Z
Wall clock: 865.056 s

Accuracy uses all expected claims in the denominator; a missing, failed, or budget-stopped pair is not a correct prediction. Per-class recall uses all claims of that gold class, while precision uses completed predictions of that class. False-supported rate is the harmful error rate among gold contradicted or insufficient-evidence claims. Latency and cost summaries use completed pairs only.

No significance claims are made: each split is small (20 dev and 10 test claims).

## Per-system totals

Tokens are shown as input/cached/output/reasoning. Totals include every recorded pair; latency percentiles include pairs with a recorded model call.

| System | Pairs | Completed | Total cost | Input tokens | Cached tokens | Output tokens | Reasoning tokens | Model calls | Tool calls | Mean latency ms | p50 ms | p95 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| single_shot@meta | 0 | 0 | 0.000000 | 0 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| agent@meta | 20 | 20 | 0.411636 | 118299 | 8536 | 64271 | 53801 | 63 | 30 | 31215.8 | 27944.8 | 47619.3 |
| single_shot@baseten | 0 | 0 | 0.000000 | 0 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| agent@baseten | 20 | 20 | 0.373179 | 188629 | 123008 | 64165 | 52238 | 64 | 36 | 12030.8 | 10994.8 | 22422.4 |

## Provider comparison

Reasoning share is reasoning tokens divided by output tokens; provider totals include both methods.

| Provider | Pairs | Completed | Accuracy | False-supported rate | Total cost | Mean latency ms | Input | Cached | Output | Reasoning | Reasoning share |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| meta | 20 | 20 | 0.650 | 0.000 | 0.411636 | 31215.8 | 118299 | 8536 | 64271 | 53801 | 0.837 |
| baseten | 20 | 20 | 0.950 | 0.000 | 0.373179 | 12030.8 | 188629 | 123008 | 64165 | 52238 | 0.814 |

## Prompt versions

| Prompt | SHA-256 prefix |
|---|---|
| agent_tool_loop_instructions | bbe6c9df1e88 |
| agent_final_verdict_prompt | 60242d984bcb |
| baseten_tool_loop_instructions | bbe6c9df1e88 |
| baseten_final_verdict_prompt | c4fdd301e84a |
| baseten_repair_prompt | ad1480520494 |
| baseten_single_shot_instructions | 07437d0222d2 |
| verdict_json_schema | 1dc36f8ebdbc |
| tool_schemas | 267f0d54106d |
| single_shot_instructions | 9677f9a3b64a |

## Metrics

| System | Split | n | completed | errors | accuracy | false-supported rate | insufficient rate | mean latency ms | p50 ms | p95 ms | total cost | mean cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| single_shot@meta | dev | 20 | 0 | 20 | 0.000 | 0.000 | 0.000 | — | — | — | 0.000000 | — |
| single_shot@meta | test | 0 | 0 | 0 | 0.000 | 0.000 | 0.000 | — | — | — | 0.000000 | — |
| agent@meta | dev | 20 | 20 | 0 | 0.650 | 0.000 | 0.400 | 31215.8 | 27944.8 | 47619.3 | 0.411636 | 0.020582 |
| agent@meta | test | 0 | 0 | 0 | 0.000 | 0.000 | 0.000 | — | — | — | 0.000000 | — |
| single_shot@baseten | dev | 20 | 0 | 20 | 0.000 | 0.000 | 0.000 | — | — | — | 0.000000 | — |
| single_shot@baseten | test | 0 | 0 | 0 | 0.000 | 0.000 | 0.000 | — | — | — | 0.000000 | — |
| agent@baseten | dev | 20 | 20 | 0 | 0.950 | 0.000 | 0.100 | 12030.8 | 10994.8 | 22422.4 | 0.373179 | 0.018659 |
| agent@baseten | test | 0 | 0 | 0 | 0.000 | 0.000 | 0.000 | — | — | — | 0.000000 | — |

### Per-gold-class precision and recall

| System | Split | Gold class | Support | Predicted | Precision | Recall |
|---|---|---|---:|---:|---:|---:|
| single_shot@meta | dev | supported | 10 | 0 | 0.000 | 0.000 |
| single_shot@meta | dev | contradicted | 9 | 0 | 0.000 | 0.000 |
| single_shot@meta | dev | insufficient_evidence | 1 | 0 | 0.000 | 0.000 |
| single_shot@meta | test | supported | 0 | 0 | 0.000 | 0.000 |
| single_shot@meta | test | contradicted | 0 | 0 | 0.000 | 0.000 |
| single_shot@meta | test | insufficient_evidence | 0 | 0 | 0.000 | 0.000 |
| agent@meta | dev | supported | 10 | 5 | 1.000 | 0.500 |
| agent@meta | dev | contradicted | 9 | 7 | 1.000 | 0.778 |
| agent@meta | dev | insufficient_evidence | 1 | 8 | 0.125 | 1.000 |
| agent@meta | test | supported | 0 | 0 | 0.000 | 0.000 |
| agent@meta | test | contradicted | 0 | 0 | 0.000 | 0.000 |
| agent@meta | test | insufficient_evidence | 0 | 0 | 0.000 | 0.000 |
| single_shot@baseten | dev | supported | 10 | 0 | 0.000 | 0.000 |
| single_shot@baseten | dev | contradicted | 9 | 0 | 0.000 | 0.000 |
| single_shot@baseten | dev | insufficient_evidence | 1 | 0 | 0.000 | 0.000 |
| single_shot@baseten | test | supported | 0 | 0 | 0.000 | 0.000 |
| single_shot@baseten | test | contradicted | 0 | 0 | 0.000 | 0.000 |
| single_shot@baseten | test | insufficient_evidence | 0 | 0 | 0.000 | 0.000 |
| agent@baseten | dev | supported | 10 | 9 | 1.000 | 0.900 |
| agent@baseten | dev | contradicted | 9 | 9 | 1.000 | 1.000 |
| agent@baseten | dev | insufficient_evidence | 1 | 2 | 0.500 | 1.000 |
| agent@baseten | test | supported | 0 | 0 | 0.000 | 0.000 |
| agent@baseten | test | contradicted | 0 | 0 | 0.000 | 0.000 |
| agent@baseten | test | insufficient_evidence | 0 | 0 | 0.000 | 0.000 |

## Per-claim results

Tokens are shown as input/cached/output/reasoning for each system.

| ID | Split | Category | Claim | Gold | Single Shot verdict | Single Shot correct? | Single Shot cost | Single Shot latency ms | Single Shot tokens (i/c/o/r) | Agent verdict | Agent correct? | Agent cost | Agent latency ms | Agent tokens (i/c/o/r) | Single Shot@Baseten verdict | Single Shot@Baseten correct? | Single Shot@Baseten cost | Single Shot@Baseten latency ms | Single Shot@Baseten tokens (i/c/o/r) | Agent@Baseten verdict | Agent@Baseten correct? | Agent@Baseten cost | Agent@Baseten latency ms | Agent@Baseten tokens (i/c/o/r) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C01 | dev | exact_value_true | Meta's second-quarter 2025 revenue landed at $47.5 billion. | supported | missing | no | — | — | — | supported | yes | 0.015079 | 26614.8 | 5257/113/2031/1535 | missing | no | — | — | — | supported | yes | 0.017249 | 10960.6 | 7345/3712/2859/2349 |
| C02 | dev | exact_value_true | Tesla reported $28.1 billion in revenue for Q3 2025. | supported | missing | no | — | — | — | supported | yes | 0.014977 | 31154.1 | 4652/113/2185/1783 | missing | no | — | — | — | supported | yes | 0.015807 | 8655.8 | 8268/3456/2182/1501 |
| C03 | dev | exact_value_true | Alphabet's Q3 2025 revenue was $102.3 billion. | supported | missing | no | — | — | — | supported | yes | 0.016724 | 47519.3 | 5272/744/2577/2126 | missing | no | — | — | — | supported | yes | 0.021986 | 15580.0 | 10771/8704/4258/3650 |
| C05 | dev | exact_value_false | Meta's Q2 2025 revenue was $47.4 billion, according to the filing. | contradicted | missing | no | — | — | — | contradicted | yes | 0.016605 | 26954.7 | 4699/0/2525/2084 | missing | no | — | — | — | contradicted | yes | 0.015752 | 11346.7 | 7349/6016/3102/2549 |
| C06 | dev | exact_value_false | Tesla's Q3 2025 net income was $1.3 billion. | contradicted | missing | no | — | — | — | contradicted | yes | 0.019579 | 26742.8 | 5327/0/3040/2477 | missing | no | — | — | — | contradicted | yes | 0.024380 | 15998.1 | 11350/8704/4651/3970 |
| C07 | dev | exact_value_false | Microsoft closed fiscal 2025 with $281.6 billion in revenue. | contradicted | missing | no | — | — | — | contradicted | yes | 0.033180 | 49519.1 | 5139/488/6422/6043 | missing | no | — | — | — | contradicted | yes | 0.031605 | 25319.8 | 9280/7936/6761/6286 |
| C09 | dev | approximate | Tesla's Q3 2025 profit was about $1.4 billion. | supported | missing | no | — | — | — | insufficient_evidence | no | 0.017509 | 24663.4 | 5249/0/2576/2085 | missing | no | — | — | — | insufficient_evidence | no | 0.011207 | 7591.5 | 7317/6016/2042/1554 |
| C10 | dev | approximate | Microsoft's September quarter brought in roughly $77 billion of revenue. | supported | missing | no | — | — | — | insufficient_evidence | no | 0.022265 | 36179.9 | 6497/0/3328/2795 | missing | no | — | — | — | supported | yes | 0.016418 | 11253.0 | 10859/8576/2889/2186 |
| C12 | dev | inequality | Alphabet's Q3 2025 revenue topped $100 billion. | supported | missing | no | — | — | — | insufficient_evidence | no | 0.015071 | 27787.7 | 4609/1265/2518/2159 | missing | no | — | — | — | supported | yes | 0.010920 | 8187.4 | 7247/6016/1995/1633 |
| C13 | dev | inequality | Amazon's Q3 2025 revenue came in below $181 billion. | supported | missing | no | — | — | — | supported | yes | 0.017109 | 23123.6 | 5316/0/2462/1986 | missing | no | — | — | — | supported | yes | 0.010817 | 7487.6 | 7307/4864/1655/1241 |
| C15 | dev | yoy_true | Meta's Q2 2025 revenue was up 22% year over year. | supported | missing | no | — | — | — | insufficient_evidence | no | 0.018957 | 28101.9 | 6139/0/2655/2178 | missing | no | — | — | — | supported | yes | 0.015788 | 11028.9 | 8751/6016/2698/2277 |
| C17 | dev | yoy_true | Tesla's Q3 2025 sales grew 12% from the same quarter a year earlier. | supported | missing | no | — | — | — | insufficient_evidence | no | 0.022657 | 26035.8 | 6202/0/3507/2911 | missing | no | — | — | — | supported | yes | 0.025963 | 19195.0 | 8823/6016/5071/4530 |
| C18 | dev | yoy_false | Tesla's Q3 2025 revenue fell 10% year over year. | contradicted | missing | no | — | — | — | contradicted | yes | 0.018744 | 29366.4 | 6221/1265/2908/2341 | missing | no | — | — | — | contradicted | yes | 0.012124 | 7043.7 | 8788/6016/1825/1350 |
| C19 | dev | yoy_false | Meta's Q2 2025 revenue rose 30% from a year earlier. | contradicted | missing | no | — | — | — | contradicted | yes | 0.020250 | 27153.6 | 6144/113/2987/2489 | missing | no | — | — | — | contradicted | yes | 0.014365 | 9095.3 | 8752/6016/2363/1944 |
| C21 | dev | period_trap | Apple's fiscal 2025 revenue of $416.2 billion was generated in the fourth quarter. | contradicted | missing | no | — | — | — | insufficient_evidence | no | 0.029020 | 31026.3 | 5624/0/5174/4407 | missing | no | — | — | — | contradicted | yes | 0.018283 | 11440.5 | 8643/6016/3317/2430 |
| C22 | dev | period_trap | Microsoft's fourth-quarter 2025 revenue was $281.7 billion. | contradicted | missing | no | — | — | — | insufficient_evidence | no | 0.018669 | 45222.9 | 5676/4322/3842/3086 | missing | no | — | — | — | contradicted | yes | 0.020345 | 11695.6 | 9121/4608/3297/2452 |
| C24 | dev | unit_trap | Amazon's Q3 2025 revenue was $180.2 million. | contradicted | missing | no | — | — | — | contradicted | yes | 0.020265 | 27395.0 | 5315/0/3205/2714 | missing | no | — | — | — | contradicted | yes | 0.014725 | 10387.6 | 10810/8704/2538/1917 |
| C26 | dev | multi_part | Meta's Q2 2025 revenue was $47.5 billion, and net income was $18.9 billion. | contradicted | missing | no | — | — | — | contradicted | yes | 0.024775 | 34442.1 | 7115/113/3766/3074 | missing | no | — | — | — | contradicted | yes | 0.012087 | 7518.0 | 8065/6016/2029/1270 |
| C28 | dev | record_first | Meta's Q2 2026 revenue was the first quarterly result above $60 billion. | supported | missing | no | — | — | — | supported | yes | 0.032722 | 36646.6 | 15223/0/3222/2506 | missing | no | — | — | — | supported | yes | 0.052197 | 22269.9 | 25530/6016/6330/5230 |
| C29 | dev | insufficient_evidence | Tesla expects to deliver 2.2 million vehicles in 2026. | insufficient_evidence | missing | no | — | — | — | insufficient_evidence | yes | 0.017478 | 18665.6 | 2623/0/3341/3022 | missing | no | — | — | — | insufficient_evidence | yes | 0.011162 | 8561.7 | 4253/3584/2303/1919 |

## Agent errors

None recorded.

## Accounting

Budget stop: none recorded.
Ledger spend before/after: $0.000000 / $0.784815.
