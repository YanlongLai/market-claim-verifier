# Market claim evaluation report

Generated: 2026-10-28T00:51:28.540830Z
Run window: 2026-10-28T00:30:53.536496Z → 2026-10-28T00:51:28.371969Z
Wall clock: 1234.829 s

Accuracy uses all expected claims in the denominator; a missing, failed, or budget-stopped pair is not a correct prediction. Per-class recall uses all claims of that gold class, while precision uses completed predictions of that class. False-supported rate is the harmful error rate among gold contradicted or insufficient-evidence claims. Latency and cost summaries use completed pairs only.

No significance claims are made: each split is small (20 dev and 10 test claims).

## Per-system totals

Tokens are shown as input/cached/output/reasoning. Totals include every recorded pair; latency percentiles include pairs with a recorded model call.

| System | Pairs | Completed | Total cost | Input tokens | Cached tokens | Output tokens | Reasoning tokens | Model calls | Tool calls | Mean latency ms | p50 ms | p95 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| single_shot@meta | 0 | 0 | 0.000000 | 0 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| agent@meta | 30 | 29 | 0.645645 | 178260 | 27281 | 98950 | 82074 | 93 | 49 | 31369.1 | 27854.3 | 49602.7 |
| single_shot@baseten | 0 | 0 | 0.000000 | 0 | 0 | 0 | 0 | 0 | 0 | — | — | — |
| agent@baseten | 30 | 30 | 0.460989 | 273397 | 191872 | 77718 | 60517 | 94 | 53 | 9786.1 | 9643.7 | 14119.5 |

## Provider comparison

Reasoning share is reasoning tokens divided by output tokens; provider totals include both methods.

| Provider | Pairs | Completed | Accuracy | False-supported rate | Total cost | Mean latency ms | Input | Cached | Output | Reasoning | Reasoning share |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| meta | 30 | 29 | 0.867 | 0.000 | 0.602091 | 31919.2 | 178260 | 27281 | 98950 | 82074 | 0.829 |
| baseten | 30 | 30 | 0.967 | 0.000 | 0.460989 | 9786.1 | 273397 | 191872 | 77718 | 60517 | 0.779 |

## Prompt versions

| Prompt | SHA-256 prefix |
|---|---|
| agent_tool_loop_instructions | 4fd6e765db32 |
| agent_final_verdict_prompt | ea9ff5500ad7 |
| baseten_tool_loop_instructions | 4fd6e765db32 |
| baseten_final_verdict_prompt | 8a0f8f1b51f9 |
| baseten_repair_prompt | 0e13993581ac |
| baseten_single_shot_instructions | 50875e0b864d |
| verdict_json_schema | 641d01f47032 |
| tool_schemas | 267f0d54106d |
| single_shot_instructions | 9677f9a3b64a |

## Metrics

| System | Split | n | completed | errors | accuracy | false-supported rate | insufficient rate | mean latency ms | p50 ms | p95 ms | total cost | mean cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| single_shot@meta | dev | 20 | 0 | 20 | 0.000 | 0.000 | 0.000 | — | — | — | 0.000000 | — |
| single_shot@meta | test | 10 | 0 | 10 | 0.000 | 0.000 | 0.000 | — | — | — | 0.000000 | — |
| agent@meta | dev | 20 | 19 | 1 | 0.900 | 0.000 | 0.100 | 34062.9 | 28672.0 | 52327.0 | 0.419673 | 0.022088 |
| agent@meta | test | 10 | 10 | 0 | 0.800 | 0.000 | 0.300 | 27846.0 | 26606.4 | 37453.1 | 0.182417 | 0.018242 |
| single_shot@baseten | dev | 20 | 0 | 20 | 0.000 | 0.000 | 0.000 | — | — | — | 0.000000 | — |
| single_shot@baseten | test | 10 | 0 | 10 | 0.000 | 0.000 | 0.000 | — | — | — | 0.000000 | — |
| agent@baseten | dev | 20 | 20 | 0 | 0.950 | 0.000 | 0.100 | 9589.9 | 9370.5 | 14130.3 | 0.302636 | 0.015132 |
| agent@baseten | test | 10 | 10 | 0 | 1.000 | 0.000 | 0.100 | 10178.4 | 10046.2 | 13720.6 | 0.158352 | 0.015835 |

### Per-gold-class precision and recall

