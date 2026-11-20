# Results (budget B=384 tokens, test split)


## Llama-3.1-8B-Instruct

| Condition | accuracy | violation | over_restriction | premature | duplicate | missed_clarify | state_recall | mem tok |
|---|---|---|---|---|---|---|---|---|
| Full history (no compaction) | 81.6 [77.9, 84.8] | 4.7 [1.9, 7.9] | 8.3 [4.5, 12.7] | 10.9 [5.3, 16.9] | 36.8 [25.0, 50.0] | 4.5 [0.0, 15.0] | 76.1 [70.3, 81.4] | 0 |
| Ordinary compaction | 73.5 [70.2, 76.7] | 7.3 [3.6, 11.6] | 4.7 [2.1, 7.8] | 11.7 [4.2, 20.5] | 19.1 [11.1, 26.9] | 0.0 [0.0, 0.0] | 64.6 [58.2, 70.4] | 166 |
| Constraint pinning | 66.4 [62.9, 70.2] | 10.3 [6.7, 14.0] | 12.0 [6.7, 17.2] | 9.4 [5.0, 14.6] | 23.5 [12.5, 35.9] | 0.0 [0.0, 0.0] | 63.3 [58.9, 67.5] | 314 |
| Chronological event ledger | 77.0 [72.4, 81.2] | 10.8 [5.5, 16.5] | 5.2 [2.3, 8.5] | 10.2 [3.8, 17.6] | 33.8 [22.1, 45.6] | 2.3 [0.0, 7.5] | 67.5 [63.1, 71.9] | 303 |
| Typed ledger, LLM transitions | 69.4 [65.0, 73.9] | 9.1 [4.3, 13.6] | 14.6 [10.5, 18.8] | 8.6 [3.0, 15.6] | 16.2 [6.2, 27.9] | 0.0 [0.0, 0.0] | 70.0 [66.1, 73.6] | 276 |
| Lifecycle ledger (ours) | 71.1 [66.1, 76.0] | 8.6 [4.7, 12.7] | 7.3 [3.6, 11.3] | 7.8 [2.7, 13.7] | 8.8 [1.5, 17.9] | 2.3 [0.0, 7.5] | 76.7 [72.4, 80.7] | 278 |
| Lifecycle ledger, gold events | 81.5 [78.2, 84.3] | 6.0 [2.6, 10.0] | 4.7 [2.1, 7.8] | 9.4 [4.2, 15.0] | 14.7 [6.2, 23.6] | 0.0 [0.0, 0.0] | 83.4 [79.2, 87.9] | 278 |
| Ours - guard logic | 77.6 [73.7, 81.5] | 6.9 [3.1, 10.7] | 7.3 [4.3, 10.2] | 14.8 [7.5, 23.1] | 13.2 [4.7, 23.4] | 2.3 [0.0, 7.5] | 77.3 [72.8, 81.5] | 279 |
| Ours - receipt evidence | 68.8 [63.1, 74.4] | 7.8 [3.8, 11.7] | 12.0 [7.5, 16.8] | 7.0 [2.2, 12.5] | 13.2 [2.9, 25.0] | 0.0 [0.0, 0.0] | 72.4 [67.9, 76.8] | 277 |
| Ours, strict hedging (post-hoc) | 76.8 [72.5, 81.1] | 7.8 [4.2, 11.2] | 5.7 [2.6, 9.6] | 9.4 [3.4, 16.4] | 13.2 [3.1, 25.0] | 0.0 [0.0, 0.0] | 76.7 [72.1, 80.9] | 277 |

## Qwen2.5-7B-Instruct

