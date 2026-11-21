# Control experiments (B=384, test split)

## Accuracy

| variant      | model                 | condition        |   accuracy |   lo |   hi |   execute |   execute_lo |   execute_hi |   memory_tokens |   over_budget |   invalid |
|:-------------|:----------------------|:-----------------|-----------:|-----:|-----:|----------:|-------------:|-------------:|----------------:|--------------:|----------:|
| original     | Llama-3.1-8B-Instruct | abl_noguard      |       77.6 | 73.7 | 81.5 |      88.9 |         86.2 |         91.7 |             295 |           8.8 |       0   |
| original     | Llama-3.1-8B-Instruct | abl_noreceipt    |       68.8 | 63.1 | 74.4 |      87   |         84.2 |         89.9 |             292 |           8   |       0   |
| original     | Llama-3.1-8B-Instruct | chrono           |       77   | 72.4 | 81.2 |      85.5 |         82.2 |         88.5 |             321 |          17.5 |       0   |
| original     | Llama-3.1-8B-Instruct | full             |       81.6 | 77.9 | 84.8 |      86.9 |         84.3 |         89.3 |               0 |           0   |       0   |
| original     | Llama-3.1-8B-Instruct | lifecycle        |       71.1 | 66.1 | 76   |      89   |         86.1 |         91.8 |             294 |           7   |       0   |
| original     | Llama-3.1-8B-Instruct | lifecycle_gold   |       81.5 | 78.2 | 84.3 |      90.7 |         87.9 |         93.2 |             294 |           4.6 |       0   |
| original     | Llama-3.1-8B-Instruct | lifecycle_strict |       76.8 | 72.5 | 81.1 |      89   |         86.2 |         91.8 |             292 |           7.5 |       0   |
| original     | Llama-3.1-8B-Instruct | pinning          |       66.4 | 62.9 | 70.2 |      83.1 |         79.7 |         86.7 |             332 |          22.6 |       0   |
| original     | Llama-3.1-8B-Instruct | summary          |       73.5 | 70.2 | 76.7 |      87.5 |         84   |         90.6 |             181 |           0   |       0   |
| original     | Llama-3.1-8B-Instruct | typed_llm        |       69.4 | 65   | 73.9 |      85.8 |         82.7 |         89.1 |             292 |           7.5 |       0   |
| original     | Qwen2.5-7B-Instruct   | abl_noguard      |       74.5 | 70.7 | 78.1 |      86.3 |         83.6 |         88.9 |             254 |           1.5 |       0   |
| original     | Qwen2.5-7B-Instruct   | abl_noreceipt    |       74.7 | 70.8 | 78.7 |      86.7 |         84   |         89.6 |             251 |           1.8 |       0   |
| original     | Qwen2.5-7B-Instruct   | chrono           |       69.9 | 66.4 | 73.3 |      85.5 |         82.4 |         88.5 |             286 |           7.2 |       0.2 |
| original     | Qwen2.5-7B-Instruct   | full             |       60.4 | 55.2 | 64.9 |      83.9 |         80.2 |         87.6 |               0 |           0   |       0   |
| original     | Qwen2.5-7B-Instruct   | lifecycle        |       76.4 | 72.7 | 80.2 |      88.1 |         85.7 |         90.5 |             252 |           1   |       0   |
| original     | Qwen2.5-7B-Instruct   | lifecycle_gold   |       83.1 | 80   | 85.8 |      90.7 |         88.6 |         92.5 |             263 |           1   |       0   |
| original     | Qwen2.5-7B-Instruct   | lifecycle_strict |       76.1 | 72.4 | 79.4 |      88.3 |         86   |         90.7 |             253 |           1.3 |       0   |
| original     | Qwen2.5-7B-Instruct   | pinning          |       64.2 | 59.5 | 68.5 |      80.4 |         77.2 |         83.4 |             192 |           0.5 |       0   |
| original     | Qwen2.5-7B-Instruct   | summary          |       60.1 | 56.3 | 63.7 |      80   |         77   |         83.1 |             132 |           0.5 |       0   |
| original     | Qwen2.5-7B-Instruct   | typed_llm        |       69.1 | 64.6 | 73.4 |      81.5 |         77.3 |         85.4 |             249 |           1.5 |       0   |
| pace_nocap   | Llama-3.1-8B-Instruct | abl_noguard      |       77.3 | 73.5 | 81.1 |      89   |         86.1 |         91.6 |             293 |           6.1 |       0   |
| pace_nocap   | Llama-3.1-8B-Instruct | abl_noreceipt    |       69.4 | 64.3 | 74.4 |      86.4 |         83.2 |         89.5 |             289 |           4.6 |       0   |
| pace_nocap   | Llama-3.1-8B-Instruct | chrono           |       78.6 | 74.3 | 82.6 |      85.1 |         81.3 |         88.7 |             322 |          17.7 |       0   |
| pace_nocap   | Llama-3.1-8B-Instruct | full             |       81.3 | 77.6 | 84.5 |      87   |         84.3 |         89.6 |               0 |           0   |       0   |
| pace_nocap   | Llama-3.1-8B-Instruct | lifecycle        |       70   | 64.9 | 75.2 |      88.9 |         85.9 |         91.7 |             293 |           7.5 |       0   |
| pace_nocap   | Llama-3.1-8B-Instruct | lifecycle_gold   |       83.1 | 79.7 | 86.3 |      92.3 |         89.9 |         94.5 |             296 |           5.4 |       0   |
| pace_nocap   | Llama-3.1-8B-Instruct | lifecycle_nohint |       74.8 | 70.8 | 78.8 |      86.6 |         82.9 |         90.1 |             273 |           3.3 |       0.2 |
| pace_nocap   | Llama-3.1-8B-Instruct | lifecycle_strict |       76.4 | 72.1 | 80.6 |      88.6 |         85.5 |         91.6 |             292 |           6.2 |       0   |
| pace_nocap   | Llama-3.1-8B-Instruct | pinning          |       68.8 | 66.1 | 71.4 |      83.3 |         80.3 |         86.2 |             332 |          23.6 |       0   |
| pace_nocap   | Llama-3.1-8B-Instruct | summary          |       72.7 | 69.4 | 76   |      88   |         85.1 |         90.8 |             183 |           0.8 |       0   |
| pace_nocap   | Llama-3.1-8B-Instruct | typed_llm        |       68.8 | 64.3 | 73.5 |      85.5 |         82.5 |         88.6 |             290 |           6.2 |       0   |
| pace_nocap   | Qwen2.5-7B-Instruct   | abl_noguard      |       74.4 | 70.5 | 77.9 |      86   |         83.3 |         88.6 |             254 |           1.6 |       0   |
| pace_nocap   | Qwen2.5-7B-Instruct   | abl_noreceipt    |       72.7 | 68.4 | 76.7 |      85.2 |         82.6 |         87.8 |             253 |           1.5 |       0.2 |
| pace_nocap   | Qwen2.5-7B-Instruct   | chrono           |       68.8 | 64.6 | 72.7 |      84.6 |         81.2 |         87.7 |             285 |           4.7 |       0.2 |
| pace_nocap   | Qwen2.5-7B-Instruct   | full             |       60.8 | 56   | 65.2 |      84.3 |         81   |         87.6 |               0 |           0   |       0   |
| pace_nocap   | Qwen2.5-7B-Instruct   | lifecycle        |       77   | 73   | 80.8 |      88.6 |         85.9 |         91.2 |             255 |           2.1 |       0   |
| pace_nocap   | Qwen2.5-7B-Instruct   | lifecycle_gold   |       82.1 | 79.3 | 84.8 |      91   |         88.8 |         93   |             263 |           2.1 |       0   |
| pace_nocap   | Qwen2.5-7B-Instruct   | lifecycle_nohint |       68.7 | 65.2 | 72   |      85.2 |         83.1 |         87.6 |             239 |           1   |       0.2 |
| pace_nocap   | Qwen2.5-7B-Instruct   | lifecycle_strict |       76.2 | 72.3 | 79.9 |      88.6 |         85.8 |         91.3 |             252 |           1.3 |       0.2 |
| pace_nocap   | Qwen2.5-7B-Instruct   | pinning          |       63.7 | 59.5 | 67.8 |      81.6 |         78.9 |         84.3 |             194 |           0.5 |       0.2 |
| pace_nocap   | Qwen2.5-7B-Instruct   | summary          |       57.4 | 53.5 | 61.1 |      79.8 |         77   |         82.8 |             131 |           0   |       0   |
| pace_nocap   | Qwen2.5-7B-Instruct   | typed_llm        |       71.1 | 66.7 | 75.3 |      83.4 |         79.9 |         86.9 |             249 |           1   |       0   |
| pace_hardcap | Llama-3.1-8B-Instruct | abl_noguard      |       77.4 | 73.2 | 81.4 |      88.7 |         85.7 |         91.6 |             291 |           0   |       0   |
| pace_hardcap | Llama-3.1-8B-Instruct | abl_noreceipt    |       69.4 | 64.3 | 74.6 |      86.6 |         83.4 |         89.8 |             289 |           0   |       0   |
| pace_hardcap | Llama-3.1-8B-Instruct | chrono           |       78.3 | 74.1 | 82.2 |      85.4 |         81.6 |         88.8 |             317 |           0   |       0   |
| pace_hardcap | Llama-3.1-8B-Instruct | full             |       81.3 | 77.6 | 84.5 |      87   |         84.3 |         89.6 |               0 |           0   |       0   |
| pace_hardcap | Llama-3.1-8B-Instruct | lifecycle        |       70.8 | 65.3 | 76.1 |      88.4 |         85.2 |         91.5 |             291 |           0   |       0   |
| pace_hardcap | Llama-3.1-8B-Instruct | lifecycle_gold   |       83.3 | 79.8 | 86.5 |      92.5 |         90   |         94.7 |             296 |           0   |       0   |
| pace_hardcap | Llama-3.1-8B-Instruct | lifecycle_nohint |       74.8 | 70.9 | 78.7 |      86.7 |         83.1 |         90.2 |             273 |           0   |       0.2 |
| pace_hardcap | Llama-3.1-8B-Instruct | lifecycle_strict |       77.4 | 73.1 | 81.4 |      88.9 |         85.8 |         91.9 |             290 |           0   |       0   |
| pace_hardcap | Llama-3.1-8B-Instruct | pinning          |       68.4 | 65.8 | 70.9 |      83   |         80.1 |         85.7 |             327 |           0   |       0   |
| pace_hardcap | Llama-3.1-8B-Instruct | summary          |       72.7 | 69.4 | 76   |      88   |         85.1 |         90.8 |             183 |           0   |       0   |
| pace_hardcap | Llama-3.1-8B-Instruct | typed_llm        |       69   | 64.3 | 73.7 |      85.4 |         82.4 |         88.3 |             289 |           0   |       0   |
| pace_hardcap | Qwen2.5-7B-Instruct   | abl_noguard      |       73.9 | 69.9 | 77.7 |      86.4 |         83.8 |         89.1 |             255 |           0   |       0   |
| pace_hardcap | Qwen2.5-7B-Instruct   | abl_noreceipt    |       74.1 | 69.7 | 78.2 |      86.6 |         83.7 |         89.4 |             252 |           0   |       0   |
| pace_hardcap | Qwen2.5-7B-Instruct   | chrono           |       68.2 | 64.2 | 71.9 |      84.5 |         81.1 |         87.5 |             283 |           0   |       0.2 |
| pace_hardcap | Qwen2.5-7B-Instruct   | full             |       60.8 | 56   | 65.2 |      84.3 |         81   |         87.6 |               0 |           0   |       0   |
| pace_hardcap | Qwen2.5-7B-Instruct   | lifecycle        |       75.5 | 71.4 | 79.1 |      88.1 |         85.6 |         90.7 |             254 |           0   |       0   |
| pace_hardcap | Qwen2.5-7B-Instruct   | lifecycle_gold   |       82.8 | 79.8 | 85.7 |      91.7 |         89.4 |         93.8 |             263 |           0   |       0   |
| pace_hardcap | Qwen2.5-7B-Instruct   | lifecycle_nohint |       68.8 | 65.3 | 72.2 |      85.4 |         83.3 |         87.7 |             238 |           0   |       0.2 |
| pace_hardcap | Qwen2.5-7B-Instruct   | lifecycle_strict |       75.3 | 71.2 | 79   |      88   |         85.4 |         90.5 |             253 |           0   |       0   |
| pace_hardcap | Qwen2.5-7B-Instruct   | pinning          |       63.7 | 59.5 | 67.8 |      81.6 |         78.9 |         84.3 |             194 |           0   |       0.2 |
| pace_hardcap | Qwen2.5-7B-Instruct   | summary          |       57.4 | 53.5 | 61.1 |      79.8 |         77   |         82.8 |             131 |           0   |       0   |
| pace_hardcap | Qwen2.5-7B-Instruct   | typed_llm        |       71.1 | 66.7 | 75.4 |      83.3 |         79.9 |         86.7 |             250 |           0   |       0   |