| System | Split | Gold class | Support | Predicted | Precision | Recall |
|---|---|---|---:|---:|---:|---:|
| single_shot@meta | dev | supported | 10 | 0 | 0.000 | 0.000 |
| single_shot@meta | dev | contradicted | 9 | 0 | 0.000 | 0.000 |
| single_shot@meta | dev | insufficient_evidence | 1 | 0 | 0.000 | 0.000 |
| single_shot@meta | test | supported | 4 | 0 | 0.000 | 0.000 |
| single_shot@meta | test | contradicted | 5 | 0 | 0.000 | 0.000 |
| single_shot@meta | test | insufficient_evidence | 1 | 0 | 0.000 | 0.000 |
| agent@meta | dev | supported | 10 | 9 | 1.000 | 0.900 |
| agent@meta | dev | contradicted | 9 | 8 | 1.000 | 0.889 |
| agent@meta | dev | insufficient_evidence | 1 | 2 | 0.500 | 1.000 |
| agent@meta | test | supported | 4 | 2 | 1.000 | 0.500 |
| agent@meta | test | contradicted | 5 | 5 | 1.000 | 1.000 |
| agent@meta | test | insufficient_evidence | 1 | 3 | 0.333 | 1.000 |
| single_shot@baseten | dev | supported | 10 | 0 | 0.000 | 0.000 |
| single_shot@baseten | dev | contradicted | 9 | 0 | 0.000 | 0.000 |
| single_shot@baseten | dev | insufficient_evidence | 1 | 0 | 0.000 | 0.000 |
| single_shot@baseten | test | supported | 4 | 0 | 0.000 | 0.000 |
| single_shot@baseten | test | contradicted | 5 | 0 | 0.000 | 0.000 |
| single_shot@baseten | test | insufficient_evidence | 1 | 0 | 0.000 | 0.000 |
| agent@baseten | dev | supported | 10 | 9 | 1.000 | 0.900 |
| agent@baseten | dev | contradicted | 9 | 9 | 1.000 | 1.000 |
| agent@baseten | dev | insufficient_evidence | 1 | 2 | 0.500 | 1.000 |
| agent@baseten | test | supported | 4 | 4 | 1.000 | 1.000 |
| agent@baseten | test | contradicted | 5 | 5 | 1.000 | 1.000 |
| agent@baseten | test | insufficient_evidence | 1 | 1 | 1.000 | 1.000 |

## Per-claim results

Tokens are shown as input/cached/output/reasoning for each system.