| Condition | accuracy | violation | over_restriction | premature | duplicate | missed_clarify | state_recall | mem tok |
|---|---|---|---|---|---|---|---|---|
| Full history (no compaction) | 60.4 [55.2, 64.9] | 3.9 [1.6, 6.4] | 30.2 [21.0, 39.5] | 0.8 [0.0, 2.5] | 4.4 [0.0, 9.4] | 0.0 [0.0, 0.0] | 73.5 [68.6, 77.9] | 0 |
| Ordinary compaction | 60.1 [56.3, 63.7] | 12.5 [7.7, 17.5] | 28.6 [20.6, 37.2] | 8.6 [4.0, 13.2] | 17.6 [8.3, 26.7] | 2.3 [0.0, 7.5] | 64.5 [58.7, 69.2] | 121 |
| Constraint pinning | 64.2 [59.5, 68.5] | 7.3 [3.0, 12.1] | 35.9 [27.1, 44.6] | 2.3 [0.0, 5.0] | 17.6 [8.9, 27.9] | 0.0 [0.0, 0.0] | 67.9 [63.4, 72.1] | 181 |
| Chronological event ledger | 69.9 [66.4, 73.3] | 11.2 [7.0, 15.4] | 18.8 [12.2, 26.0] | 3.9 [0.8, 7.8] | 10.3 [3.6, 17.9] | 0.0 [0.0, 0.0] | 73.9 [69.0, 78.6] | 271 |
| Typed ledger, LLM transitions | 69.1 [64.6, 73.4] | 7.3 [3.3, 12.1] | 35.4 [26.1, 44.4] | 11.7 [6.5, 17.5] | 14.7 [6.7, 23.6] | 0.0 [0.0, 0.0] | 72.7 [69.2, 76.2] | 237 |
| Lifecycle ledger (ours) | 76.4 [72.7, 80.2] | 4.7 [2.6, 6.8] | 19.3 [13.0, 26.0] | 4.7 [1.7, 7.6] | 14.7 [6.6, 23.3] | 0.0 [0.0, 0.0] | 87.8 [83.9, 91.1] | 239 |
| Lifecycle ledger, gold events | 83.1 [80.0, 85.8] | 2.2 [0.4, 4.3] | 19.8 [14.6, 25.5] | 0.8 [0.0, 2.5] | 7.4 [1.9, 12.5] | 0.0 [0.0, 0.0] | 91.4 [88.5, 94.1] | 250 |
| Ours - guard logic | 74.5 [70.7, 78.1] | 5.6 [3.2, 8.0] | 19.8 [13.9, 26.1] | 15.6 [9.3, 22.7] | 10.3 [3.6, 17.9] | 0.0 [0.0, 0.0] | 84.5 [81.1, 87.7] | 242 |
| Ours - receipt evidence | 74.7 [70.8, 78.7] | 3.0 [1.3, 4.8] | 25.0 [17.6, 33.2] | 3.9 [1.0, 7.1] | 14.7 [6.2, 23.7] | 0.0 [0.0, 0.0] | 83.4 [79.2, 87.1] | 239 |
| Ours, strict hedging (post-hoc) | 76.1 [72.4, 79.4] | 3.0 [1.3, 4.8] | 20.8 [15.0, 26.6] | 5.5 [2.0, 9.6] | 13.2 [5.6, 21.9] | 0.0 [0.0, 0.0] | 87.8 [83.4, 91.5] | 241 |

## Paired differences: lifecycle (ours) minus baseline (timeline-cluster bootstrap)

| Model | Baseline | metric | diff (pp) | 95% CI | p |
|---|---|---|---|---|---|
| Llama-3.1-8B-Instruct | Ordinary compaction | accuracy | -2.4 | [-7.5, +2.3] | 0.350 |
| Llama-3.1-8B-Instruct | Ordinary compaction | violation | +1.3 | [-4.3, +6.4] | 0.675 |
| Llama-3.1-8B-Instruct | Ordinary compaction | over_restriction | +2.6 | [-2.4, +7.4] | 0.382 |
| Llama-3.1-8B-Instruct | Ordinary compaction | premature | -3.9 | [-9.2, +1.0] | 0.160 |
| Llama-3.1-8B-Instruct | Ordinary compaction | duplicate | -10.3 | [-21.9, +1.4] | 0.089 |
| Llama-3.1-8B-Instruct | Constraint pinning | accuracy | +4.7 | [-0.6, +9.9] | 0.092 |
| Llama-3.1-8B-Instruct | Constraint pinning | violation | -1.7 | [-6.2, +2.6] | 0.505 |
| Llama-3.1-8B-Instruct | Constraint pinning | over_restriction | -4.7 | [-10.1, +1.0] | 0.132 |
| Llama-3.1-8B-Instruct | Constraint pinning | premature | -1.6 | [-9.3, +5.7] | 0.739 |
| Llama-3.1-8B-Instruct | Constraint pinning | duplicate | -14.7 | [-27.9, -1.7] | 0.036 |
| Llama-3.1-8B-Instruct | Chronological event ledger | accuracy | -5.9 | [-11.0, -0.7] | 0.027 |
| Llama-3.1-8B-Instruct | Typed ledger, LLM transitions | accuracy | +1.7 | [-2.1, +5.1] | 0.386 |
| Llama-3.1-8B-Instruct | Full history (no compaction) | accuracy | -10.5 | [-16.1, -4.5] | 0.001 |
| Llama-3.1-8B-Instruct | Ours - guard logic | accuracy | -6.5 | [-9.9, -3.3] | 0.000 |
| Llama-3.1-8B-Instruct | Ours - receipt evidence | accuracy | +2.3 | [-0.3, +5.2] | 0.102 |
| Llama-3.1-8B-Instruct | Lifecycle ledger, gold events | accuracy | -10.4 | [-15.6, -5.4] | 0.000 |
| Llama-3.1-8B-Instruct | Ours, strict hedging (post-hoc) | accuracy | -5.7 | [-8.8, -2.5] | 0.000 |
| Qwen2.5-7B-Instruct | Ordinary compaction | accuracy | +16.3 | [+12.3, +20.1] | 0.000 |
| Qwen2.5-7B-Instruct | Ordinary compaction | violation | -7.8 | [-12.3, -3.5] | 0.000 |
| Qwen2.5-7B-Instruct | Ordinary compaction | over_restriction | -9.4 | [-17.8, -1.1] | 0.029 |
| Qwen2.5-7B-Instruct | Ordinary compaction | premature | -3.9 | [-8.8, +0.7] | 0.142 |
| Qwen2.5-7B-Instruct | Ordinary compaction | duplicate | -2.9 | [-12.5, +7.9] | 0.666 |
| Qwen2.5-7B-Instruct | Constraint pinning | accuracy | +12.2 | [+7.2, +17.3] | 0.000 |
| Qwen2.5-7B-Instruct | Constraint pinning | violation | -2.6 | [-7.6, +1.8] | 0.306 |
| Qwen2.5-7B-Instruct | Constraint pinning | over_restriction | -16.7 | [-26.0, -7.2] | 0.000 |
| Qwen2.5-7B-Instruct | Constraint pinning | premature | +2.3 | [+0.0, +4.7] | 0.086 |
| Qwen2.5-7B-Instruct | Constraint pinning | duplicate | -2.9 | [-14.1, +7.7] | 0.723 |
| Qwen2.5-7B-Instruct | Chronological event ledger | accuracy | +6.5 | [+2.2, +10.2] | 0.002 |
| Qwen2.5-7B-Instruct | Typed ledger, LLM transitions | accuracy | +7.2 | [+4.1, +10.5] | 0.000 |
| Qwen2.5-7B-Instruct | Full history (no compaction) | accuracy | +16.0 | [+10.9, +21.1] | 0.000 |
| Qwen2.5-7B-Instruct | Ours - guard logic | accuracy | +1.8 | [-0.6, +4.0] | 0.147 |
| Qwen2.5-7B-Instruct | Ours - receipt evidence | accuracy | +1.7 | [-1.4, +4.9] | 0.318 |
| Qwen2.5-7B-Instruct | Lifecycle ledger, gold events | accuracy | -6.8 | [-10.1, -3.2] | 0.000 |
| Qwen2.5-7B-Instruct | Ours, strict hedging (post-hoc) | accuracy | +0.3 | [-1.8, +2.3] | 0.789 |

