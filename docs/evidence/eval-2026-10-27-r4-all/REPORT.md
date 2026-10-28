# Market claim evaluation report

Generated: 2026-10-28T02:26:37.187194Z
Run window: 2026-10-28T01:07:47.420169Z → 2026-10-28T02:26:36.731268Z
Wall clock: 4729.287 s

Accuracy uses all expected claims in the denominator; a missing, failed, or budget-stopped pair is not a correct prediction. Per-class recall uses all claims of that gold class, while precision uses completed predictions of that class. False-supported rate is the harmful error rate among gold contradicted or insufficient-evidence claims. Latency and cost summaries use completed pairs only.

## Per-system totals

Tokens are shown as input/cached/output/reasoning. Totals include every recorded pair; latency percentiles include pairs with a recorded model call.

| System | Pairs | Completed | Total cost | Input tokens | Cached tokens | Output tokens | Reasoning tokens | Model calls | Tool calls | Mean latency ms | p50 ms | p95 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|

No significance claims are made for groups with n < 50; Wilson intervals and paired tests there are descriptive and unstable.

| single_shot@meta | 30 | 30 | 0.572645 | 19487 | 6002 | 130562 | 124182 | 44 | 0 | 14618.8 | 9902.4 | 24430.5 |
| agent@meta | 30 | 30 | 0.619167 | 179694 | 29126 | 92934 | 78171 | 96 | 39 | 31527.0 | 29288.1 | 49404.2 |
| single_shot@baseten | 30 | 28 | 0.459981 | 24708 | 16128 | 105138 | 97435 | 44 | 0 | 11329.3 | 8710.2 | 24860.4 |
| agent@baseten | 30 | 30 | 0.469959 | 262178 | 186624 | 81770 | 65718 | 91 | 45 | 10379.3 | 9168.9 | 17007.8 |
| single_shot@fireworks | 30 | 30 | 0.335504 | 19459 | 13056 | 76598 | 69743 | 36 | 0 | 41429.4 | 34890.5 | 103222.3 |
| agent@fireworks | 30 | 30 | 0.492430 | 265905 | 156800 | 78242 | 61925 | 90 | 46 | 48347.3 | 45436.0 | 84941.4 |

## Provider comparison

Reasoning share is reasoning tokens divided by output tokens; provider totals include both methods.

| Provider | Pairs | Completed | Accuracy | False-supported rate | Total cost | Mean latency ms | Input | Cached | Output | Reasoning | Reasoning share |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| meta | 60 | 60 | 0.733 | 0.000 | 1.191812 | 23072.9 | 199181 | 35128 | 223496 | 202353 | 0.905 |
| baseten | 60 | 58 | 0.600 | 0.000 | 0.852576 | 10205.4 | 286886 | 202752 | 186908 | 163153 | 0.873 |
| fireworks | 60 | 60 | 0.667 | 0.000 | 0.827933 | 44888.4 | 285364 | 169856 | 154840 | 131668 | 0.850 |

## Prompt versions

| Prompt | SHA-256 prefix |
|---|---|
| agent_tool_loop_instructions | ee16273388a2 |
| agent_final_verdict_prompt | ea9ff5500ad7 |
| baseten_tool_loop_instructions | ee16273388a2 |
| baseten_final_verdict_prompt | 8a0f8f1b51f9 |
| baseten_repair_prompt | 0e13993581ac |
| baseten_single_shot_instructions | 50875e0b864d |
| fireworks_tool_loop_instructions | ee16273388a2 |
| fireworks_final_verdict_prompt | 8a0f8f1b51f9 |
| fireworks_repair_prompt | 0e13993581ac |
| fireworks_single_shot_instructions | 50875e0b864d |
| verdict_json_schema | 641d01f47032 |
| tool_schemas | c29120ac4262 |
| single_shot_instructions | 9677f9a3b64a |

## Metrics