| ID | Split | Category | Claim | Gold | Single Shot verdict | Single Shot correct? | Single Shot cost | Single Shot latency ms | Single Shot tokens (i/c/o/r) | Agent verdict | Agent correct? | Agent cost | Agent latency ms | Agent tokens (i/c/o/r) | Single Shot@Baseten verdict | Single Shot@Baseten correct? | Single Shot@Baseten cost | Single Shot@Baseten latency ms | Single Shot@Baseten tokens (i/c/o/r) | Agent@Baseten verdict | Agent@Baseten correct? | Agent@Baseten cost | Agent@Baseten latency ms | Agent@Baseten tokens (i/c/o/r) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C01 | dev | exact_value_true | Meta's second-quarter 2025 revenue landed at $47.5 billion. | supported | missing | no | — | — | — | supported | yes | 0.016545 | 27546.1 | 5380/1265/2638/2090 | missing | no | — | — | — | supported | yes | 0.014613 | 7371.5 | 8078/3456/1957/1390 |
| C02 | dev | exact_value_true | Tesla reported $28.1 billion in revenue for Q3 2025. | supported | missing | no | — | — | — | supported | yes | 0.013754 | 22541.3 | 4691/1265/2184/1800 | missing | no | — | — | — | supported | yes | 0.018128 | 13843.7 | 7546/6016/3603/3055 |
| C03 | dev | exact_value_true | Alphabet's Q3 2025 revenue was $102.3 billion. | supported | missing | no | — | — | — | supported | yes | 0.016113 | 37054.8 | 5344/1265/2547/2052 | missing | no | — | — | — | supported | yes | 0.013860 | 9351.5 | 8069/6016/2445/1869 |
| C04 | test | exact_value_true | Amazon's Q3 2023 net income came in at $9.9 billion. | supported | missing | no | — | — | — | supported | yes | 0.018450 | 21648.6 | 4751/113/2973/2539 | missing | no | — | — | — | supported | yes | 0.013372 | 9227.6 | 7400/6016/2527/2131 |
| C05 | dev | exact_value_false | Meta's Q2 2025 revenue was $47.4 billion, according to the filing. | contradicted | missing | no | — | — | — | contradicted | yes | 0.035852 | 50280.9 | 6324/113/6605/5713 | missing | no | — | — | — | contradicted | yes | 0.011458 | 7883.4 | 7460/6016/2059/1602 |
| C06 | dev | exact_value_false | Tesla's Q3 2025 net income was $1.3 billion. | contradicted | missing | no | — | — | — | contradicted | yes | 0.016710 | 24045.8 | 4706/1265/2875/2459 | missing | no | — | — | — | contradicted | yes | 0.012583 | 9123.6 | 7401/6016/2341/1924 |
| C07 | dev | exact_value_false | Microsoft closed fiscal 2025 with $281.6 billion in revenue. | contradicted | missing | no | — | — | — | contradicted | yes | 0.015172 | 23482.7 | 4642/1265/2532/2184 | missing | no | — | — | — | contradicted | yes | 0.013898 | 9981.3 | 7416/6016/2646/2189 |
| C08 | test | exact_value_false | Apple's fiscal 2025 net income was $111.0 billion. | contradicted | missing | no | — | — | — | contradicted | yes | 0.015197 | 25376.3 | 4723/1265/2514/2068 | missing | no | — | — | — | contradicted | yes | 0.008818 | 5707.0 | 7381/6016/1461/1074 |
| C09 | dev | approximate | Tesla's Q3 2025 profit was about $1.4 billion. | supported | missing | no | — | — | — | supported | yes | 0.015401 | 23250.6 | 4650/0/2256/1914 | missing | no | — | — | — | supported | yes | 0.008948 | 5803.7 | 7444/6016/1473/992 |
| C10 | dev | approximate | Microsoft's September quarter brought in roughly $77 billion of revenue. | supported | missing | no | — | — | — | supported | yes | 0.018581 | 27813.2 | 5322/113/2836/2345 | missing | no | — | — | — | supported | yes | 0.015927 | 10545.3 | 10969/8576/2741/2135 |
| C11 | test | approximate | NVIDIA's quarter ended in late July 2026 generated about $96 billion in revenue. | supported | missing | no | — | — | — | insufficient_evidence | no | 0.021811 | 28182.2 | 5604/113/3513/2794 | missing | no | — | — | — | supported | yes | 0.016667 | 11063.0 | 8319/6016/3032/2414 |
| C12 | dev | inequality | Alphabet's Q3 2025 revenue topped $100 billion. | supported | missing | no | — | — | — | supported | yes | 0.017673 | 28672.0 | 5364/241/2643/2082 | missing | no | — | — | — | supported | yes | 0.014898 | 9389.5 | 10871/8832/2594/2040 |
| C13 | dev | inequality | Amazon's Q3 2025 revenue came in below $181 billion. | supported | missing | no | — | — | — | supported | yes | 0.018355 | 21895.7 | 5342/113/2777/2319 | missing | no | — | — | — | supported | yes | 0.007431 | 4839.0 | 7380/6016/1135/769 |
| C14 | test | inequality | Apple's June 2026 quarter cleared $110 billion in revenue. | contradicted | missing | no | — | — | — | contradicted | yes | 0.019023 | 28636.7 | 5349/113/2932/2448 | missing | no | — | — | — | contradicted | yes | 0.018111 | 12016.3 | 8121/6016/3430/2836 |
| C15 | dev | yoy_true | Meta's Q2 2025 revenue was up 22% year over year. | supported | missing | no | — | — | — | supported | yes | 0.021363 | 43256.9 | 6243/2402/3812/3281 | missing | no | — | — | — | supported | yes | 0.012335 | 7203.6 | 8889/6016/1845/1408 |
| C16 | test | yoy_true | NVIDIA's revenue for the quarter ended October 2025 jumped 62% from a year earlier. | supported | missing | no | — | — | — | insufficient_evidence | no | 0.024964 | 40445.0 | 8819/1634/3703/2886 | missing | no | — | — | — | supported | yes | 0.025139 | 14345.1 | 15146/8576/3680/2753 |
| C17 | dev | yoy_true | Tesla's Q3 2025 sales grew 12% from the same quarter a year earlier. | supported | missing | no | — | — | — | insufficient_evidence | no | 0.018996 | 27895.4 | 6256/1265/2957/2453 | missing | no | — | — | — | supported | yes | 0.015144 | 10076.0 | 8930/6016/2494/2041 |
| C18 | dev | yoy_false | Tesla's Q3 2025 revenue fell 10% year over year. | contradicted | missing | no | — | — | — | contradicted | yes | 0.024071 | 32858.8 | 6223/1265/4161/3663 | missing | no | — | — | — | contradicted | yes | 0.013463 | 7896.8 | 8913/3712/1507/1052 |
| C19 | dev | yoy_false | Meta's Q2 2025 revenue rose 30% from a year earlier. | contradicted | missing | no | — | — | — | failed | no | 0.043554 | 15416.6 | 4863/113/1249/971 | missing | no | — | — | — | contradicted | yes | 0.014305 | 9063.3 | 8891/6016/2308/1852 |
| C20 | test | yoy_false | Apple's June 2026 revenue was down 8% year over year. | contradicted | missing | no | — | — | — | contradicted | yes | 0.020239 | 26825.6 | 8420/1265/2613/2028 | missing | no | — | — | — | contradicted | yes | 0.019415 | 10422.8 | 11160/6016/2843/2198 |
| C21 | dev | period_trap | Apple's fiscal 2025 revenue of $416.2 billion was generated in the fourth quarter. | contradicted | missing | no | — | — | — | contradicted | yes | 0.037411 | 48773.8 | 6825/1506/7185/6209 | missing | no | — | — | — | contradicted | yes | 0.020208 | 11808.5 | 9418/6016/3542/2557 |
| C22 | dev | period_trap | Microsoft's fourth-quarter 2025 revenue was $281.7 billion. | contradicted | missing | no | — | — | — | contradicted | yes | 0.023249 | 35433.1 | 5702/354/3885/3188 | missing | no | — | — | — | contradicted | yes | 0.017562 | 11498.2 | 8355/6016/3232/2540 |
| C23 | test | period_trap | NVIDIA's fiscal 2025 third-quarter revenue was $57.0 billion. | contradicted | missing | no | — | — | — | contradicted | yes | 0.013780 | 25029.8 | 4715/1265/2183/1766 | missing | no | — | — | — | contradicted | yes | 0.008821 | 6730.2 | 7397/6016/1457/1010 |
| C24 | dev | unit_trap | Amazon's Q3 2025 revenue was $180.2 million. | contradicted | missing | no | — | — | — | contradicted | yes | 0.016952 | 31054.7 | 4716/1265/2929/2492 | missing | no | — | — | — | contradicted | yes | 0.008954 | 5934.0 | 7446/6016/1474/1036 |
| C25 | test | unit_trap | Meta's Q2 2025 revenue was $47,516 million. | supported | missing | no | — | — | — | supported | yes | 0.013457 | 26387.2 | 4688/1265/2115/1743 | missing | no | — | — | — | supported | yes | 0.014748 | 9669.6 | 10890/8832/2553/1983 |
| C26 | dev | multi_part | Meta's Q2 2025 revenue was $47.5 billion, and net income was $18.9 billion. | contradicted | missing | no | — | — | — | contradicted | yes | 0.023237 | 47782.1 | 6854/1265/3779/2706 | missing | no | — | — | — | contradicted | yes | 0.015067 | 9641.8 | 8222/6016/2684/1931 |
| C27 | test | multi_part | Amazon's Q3 2025 revenue topped $180 billion, while net income topped $22 billion. | contradicted | missing | no | — | — | — | contradicted | yes | 0.020688 | 33796.3 | 6750/1265/3210/2335 | missing | no | — | — | — | contradicted | yes | 0.021626 | 12957.3 | 12715/9088/3701/2650 |
| C28 | dev | record_first | Meta's Q2 2026 revenue was the first quarterly result above $60 billion. | supported | missing | no | — | — | — | supported | yes | 0.056337 | 70742.3 | 19657/2402/8096/6901 | missing | no | — | — | — | insufficient_evidence | no | 0.039188 | 19575.6 | 24535/13312/5450/4359 |
| C29 | dev | insufficient_evidence | Tesla expects to deliver 2.2 million vehicles in 2026. | insufficient_evidence | missing | no | — | — | — | insufficient_evidence | yes | 0.013902 | 22815.2 | 2660/241/2551/2269 | missing | no | — | — | — | insufficient_evidence | yes | 0.014666 | 10967.9 | 4309/3584/3111/2731 |
| C30 | test | insufficient_evidence | NVIDIA held roughly 90% of the 2025 AI accelerator market. | insufficient_evidence | missing | no | — | — | — | insufficient_evidence | yes | 0.014809 | 22132.6 | 2677/0/2697/2376 | missing | no | — | — | — | insufficient_evidence | yes | 0.011635 | 9645.5 | 4326/3584/2393/1996 |

## Agent errors

| ID | Split | Category | Status | Message |
|---|---|---|---|---|
| C19 | dev | model_error | failed | Error code: 400 - Referenced reasoning item 'rs_6ae14500ca175612d3704e28:rs_dda415a0-ba74-41b8-850c-3c2a4005ec45' was not found or has expired. |

## Accounting

Budget stop: none recorded.
Ledger spend before/after: $0.000000 / $1.106633.