## LADL minus baselines, hard cap (Holm within metric)

| metric   | model                 | baseline   |   diff |    lo |   hi |     p |   p_holm | significant_holm   |
|:---------|:----------------------|:-----------|-------:|------:|-----:|------:|---------:|:-------------------|
| four_way | Llama-3.1-8B-Instruct | summary    |   -2   |  -7.8 |  3.6 | 0.49  |    1     | False              |
| four_way | Llama-3.1-8B-Instruct | pinning    |    2.4 |  -3.8 |  8.6 | 0.48  |    1     | False              |
| four_way | Llama-3.1-8B-Instruct | chrono     |   -7.5 | -13   | -2.2 | 0.006 |    0.03  | True               |
| four_way | Llama-3.1-8B-Instruct | typed_llm  |    1.8 |  -2   |  5.7 | 0.358 |    1     | False              |
| four_way | Qwen2.5-7B-Instruct   | summary    |   18.1 |  13.6 | 22.4 | 0.001 |    0.008 | True               |
| four_way | Qwen2.5-7B-Instruct   | pinning    |   11.7 |   7.9 | 15.8 | 0.001 |    0.008 | True               |
| four_way | Qwen2.5-7B-Instruct   | chrono     |    7.2 |   3.4 | 11.3 | 0.001 |    0.008 | True               |
| four_way | Qwen2.5-7B-Instruct   | typed_llm  |    4.4 |   0.9 |  7.9 | 0.016 |    0.064 | False              |
| execute  | Llama-3.1-8B-Instruct | summary    |    0.5 |  -2.7 |  3.6 | 0.81  |    0.81  | False              |
| execute  | Llama-3.1-8B-Instruct | pinning    |    5.4 |   1   | 10   | 0.021 |    0.084 | False              |
| execute  | Llama-3.1-8B-Instruct | chrono     |    3   |  -0.9 |  7.4 | 0.156 |    0.312 | False              |
| execute  | Llama-3.1-8B-Instruct | typed_llm  |    3   |   0.6 |  5.5 | 0.012 |    0.06  | False              |
| execute  | Qwen2.5-7B-Instruct   | summary    |    8.3 |   4.5 | 11.9 | 0.001 |    0.008 | True               |
| execute  | Qwen2.5-7B-Instruct   | pinning    |    6.5 |   4   |  9.1 | 0.001 |    0.008 | True               |
| execute  | Qwen2.5-7B-Instruct   | chrono     |    3.6 |   0.5 |  6.6 | 0.023 |    0.084 | False              |
| execute  | Qwen2.5-7B-Instruct   | typed_llm  |    4.8 |   1.6 |  8.4 | 0.002 |    0.012 | True               |