| System | Split | n | completed | errors | accuracy | accuracy 95% CI | false-supported rate | false-supported 95% CI | insufficient rate | insufficient 95% CI | mean latency ms | p50 ms | p95 ms | total cost | mean cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| single_shot@meta | dev | 20 | 20 | 0 | 0.650 | [0.433, 0.819] | 0.000 | [0.000, 0.278] | 0.400 | [0.219, 0.613] | 16365.7 | 18852.1 | 24815.2 | 0.431532 | 0.021577 |
| single_shot@meta | test | 10 | 10 | 0 | 0.500 | [0.237, 0.763] | 0.000 | [0.000, 0.390] | 0.600 | [0.313, 0.832] | 11125.2 | 9058.8 | 22367.9 | 0.141113 | 0.014111 |
| agent@meta | dev | 20 | 20 | 0 | 0.850 | [0.640, 0.948] | 0.000 | [0.000, 0.278] | 0.200 | [0.081, 0.416] | 33174.3 | 29288.1 | 50694.7 | 0.399676 | 0.019984 |
| agent@meta | test | 10 | 10 | 0 | 0.900 | [0.596, 0.982] | 0.000 | [0.000, 0.390] | 0.200 | [0.057, 0.510] | 28232.4 | 28215.2 | 36084.9 | 0.219492 | 0.021949 |
| single_shot@baseten | dev | 20 | 18 | 2 | 0.150 | [0.052, 0.360] | 0.000 | [0.000, 0.278] | 0.800 | [0.584, 0.919] | 10510.5 | 8935.5 | 18158.7 | 0.258481 | 0.014360 |
| single_shot@baseten | test | 10 | 10 | 0 | 0.300 | [0.108, 0.603] | 0.000 | [0.000, 0.390] | 0.800 | [0.490, 0.943] | 9134.6 | 7342.2 | 17994.4 | 0.124136 | 0.012414 |
| agent@baseten | dev | 20 | 20 | 0 | 1.000 | [0.839, 1.000] | 0.000 | [0.000, 0.278] | 0.050 | [0.009, 0.236] | 10683.6 | 9303.2 | 16997.8 | 0.320115 | 0.016006 |
| agent@baseten | test | 10 | 10 | 0 | 1.000 | [0.722, 1.000] | 0.000 | [0.000, 0.390] | 0.100 | [0.018, 0.404] | 9770.7 | 8827.4 | 15805.4 | 0.149843 | 0.014984 |
| single_shot@fireworks | dev | 20 | 20 | 0 | 0.250 | [0.112, 0.469] | 0.000 | [0.000, 0.278] | 0.800 | [0.584, 0.919] | 42550.2 | 35241.8 | 99806.4 | 0.223515 | 0.011176 |
| single_shot@fireworks | test | 10 | 10 | 0 | 0.500 | [0.237, 0.763] | 0.000 | [0.000, 0.390] | 0.600 | [0.313, 0.832] | 39187.7 | 30874.1 | 85856.4 | 0.111989 | 0.011199 |
| agent@fireworks | dev | 20 | 20 | 0 | 1.000 | [0.839, 1.000] | 0.000 | [0.000, 0.278] | 0.050 | [0.009, 0.236] | 45358.7 | 45436.0 | 68131.8 | 0.335861 | 0.016793 |
| agent@fireworks | test | 10 | 10 | 0 | 1.000 | [0.722, 1.000] | 0.000 | [0.000, 0.390] | 0.100 | [0.018, 0.404] | 54324.7 | 45764.8 | 98921.7 | 0.156568 | 0.015657 |

### Per-gold-class precision and recall

