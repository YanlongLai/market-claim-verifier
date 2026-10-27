# Market claim evaluation report

Generated: 2026-10-27T23:40:20.416790Z
Run window: 2026-10-27T23:17:38.196909Z → 2026-10-27T23:40:17.253427Z
Wall clock: 1359.051 s

Accuracy uses all expected claims in the denominator; a missing, failed, or budget-stopped pair is not a correct prediction. Per-class recall uses all claims of that gold class, while precision uses completed predictions of that class. False-supported rate is the harmful error rate among gold contradicted or insufficient-evidence claims. Latency and cost summaries use completed pairs only.

No significance claims are made: each split is small (20 dev and 10 test claims).

## Per-system totals

Tokens are shown as input/cached/output/reasoning. Totals include every recorded pair; latency percentiles include pairs with a recorded model call.

| System | Pairs | Completed | Total cost | Input tokens | Cached tokens | Output tokens | Reasoning tokens | Model calls | Tool calls | Mean latency ms | p50 ms | p95 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| single_shot@meta | 20 | 20 | 0.437603 | 13686 | 5648 | 100402 | 96417 | 33 | 0 | 17115.2 | 20409.9 | 24966.6 |
| agent@meta | 20 | 19 | 0.372290 | 113099 | 28576 | 58497 | 48453 | 66 | 28 | 31305.2 | 26946.8 | 54330.4 |
| single_shot@baseten | 20 | 20 | 0.272945 | 14968 | 8832 | 62106 | 57014 | 29 | 0 | 10219.8 | 8570.6 | 18790.1 |
| agent@baseten | 20 | 20 | 0.285506 | 158561 | 111488 | 49398 | 38006 | 63 | 33 | 9304.8 | 8445.4 | 14274.1 |

## Provider comparison

Reasoning share is reasoning tokens divided by output tokens; provider totals include both methods.

| Provider | Pairs | Completed | Accuracy | False-supported rate | Total cost | Mean latency ms | Input | Cached | Output | Reasoning | Reasoning share |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| meta | 40 | 39 | 0.675 | 0.150 | 0.787512 | 24176.7 | 126785 | 34224 | 158899 | 144870 | 0.912 |
| baseten | 40 | 40 | 0.575 | 0.150 | 0.558451 | 9762.3 | 173529 | 120320 | 111504 | 95020 | 0.852 |

## Prompt versions

| Prompt | SHA-256 prefix |
|---|---|
| agent_tool_loop_instructions | 478b835a5ef4 |
| agent_final_verdict_prompt | 7a61b67c5136 |
| baseten_tool_loop_instructions | 478b835a5ef4 |
| baseten_final_verdict_prompt | 7dc73f1427f8 |
| baseten_repair_prompt | 7b20eb8f20ed |
| baseten_single_shot_instructions | be3902891198 |
| verdict_json_schema | 137fb8d1621d |
| tool_schemas | 3e31b62d40fe |
| single_shot_instructions | 9677f9a3b64a |

## Metrics

| System | Split | n | completed | errors | accuracy | false-supported rate | insufficient rate | mean latency ms | p50 ms | p95 ms | total cost | mean cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| single_shot@meta | dev | 20 | 20 | 0 | 0.600 | 0.100 | 0.400 | 17115.2 | 20409.9 | 24966.6 | 0.437603 | 0.021880 |
| single_shot@meta | test | 0 | 0 | 0 | 0.000 | 0.000 | 0.000 | — | — | — | 0.000000 | — |
| agent@meta | dev | 20 | 19 | 1 | 0.750 | 0.200 | 0.150 | 31609.8 | 27129.4 | 54952.4 | 0.349909 | 0.018416 |
| agent@meta | test | 0 | 0 | 0 | 0.000 | 0.000 | 0.000 | — | — | — | 0.000000 | — |
| single_shot@baseten | dev | 20 | 20 | 0 | 0.400 | 0.000 | 0.650 | 10219.8 | 8570.6 | 18790.1 | 0.272945 | 0.013647 |
| single_shot@baseten | test | 0 | 0 | 0 | 0.000 | 0.000 | 0.000 | — | — | — | 0.000000 | — |
| agent@baseten | dev | 20 | 20 | 0 | 0.750 | 0.300 | 0.150 | 9304.8 | 8445.4 | 14274.1 | 0.285506 | 0.014275 |
| agent@baseten | test | 0 | 0 | 0 | 0.000 | 0.000 | 0.000 | — | — | — | 0.000000 | — |

