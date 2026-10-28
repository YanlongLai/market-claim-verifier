# Market claim evaluation report

Generated: 2026-10-28T00:23:42.500712Z
Run window: 2026-10-28T00:13:23.543467Z → 2026-10-28T00:23:42.295427Z
Wall clock: 618.750 s

Accuracy uses all expected claims in the denominator; a missing, failed, or budget-stopped pair is not a correct prediction. Per-class recall uses all claims of that gold class, while precision uses completed predictions of that class. False-supported rate is the harmful error rate among gold contradicted or insufficient-evidence claims. Latency and cost summaries use completed pairs only.

No significance claims are made: each split is small (20 dev and 10 test claims).

## Per-system totals

Tokens are shown as input/cached/output/reasoning. Totals include every recorded pair; latency percentiles include pairs with a recorded model call.

| System | Pairs | Completed | Total cost | Input tokens | Cached tokens | Output tokens | Reasoning tokens | Model calls | Tool calls | Mean latency ms | p50 ms | p95 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| single_shot@meta | 10 | 10 | 0.208081 | 6899 | 3419 | 47816 | 45263 | 16 | 0 | 15456.7 | 17435.4 | 23677.7 |
| agent@meta | 10 | 10 | 0.161059 | 54477 | 15186 | 25804 | 20855 | 30 | 15 | 28086.5 | 27360.2 | 38962.4 |
| single_shot@baseten | 10 | 10 | 0.097851 | 5477 | 3072 | 22208 | 19146 | 11 | 0 | 7270.3 | 7217.3 | 12436.5 |
| agent@baseten | 10 | 10 | 0.171258 | 91253 | 63360 | 29856 | 23534 | 31 | 25 | 11052.3 | 10853.7 | 17622.0 |

## Provider comparison

Reasoning share is reasoning tokens divided by output tokens; provider totals include both methods.

| Provider | Pairs | Completed | Accuracy | False-supported rate | Total cost | Mean latency ms | Input | Cached | Output | Reasoning | Reasoning share |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| meta | 20 | 20 | 0.600 | 0.000 | 0.369140 | 21771.6 | 61376 | 18605 | 73620 | 66118 | 0.898 |
| baseten | 20 | 20 | 0.650 | 0.000 | 0.269109 | 9161.3 | 96730 | 66432 | 52064 | 42680 | 0.820 |

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
| single_shot@meta | dev | 0 | 0 | 0 | 0.000 | 0.000 | 0.000 | — | — | — | 0.000000 | — |
| single_shot@meta | test | 10 | 10 | 0 | 0.500 | 0.000 | 0.600 | 15456.7 | 17435.4 | 23677.7 | 0.208081 | 0.020808 |
| agent@meta | dev | 0 | 0 | 0 | 0.000 | 0.000 | 0.000 | — | — | — | 0.000000 | — |
| agent@meta | test | 10 | 10 | 0 | 0.700 | 0.000 | 0.400 | 28086.5 | 27360.2 | 38962.4 | 0.161059 | 0.016106 |
| single_shot@baseten | dev | 0 | 0 | 0 | 0.000 | 0.000 | 0.000 | — | — | — | 0.000000 | — |
| single_shot@baseten | test | 10 | 10 | 0 | 0.300 | 0.000 | 0.800 | 7270.3 | 7217.3 | 12436.5 | 0.097851 | 0.009785 |
| agent@baseten | dev | 0 | 0 | 0 | 0.000 | 0.000 | 0.000 | — | — | — | 0.000000 | — |
| agent@baseten | test | 10 | 10 | 0 | 1.000 | 0.000 | 0.100 | 11052.3 | 10853.7 | 17622.0 | 0.171258 | 0.017126 |

### Per-gold-class precision and recall