## Accuracy by category / gold reason - Qwen2.5-7B-Instruct

| condition        |   completion |   conditional |   revocation |   static |   ambiguous |   cancelled |   completed |   guard_unmet |   prohibited_active |   ready |   retry_after_failure |   revoked |
|:-----------------|-------------:|--------------:|-------------:|---------:|------------:|------------:|------------:|--------------:|--------------------:|--------:|----------------------:|----------:|
| full             |         63.8 |          72.3 |         64.1 |     34.7 |        84.1 |        71.4 |        86.8 |          86.7 |                37.3 |    42.3 |                  31.2 |      66.3 |
| summary          |         57.8 |          67.3 |         69.6 |     38.9 |        79.5 |        67.9 |        66.2 |          76.6 |                44.1 |    46.2 |                  45.8 |      71.7 |
| pinning          |         50   |          70.5 |         67.9 |     61.1 |        84.1 |        42.9 |        63.2 |          88.3 |                62.3 |    42.3 |                  31.2 |      62   |
| chrono           |         62.1 |          70.5 |         77.2 |     66   |        86.4 |        42.9 |        70.6 |          75   |                66.7 |    73.1 |                  50   |      78.3 |
| typed_llm        |         51.7 |          66.8 |         81   |     71.5 |        97.7 |        46.4 |        69.1 |          76.6 |                72.1 |    46.2 |                  27.1 |      80.4 |
| lifecycle        |         68.1 |          78.6 |         80.4 |     74.3 |        97.7 |        75   |        70.6 |          79.7 |                75   |    73.1 |                  64.6 |      77.2 |
| lifecycle_gold   |         81.9 |          82.3 |         81.5 |     87.5 |        93.2 |        78.6 |        86.8 |          87.5 |                86.8 |    67.3 |                  75   |      76.1 |
| abl_noguard      |         69.8 |          74.5 |         78.8 |     72.9 |        93.2 |        67.9 |        76.5 |          71.9 |                73.5 |    80.8 |                  60.4 |      76.1 |
| abl_noreceipt    |         54.3 |          80.9 |         80.4 |     74.3 |        97.7 |        78.6 |        70.6 |          81.2 |                75   |    76.9 |                  31.2 |      77.2 |
| lifecycle_strict |         66.4 |          78.2 |         79.9 |     75.7 |        97.7 |        75   |        69.1 |          80.5 |                75.5 |    69.2 |                  62.5 |      77.2 |