### Per-gold-class precision and recall

| System | Split | Gold class | Support | Predicted | Precision | Recall |
|---|---|---|---:|---:|---:|---:|
| single_shot@meta | dev | supported | 10 | 6 | 0.833 | 0.500 |
| single_shot@meta | dev | contradicted | 9 | 6 | 1.000 | 0.667 |
| single_shot@meta | dev | insufficient_evidence | 1 | 8 | 0.125 | 1.000 |
| single_shot@meta | test | supported | 0 | 0 | 0.000 | 0.000 |
| single_shot@meta | test | contradicted | 0 | 0 | 0.000 | 0.000 |
| single_shot@meta | test | insufficient_evidence | 0 | 0 | 0.000 | 0.000 |
| agent@meta | dev | supported | 10 | 11 | 0.818 | 0.900 |
| agent@meta | dev | contradicted | 9 | 5 | 1.000 | 0.556 |
| agent@meta | dev | insufficient_evidence | 1 | 3 | 0.333 | 1.000 |
| agent@meta | test | supported | 0 | 0 | 0.000 | 0.000 |
| agent@meta | test | contradicted | 0 | 0 | 0.000 | 0.000 |
| agent@meta | test | insufficient_evidence | 0 | 0 | 0.000 | 0.000 |
| single_shot@baseten | dev | supported | 10 | 4 | 1.000 | 0.400 |
| single_shot@baseten | dev | contradicted | 9 | 3 | 1.000 | 0.333 |
| single_shot@baseten | dev | insufficient_evidence | 1 | 13 | 0.077 | 1.000 |
| single_shot@baseten | test | supported | 0 | 0 | 0.000 | 0.000 |
| single_shot@baseten | test | contradicted | 0 | 0 | 0.000 | 0.000 |
| single_shot@baseten | test | insufficient_evidence | 0 | 0 | 0.000 | 0.000 |
| agent@baseten | dev | supported | 10 | 13 | 0.769 | 1.000 |
| agent@baseten | dev | contradicted | 9 | 4 | 1.000 | 0.444 |
| agent@baseten | dev | insufficient_evidence | 1 | 3 | 0.333 | 1.000 |
| agent@baseten | test | supported | 0 | 0 | 0.000 | 0.000 |
| agent@baseten | test | contradicted | 0 | 0 | 0.000 | 0.000 |
| agent@baseten | test | insufficient_evidence | 0 | 0 | 0.000 | 0.000 |

## Per-claim results

Tokens are shown as input/cached/output/reasoning for each system.