| System | Split | Gold class | Support | Predicted | Precision | Recall |
|---|---|---|---:|---:|---:|---:|
| single_shot@meta | dev | supported | 0 | 0 | 0.000 | 0.000 |
| single_shot@meta | dev | contradicted | 0 | 0 | 0.000 | 0.000 |
| single_shot@meta | dev | insufficient_evidence | 0 | 0 | 0.000 | 0.000 |
| single_shot@meta | test | supported | 4 | 3 | 1.000 | 0.750 |
| single_shot@meta | test | contradicted | 5 | 1 | 1.000 | 0.200 |
| single_shot@meta | test | insufficient_evidence | 1 | 6 | 0.167 | 1.000 |
| agent@meta | dev | supported | 0 | 0 | 0.000 | 0.000 |
| agent@meta | dev | contradicted | 0 | 0 | 0.000 | 0.000 |
| agent@meta | dev | insufficient_evidence | 0 | 0 | 0.000 | 0.000 |
| agent@meta | test | supported | 4 | 3 | 1.000 | 0.750 |
| agent@meta | test | contradicted | 5 | 3 | 1.000 | 0.600 |
| agent@meta | test | insufficient_evidence | 1 | 4 | 0.250 | 1.000 |
| single_shot@baseten | dev | supported | 0 | 0 | 0.000 | 0.000 |
| single_shot@baseten | dev | contradicted | 0 | 0 | 0.000 | 0.000 |
| single_shot@baseten | dev | insufficient_evidence | 0 | 0 | 0.000 | 0.000 |
| single_shot@baseten | test | supported | 4 | 1 | 1.000 | 0.250 |
| single_shot@baseten | test | contradicted | 5 | 1 | 1.000 | 0.200 |
| single_shot@baseten | test | insufficient_evidence | 1 | 8 | 0.125 | 1.000 |
| agent@baseten | dev | supported | 0 | 0 | 0.000 | 0.000 |
| agent@baseten | dev | contradicted | 0 | 0 | 0.000 | 0.000 |
| agent@baseten | dev | insufficient_evidence | 0 | 0 | 0.000 | 0.000 |
| agent@baseten | test | supported | 4 | 4 | 1.000 | 1.000 |
| agent@baseten | test | contradicted | 5 | 5 | 1.000 | 1.000 |
| agent@baseten | test | insufficient_evidence | 1 | 1 | 1.000 | 1.000 |

## Per-claim results

Tokens are shown as input/cached/output/reasoning for each system.