## LADL minus baselines, PACE without cap (Holm within metric)

| metric   | model                 | baseline   |   diff |    lo |   hi |     p |   p_holm | significant_holm   |
|:---------|:----------------------|:-----------|-------:|------:|-----:|------:|---------:|:-------------------|
| four_way | Llama-3.1-8B-Instruct | summary    |   -2.7 |  -7.7 |  2.3 | 0.306 |    0.918 | False              |
| four_way | Llama-3.1-8B-Instruct | pinning    |    1.2 |  -4.5 |  6.6 | 0.697 |    1     | False              |
| four_way | Llama-3.1-8B-Instruct | chrono     |   -8.6 | -14.4 | -3   | 0.004 |    0.016 | True               |
| four_way | Llama-3.1-8B-Instruct | typed_llm  |    1.2 |  -2.2 |  4.7 | 0.524 |    1     | False              |
| four_way | Qwen2.5-7B-Instruct   | summary    |   19.6 |  15.6 | 23.6 | 0.001 |    0.008 | True               |
| four_way | Qwen2.5-7B-Instruct   | pinning    |   13.3 |   9.2 | 17.3 | 0.001 |    0.008 | True               |
| four_way | Qwen2.5-7B-Instruct   | chrono     |    8.1 |   4   | 12.4 | 0.001 |    0.008 | True               |
| four_way | Qwen2.5-7B-Instruct   | typed_llm  |    5.9 |   2.1 |  9.6 | 0.002 |    0.01  | True               |
| execute  | Llama-3.1-8B-Instruct | summary    |    0.9 |  -2.3 |  3.8 | 0.602 |    0.602 | False              |
| execute  | Llama-3.1-8B-Instruct | pinning    |    5.6 |   1.4 |  9.6 | 0.007 |    0.035 | True               |
| execute  | Llama-3.1-8B-Instruct | chrono     |    3.8 |  -0.3 |  8.1 | 0.08  |    0.16  | False              |
| execute  | Llama-3.1-8B-Instruct | typed_llm  |    3.3 |   0.9 |  5.7 | 0.007 |    0.035 | True               |
| execute  | Qwen2.5-7B-Instruct   | summary    |    8.7 |   5.2 | 12.1 | 0.001 |    0.008 | True               |
| execute  | Qwen2.5-7B-Instruct   | pinning    |    6.9 |   4.2 |  9.6 | 0.001 |    0.008 | True               |
| execute  | Qwen2.5-7B-Instruct   | chrono     |    3.9 |   0.7 |  7.2 | 0.022 |    0.066 | False              |
| execute  | Qwen2.5-7B-Instruct   | typed_llm  |    5.1 |   1.7 |  8.7 | 0.004 |    0.024 | True               |