| ID | Split | Category | Claim | Gold | Single Shot verdict | Single Shot correct? | Single Shot cost | Single Shot latency ms | Single Shot tokens (i/c/o/r) | Agent verdict | Agent correct? | Agent cost | Agent latency ms | Agent tokens (i/c/o/r) | Single Shot@Baseten verdict | Single Shot@Baseten correct? | Single Shot@Baseten cost | Single Shot@Baseten latency ms | Single Shot@Baseten tokens (i/c/o/r) | Agent@Baseten verdict | Agent@Baseten correct? | Agent@Baseten cost | Agent@Baseten latency ms | Agent@Baseten tokens (i/c/o/r) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C01 | dev | exact_value_true | Meta's second-quarter 2025 revenue landed at $47.5 billion. | supported | supported | yes | 0.011291 | 8704.8 | 414/0/2535/2370 | failed | no | 0.022381 | 25517.9 | 3730/113/966/738 | insufficient_evidence | no | 0.008042 | 5778.8 | 480/0/1751/1565 | supported | yes | 0.009400 | 6248.0 | 6576/5248/1636/1081 |
| C02 | dev | exact_value_true | Tesla reported $28.1 billion in revenue for Q3 2025. | supported | supported | yes | 0.011585 | 8049.6 | 414/0/2604/2438 | supported | yes | 0.012486 | 26362.9 | 4258/2146/2241/1848 | supported | yes | 0.010565 | 8193.3 | 480/384/2444/2208 | supported | yes | 0.009488 | 5319.5 | 6401/3072/1145/757 |
| C03 | dev | exact_value_true | Alphabet's Q3 2025 revenue was $102.3 billion. | supported | supported | yes | 0.028071 | 21871.7 | 826/0/6362/6207 | supported | yes | 0.014472 | 31132.3 | 4214/113/2195/1834 | supported | yes | 0.013179 | 10502.1 | 479/0/2960/2754 | supported | yes | 0.008750 | 6523.5 | 6433/5248/1525/1107 |
| C05 | dev | exact_value_false | Meta's Q2 2025 revenue was $47.4 billion, according to the filing. | contradicted | insufficient_evidence | no | 0.026732 | 22503.1 | 836/0/6044/5892 | contradicted | yes | 0.020872 | 31585.6 | 4292/113/3678/3155 | insufficient_evidence | no | 0.007399 | 5400.4 | 484/384/1698/1528 | supported | no | 0.011585 | 8195.0 | 6427/5248/2194/1796 |
| C06 | dev | exact_value_false | Tesla's Q3 2025 net income was $1.3 billion. | contradicted | insufficient_evidence | no | 0.024038 | 24860.3 | 828/369/5508/5334 | supported | no | 0.021318 | 30823.0 | 4261/113/3792/3373 | insufficient_evidence | no | 0.004922 | 3210.4 | 480/0/1017/853 | supported | no | 0.018232 | 13035.0 | 6471/4352/3513/3017 |
| C07 | dev | exact_value_false | Microsoft closed fiscal 2025 with $281.6 billion in revenue. | contradicted | supported | no | 0.029059 | 21734.3 | 826/369/6690/6515 | supported | no | 0.013302 | 24636.5 | 4220/113/1918/1546 | insufficient_evidence | no | 0.024272 | 17696.7 | 958/768/5628/5291 | supported | no | 0.009287 | 6338.8 | 6407/5248/1659/1239 |
| C09 | dev | approximate | Tesla's Q3 2025 profit was about $1.4 billion. | supported | insufficient_evidence | no | 0.027298 | 22281.4 | 828/369/6275/6084 | supported | yes | 0.013418 | 26764.2 | 4224/113/1944/1581 | supported | yes | 0.024085 | 19453.1 | 960/384/5484/5258 | supported | yes | 0.009507 | 6937.2 | 6444/5248/1700/1233 |
| C10 | dev | approximate | Microsoft's September quarter brought in roughly $77 billion of revenue. | supported | insufficient_evidence | no | 0.025835 | 20201.6 | 822/0/5837/5627 | supported | yes | 0.028093 | 53708.4 | 8470/1619/4538/3912 | insufficient_evidence | no | 0.009283 | 6955.1 | 477/0/2044/1873 | supported | yes | 0.017867 | 13969.0 | 10789/8064/3118/2438 |
| C12 | dev | inequality | Alphabet's Q3 2025 revenue topped $100 billion. | supported | supported | yes | 0.030036 | 21123.9 | 822/241/6888/6671 | supported | yes | 0.011494 | 25233.4 | 4260/2146/2007/1609 | supported | yes | 0.024046 | 18333.5 | 954/768/5576/5187 | supported | yes | 0.013403 | 8895.5 | 6701/5248/2541/2017 |
| C13 | dev | inequality | Amazon's Q3 2025 revenue came in below $181 billion. | supported | insufficient_evidence | no | 0.012100 | 9856.5 | 413/369/2821/2640 | supported | yes | 0.011260 | 24132.2 | 4273/2146/1948/1571 | insufficient_evidence | no | 0.007087 | 5685.7 | 479/384/1626/1479 | supported | yes | 0.006851 | 4866.8 | 6407/5248/1086/709 |
| C15 | dev | yoy_true | Meta's Q2 2025 revenue was up 22% year over year. | supported | supported | yes | 0.008547 | 6269.5 | 415/0/1889/1727 | supported | yes | 0.015637 | 29312.4 | 5643/1265/2347/1891 | insufficient_evidence | no | 0.020337 | 15335.8 | 962/768/4701/4550 | supported | yes | 0.018045 | 11640.8 | 7848/5248/3296/2753 |
| C17 | dev | yoy_true | Tesla's Q3 2025 sales grew 12% from the same quarter a year earlier. | supported | insufficient_evidence | no | 0.029565 | 24095.7 | 836/241/6773/6561 | supported | yes | 0.018439 | 29294.0 | 5726/2146/3210/2713 | insufficient_evidence | no | 0.012825 | 8947.9 | 1477/768/2782/2389 | supported | yes | 0.013798 | 8695.7 | 7830/5248/2302/1824 |
| C18 | dev | yoy_false | Tesla's Q3 2025 revenue fell 10% year over year. | contradicted | contradicted | yes | 0.028745 | 24113.1 | 828/738/6711/6524 | contradicted | yes | 0.016791 | 25183.1 | 5668/2033/2810/2315 | insufficient_evidence | no | 0.007492 | 5419.2 | 480/384/1721/1559 | contradicted | yes | 0.012932 | 7759.6 | 7800/5248/2107/1627 |
| C19 | dev | yoy_false | Meta's Q2 2025 revenue rose 30% from a year earlier. | contradicted | contradicted | yes | 0.007899 | 5945.8 | 415/369/1832/1644 | contradicted | yes | 0.017297 | 27129.4 | 5638/113/2441/1979 | contradicted | yes | 0.018735 | 14783.8 | 962/768/4324/4115 | contradicted | yes | 0.013009 | 8986.2 | 7790/5248/2128/1691 |
| C21 | dev | period_trap | Apple's fiscal 2025 revenue of $416.2 billion was generated in the fourth quarter. | contradicted | contradicted | yes | 0.025474 | 17149.1 | 836/738/5939/5677 | insufficient_evidence | no | 0.036076 | 66148.4 | 11980/4563/6146/4998 | insufficient_evidence | no | 0.019312 | 14063.9 | 968/768/4458/4231 | insufficient_evidence | no | 0.034376 | 19528.2 | 17090/11776/6110/4548 |
| C22 | dev | period_trap | Microsoft's fourth-quarter 2025 revenue was $281.7 billion. | contradicted | contradicted | yes | 0.023698 | 18361.4 | 826/738/5524/5318 | insufficient_evidence | no | 0.023116 | 52176.3 | 8901/5316/4197/3425 | contradicted | yes | 0.007520 | 5652.2 | 479/384/1728/1508 | insufficient_evidence | no | 0.018149 | 12683.3 | 9796/7680/3377/2688 |
| C24 | dev | unit_trap | Amazon's Q3 2025 revenue was $180.2 million. | contradicted | contradicted | yes | 0.028426 | 20618.2 | 826/369/6541/6362 | contradicted | yes | 0.011072 | 23001.1 | 4262/2146/1907/1512 | contradicted | yes | 0.007492 | 6200.3 | 479/0/1622/1419 | contradicted | yes | 0.009051 | 6849.7 | 6433/5248/1596/1152 |
| C26 | dev | multi_part | Meta's Q2 2025 revenue was $47.5 billion, and net income was $18.9 billion. | contradicted | contradicted | yes | 0.035576 | 26987.2 | 846/738/8313/8016 | contradicted | yes | 0.013478 | 24025.1 | 4885/2146/2290/1685 | insufficient_evidence | no | 0.026298 | 18755.2 | 978/768/6099/5554 | contradicted | yes | 0.013672 | 8766.3 | 7182/5248/2463/1680 |
| C28 | dev | record_first | Meta's Q2 2026 revenue was the first quarterly result above $60 billion. | supported | insufficient_evidence | no | 0.012144 | 9281.3 | 416/0/2735/2448 | supported | yes | 0.031437 | 30500.4 | 11846/113/3942/3133 | insufficient_evidence | no | 0.015259 | 10114.9 | 1473/768/3356/2795 | supported | yes | 0.028915 | 13997.6 | 14079/5248/4021/3133 |
| C29 | dev | insufficient_evidence | Tesla expects to deliver 2.2 million vehicles in 2026. | insufficient_evidence | insufficient_evidence | yes | 0.011485 | 8295.4 | 413/0/2581/2362 | insufficient_evidence | yes | 0.019850 | 19437.7 | 2348/0/3980/3635 | insufficient_evidence | yes | 0.004796 | 3913.5 | 479/384/1087/898 | insufficient_evidence | yes | 0.009186 | 6859.7 | 3657/3072/1881/1516 |

## Agent errors

| ID | Split | Category | Status | Message |
|---|---|---|---|---|
| C01 | dev | model_error | failed | Error code: 400 - referenced response not found or expired |

## Accounting

Budget stop: none recorded.
Ledger spend before/after: $0.000000 / $1.368344.