## Accuracy by category / gold reason - Llama-3.1-8B-Instruct

| condition        |   completion |   conditional |   revocation |   static |   ambiguous |   cancelled |   completed |   guard_unmet |   prohibited_active |   ready |   retry_after_failure |   revoked |
|:-----------------|-------------:|--------------:|-------------:|---------:|------------:|------------:|------------:|--------------:|--------------------:|--------:|----------------------:|----------:|
| full             |         71.6 |          75   |         88.6 |     91   |        84.1 |        67.9 |        55.9 |          78.1 |                93.6 |    75   |                  93.8 |      79.3 |
| summary          |         74.1 |          67.7 |         78.8 |     75   |        77.3 |        50   |        70.6 |          67.2 |                74.5 |    80.8 |                  79.2 |      80.4 |
| pinning          |         68.1 |          60   |         72.3 |     67.4 |        77.3 |        53.6 |        69.1 |          59.4 |                67.2 |    69.2 |                  66.7 |      69.6 |
| chrono           |         69.8 |          66.8 |         84.8 |     88.2 |        93.2 |        28.6 |        54.4 |          66.4 |                89.2 |    86.5 |                  91.7 |      75   |
| typed_llm        |         74.1 |          54.1 |         78.8 |     77.1 |        93.2 |        35.7 |        70.6 |          53.1 |                75   |    57.7 |                  79.2 |      79.3 |
| lifecycle        |         77.6 |          46.4 |         91.3 |     77.8 |        93.2 |        46.4 |        75   |          37.5 |                79.9 |    61.5 |                  81.2 |      92.4 |
| lifecycle_gold   |         80.2 |          71.8 |         90.2 |     86.1 |        97.7 |        50   |        76.5 |          72.7 |                84.8 |    75   |                  85.4 |      93.5 |
| abl_noguard      |         76.7 |          64.5 |         90.8 |     81.2 |        93.2 |        53.6 |        75   |          61.7 |                81.4 |    75   |                  79.2 |      93.5 |
| abl_noreceipt    |         68.1 |          47.7 |         88   |     77.1 |        97.7 |        53.6 |        73.5 |          37.5 |                77.9 |    59.6 |                  60.4 |      89.1 |
| lifecycle_strict |         76.7 |          63.6 |         89.1 |     81.2 |        97.7 |        46.4 |        73.5 |          63.3 |                80.9 |    67.3 |                  81.2 |      91.3 |

## Accuracy by compactions since the item's last transition (0,1,2,3+)

|                                               |    0 |    1 |    2 |    3 |
|:----------------------------------------------|-----:|-----:|-----:|-----:|
| ('Llama-3.1-8B-Instruct', 'abl_noguard')      | 84   | 71.8 | 78.3 | 65.8 |
| ('Llama-3.1-8B-Instruct', 'abl_noreceipt')    | 77.1 | 61.2 | 71.1 | 52.6 |
| ('Llama-3.1-8B-Instruct', 'chrono')           | 84   | 72.9 | 74.7 | 55.3 |
| ('Llama-3.1-8B-Instruct', 'full')             | 81.9 | 83.5 | 77.1 | 76.3 |
| ('Llama-3.1-8B-Instruct', 'lifecycle')        | 77.1 | 63.5 | 74.7 | 68.4 |
| ('Llama-3.1-8B-Instruct', 'lifecycle_gold')   | 87.8 | 74.9 | 80.7 | 78.9 |
| ('Llama-3.1-8B-Instruct', 'lifecycle_strict') | 84.4 | 69.8 | 79.5 | 60.5 |
| ('Llama-3.1-8B-Instruct', 'pinning')          | 82.6 | 53.3 | 55.4 | 55.3 |
| ('Llama-3.1-8B-Instruct', 'summary')          | 87.2 | 62.7 | 67.5 | 55.3 |
| ('Llama-3.1-8B-Instruct', 'typed_llm')        | 76.7 | 62.4 | 72.3 | 55.3 |
| ('Qwen2.5-7B-Instruct', 'abl_noguard')        | 77.1 | 75.7 | 63.9 | 71.1 |
| ('Qwen2.5-7B-Instruct', 'abl_noreceipt')      | 81.9 | 72.5 | 59   | 68.4 |
| ('Qwen2.5-7B-Instruct', 'chrono')             | 76.7 | 68.6 | 56.6 | 55.3 |
| ('Qwen2.5-7B-Instruct', 'full')               | 64.6 | 59.6 | 51.8 | 52.6 |
| ('Qwen2.5-7B-Instruct', 'lifecycle')          | 81.2 | 75.3 | 67.5 | 65.8 |
| ('Qwen2.5-7B-Instruct', 'lifecycle_gold')     | 82.6 | 85.1 | 74.7 | 92.1 |
| ('Qwen2.5-7B-Instruct', 'lifecycle_strict')   | 81.2 | 75.7 | 60.2 | 73.7 |
| ('Qwen2.5-7B-Instruct', 'pinning')            | 71.5 | 62   | 53   | 47.4 |
| ('Qwen2.5-7B-Instruct', 'summary')            | 69.1 | 58.8 | 42.2 | 39.5 |
| ('Qwen2.5-7B-Instruct', 'typed_llm')          | 74.7 | 66.7 | 62.7 | 57.9 |