## Ledger action-hint control, hard cap (Holm within metric)

| metric   | model                 | a                | b                |   diff |   lo |   hi |     p |   p_holm |
|:---------|:----------------------|:-----------------|:-----------------|-------:|-----:|-----:|------:|---------:|
| four_way | Llama-3.1-8B-Instruct | lifecycle        | lifecycle_nohint |   -4.1 | -8.2 |  0   | 0.052 |    0.26  |
| four_way | Llama-3.1-8B-Instruct | lifecycle_nohint | summary          |    2.1 | -1.6 |  5.7 | 0.284 |    0.852 |
| four_way | Llama-3.1-8B-Instruct | lifecycle_nohint | pinning          |    6.5 |  2   | 11   | 0.003 |    0.018 |
| four_way | Llama-3.1-8B-Instruct | lifecycle_nohint | chrono           |   -3.5 | -7.7 |  0.8 | 0.116 |    0.464 |
| four_way | Llama-3.1-8B-Instruct | lifecycle_nohint | typed_llm        |    5.9 |  1.9 | 10   | 0.001 |    0.01  |
| four_way | Qwen2.5-7B-Instruct   | lifecycle        | lifecycle_nohint |    6.6 |  3.4 |  9.8 | 0.001 |    0.01  |
| four_way | Qwen2.5-7B-Instruct   | lifecycle_nohint | summary          |   11.4 |  7.9 | 15   | 0.001 |    0.01  |
| four_way | Qwen2.5-7B-Instruct   | lifecycle_nohint | pinning          |    5.1 |  1.5 |  8.8 | 0.002 |    0.014 |
| four_way | Qwen2.5-7B-Instruct   | lifecycle_nohint | chrono           |    0.6 | -3.1 |  4.4 | 0.758 |    0.852 |
| four_way | Qwen2.5-7B-Instruct   | lifecycle_nohint | typed_llm        |   -2.3 | -6.4 |  1.6 | 0.287 |    0.852 |
| execute  | Llama-3.1-8B-Instruct | lifecycle        | lifecycle_nohint |    1.7 | -1.4 |  4.6 | 0.294 |    1     |
| execute  | Llama-3.1-8B-Instruct | lifecycle_nohint | summary          |   -1.2 | -4.5 |  1.9 | 0.491 |    1     |
| execute  | Llama-3.1-8B-Instruct | lifecycle_nohint | pinning          |    3.8 | -0   |  7.6 | 0.062 |    0.434 |
| execute  | Llama-3.1-8B-Instruct | lifecycle_nohint | chrono           |    1.4 | -2.5 |  5.7 | 0.545 |    1     |
| execute  | Llama-3.1-8B-Instruct | lifecycle_nohint | typed_llm        |    1.4 | -0.8 |  3.7 | 0.276 |    1     |
| execute  | Qwen2.5-7B-Instruct   | lifecycle        | lifecycle_nohint |    2.7 |  0.4 |  4.8 | 0.023 |    0.184 |
| execute  | Qwen2.5-7B-Instruct   | lifecycle_nohint | summary          |    5.6 |  2.8 |  8.2 | 0.001 |    0.01  |
| execute  | Qwen2.5-7B-Instruct   | lifecycle_nohint | pinning          |    3.8 |  1   |  6.7 | 0.007 |    0.063 |
| execute  | Qwen2.5-7B-Instruct   | lifecycle_nohint | chrono           |    0.9 | -1.8 |  3.8 | 0.522 |    1     |
| execute  | Qwen2.5-7B-Instruct   | lifecycle_nohint | typed_llm        |    2.1 | -1.2 |  5.5 | 0.242 |    1     |