| System | Split | Gold class | Support | Predicted | Precision | Recall |
|---|---|---|---:|---:|---:|---:|
| single_shot@meta | dev | supported | 10 | 6 | 1.000 | 0.600 |
| single_shot@meta | dev | contradicted | 9 | 6 | 1.000 | 0.667 |
| single_shot@meta | dev | insufficient_evidence | 1 | 8 | 0.125 | 1.000 |
| single_shot@meta | test | supported | 4 | 3 | 1.000 | 0.750 |
| single_shot@meta | test | contradicted | 5 | 1 | 1.000 | 0.200 |
| single_shot@meta | test | insufficient_evidence | 1 | 6 | 0.167 | 1.000 |
| agent@meta | dev | supported | 10 | 9 | 1.000 | 0.900 |
| agent@meta | dev | contradicted | 9 | 7 | 1.000 | 0.778 |
| agent@meta | dev | insufficient_evidence | 1 | 4 | 0.250 | 1.000 |
| agent@meta | test | supported | 4 | 3 | 1.000 | 0.750 |
| agent@meta | test | contradicted | 5 | 5 | 1.000 | 1.000 |
| agent@meta | test | insufficient_evidence | 1 | 2 | 0.500 | 1.000 |
| single_shot@baseten | dev | supported | 10 | 2 | 1.000 | 0.200 |
| single_shot@baseten | dev | contradicted | 9 | 0 | 0.000 | 0.000 |
| single_shot@baseten | dev | insufficient_evidence | 1 | 16 | 0.062 | 1.000 |
| single_shot@baseten | test | supported | 4 | 2 | 1.000 | 0.500 |
| single_shot@baseten | test | contradicted | 5 | 0 | 0.000 | 0.000 |
| single_shot@baseten | test | insufficient_evidence | 1 | 8 | 0.125 | 1.000 |
| agent@baseten | dev | supported | 10 | 10 | 1.000 | 1.000 |
| agent@baseten | dev | contradicted | 9 | 9 | 1.000 | 1.000 |
| agent@baseten | dev | insufficient_evidence | 1 | 1 | 1.000 | 1.000 |
| agent@baseten | test | supported | 4 | 4 | 1.000 | 1.000 |
| agent@baseten | test | contradicted | 5 | 5 | 1.000 | 1.000 |
| agent@baseten | test | insufficient_evidence | 1 | 1 | 1.000 | 1.000 |
| single_shot@fireworks | dev | supported | 10 | 0 | 0.000 | 0.000 |
| single_shot@fireworks | dev | contradicted | 9 | 4 | 1.000 | 0.444 |
| single_shot@fireworks | dev | insufficient_evidence | 1 | 16 | 0.062 | 1.000 |
| single_shot@fireworks | test | supported | 4 | 2 | 1.000 | 0.500 |
| single_shot@fireworks | test | contradicted | 5 | 2 | 1.000 | 0.400 |
| single_shot@fireworks | test | insufficient_evidence | 1 | 6 | 0.167 | 1.000 |
| agent@fireworks | dev | supported | 10 | 10 | 1.000 | 1.000 |
| agent@fireworks | dev | contradicted | 9 | 9 | 1.000 | 1.000 |
| agent@fireworks | dev | insufficient_evidence | 1 | 1 | 1.000 | 1.000 |
| agent@fireworks | test | supported | 4 | 4 | 1.000 | 1.000 |
| agent@fireworks | test | contradicted | 5 | 5 | 1.000 | 1.000 |
| agent@fireworks | test | insufficient_evidence | 1 | 1 | 1.000 | 1.000 |

### Paired comparisons

Accuracy difference is left minus right; bootstrap intervals use 10,000 seeded paired resamples and McNemar is exact two-sided.

| Pair | n | Accuracy difference | Bootstrap 95% CI | McNemar exact p | Discordant left/right |
|---|---:|---:|---|---:|---:|
| agent@meta_vs_single_shot@meta | 30 | 0.267 | [0.067, 0.467] | 0.0386 | 10/2 |
| agent@baseten_vs_single_shot@baseten | 28 | 0.786 | [0.607, 0.929] | 0.0000 | 22/0 |
| agent@fireworks_vs_single_shot@fireworks | 30 | 0.667 | [0.500, 0.833] | 0.0000 | 20/0 |
| agent@meta_vs_agent@baseten | 30 | -0.133 | [-0.267, -0.033] | 0.1250 | 0/4 |
| agent@meta_vs_agent@fireworks | 30 | -0.133 | [-0.267, -0.033] | 0.1250 | 0/4 |
| agent@baseten_vs_agent@fireworks | 30 | 0.000 | [0.000, 0.000] | 1.0000 | 0/0 |
| single_shot@meta_vs_single_shot@baseten | 28 | 0.357 | [0.143, 0.571] | 0.0063 | 11/1 |
| single_shot@meta_vs_single_shot@fireworks | 30 | 0.267 | [0.100, 0.467] | 0.0215 | 9/1 |
| single_shot@baseten_vs_single_shot@fireworks | 28 | -0.107 | [-0.321, 0.107] | 0.5078 | 3/6 |