| ID | Split | Category | Claim | Gold | Single Shot verdict | Single Shot correct? | Single Shot cost | Single Shot latency ms | Single Shot tokens (i/c/o/r) | Agent verdict | Agent correct? | Agent cost | Agent latency ms | Agent tokens (i/c/o/r) | Single Shot@Baseten verdict | Single Shot@Baseten correct? | Single Shot@Baseten cost | Single Shot@Baseten latency ms | Single Shot@Baseten tokens (i/c/o/r) | Agent@Baseten verdict | Agent@Baseten correct? | Agent@Baseten cost | Agent@Baseten latency ms | Agent@Baseten tokens (i/c/o/r) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C04 | test | exact_value_true | Amazon's Q3 2023 net income came in at $9.9 billion. | supported | supported | yes | 0.024713 | 17655.4 | 864/241/5623/5444 | supported | yes | 0.014982 | 25974.7 | 4676/0/2150/1743 | insufficient_evidence | no | 0.007964 | 5639.6 | 499/0/1727/1566 | supported | yes | 0.014238 | 10746.7 | 7304/6016/2759/2303 |
| C08 | test | exact_value_false | Apple's fiscal 2025 net income was $111.0 billion. | contradicted | insufficient_evidence | no | 0.027575 | 21054.5 | 858/0/6236/6033 | contradicted | yes | 0.014574 | 23226.1 | 4649/113/2091/1701 | insufficient_evidence | no | 0.005621 | 4358.1 | 496/384/1276/1029 | contradicted | yes | 0.011000 | 7488.8 | 7294/6016/2000/1560 |
| C11 | test | approximate | NVIDIA's quarter ended in late July 2026 generated about $96 billion in revenue. | supported | insufficient_evidence | no | 0.032664 | 25083.3 | 864/241/7494/7106 | insufficient_evidence | no | 0.020318 | 28494.5 | 5522/2289/3749/3127 | insufficient_evidence | no | 0.020690 | 15790.5 | 998/384/4674/3981 | supported | yes | 0.028474 | 18859.1 | 9125/6016/5573/4729 |
| C14 | test | inequality | Apple's June 2026 quarter cleared $110 billion in revenue. | contradicted | insufficient_evidence | no | 0.011294 | 8651.9 | 428/369/2627/2420 | insufficient_evidence | no | 0.014633 | 37750.1 | 5315/2137/2433/1935 | insufficient_evidence | no | 0.010626 | 7413.6 | 495/384/2454/2129 | contradicted | yes | 0.017177 | 12260.5 | 7955/6016/3259/2718 |
| C16 | test | yoy_true | NVIDIA's revenue for the quarter ended October 2025 jumped 62% from a year earlier. | supported | supported | yes | 0.029548 | 21959.8 | 868/610/6855/6525 | supported | yes | 0.019824 | 39954.3 | 8579/2402/2763/2114 | supported | yes | 0.009392 | 7021.0 | 501/384/2162/1768 | supported | yes | 0.026790 | 16109.9 | 15005/8576/4110/3190 |
| C20 | test | yoy_false | Apple's June 2026 revenue was down 8% year over year. | contradicted | insufficient_evidence | no | 0.008058 | 5776.3 | 430/369/1865/1693 | insufficient_evidence | no | 0.025444 | 26759.3 | 8462/0/3498/2847 | insufficient_evidence | no | 0.005020 | 3434.8 | 497/0/1035/827 | contradicted | yes | 0.021600 | 10960.7 | 12350/6016/3007/2215 |
| C23 | test | period_trap | NVIDIA's fiscal 2025 third-quarter revenue was $57.0 billion. | contradicted | contradicted | yes | 0.012448 | 8528.0 | 430/369/2898/2718 | contradicted | yes | 0.011193 | 23723.5 | 4666/2402/1883/1437 | contradicted | yes | 0.010548 | 8337.1 | 497/384/2435/2224 | contradicted | yes | 0.012779 | 7825.3 | 8173/6016/2160/1577 |
| C25 | test | unit_trap | Meta's Q2 2025 revenue was $47,516 million. | supported | supported | yes | 0.010913 | 8285.8 | 429/241/2504/2344 | supported | yes | 0.010802 | 29328.9 | 4609/3554/2106/1760 | insufficient_evidence | no | 0.010674 | 7619.7 | 496/384/2465/2315 | supported | yes | 0.008552 | 6027.6 | 7318/6016/1417/971 |
| C27 | test | multi_part | Amazon's Q3 2025 revenue topped $180 billion, while net income topped $22 billion. | contradicted | insufficient_evidence | no | 0.023989 | 17215.3 | 870/369/5484/5150 | contradicted | yes | 0.017734 | 27961.0 | 5388/0/2588/1914 | insufficient_evidence | no | 0.006223 | 4753.5 | 502/384/1416/1110 | contradicted | yes | 0.020773 | 12844.3 | 12502/9088/3563/2650 |
| C30 | test | insufficient_evidence | NVIDIA held roughly 90% of the 2025 AI accelerator market. | insufficient_evidence | insufficient_evidence | yes | 0.026879 | 20357.1 | 858/610/6230/5830 | insufficient_evidence | yes | 0.011554 | 17692.9 | 2611/2289/2543/2277 | insufficient_evidence | yes | 0.011095 | 8335.4 | 496/384/2564/2197 | insufficient_evidence | yes | 0.009875 | 7400.1 | 4227/3584/2008/1621 |

## Agent errors

None recorded.

## Accounting

Budget stop: none recorded.
Ledger spend before/after: $0.000000 / $0.638249.