## Hard cap minus no cap

| model                 | condition        |   diff |   lo |   hi |     p |
|:----------------------|:-----------------|-------:|-----:|-----:|------:|
| Qwen2.5-7B-Instruct   | summary          |    0   |  0   |  0   | 1     |
| Qwen2.5-7B-Instruct   | pinning          |    0   |  0   |  0   | 1     |
| Qwen2.5-7B-Instruct   | chrono           |   -0.6 | -1.2 | -0.1 | 0.035 |
| Qwen2.5-7B-Instruct   | typed_llm        |    0   | -0.6 |  0.6 | 1     |
| Qwen2.5-7B-Instruct   | lifecycle        |   -1.5 | -3.2 |  0.1 | 0.087 |
| Qwen2.5-7B-Instruct   | lifecycle_nohint |    0.2 |  0   |  0.5 | 0.695 |
| Qwen2.5-7B-Instruct   | lifecycle_gold   |    0.8 | -0.1 |  1.8 | 0.13  |
| Qwen2.5-7B-Instruct   | abl_noguard      |   -0.5 | -2.3 |  1.3 | 0.67  |
| Qwen2.5-7B-Instruct   | abl_noreceipt    |    1.4 | -0.4 |  3.3 | 0.158 |
| Qwen2.5-7B-Instruct   | lifecycle_strict |   -0.9 | -1.9 |  0   | 0.08  |
| Llama-3.1-8B-Instruct | summary          |    0   |  0   |  0   | 1     |
| Llama-3.1-8B-Instruct | pinning          |   -0.5 | -1.7 |  0.9 | 0.588 |
| Llama-3.1-8B-Instruct | chrono           |   -0.3 | -1.6 |  1   | 0.708 |
| Llama-3.1-8B-Instruct | typed_llm        |    0.2 | -0.5 |  0.8 | 0.835 |
| Llama-3.1-8B-Instruct | lifecycle        |    0.8 | -1.4 |  3.1 | 0.574 |
| Llama-3.1-8B-Instruct | lifecycle_nohint |    0   | -0.4 |  0.4 | 1     |
| Llama-3.1-8B-Instruct | lifecycle_gold   |    0.2 | -0.3 |  0.6 | 0.793 |
| Llama-3.1-8B-Instruct | abl_noguard      |    0.2 | -1.5 |  2   | 0.941 |
| Llama-3.1-8B-Instruct | abl_noreceipt    |    0   | -1.8 |  1.8 | 1     |
| Llama-3.1-8B-Instruct | lifecycle_strict |    1.1 | -0.3 |  2.4 | 0.156 |