## Accuracy by number of compactions in the dialogue

|                                               |    1 |    2 |    3 |    5 |
|:----------------------------------------------|-----:|-----:|-----:|-----:|
| ('Llama-3.1-8B-Instruct', 'abl_noguard')      | 78.3 | 80.1 | 75.9 | 75.9 |
| ('Llama-3.1-8B-Instruct', 'abl_noreceipt')    | 74.7 | 70.5 | 65.1 | 65.1 |
| ('Llama-3.1-8B-Instruct', 'chrono')           | 78.9 | 80.7 | 73.5 | 74.7 |
| ('Llama-3.1-8B-Instruct', 'full')             | 85.5 | 77.7 | 85.5 | 77.7 |
| ('Llama-3.1-8B-Instruct', 'lifecycle')        | 75.9 | 71.7 | 69.3 | 67.5 |
| ('Llama-3.1-8B-Instruct', 'lifecycle_gold')   | 83.7 | 83.7 | 77.7 | 80.7 |
| ('Llama-3.1-8B-Instruct', 'lifecycle_strict') | 77.1 | 82.5 | 73.5 | 74.1 |
| ('Llama-3.1-8B-Instruct', 'pinning')          | 75.3 | 64.5 | 59.6 | 66.3 |
| ('Llama-3.1-8B-Instruct', 'summary')          | 80.1 | 72.9 | 69.3 | 71.7 |
| ('Llama-3.1-8B-Instruct', 'typed_llm')        | 73.5 | 69.9 | 64.5 | 69.9 |
| ('Qwen2.5-7B-Instruct', 'abl_noguard')        | 72.9 | 75.3 | 77.1 | 72.9 |
| ('Qwen2.5-7B-Instruct', 'abl_noreceipt')      | 74.1 | 77.1 | 75.9 | 71.7 |
| ('Qwen2.5-7B-Instruct', 'chrono')             | 70.5 | 72.9 | 74.7 | 61.4 |
| ('Qwen2.5-7B-Instruct', 'full')               | 56   | 61.4 | 60.8 | 63.3 |
| ('Qwen2.5-7B-Instruct', 'lifecycle')          | 76.5 | 78.3 | 78.9 | 71.7 |
| ('Qwen2.5-7B-Instruct', 'lifecycle_gold')     | 80.7 | 85.5 | 83.1 | 83.1 |
| ('Qwen2.5-7B-Instruct', 'lifecycle_strict')   | 75.3 | 78.9 | 78.9 | 71.1 |
| ('Qwen2.5-7B-Instruct', 'pinning')            | 64.5 | 68.1 | 62.7 | 61.4 |
| ('Qwen2.5-7B-Instruct', 'summary')            | 62.7 | 60.8 | 61.4 | 55.4 |
| ('Qwen2.5-7B-Instruct', 'typed_llm')          | 69.9 | 72.3 | 71.1 | 63.3 |

## RQ1: state-recall error composition (share of probes)