## Per-claim results

Tokens are shown as input/cached/output/reasoning for each system.

| ID | Split | Category | Claim | Gold | Single Shot verdict | Single Shot correct? | Single Shot cost | Single Shot latency ms | Single Shot tokens (i/c/o/r) | Agent verdict | Agent correct? | Agent cost | Agent latency ms | Agent tokens (i/c/o/r) | Single Shot@Baseten verdict | Single Shot@Baseten correct? | Single Shot@Baseten cost | Single Shot@Baseten latency ms | Single Shot@Baseten tokens (i/c/o/r) | Agent@Baseten verdict | Agent@Baseten correct? | Agent@Baseten cost | Agent@Baseten latency ms | Agent@Baseten tokens (i/c/o/r) | Single Shot@Fireworks verdict | Single Shot@Fireworks correct? | Single Shot@Fireworks cost | Single Shot@Fireworks latency ms | Single Shot@Fireworks tokens (i/c/o/r) | Agent@Fireworks verdict | Agent@Fireworks correct? | Agent@Fireworks cost | Agent@Fireworks latency ms | Agent@Fireworks tokens (i/c/o/r) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C01 | dev | exact_value_true | Meta's second-quarter 2025 revenue landed at $47.5 billion. | supported | supported | yes | 0.013018 | 9821.6 | 442/0/2933/2749 | supported | yes | 0.017542 | 27518.8 | 4848/113/2731/2336 | insufficient_evidence | no | 0.017892 | 11958.2 | 1585/256/3810/3391 | supported | yes | 0.038113 | 29248.7 | 9813/6400/7738/7276 | insufficient_evidence | no | 0.010835 | 34728.9 | 508/0/2400/2228 | supported | yes | 0.016723 | 62722.1 | 7769/2624/2329/1912 |
| C02 | dev | exact_value_true | Tesla reported $28.1 billion in revenue for Q3 2025. | supported | supported | yes | 0.027604 | 20775.4 | 884/0/6235/6079 | supported | yes | 0.016490 | 24340.8 | 4855/0/2452/2040 | insufficient_evidence | no | 0.011664 | 9203.3 | 509/256/2661/2492 | supported | yes | 0.013244 | 10364.3 | 7669/6272/2484/2038 | insufficient_evidence | no | 0.010537 | 48215.3 | 508/0/2330/2142 | supported | yes | 0.014515 | 26056.4 | 7760/2624/1812/1407 |
| C03 | dev | exact_value_true | Alphabet's Q3 2025 revenue was $102.3 billion. | supported | supported | yes | 0.031843 | 24630.7 | 882/0/7233/7072 | supported | yes | 0.014532 | 24362.6 | 4806/113/2035/1651 | failed | no | 0.038675 | 31599.1 | 1016/768/9000/8986 | supported | yes | 0.015048 | 11274.6 | 7647/6272/2915/2506 | insufficient_evidence | no | 0.010116 | 36361.2 | 507/0/2231/2069 | supported | yes | 0.014532 | 34277.7 | 7754/3776/2116/1688 |
| C04 | test | exact_value_true | Amazon's Q3 2023 net income came in at $9.9 billion. | supported | supported | yes | 0.009822 | 7979.9 | 444/369/2276/2142 | supported | yes | 0.016514 | 24345.8 | 4831/113/2494/2068 | insufficient_evidence | no | 0.021963 | 15877.1 | 1022/768/5066/4860 | supported | yes | 0.022335 | 17543.5 | 7727/6272/4606/4080 | supported | yes | 0.008708 | 31106.9 | 510/448/2015/1855 | supported | yes | 0.015242 | 47057.1 | 7772/6400/2957/2523 |
| C05 | dev | exact_value_false | Meta's Q2 2025 revenue was $47.4 billion, according to the filing. | contradicted | insufficient_evidence | no | 0.031964 | 24185.9 | 892/241/7321/7177 | contradicted | yes | 0.021140 | 35906.6 | 4867/1265/3870/3331 | insufficient_evidence | no | 0.029585 | 21336.7 | 2106/1280/6673/6088 | contradicted | yes | 0.012039 | 8776.5 | 7684/6272/2196/1780 | insufficient_evidence | no | 0.022879 | 99464.8 | 1024/448/5198/4958 | contradicted | yes | 0.020000 | 36588.8 | 7803/2624/3090/2583 |
| C06 | dev | exact_value_false | Tesla's Q3 2025 net income was $1.3 billion. | contradicted | insufficient_evidence | no | 0.027954 | 20631.4 | 884/369/6413/6241 | contradicted | yes | 0.015297 | 27330.2 | 4803/113/2216/1843 | insufficient_evidence | no | 0.017104 | 11612.6 | 1585/768/3757/3328 | contradicted | yes | 0.009302 | 6246.7 | 7650/6272/1562/1133 | insufficient_evidence | no | 0.011324 | 32055.2 | 508/448/2631/2341 | contradicted | yes | 0.010118 | 22865.2 | 7766/6400/1753/1278 |
| C07 | dev | exact_value_false | Microsoft closed fiscal 2025 with $281.6 billion in revenue. | contradicted | insufficient_evidence | no | 0.027818 | 21493.7 | 882/0/6286/6105 | contradicted | yes | 0.014895 | 22859.9 | 4794/113/2124/1758 | insufficient_evidence | no | 0.005874 | 4379.4 | 508/384/1332/1171 | contradicted | yes | 0.013201 | 9664.7 | 7658/6272/2477/2035 | insufficient_evidence | no | 0.009389 | 27555.7 | 507/0/2060/1894 | contradicted | yes | 0.017615 | 54226.7 | 7728/2624/2551/2135 |
| C08 | test | exact_value_false | Apple's fiscal 2025 net income was $111.0 billion. | contradicted | insufficient_evidence | no | 0.009633 | 7192.3 | 441/0/2137/1950 | contradicted | yes | 0.014918 | 29707.8 | 4799/113/2128/1781 | insufficient_evidence | no | 0.005682 | 4430.0 | 508/384/1287/1128 | contradicted | yes | 0.008103 | 5402.7 | 7653/6272/1279/887 | insufficient_evidence | no | 0.006699 | 23402.9 | 507/448/1543/1385 | contradicted | yes | 0.008355 | 17525.9 | 7733/6400/1348/950 |
| C09 | dev | approximate | Tesla's Q3 2025 profit was about $1.4 billion. | supported | insufficient_evidence | no | 0.013124 | 9771.0 | 442/0/2958/2814 | supported | yes | 0.014530 | 23676.3 | 4774/113/2044/1701 | insufficient_evidence | no | 0.011859 | 7886.8 | 1585/768/2523/2089 | supported | yes | 0.011259 | 7298.4 | 7669/6272/2017/1534 | insufficient_evidence | no | 0.009917 | 33379.7 | 508/448/2300/2122 | supported | yes | 0.011084 | 23317.6 | 8383/6400/1799/1285 |
| C10 | dev | approximate | Microsoft's September quarter brought in roughly $77 billion of revenue. | supported | insufficient_evidence | no | 0.025119 | 21015.4 | 878/0/5652/5428 | supported | yes | 0.019908 | 46099.5 | 6676/3795/3703/3241 | insufficient_evidence | no | 0.011460 | 8667.7 | 506/384/2647/2471 | supported | yes | 0.011904 | 7151.4 | 8596/6272/1896/1305 | insufficient_evidence | no | 0.003292 | 9003.3 | 505/448/742/580 | supported | yes | 0.014037 | 38757.7 | 8409/6400/2486/1948 |
| C11 | test | approximate | NVIDIA's quarter ended in late July 2026 generated about $96 billion in revenue. | supported | insufficient_evidence | no | 0.013118 | 9983.2 | 444/0/2956/2631 | insufficient_evidence | no | 0.021457 | 40103.3 | 6731/1634/3492/2964 | insufficient_evidence | no | 0.011483 | 8520.0 | 511/384/2651/2336 | supported | yes | 0.014441 | 9396.2 | 11339/8960/2382/1735 | insufficient_evidence | no | 0.017913 | 57925.7 | 1587/448/3864/3347 | supported | yes | 0.020190 | 44472.5 | 11485/5376/2764/2164 |
| C12 | dev | inequality | Alphabet's Q3 2025 revenue topped $100 billion. | supported | supported | yes | 0.012392 | 8858.4 | 439/241/2849/2728 | supported | yes | 0.013064 | 30130.0 | 4793/2530/2319/1963 | insufficient_evidence | no | 0.022507 | 17597.9 | 1012/768/5197/5019 | supported | yes | 0.009672 | 6273.9 | 7654/6272/1648/1237 | insufficient_evidence | no | 0.007482 | 40342.5 | 505/448/1728/1574 | supported | yes | 0.010968 | 34843.3 | 8390/6464/1786/1314 |
| C13 | dev | inequality | Amazon's Q3 2025 revenue came in below $181 billion. | supported | supported | yes | 0.027238 | 19699.4 | 882/369/6245/6090 | supported | yes | 0.014986 | 29632.6 | 4850/113/2129/1751 | insufficient_evidence | no | 0.007030 | 5213.7 | 508/384/1604/1448 | supported | yes | 0.009289 | 6159.2 | 7653/6272/1558/1163 | insufficient_evidence | no | 0.009869 | 28383.7 | 507/448/2289/2109 | supported | yes | 0.010827 | 25827.3 | 7775/5696/1735/1314 |
| C14 | test | inequality | Apple's June 2026 quarter cleared $110 billion in revenue. | contradicted | insufficient_evidence | no | 0.008582 | 6470.0 | 440/0/1890/1695 | contradicted | yes | 0.021933 | 30473.7 | 5501/113/3572/3103 | insufficient_evidence | no | 0.005639 | 4060.5 | 507/384/1277/1049 | contradicted | yes | 0.017348 | 11338.1 | 8650/6272/3161/2504 | insufficient_evidence | no | 0.004551 | 14768.0 | 506/448/1038/835 | contradicted | yes | 0.015217 | 91732.5 | 8460/3840/2086/1534 |
| C15 | dev | yoy_true | Meta's Q2 2025 revenue was up 22% year over year. | supported | supported | yes | 0.010971 | 7364.4 | 443/0/2451/2286 | supported | yes | 0.020327 | 32910.8 | 6450/113/2915/2401 | supported | yes | 0.021476 | 16167.0 | 1020/768/4952/4735 | supported | yes | 0.022415 | 16353.0 | 9212/6272/4188/3737 | insufficient_evidence | no | 0.011185 | 35052.1 | 509/448/2598/2430 | supported | yes | 0.018514 | 50150.4 | 9334/6464/3284/2810 |
| C16 | test | yoy_true | NVIDIA's revenue for the quarter ended October 2025 jumped 62% from a year earlier. | supported | supported | yes | 0.011737 | 8789.7 | 446/369/2726/2433 | supported | yes | 0.045728 | 31173.5 | 10331/1875/4624/3960 | supported | yes | 0.027761 | 19726.7 | 1026/768/6429/6058 | supported | yes | 0.024242 | 12868.5 | 15674/8960/3413/2506 | supported | yes | 0.011320 | 35561.7 | 512/448/2629/2406 | supported | yes | 0.023659 | 40022.5 | 14104/6400/3075/2217 |
| C17 | dev | yoy_true | Tesla's Q3 2025 sales grew 12% from the same quarter a year earlier. | supported | insufficient_evidence | no | 0.026232 | 21486.5 | 892/738/6101/5851 | insufficient_evidence | no | 0.022705 | 48499.1 | 6479/113/3466/2937 | supported | yes | 0.022474 | 17556.8 | 1026/768/5185/4931 | supported | yes | 0.017620 | 11934.1 | 9266/6272/3044/2554 | insufficient_evidence | no | 0.010101 | 37469.0 | 512/448/2342/2037 | supported | yes | 0.013843 | 41346.2 | 9376/6400/2156/1640 |
| C18 | dev | yoy_false | Tesla's Q3 2025 revenue fell 10% year over year. | contradicted | contradicted | yes | 0.026123 | 18004.8 | 884/369/5982/5799 | contradicted | yes | 0.021359 | 30429.6 | 6429/113/3164/2659 | insufficient_evidence | no | 0.010767 | 7874.7 | 509/384/2483/2186 | contradicted | yes | 0.014266 | 8941.7 | 9228/6272/2266/1807 | insufficient_evidence | no | 0.009203 | 35431.6 | 508/448/2132/1959 | contradicted | yes | 0.014238 | 45398.1 | 9321/6400/2265/1805 |
| C19 | dev | yoy_false | Meta's Q2 2025 revenue rose 30% from a year earlier. | contradicted | contradicted | yes | 0.010138 | 7527.8 | 443/0/2255/2065 | insufficient_evidence | no | 0.019759 | 28943.6 | 6438/113/2785/2311 | insufficient_evidence | no | 0.009681 | 6620.0 | 510/0/2128/1958 | contradicted | yes | 0.013495 | 8606.5 | 9192/6272/2095/1684 | contradicted | yes | 0.020742 | 56576.3 | 1018/448/4697/4486 | contradicted | yes | 0.023584 | 47559.2 | 9341/2624/3481/2974 |
| C20 | test | yoy_false | Apple's June 2026 revenue was down 8% year over year. | contradicted | insufficient_evidence | no | 0.010378 | 7472.7 | 442/0/2312/2115 | contradicted | yes | 0.041438 | 20146.7 | 10201/1265/3220/2580 | insufficient_evidence | no | 0.005939 | 4644.2 | 509/384/1347/1031 | contradicted | yes | 0.023001 | 13681.1 | 11558/6272/3636/2969 | insufficient_evidence | no | 0.006292 | 30641.3 | 508/448/1447/1240 | contradicted | yes | 0.024855 | 42022.8 | 13860/5696/3246/2531 |
| C21 | dev | period_trap | Apple's fiscal 2025 revenue of $416.2 billion was generated in the fourth quarter. | contradicted | contradicted | yes | 0.024263 | 16623.9 | 892/241/5509/5188 | insufficient_evidence | no | 0.024537 | 28202.4 | 5803/113/4096/3304 | failed | no | 0.038688 | 27743.5 | 1026/768/9000/8769 | contradicted | yes | 0.023934 | 15448.2 | 8744/6272/4683/3846 | contradicted | yes | 0.009688 | 37136.0 | 512/448/2245/1908 | contradicted | yes | 0.023293 | 68154.2 | 8826/5696/4359/3534 |
| C22 | dev | period_trap | Microsoft's fourth-quarter 2025 revenue was $281.7 billion. | contradicted | contradicted | yes | 0.012398 | 8897.7 | 441/369/2883/2702 | contradicted | yes | 0.042903 | 61142.1 | 7316/0/7943/6916 | insufficient_evidence | no | 0.007489 | 5188.2 | 508/384/1712/1555 | contradicted | yes | 0.023206 | 14990.2 | 8679/6272/4531/3736 | insufficient_evidence | no | 0.008458 | 28453.6 | 507/448/1957/1786 | contradicted | yes | 0.025984 | 62041.7 | 8755/4992/4831/4028 |
| C23 | test | period_trap | NVIDIA's fiscal 2025 third-quarter revenue was $57.0 billion. | contradicted | contradicted | yes | 0.012270 | 9333.5 | 442/0/2757/2552 | contradicted | yes | 0.010770 | 26722.5 | 4825/3682/2068/1682 | insufficient_evidence | no | 0.011812 | 8752.8 | 509/384/2729/2547 | contradicted | yes | 0.008650 | 6224.4 | 7652/6272/1408/988 | contradicted | yes | 0.034349 | 108708.8 | 2091/1344/7815/7341 | contradicted | yes | 0.010676 | 76641.1 | 7739/5696/1710/1296 |
| C24 | dev | unit_trap | Amazon's Q3 2025 revenue was $180.2 million. | contradicted | contradicted | yes | 0.033722 | 28321.8 | 882/610/7833/7639 | contradicted | yes | 0.011899 | 24099.9 | 4829/2417/2005/1624 | insufficient_evidence | no | 0.023345 | 17065.4 | 1016/768/5393/5205 | contradicted | yes | 0.008405 | 5717.3 | 7677/6272/1343/913 | contradicted | yes | 0.008577 | 67799.2 | 507/448/1985/1793 | contradicted | yes | 0.012562 | 45473.8 | 7760/4928/1949/1525 |
| C25 | test | unit_trap | Meta's Q2 2025 revenue was $47,516 million. | supported | supported | yes | 0.011671 | 9327.9 | 441/369/2712/2561 | supported | yes | 0.012076 | 25577.8 | 4798/2530/2085/1723 | supported | yes | 0.007990 | 6164.5 | 508/384/1830/1625 | supported | yes | 0.008093 | 5569.9 | 7652/6272/1277/880 | insufficient_evidence | no | 0.005390 | 18030.5 | 507/448/1235/1090 | supported | yes | 0.009906 | 26613.4 | 7737/5760/1546/1159 |
| C26 | dev | multi_part | Meta's Q2 2025 revenue was $47.5 billion, and net income was $18.9 billion. | contradicted | contradicted | yes | 0.029722 | 22977.3 | 902/610/6886/6555 | contradicted | yes | 0.021894 | 50144.8 | 7361/226/3045/2395 | insufficient_evidence | no | 0.008079 | 5697.4 | 518/384/1848/1582 | contradicted | yes | 0.013136 | 8128.5 | 8460/6272/2226/1492 | contradicted | yes | 0.025362 | 106296.6 | 1034/960/5912/5636 | contradicted | yes | 0.014491 | 60173.8 | 8499/6464/2583/1898 |
| C27 | test | multi_part | Amazon's Q3 2025 revenue topped $180 billion, while net income topped $22 billion. | contradicted | insufficient_evidence | no | 0.027164 | 22184.7 | 894/369/6224/5851 | contradicted | yes | 0.016716 | 30825.2 | 5638/3682/3228/2431 | insufficient_evidence | no | 0.018013 | 13359.0 | 1028/896/4168/3922 | contradicted | yes | 0.012146 | 7424.1 | 8434/5760/1868/1183 | contradicted | yes | 0.012061 | 56285.0 | 513/448/2803/2510 | contradicted | yes | 0.012197 | 52355.6 | 8566/6400/2007/1292 |
| C28 | dev | record_first | Meta's Q2 2026 revenue was the first quarterly result above $60 billion. | supported | insufficient_evidence | no | 0.008392 | 6657.4 | 444/0/1844/1507 | supported | yes | 0.038948 | 48059.9 | 15350/226/4708/4026 | insufficient_evidence | no | 0.008423 | 5878.2 | 511/384/1931/1596 | supported | yes | 0.027520 | 11342.6 | 16808/6272/3155/2213 | insufficient_evidence | no | 0.007540 | 34402.9 | 510/448/1740/1452 | supported | yes | 0.031012 | 59262.5 | 16910/6400/3980/3054 |
| C29 | dev | insufficient_evidence | Tesla expects to deliver 2.2 million vehicles in 2026. | insufficient_evidence | insufficient_evidence | yes | 0.011499 | 8569.1 | 441/0/2576/2377 | insufficient_evidence | yes | 0.012959 | 19197.1 | 2777/2417/2858/2528 | insufficient_evidence | yes | 0.011773 | 9285.0 | 508/384/2720/2249 | insufficient_evidence | yes | 0.013049 | 9751.5 | 4444/3712/2724/2345 | insufficient_evidence | yes | 0.007017 | 22897.1 | 507/448/1618/1325 | insufficient_evidence | yes | 0.017921 | 68130.6 | 4502/3776/3870/3443 |
| C30 | test | insufficient_evidence | NVIDIA held roughly 90% of the 2025 AI accelerator market. | insufficient_evidence | insufficient_evidence | yes | 0.026736 | 22517.8 | 882/369/6127/5800 | insufficient_evidence | yes | 0.017940 | 23247.4 | 2741/0/3415/3163 | insufficient_evidence | yes | 0.007854 | 5811.7 | 508/384/1798/1630 | insufficient_evidence | yes | 0.011485 | 8258.7 | 4436/2304/1994/1652 | insufficient_evidence | yes | 0.004705 | 15446.8 | 507/448/1074/905 | insufficient_evidence | yes | 0.016272 | 104803.7 | 6288/5056/3288/2684 |

## Agent errors

None recorded.

## Accounting

Budget stop: none recorded.
Ledger spend before/after: $0.000000 / $2.949685.