## Original run versus PACE rerun without cap

| model                 | condition        |   same_decision |   accuracy_original |   accuracy_pace |
|:----------------------|:-----------------|----------------:|--------------------:|----------------:|
| Llama-3.1-8B-Instruct | abl_noguard      |            86.7 |                77.6 |            77.3 |
| Llama-3.1-8B-Instruct | abl_noreceipt    |            86   |                68.8 |            69.4 |
| Llama-3.1-8B-Instruct | chrono           |            87.3 |                77   |            78.6 |
| Llama-3.1-8B-Instruct | full             |            96.7 |                81.6 |            81.3 |
| Llama-3.1-8B-Instruct | lifecycle        |            86.4 |                71.1 |            70   |
| Llama-3.1-8B-Instruct | lifecycle_gold   |            88.9 |                81.5 |            83.1 |
| Llama-3.1-8B-Instruct | lifecycle_strict |            86   |                76.8 |            76.4 |
| Llama-3.1-8B-Instruct | pinning          |            73   |                66.4 |            68.8 |
| Llama-3.1-8B-Instruct | summary          |            84.8 |                73.5 |            72.7 |
| Llama-3.1-8B-Instruct | typed_llm        |            84.9 |                69.4 |            68.8 |
| Qwen2.5-7B-Instruct   | abl_noguard      |            87.3 |                74.5 |            74.4 |
| Qwen2.5-7B-Instruct   | abl_noreceipt    |            88.4 |                74.7 |            72.7 |
| Qwen2.5-7B-Instruct   | chrono           |            80.4 |                69.9 |            68.8 |
| Qwen2.5-7B-Instruct   | full             |            94.6 |                60.4 |            60.8 |
| Qwen2.5-7B-Instruct   | lifecycle        |            88.7 |                76.4 |            77   |
| Qwen2.5-7B-Instruct   | lifecycle_gold   |            89.2 |                83.1 |            82.1 |
| Qwen2.5-7B-Instruct   | lifecycle_strict |            88.4 |                76.1 |            76.2 |
| Qwen2.5-7B-Instruct   | pinning          |            74.1 |                64.2 |            63.7 |
| Qwen2.5-7B-Instruct   | summary          |            79.8 |                60.1 |            57.4 |
| Qwen2.5-7B-Instruct   | typed_llm        |            86.7 |                69.1 |            71.1 |