| model                 | condition        | mutable   |   n |   correct |   stale |   missing |   other |
|:----------------------|:-----------------|:----------|----:|----------:|--------:|----------:|--------:|
| Llama-3.1-8B-Instruct | full             | False     | 168 |     0.839 |   0     |     0     |   0.161 |
| Llama-3.1-8B-Instruct | full             | True      | 496 |     0.734 |   0.139 |     0     |   0.127 |
| Llama-3.1-8B-Instruct | summary          | False     | 168 |     0.595 |   0     |     0.065 |   0.339 |
| Llama-3.1-8B-Instruct | summary          | True      | 496 |     0.663 |   0.091 |     0.036 |   0.21  |
| Llama-3.1-8B-Instruct | pinning          | False     | 168 |     0.685 |   0     |     0.018 |   0.298 |
| Llama-3.1-8B-Instruct | pinning          | True      | 496 |     0.615 |   0.127 |     0.004 |   0.254 |
| Llama-3.1-8B-Instruct | chrono           | False     | 168 |     0.536 |   0     |     0.024 |   0.44  |
| Llama-3.1-8B-Instruct | chrono           | True      | 496 |     0.722 |   0.052 |     0.006 |   0.22  |
| Llama-3.1-8B-Instruct | typed_llm        | False     | 168 |     0.78  |   0     |     0.024 |   0.196 |
| Llama-3.1-8B-Instruct | typed_llm        | True      | 496 |     0.673 |   0.109 |     0.006 |   0.212 |
| Llama-3.1-8B-Instruct | lifecycle        | False     | 168 |     0.762 |   0     |     0.012 |   0.226 |
| Llama-3.1-8B-Instruct | lifecycle        | True      | 496 |     0.768 |   0.105 |     0.004 |   0.123 |
| Llama-3.1-8B-Instruct | lifecycle_gold   | False     | 168 |     0.798 |   0     |     0.018 |   0.185 |
| Llama-3.1-8B-Instruct | lifecycle_gold   | True      | 496 |     0.847 |   0.093 |     0     |   0.06  |
| Llama-3.1-8B-Instruct | abl_noguard      | False     | 168 |     0.762 |   0     |     0.012 |   0.226 |
| Llama-3.1-8B-Instruct | abl_noguard      | True      | 496 |     0.776 |   0.091 |     0.004 |   0.129 |
| Llama-3.1-8B-Instruct | abl_noreceipt    | False     | 168 |     0.75  |   0     |     0.006 |   0.244 |
| Llama-3.1-8B-Instruct | abl_noreceipt    | True      | 496 |     0.716 |   0.111 |     0.006 |   0.167 |
| Llama-3.1-8B-Instruct | lifecycle_strict | False     | 168 |     0.804 |   0     |     0.006 |   0.19  |
| Llama-3.1-8B-Instruct | lifecycle_strict | True      | 496 |     0.754 |   0.109 |     0.006 |   0.131 |
| Qwen2.5-7B-Instruct   | full             | False     | 168 |     0.685 |   0     |     0     |   0.315 |
| Qwen2.5-7B-Instruct   | full             | True      | 496 |     0.752 |   0.131 |     0     |   0.117 |
| Qwen2.5-7B-Instruct   | summary          | False     | 168 |     0.667 |   0     |     0.119 |   0.214 |
| Qwen2.5-7B-Instruct   | summary          | True      | 496 |     0.637 |   0.089 |     0.06  |   0.214 |
| Qwen2.5-7B-Instruct   | pinning          | False     | 168 |     0.81  |   0     |     0.036 |   0.155 |
| Qwen2.5-7B-Instruct   | pinning          | True      | 496 |     0.635 |   0.103 |     0.042 |   0.22  |
| Qwen2.5-7B-Instruct   | chrono           | False     | 168 |     0.774 |   0     |     0.024 |   0.202 |
| Qwen2.5-7B-Instruct   | chrono           | True      | 496 |     0.728 |   0.044 |     0.018 |   0.21  |
| Qwen2.5-7B-Instruct   | typed_llm        | False     | 168 |     0.869 |   0     |     0.012 |   0.119 |
| Qwen2.5-7B-Instruct   | typed_llm        | True      | 496 |     0.679 |   0.065 |     0.01  |   0.246 |
| Qwen2.5-7B-Instruct   | lifecycle        | False     | 168 |     0.917 |   0     |     0.006 |   0.077 |
| Qwen2.5-7B-Instruct   | lifecycle        | True      | 496 |     0.865 |   0.052 |     0.012 |   0.071 |
| Qwen2.5-7B-Instruct   | lifecycle_gold   | False     | 168 |     0.923 |   0     |     0     |   0.077 |
| Qwen2.5-7B-Instruct   | lifecycle_gold   | True      | 496 |     0.911 |   0.042 |     0     |   0.046 |
| Qwen2.5-7B-Instruct   | abl_noguard      | False     | 168 |     0.917 |   0     |     0     |   0.083 |
| Qwen2.5-7B-Instruct   | abl_noguard      | True      | 496 |     0.821 |   0.046 |     0.014 |   0.119 |
| Qwen2.5-7B-Instruct   | abl_noreceipt    | False     | 168 |     0.893 |   0     |     0.006 |   0.101 |
| Qwen2.5-7B-Instruct   | abl_noreceipt    | True      | 496 |     0.815 |   0.046 |     0.01  |   0.129 |
| Qwen2.5-7B-Instruct   | lifecycle_strict | False     | 168 |     0.905 |   0     |     0     |   0.095 |
| Qwen2.5-7B-Instruct   | lifecycle_strict | True      | 496 |     0.869 |   0.046 |     0.008 |   0.077 |

### Same, restricted to probes with >=1 compaction since the item was created

|                                                      |   correct |   missing |   other |   stale |
|:-----------------------------------------------------|----------:|----------:|--------:|--------:|
| ('Llama-3.1-8B-Instruct', 'abl_noguard', False)      |     0.678 |     0.017 |   0.306 |   0     |
| ('Llama-3.1-8B-Instruct', 'abl_noguard', True)       |     0.76  |     0.005 |   0.14  |   0.096 |
| ('Llama-3.1-8B-Instruct', 'abl_noreceipt', False)    |     0.661 |     0.008 |   0.331 |   0     |
| ('Llama-3.1-8B-Instruct', 'abl_noreceipt', True)     |     0.691 |     0.007 |   0.181 |   0.12  |
| ('Llama-3.1-8B-Instruct', 'chrono', False)           |     0.43  |     0.033 |   0.537 |   0     |
| ('Llama-3.1-8B-Instruct', 'chrono', True)            |     0.691 |     0.007 |   0.245 |   0.056 |
| ('Llama-3.1-8B-Instruct', 'full', False)             |     0.851 |     0     |   0.149 |   0     |
| ('Llama-3.1-8B-Instruct', 'full', True)              |     0.716 |     0     |   0.127 |   0.157 |
| ('Llama-3.1-8B-Instruct', 'lifecycle', False)        |     0.678 |     0.017 |   0.306 |   0     |
| ('Llama-3.1-8B-Instruct', 'lifecycle', True)         |     0.748 |     0.005 |   0.137 |   0.11  |
| ('Llama-3.1-8B-Instruct', 'lifecycle_gold', False)   |     0.736 |     0.025 |   0.24  |   0     |
| ('Llama-3.1-8B-Instruct', 'lifecycle_gold', True)    |     0.828 |     0     |   0.071 |   0.1   |
| ('Llama-3.1-8B-Instruct', 'lifecycle_strict', False) |     0.736 |     0.008 |   0.256 |   0     |
| ('Llama-3.1-8B-Instruct', 'lifecycle_strict', True)  |     0.73  |     0.007 |   0.145 |   0.118 |
| ('Llama-3.1-8B-Instruct', 'pinning', False)          |     0.595 |     0.025 |   0.38  |   0     |
| ('Llama-3.1-8B-Instruct', 'pinning', True)           |     0.578 |     0.005 |   0.275 |   0.142 |
| ('Llama-3.1-8B-Instruct', 'summary', False)          |     0.471 |     0.091 |   0.438 |   0     |
| ('Llama-3.1-8B-Instruct', 'summary', True)           |     0.63  |     0.044 |   0.228 |   0.098 |
| ('Llama-3.1-8B-Instruct', 'typed_llm', False)        |     0.736 |     0.033 |   0.231 |   0     |
| ('Llama-3.1-8B-Instruct', 'typed_llm', True)         |     0.637 |     0.007 |   0.238 |   0.118 |
| ('Qwen2.5-7B-Instruct', 'abl_noguard', False)        |     0.901 |     0     |   0.099 |   0     |
| ('Qwen2.5-7B-Instruct', 'abl_noguard', True)         |     0.806 |     0.017 |   0.127 |   0.049 |
| ('Qwen2.5-7B-Instruct', 'abl_noreceipt', False)      |     0.893 |     0.008 |   0.099 |   0     |
| ('Qwen2.5-7B-Instruct', 'abl_noreceipt', True)       |     0.799 |     0.012 |   0.14  |   0.049 |
| ('Qwen2.5-7B-Instruct', 'chrono', False)             |     0.76  |     0.033 |   0.207 |   0     |
| ('Qwen2.5-7B-Instruct', 'chrono', True)              |     0.701 |     0.022 |   0.235 |   0.042 |
| ('Qwen2.5-7B-Instruct', 'full', False)               |     0.669 |     0     |   0.331 |   0     |
| ('Qwen2.5-7B-Instruct', 'full', True)                |     0.738 |     0     |   0.118 |   0.145 |
| ('Qwen2.5-7B-Instruct', 'lifecycle', False)          |     0.901 |     0.008 |   0.091 |   0     |
| ('Qwen2.5-7B-Instruct', 'lifecycle', True)           |     0.853 |     0.015 |   0.076 |   0.056 |
| ('Qwen2.5-7B-Instruct', 'lifecycle_gold', False)     |     0.926 |     0     |   0.074 |   0     |
| ('Qwen2.5-7B-Instruct', 'lifecycle_gold', True)      |     0.909 |     0     |   0.047 |   0.044 |
| ('Qwen2.5-7B-Instruct', 'lifecycle_strict', False)   |     0.893 |     0     |   0.107 |   0     |
| ('Qwen2.5-7B-Instruct', 'lifecycle_strict', True)    |     0.858 |     0.01  |   0.083 |   0.049 |
| ('Qwen2.5-7B-Instruct', 'pinning', False)            |     0.826 |     0.05  |   0.124 |   0     |
| ('Qwen2.5-7B-Instruct', 'pinning', True)             |     0.598 |     0.051 |   0.238 |   0.113 |
| ('Qwen2.5-7B-Instruct', 'summary', False)            |     0.636 |     0.165 |   0.198 |   0     |
| ('Qwen2.5-7B-Instruct', 'summary', True)             |     0.596 |     0.074 |   0.238 |   0.093 |
| ('Qwen2.5-7B-Instruct', 'typed_llm', False)          |     0.843 |     0.017 |   0.14  |   0     |
| ('Qwen2.5-7B-Instruct', 'typed_llm', True)           |     0.654 |     0.012 |   0.265 |   0.069 |

## RQ3: error attribution (share of all probes)

|                                               |   bad extraction |   bad transition |   wrong action | correct recall |   wrong action | correct state |   wrong recall |
|:----------------------------------------------|-----------------:|-----------------:|--------------------------------:|-------------------------------:|---------------:|
| ('Llama-3.1-8B-Instruct', 'abl_noguard')      |              9.2 |              0   |                             0   |                           13.3 |            0   |
| ('Llama-3.1-8B-Instruct', 'abl_noreceipt')    |             14.2 |              2   |                             0   |                           15.1 |            0   |
| ('Llama-3.1-8B-Instruct', 'chrono')           |              0   |              0   |                            13.9 |                            0   |            9.2 |
| ('Llama-3.1-8B-Instruct', 'full')             |              0   |              0   |                            12.5 |                            0   |            5.9 |
| ('Llama-3.1-8B-Instruct', 'lifecycle')        |             13.7 |              0   |                             0   |                           15.2 |            0   |
| ('Llama-3.1-8B-Instruct', 'lifecycle_gold')   |              0   |              0   |                             0   |                           18.5 |            0   |
| ('Llama-3.1-8B-Instruct', 'lifecycle_strict') |              7.2 |              0   |                             0   |                           16   |            0   |
| ('Llama-3.1-8B-Instruct', 'pinning')          |              0   |              0   |                            17.5 |                            0   |           16.1 |
| ('Llama-3.1-8B-Instruct', 'summary')          |              0   |              0   |                            14.5 |                            0   |           12   |
| ('Llama-3.1-8B-Instruct', 'typed_llm')        |             13.1 |              4.5 |                             0   |                           13   |            0   |
| ('Qwen2.5-7B-Instruct', 'abl_noguard')        |              9.5 |              2.3 |                             0   |                           13.7 |            0   |
| ('Qwen2.5-7B-Instruct', 'abl_noreceipt')      |              9.9 |              3.5 |                             0   |                           11.9 |            0   |
| ('Qwen2.5-7B-Instruct', 'chrono')             |              0   |              0   |                            18.1 |                            0   |           12   |
| ('Qwen2.5-7B-Instruct', 'full')               |              0   |              0   |                            25.3 |                            0   |           14.3 |
| ('Qwen2.5-7B-Instruct', 'lifecycle')          |              9.2 |              0   |                             0   |                           14.5 |            0   |
| ('Qwen2.5-7B-Instruct', 'lifecycle_gold')     |              0   |              0   |                             0   |                           16.9 |            0   |
| ('Qwen2.5-7B-Instruct', 'lifecycle_strict')   |              9.8 |              0   |                             0   |                           14.2 |            0   |
| ('Qwen2.5-7B-Instruct', 'pinning')            |              0   |              0   |                            19.6 |                            0   |           16.3 |
| ('Qwen2.5-7B-Instruct', 'summary')            |              0   |              0   |                            19.6 |                            0   |           20.3 |
| ('Qwen2.5-7B-Instruct', 'typed_llm')          |              9.3 |             11.7 |                             0   |                            9.8 |            0   |

## Extraction quality (turn-level, vs gold events)

- Qwen2.5-7B-Instruct: P=0.865 R=0.824 F1=0.844; per-op F1 prohibit=0.89, commit=0.83, tool_result=0.72, cancel=0.97, approve=0.87, ambiguous=0.82, revoke=0.79
- Llama-3.1-8B-Instruct: P=0.806 R=0.825 F1=0.815; per-op F1 prohibit=0.91, commit=0.80, tool_result=0.92, cancel=0.95, approve=0.54, revoke=0.96, ambiguous=0.72

## Cost (per run)

| Model | wall time (min) | GPU | calls | prompt tokens | completion tokens |
|---|---|---|---|---|---|
| Qwen2.5-7B-Instruct | 0.8 | NVIDIA RTX 6000 Ada Generation, 49140 MiB | 4061 | 4200821 | 119383 |
  - per component calls: extract=2337, summary=396, policy=664, state_query=664
| Llama-3.1-8B-Instruct | 2.1 | NVIDIA RTX 6000 Ada Generation, 49140 MiB | 4061 | 4322251 | 164488 |
  - per component calls: extract=2337, summary=396, policy=664, state_query=664
